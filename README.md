# Chat con mi perfil profesional — RAG sobre CV y portafolio

Chatbot RAG que responde preguntas sobre la trayectoria profesional de Ferney Quintero,
usando unicamente su CV y portafolio como fuente, con citacion obligatoria de la fuente
de cada afirmacion.

**Demo en vivo:** _(pendiente de deploy)_

---

## Que problema resuelve

Un reclutador que quiere saber si un candidato encaja tiene que leer un CV completo y
deducir la respuesta. Este sistema permite preguntar directamente:

- *"¿Tiene experiencia con Python?"*
- *"¿Ha trabajado con clientes reales en automatizacion?"*
- *"¿Que sabe de Odoo?"*

Y obtener una respuesta corta, precisa y **verificable** — cada afirmacion cita el archivo
y la seccion de donde salio.

## Principio de diseno: honestidad sobre optimizacion

El sistema esta construido para **no inflar el perfil**. Si una habilidad esta en
aprendizaje, lo dice. Si un proyecto fue propio y no de cliente, lo distingue. Si una
herramienta se uso via no-code, no la presenta como experiencia en codigo.

Un chatbot que exagera se descubre en la primera entrevista tecnica. El valor de esta
herramienta depende de que sea confiable.

---

## Arquitectura

```
perfil/ (privado)
   |
   |  sync_data.py   <- allowlist explicita: solo lo publico se copia
   v
data/ (corpus publico)
   |
   |  loader.py      <- chunking estructural por headers markdown
   |  indexer.py     <- embeddings (text-embedding-3-small) -> ChromaDB
   v
chroma_db/

Por cada pregunta:

pregunta + historial
   |
   |  rag.rewrite_query()  <- resuelve pronombres y referencias (gpt-4o-mini)
   v
pregunta autonoma
   |
   |  retriever.py         <- busqueda HIBRIDA: semantica + BM25, fusion RRF
   v
chunks relevantes
   |
   |  rag.answer()         <- grounding estricto -> GPT-4o -> respuesta citada
   v
app.py (Streamlit)
```

| Modulo | Responsabilidad |
|--------|-----------------|
| `sync_data.py` | Copia a `data/` solo los archivos de una allowlist explicita |
| `loader.py` | Carga los `.md` y los parte en chunks por headers `##` / `###` |
| `indexer.py` | Genera embeddings y construye el indice en ChromaDB |
| `retriever.py` | Busqueda hibrida (vectorial + BM25) fusionada con RRF |
| `rag.py` | Reescribe la pregunta, ensambla contexto, genera respuesta y filtra fuentes citadas |
| `app.py` | Interfaz de chat en Streamlit |

---

## Decisiones tecnicas y por que

### 1. Chunking estructural, no de tamano fijo

Los documentos fuente son markdown con secciones semanticamente autocontenidas (un
empleo, un proyecto, un grupo de habilidades). Partir por headers respeta esa estructura;
partir cada N caracteres la destruye.

### 2. Busqueda hibrida (el hallazgo mas importante del proyecto)

La primera version usaba solo busqueda semantica. **Fallaba** en la pregunta mas obvia:
*"¿Tiene experiencia con Python?"* no recuperaba el chunk del proyecto construido en
Python.

**Causa:** ese chunk describe un sistema de validacion documental — Vision AI, cross-check
de identidad, reglas de negocio. La palabra "Python" aparece 2 veces entre ~120. Su
centroide semantico apunta a *"sistema de validacion"*, no a *"habilidades en Python"*.

Se probaron y descartaron dos alternativas:
- **HyDE** (respuesta hipotetica como clave de busqueda): empeoro el resultado. El LLM
  invento un perfil generico de dev Python con Pandas y TensorFlow, y la busqueda aterrizo
  en los chunks mas genericos del corpus. Las distancias mejoraron (1.18 -> 0.77) mientras
  la relevancia empeoraba: la metrica media similitud con la alucinacion, no con la pregunta.
