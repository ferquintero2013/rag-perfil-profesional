# Chat con mi perfil profesional: RAG sobre CV y portafolio

Chatbot RAG que responde preguntas sobre la trayectoria profesional de Ferney Quintero,
usando unicamente su CV y portafolio como fuente, con citacion obligatoria de la fuente
de cada afirmacion.

**Demo en vivo:** https://chat-perfil-ferney.streamlit.app/

---

## Que problema resuelve

Un reclutador que quiere saber si un candidato encaja tiene que leer un CV completo y
deducir la respuesta. Este sistema permite preguntar directamente:

- *"¿Tiene experiencia con Python?"*
- *"¿Ha trabajado con clientes reales en automatizacion?"*
- *"¿Que sabe de Odoo?"*

Y obtener una respuesta corta, precisa y **verificable**: cada afirmacion cita el archivo
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
   |  indexer.py     <- embeddings (text-embedding-3-small)
   v
index_vectors.npy  (matriz 98 x 1536, float32, 588 KB)
index_meta.json    (de que archivo y seccion salio cada fila)

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
respuesta + fuentes citadas
```

El mismo motor corre en tres sitios sin cambiar de logica. Lo unico distinto
es el adaptador que traduce la peticion de cada plataforma:

| Donde | Adaptador | Como llega el codigo |
|---|---|---|
| Local | `app.py` (Streamlit) y `api.py` (FastAPI) | se importa directo |
| Vercel | `api/ask.py`, en el repositorio del portafolio | lo copia `sync_api.py` |
| AWS | `aws/handler.py` | va dentro de la imagen de contenedor |

Que el motor sea portable no es suerte: es consecuencia de que la logica nunca
supo quien la invocaba.

| Modulo | Responsabilidad |
|--------|-----------------|
| `sync_data.py` | Copia a `data/` solo los archivos de una allowlist explicita |
| `loader.py` | Carga los `.md` y los parte en chunks por headers `##` / `###` |
| `indexer.py` | Genera embeddings y guarda la matriz en `.npy` mas los metadatos en `.json` |
| `retriever.py` | Busqueda hibrida (vectorial + BM25) fusionada con RRF |
| `rag.py` | Reescribe la pregunta, ensambla contexto, genera respuesta y filtra fuentes citadas |
| `app.py` | Interfaz de chat en Streamlit, solo para desarrollo local |
| `aws/handler.py` | Adaptador de Lambda: traduce `(event, context)` a la misma llamada |
| `aws/terraform/` | Toda la infraestructura de AWS declarada como codigo |

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

**Causa:** ese chunk describe un sistema de validacion documental: Vision AI, cross-check
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
real, y el costo de una respuesta imprecisa es mucho mayor que la diferencia de precio
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
pregunta reinterpretada se muestra en la UI, y poder ver los pasos intermedios es lo que
hace debuggeable un sistema de IA.

---

## Stack

- **Python 3.12** en produccion, 3.14 en local
- **OpenAI**: `text-embedding-3-small` (embeddings) y `gpt-4o` (generacion)
- **numpy**: el indice es una matriz de 98 x 1536 en float32, y la busqueda
  semantica es un producto matricial. Con un corpus de este tamano, una base
  vectorial seria infraestructura sin trabajo que hacer
- **rank-bm25**: busqueda por palabras clave
- **Streamlit**: interfaz local de desarrollo
- **AWS**: Lambda sobre imagen de contenedor, ECR, S3, IAM, CloudWatch
- **Terraform**: la infraestructura de AWS, declarada

Construido con Claude Code como companero de desarrollo.

---

## Despliegue: el mismo sistema en Vercel y en AWS

El asistente corre en dos sitios a la vez. Vercel es el despliegue oficial, el
que usa el portafolio. AWS es el mismo codigo sobre Lambda, con la
infraestructura declarada en Terraform.

Se hizo por una razon concreta: en dos semanas aparecieron cuatro ofertas senior
de IA y las cuatro pedian lo mismo, que no era LLMs ni RAG sino cloud e
infraestructura. Migrar algo que ya funcionaba parecia mejor prueba que empezar
un proyecto nuevo.

```
Vercel                          AWS
------                          ---
funcion Python                  Lambda desde imagen de contenedor
indice en el repositorio        indice en S3, descargado al arrancar
clave en variable de entorno    rol IAM con s3:GetObject sobre un prefijo
logs de la plataforma           CloudWatch, 14 dias de retencion
deploy = git push               deploy = git push, por GitHub Actions
configurado en una consola      11 recursos en Terraform
```

