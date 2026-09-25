# Proyecto: asistente de documentacion tecnica con LangGraph

> Periodo: septiembre de 2026. Proyecto propio, codigo abierto.
> Repositorio: https://github.com/ferquintero2013/langgraph-doc-assistant
> Demostracion tecnica independiente construida sobre documentacion publica de terceros. No esta afiliada a la empresa cuya documentacion se uso.

## Que construyo

Un asistente que responde preguntas sobre documentacion tecnica de una API y **muestra como llego a cada respuesta**. El corpus son 503 fragmentos extraidos de 64 paginas de documentacion publica de una plataforma de firma electronica y validacion de identidad.

La diferencia con un RAG convencional esta en la arquitectura. La mayoria son lineales —buscar, responder— y por eso fallan de la peor forma posible: si la busqueda no encuentra lo correcto, el modelo responde igual, con la misma confianza, y quien pregunta no tiene como saberlo.

Aqui la orquestacion es un **grafo de LangGraph con decisiones y ciclos**.

## Arquitectura del grafo

| Nodo | Que decide |
|------|------------|
| Contextualizar | Resuelve la pregunta contra la conversacion previa, ANTES de buscar |
| Buscar | Recuperacion hibrida: BM25 + embeddings, fusionados con Reciprocal Rank Fusion |
| Evaluar | ¿Lo recuperado responde de verdad? Si no, devuelve el control al ciclo |
| Reformular | Traduce la consulta al vocabulario tecnico del producto y reintenta |
| Responder | Redacta unicamente con lo recuperado |
| Verificar | Revisa la respuesta contra las fuentes ANTES de entregarla |
| Declinar | Si la respuesta no queda respaldada, se descarta |

El ciclo `buscar -> evaluar -> reformular -> buscar` es una arista hacia atras en el grafo, con tope de dos intentos.

## Decisiones tecnicas destacadas

**La verificacion es una compuerta del grafo, no una instruccion del prompt.** Pedirle a un modelo "no inventes" es una sugerencia que puede ignorar. Un nodo que compara la respuesta contra las fuentes y la descarta es un control que no depende de su obediencia. Es la diferencia entre pedir y garantizar.

**Chunking contextual.** Cortar la documentacion por encabezados produce fragmentos que pierden la identidad de su pagina: una seccion titulada "Parametros de consulta" es indistinguible de las otras treinta secciones con ese mismo titulo en el corpus, porque el nombre del endpoint vive en la introduccion, no en la tabla. Cada fragmento se prefija con su pagina y su endpoint **antes** de generar el embedding, de modo que esa identidad entra tanto al indice vectorial como al de BM25. Medido: fragmentos que no aparecian en ninguna busqueda pasaron a ser el resultado numero uno.

**Ausencia de evidencia no es evidencia de ausencia.** Un asistente sobre documentacion tiene una forma de fallar que es peor que no responder: afirmar que un endpoint "no requiere parametros" cuando lo cierto es que no los encontro. Para quien esta integrando una API, esas dos frases llevan a sitios muy distintos. El redactor y el verificador tienen reglas explicitas que separan una afirmacion sobre el producto de una afirmacion sobre la busqueda.

**Ventana de recuperacion medida, no supuesta.** El numero de fragmentos que se le pasan al redactor se fijo midiendo en que posicion del ranking caian las respuestas correctas, no eligiendo un numero redondo.

**Dos modelos segun la tarea.** GPT-4o redacta la respuesta al usuario; GPT-4o-mini toma las decisiones mecanicas del grafo (evaluar, reformular, verificar), con salida JSON estructurada para que el enrutamiento no dependa de interpretar texto libre.

**Sin base vectorial, a proposito.** Con 503 fragmentos los vectores normalizados caben en un array de numpy y la similitud coseno es una multiplicacion de matrices. Una base vectorial aqui es infraestructura que no paga su costo. Misma decision, y por la misma razon medida, que en el chatbot RAG del portafolio.

**Memoria del lado del servidor.** El checkpointer de LangGraph (`MemorySaver`) guarda el estado por `thread_id`, de modo que cada conversacion continua sin que el cliente reenvie el historial. El historial se declara con un reducer (`Annotated[list, add]`) para que se acumule en vez de sobrescribirse — sin ese detalle la memoria parece funcionar y no funciona.

## La interfaz muestra el razonamiento

Cada respuesta trae un desplegable con el recorrido que hizo el grafo: cuando reformulo la busqueda, cuando se rindio, cuando descarto su propia respuesta por no estar respaldada. Un chatbot que responde bien no se distingue a simple vista de uno que acerto por casualidad; uno que muestra por donde paso, si.

## Que demuestra este proyecto

- Orquestacion de agentes con LangGraph: estado tipado, aristas condicionales, ciclos, subgrafos, checkpointers y reducers
- Diseno de sistemas que fallan de forma segura: declinar es un resultado valido del grafo, no un error
- Criterio para elegir arquitectura segun el volumen real de datos, no segun la moda
- Extraccion y estructuracion de un corpus desde cero: scraping respetuoso (una peticion por segundo), chunking estructural, indexacion por lotes
- Capacidad de depurar sistemas de recuperacion midiendo, no suponiendo

## Tecnologias

Python, LangGraph, OpenAI (GPT-4o, GPT-4o-mini, text-embedding-3-small), rank-bm25, numpy, BeautifulSoup, Streamlit. Construido con Claude Code.