- **HyDE con grounding + fusion RRF**: mejora marginal.

**Solucion:** BM25 + busqueda semantica, fusionadas con Reciprocal Rank Fusion. Los
embeddings son fuertes en conceptos y debiles en terminos exactos; BM25 es lo contrario.
Las preguntas de reclutador son mayoritariamente sobre entidades nombradas ("¿sabe X?"),
justo donde la busqueda vectorial pura es mas debil.

### 3. Reciprocal Rank Fusion en lugar de promediar scores

BM25 devuelve scores tipo `4.7`; ChromaDB devuelve distancias tipo `1.13`. Escalas
incomparables. RRF usa solo la **posicion** en cada ranking, asi que no requiere
normalizar nada.

### 4. Se muestran las fuentes *citadas*, no las *recuperadas*

El retriever trae 5 candidatos; el modelo suele usar 1 o 2. Mostrar los 5 como "fuentes"
sugiere que la respuesta salio de todos. `extract_cited()` filtra a las que el modelo
realmente referencio.

### 5. Curacion por allowlist, no por blocklist

`sync_data.py` copia unicamente los archivos de una lista explicita. Un archivo nuevo en
el directorio privado es privado por defecto: publicar es un acto deliberado, no un
descuido posible.

### 6. Modelos segun el costo de equivocarse

`gpt-4o` para generar las respuestas. Es contenido que leen reclutadores sobre una carrera
real — el costo de una respuesta imprecisa es mucho mayor que la diferencia de precio
por token. `gpt-4o-mini` para reescribir preguntas: es una tarea sintactica, no de
razonamiento.

### 7. Query rewriting antes del retrieval, no despues

Para soportar seguimientos (*"¿y en que año?"*) no basta con pasarle el historial al
generador: **la busqueda ocurre antes**. El retriever buscaria literalmente `"y en que
año"` contra el indice y traeria ruido, por mucho historial que reciba despues el modelo.

La solucion es un paso previo que convierte la pregunta en autonoma usando la
conversacion:

```
"¿en que año lo hizo?" + historial  ->  "¿En que año uso Ferney Pinecone en n8n?"
```

Detalles: ventana de 3 turnos (mas historial arrastra temas viejos a preguntas nuevas),
`temperature=0` (la misma pregunta debe producir siempre la misma busqueda), y la
pregunta reinterpretada se muestra en la UI — poder ver los pasos intermedios es lo que
hace debuggeable un sistema de IA.

---

## Stack

- **Python 3.14**
- **Streamlit** — interfaz de chat
- **OpenAI** — `text-embedding-3-small` (embeddings) + `gpt-4o` (generacion)
- **ChromaDB** — base de datos vectorial local y persistente
- **rank-bm25** — busqueda por palabras clave

Construido con Claude Code como companero de desarrollo.

---

## Como correrlo localmente

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

Crear un archivo `.env` en la raiz:

```
OPENAI_API_KEY=sk-tu-api-key
```

Construir el indice y lanzar la app:

```bash
python indexer.py
streamlit run app.py
```

> El indice (`chroma_db/`) no esta versionado porque es regenerable. Si editas los
> archivos de `data/`, hay que volver a correr `python indexer.py` — de lo contrario el
> indice queda desactualizado y el chatbot responde con la version vieja.

---

## Limitaciones conocidas

- **La reescritura de pregunta anade una llamada extra al LLM** por turno (~0.3s y unos
  pocos centavos por cada mil preguntas). Se salta cuando no hay historial.
- **Corpus pequeno** (~37 chunks). Las distancias vectoriales viven en un rango estrecho
  porque todos los documentos hablan de la misma persona, asi que no es viable usar un
  umbral absoluto de distancia; solo el ranking relativo es util.
- **Re-indexado manual.** No hay deteccion automatica de cambios en los archivos fuente.

---

## Autor

**Ferney Quintero** — AI Automation Engineer
- Portafolio: https://ferney-portfolio.vercel.app/
- GitHub: https://github.com/ferquintero2013