### Lo que midio la migracion

Medido el 2026-11-07 desde Bogota contra `us-east-1`, con preguntas reales y
distintas en cada llamada.

| | Vercel | AWS Lambda |
|---|---|---|
| Primera peticion | 6294 ms | 8700 ms |
| Peticiones siguientes | 2266 ms | 3004 ms |

Dentro de Lambda, donde CloudWatch separa el arranque del trabajo:

```
arranque en frio   Init 2505 ms  +  primera peticion 5514 ms
peticiones calidas 2475 a 2765 ms
```

**La conclusion honesta es que la migracion no mejoro la latencia.** Vercel
salio igual o un poco mejor. Y tiene sentido: entre dos y tres segundos de cada
respuesta son las dos llamadas a OpenAI, una para convertir la pregunta en
embedding y otra para redactar. Eso se paga igual en cualquier plataforma. Lo
que la infraestructura aporta son milisegundos sobre un cuello de botella que
esta en otro sitio.

Quien migre esperando velocidad se va a llevar una decepcion. Lo que se gana es
otra cosa: control de la infraestructura, permisos explicitos, observabilidad
con retencion y techos de gasto.

### La medicion que corrigio una suposicion

La configuracion inicial fueron 1024 MB de memoria, con el argumento de que en
Lambda la memoria tambien asigna CPU y por tanto acelera el arranque. Suena
bien y se repite mucho. Aqui resulto falso.

Cuatro arranques en frio por tamano, mediana del `Init Duration`:

| Memoria | Arranque en frio |
|---|---|
| 512 MB | 2267 ms |
| 1024 MB | 2240 ms |
| 1769 MB | 2249 ms |
| 2048 MB | 2232 ms |

35 ms de diferencia entre el menor y el mayor, con el cuadruple de memoria. La
dispersion dentro de un mismo tamano fue de 617 ms, casi veinte veces mayor que
el efecto que se buscaba. Incluso 1769 MB, que es el umbral donde Lambda asigna
una vCPU completa, quedo dentro del ruido.

El motivo es que este arranque no gasta CPU. Baja una imagen, importa numpy y
trae 593 KB de S3: es espera de entrada y salida, y la CPU de mas no acelera una
espera. El `Max Memory Used` en produccion son 182 MB.

**Se bajo a 512 MB**, que cuesta la mitad por milisegundo y rinde igual.

Vale la pena dejarlo escrito tal cual, porque el comentario original del
Terraform afirmaba lo contrario sin una sola medicion detras.

### Costo

```
imagen en ECR        224.7 MB
indice en S3         593 KB
memoria x duracion   0.5 GB x ~2.5 s = 1.25 GB-s por peticion
```

> Las cifras de esta seccion y de la anterior son las del dia de la medicion,
> el 2026-11-07. El indice ha crecido despues a 98 fragmentos y 687 KB al
> incorporar esta misma migracion al corpus. No se reescriben hacia atras:
> una medicion vale por las condiciones en que se tomo.

La capa gratuita de Lambda es de 1 millon de peticiones y 400.000 GB-segundo al
mes, y no caduca. A 1,25 GB-segundo por peticion, eso cubre unas 320.000
preguntas mensuales. S3 y CloudWatch a este volumen son centavos, y ECR pasa a
costar unos 0,02 USD al mes cuando termine el primer ano.

El costo real del sistema es OpenAI, y es identico en las dos plataformas.

### Lo que costo caro

Una Function URL publica necesita **dos** permisos, no uno:

```
lambda:InvokeFunctionUrl   con la condicion FunctionUrlAuthType = NONE
lambda:InvokeFunction      sin condicion (AWS la rechaza si se pone)
```

Con solo el primero, la URL devuelve `403 AccessDeniedException` a todo el mundo
y la funcion ni se entera: la peticion muere en el borde sin dejar una linea en
CloudWatch. La documentacion de AWS describe el primero. La consola crea los dos
en silencio, de donde sale el clasico "desde la consola funciona pero por codigo
no".

Se descartaron antes, con evidencia: politica corrupta, URL en mal estado, SCP
de Organization, qualifier desalineado, concurrencia en cero y problema del
cliente HTTP. La causa se demostro quitando el permiso y viendo volver el 403,
no suponiendo.

### La deriva que la migracion provoco, y como se cerro

El motor vive en un solo sitio, pero tiene que llegar a tres: local, Vercel y
Lambda. Y los tres necesitan el codigo con nombres distintos, porque Vercel
convierte en endpoint publico cualquier `.py` dentro de `/api/` que no empiece
por guion bajo.

Para Vercel habia un script, `sync_api.py`. Para AWS no: esa copia se hizo a
mano al crear `aws/`. El resultado aparecio al revisar antes de escribir esto:

```
retriever.py          (fuente, con la rama de S3)
aws/_retriever.py     identico a la fuente
api/_retriever.py     62 lineas de diferencia, sin la rama de S3
```

Vercel llevaba dias sirviendo una version anterior del retriever. No se noto
porque la rama vieja lee del disco, que es justo lo que Vercel necesita, asi
que el sistema funcionaba. Habria explotado con la primera correccion de un
bug que importara, aplicada en un sitio y no en el otro.

`sync_api.py` ahora distribuye a los dos destinos con el conjunto de archivos
que corresponde a cada uno: Vercel recibe el indice al lado del codigo, AWS no,
porque lo baja de S3. El modulo de registro, que antes solo existia duplicado
en los dos destinos sin fuente en ninguna parte, pasa a tener la suya en
`log.py`.

La leccion no es que faltara un script. Es que **anadir un despliegue sin
extender el mecanismo de distribucion crea una copia huerfana**, y una copia
huerfana que funciona es peor que una que falla, porque nadie la mira.

### El despliegue, de manual a automatico

Durante la migracion el despliegue a AWS fue manual: construir la imagen,
subirla a ECR y llamar a `update-function-code`, en ese orden y sin olvidar
ninguno de los tres. Funciona mientras lo haga una sola persona que se acuerde.
Ahora lo hace un workflow en cada push a `main` que toque `aws/`.

La autenticacion es por OIDC, sin claves guardadas en el repositorio. GitHub
emite un token firmado en cada ejecucion y AWS lo cambia por credenciales
temporales que duran lo que dure el job. Es el mismo principio que ya usaba la
funcion: identidades que asumen un rol, no credenciales permanentes.

La imagen se etiqueta con el SHA del commit, no solo con `latest`, para poder
saber que version esta corriendo mirando la funcion. Eso obligo a declarar
quien es dueno de que: `ignore_changes` sobre `image_uri`, porque Terraform es
dueno de la infraestructura y el pipeline es dueno de la version del codigo.
Sin esa linea, el siguiente `apply` revertiria el despliegue.

Cierra con una prueba de humo que invoca con el cuerpo vacio y exige un 400.
Para contestar ese 400, Lambda tuvo que bajar la imagen nueva, importar numpy y
traer el indice de S3, asi que verifica el arranque completo sin gastar un solo
token.

**Los dos fallos del primer intento valen mas que el resultado.**

El primero fue un `AccessDenied` al asumir el rol, sin mas explicacion. El log
del workflow no podia decir mas, porque el rechazo ocurre del lado de AWS y AWS
no explica por que rechaza. El evento de `AssumeRoleWithWebIdentity` en
CloudTrail si traia el `sub` que GitHub habia presentado de verdad:

```
repo:ferquintero2013@118778024/rag-perfil-profesional@1361957228:ref:refs/heads/main
```

GitHub ya no manda `propietario/repositorio`: manda los identificadores
internos, que no cambian nunca. La condicion escrita a mano ataba el permiso a
un nombre, la real lo ata a una identidad, y un repositorio borrado y vuelto a
crear con el mismo nombre no la hereda.

El segundo fue `The image manifest, config or layer media type is not
supported`. Un `docker build` normal en un runner moderno usa BuildKit, que
adjunta atestaciones de procedencia, convirtiendo lo subido en una lista de
manifiestos, y escribe en formato OCI. Lambda quiere un manifiesto solo y en
formato Docker, manifest v2 schema 2.

Ninguno de los dos se ve al construir en local. Los dos aparecen al desplegar.

### La misma leccion, otra vez

Arriba esta escrito en negrita que **anadir un despliegue sin extender el
mecanismo de distribucion crea una copia huerfana**. Una semana despues de
escribirlo, el mismo error con otra victima.

`actualizar.py` existe, segun su propio docstring, "para que no haya que
acordarse de los cinco" eslabones de la cadena. Eran cinco y faltaba uno. El
indice reconstruido llegaba a Vercel, porque `sync_api.py` lo copia al lado del
codigo en el repositorio del portafolio. A Lambda no llegaba nunca: alli el
indice no viaja en la imagen, vive en S3, y ningun paso lo subia.

Lo grave no es que fallara. Es que no fallaba:

```
$ python actualizar.py
  [1] Copiar del perfil al corpus publico      OK
  [2] Regenerar embeddings e indice            OK
  [3] Comprobar que sigue respondiendo bien    25/25
  [4] Copiar el motor al repositorio           OK
  Listo.
```

Cadena en verde, y Lambda respondiendo con el perfil de la semana anterior. Se
descubrio usando el sistema, no leyendolo: preguntarle al endpoint por CI/CD
devolvio "no hay evidencia de que Ferney tenga experiencia directa con CI/CD"
el dia despues de haber montado el pipeline.

Lo cierra `publicar_indice.py`, como paso 5. Tres decisiones dentro:

- **El nombre del bucket no esta escrito en el script.** Sale de
  `terraform output -raw bucket_indice`, o de `INDEX_BUCKET` si esta definida.
  Escribirlo a mano seria una tercera copia del mismo dato, que es la forma en
  que empezo este problema.
- **Falla fuerte a proposito.** La tentacion es tolerar el fallo para que la
  cadena no se corte cuando faltan credenciales. Esa tolerancia es justo el bug
  que el paso vino a cerrar.
- **El mensaje dice cuando se vera el efecto**, no solo que subio: Lambda lee el
  indice al arrancar en frio, asi que un contenedor caliente sigue respondiendo
  con el anterior unos minutos.

Y un tercer hallazgo del mismo tipo: el mensaje de cierre de `sync_api.py`
seguia diciendo que para AWS habia que reconstruir la imagen y correr
`update-function-code` a mano. Dejo de ser verdad el dia que el despliegue paso
a GitHub Actions. **Un mensaje desactualizado es peor que no tener mensaje,
porque se obedece.**

### Una cara para el backend

El backend estaba publico desde el primer despliegue, pero solo hablaba JSON por
POST. Se podia contar y no mostrar, que para un portafolio es casi lo mismo que
no existir.

**Demo:** https://ferquintero2013.github.io/rag-perfil-profesional/

Una pagina en `docs/`, servida por GitHub Pages, que llama a la Function URL.
Sin frameworks, sin CDN, sin fuentes remotas: para un formulario y una lista,
traer 80 KB de libreria seria el mismo error que agregar API Gateway para poder
decir que se uso.

Tres cosas que la pagina hace a proposito:

- **Muestra el tiempo de cada respuesta.** El arranque en frio tarda entre 8 y
  13 segundos y parece una averia si no se explica. Con el numero a la vista,
  deja de ser un sintoma y pasa a ser un dato.
- **Muestra las fuentes citadas.** Es el punto de un RAG: que la respuesta sea
  rastreable. Una demo que solo muestra texto no demuestra nada que un modelo
  suelto no pueda fingir.
- **No esconde el endpoint.** Esta en el codigo del cliente porque no hay otro
  sitio donde pueda estar: una pagina estatica que llama a una API lleva la
  direccion dentro, y meterla en una variable no la oculta de las herramientas
  del navegador. El control del gasto esta del otro lado, en el tope de consumo
  de la cuenta de OpenAI. La Function URL no tiene autenticacion, y eso es una
  decision con su contrapartida, no un descuido.

El origen de GitHub Pages esta en la lista de CORS de la Function URL. Vale la
pena ver como se comporta, porque explica por que CORS se depura en el navegador
y no en los logs del servidor:

```
$ curl -i -X OPTIONS <function-url> -H "Origin: https://ferquintero2013.github.io"
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://ferquintero2013.github.io

$ curl -i -X OPTIONS <function-url> -H "Origin: https://cualquier-otro.example"
HTTP/1.1 200 OK
```

Los dos devuelven 200. La diferencia es la **ausencia** del encabezado en el
segundo, y es el navegador del visitante el que decide bloquear la respuesta por
eso. La funcion responde igual a todo el mundo.

Vercel sigue siendo el portafolio oficial. Esta pagina no lo reemplaza, le pone
cara al otro despliegue.

### Lo que no se hizo, y por que

- **API Gateway.** Aporta autenticacion, limites de tasa y dominios propios, y
  aqui no hace falta nada de eso. Agregarlo solo para poder decir que se uso es
  sobreingenieria.
- **Concurrencia reservada.** Esta escrita y comentada en el Terraform. AWS
  exige dejar al menos 10 ejecuciones sin reservar, y esta cuenta tiene un
  limite total de 10. El techo de la cuenta ya cumple la funcion.
- **Integracion continua.** Lo que hay montado es entrega continua: el pipeline
  construye, publica, despliega y corre una prueba de humo. No hay suite de
  pruebas por pull request ni proteccion de rama, porque el repositorio es de un
  solo autor y exigir aprobaciones bloquearia al unico que puede darlas. Se
  nombra como lo que es en vez de llamarlo CI/CD y esperar que nadie pregunte.
- **CloudFront y dominio propio para la demo.** La pagina se sirve desde GitHub
  Pages, que ya da HTTPS y no cuesta nada. Montar una distribucion para una
  pagina estatica de un portafolio es, otra vez, agregar un servicio para poder
  decir que se uso.
- **Bedrock, evaluaciones en CI y ECS.** Son los siguientes pasos del plan, no
  omisiones de este.

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

> Si editas los archivos de `data/`, hay que volver a correr `python indexer.py`,
> porque si no el indice queda desactualizado y el chatbot responde con la version
> vieja. En AWS hace falta ademas subir el indice nuevo a S3: el despliegue no lo
> arrastra, y esa separacion es justamente lo que permite actualizar el perfil sin
> reconstruir la imagen.

---

## Limitaciones conocidas

- **La reescritura de pregunta anade una llamada extra al LLM** por turno (~0.3s y unos
  pocos centavos por cada mil preguntas). Se salta cuando no hay historial.
- **Corpus pequeno** (99 chunks). Las distancias vectoriales viven en un rango estrecho
  porque todos los documentos hablan de la misma persona, asi que no es viable usar un
  umbral absoluto de distancia; solo el ranking relativo es util.
- **Re-indexado manual.** No hay deteccion automatica de cambios en los archivos fuente.
- **La suite de evaluacion no es un semaforo fiable, y la razon es mas de fondo
  que un juez ruidoso.** Lo primero que se noto fue el juez LLM: dos corridas
  seguidas sobre el mismo indice, sin cambiar una linea en medio, dieron 19/25 y
  22/25 con conjuntos distintos de casos fallidos. Y en una de ellas reprobo un
  caso por hacer exactamente lo que su propio criterio permitia: el criterio de
  "Dame info" dice "debe responder del perfil **o** pedir una aclaracion
  limpia", el asistente respondio del perfil, y el juez lo marco mal por no
  pedir aclaracion.

  La conclusion facil era "el juez es el problema, las aserciones deterministas
  son la compuerta de verdad". Se escribio eso aqui y duro veinte minutos: tres
  corridas de `--sin-juez` sobre el mismo indice dieron PASS, FAIL, FAIL en el
  caso de LangChain. El motivo del fallo:

  ```
  → mood=unsure, esperado ['declined', 'answering']
  respuesta: "Ferney no tiene experiencia documentada con LangChain. Aunque ha
              trabajado con LangGraph, que es una libreria distinta de la misma
              familia, ..."
  ```

  La respuesta era correcta en las tres corridas. Declinaba, no inventaba anos y
  distinguia LangGraph de LangChain. Lo unico que cambiaba era `mood`, que es una
  etiqueta que el modelo se pone a si mismo. **La asercion no es menos
  determinista que el juez: es determinista sobre una entrada que no lo es.**

  Es el mismo error de diseno que aparece en el MVP de validacion documental de
  este portafolio, donde el indice de confianza tambien lo autodeclara el modelo.
  Alli esta mitigado porque la confianza es una de cinco reglas y las otras cuatro
  son deterministas de verdad. Aqui no estaba mitigado: el caso media la etiqueta
  en lugar de medir la respuesta.

  Lo que se puede afirmar hoy, sin adornos: la suite sirve para encontrar
  regresiones reales y ha encontrado varias, pero su tasa de falsos positivos es
  lo bastante alta como para que `actualizar.py` se detenga con frecuencia por
  cosas que no son regresiones, y la decision de continuar la toma quien lee los
  motivos. Para convertirla en compuerta hay dos caminos y los dos estan
  pendientes: afirmar sobre lo que la respuesta dice y no sobre lo que el modelo
  dice de ella, y correr cada caso varias veces en vez de una.

---

## Autor

**Ferney Quintero**, AI Automation Engineer
- Portafolio: https://ferney-portfolio.vercel.app/
- GitHub: https://github.com/ferquintero2013
