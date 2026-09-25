# Portafolio de Proyectos - Ferney Quintero

## Sobre el asistente que responde en esta pagina

Quien responde estas preguntas es un asistente, no Ferney. Si alguien pregunta "quien eres", "que eres", "que es este asistente" o "como funcionas", la respuesta habla del asistente, no de la biografia de Ferney.

Como se presenta, en pocas palabras: **es el asistente del portafolio de Ferney Quintero, y ayuda a conocer su perfil profesional y sus proyectos.** Responde unicamente desde su CV y la documentacion de sus proyectos, cita de donde sale cada dato, y dice cuando algo no esta documentado en vez de inventarlo.

**Su codigo es abierto.** Quien quiera ver como esta construido puede revisarlo en el repositorio (github.com/ferquintero2013/rag-perfil-profesional) o en la pagina "Como funciona el asistente" del propio portafolio.

Los detalles tecnicos —busqueda hibrida, fusion de rankings, evaluaciones automatizadas— estan mas abajo, en la ficha del proyecto. No hacen falta para presentarse: se explican solo si alguien pregunta especificamente como funciona.

## Proyectos destacados

### 1. Chatbot RAG sobre CV y portafolio — PUBLICO
- **Descripcion**: Sistema RAG que responde preguntas sobre mi trayectoria profesional usando unicamente mi CV y portafolio como fuente. Cada afirmacion cita el archivo y la seccion de donde salio, de modo que la respuesta es verificable y no una opinion del modelo.
- **Rol**: Arquitecto y desarrollador unico (100% del codigo, diseno y deploy)
- **Tecnologias**: Python, rank-bm25, OpenAI (text-embedding-3-small + GPT-4o + GPT-4o-mini), funciones serverless en Vercel. Construido con Claude Code.
- **Decisiones tecnicas destacadas**:
  - **Busqueda hibrida**: BM25 + embeddings, fusionados con Reciprocal Rank Fusion. La busqueda puramente vectorial fallaba en preguntas sobre entidades nombradas por dilucion semantica en chunks tematicamente mixtos.
  - **HyDE probado y descartado con datos**: mejoraba las distancias de similitud (1.13 -> 0.77) mientras empeoraba la relevancia real, porque la metrica media parecido con la respuesta hipotetica y no con la pregunta.
  - **Query rewriting previo al retrieval** para soportar preguntas de seguimiento: el historial no sirve si se le pasa solo al generador, porque la busqueda ya ocurrio.
  - **Grounding estricto**: si el dato no esta en el corpus, lo dice; respeta matices (una habilidad en aprendizaje no se presenta como dominada).
  - **Curacion por allowlist**: el corpus publico es un subconjunto declarado explicitamente; lo nuevo es privado por defecto.
- **Periodo**: Septiembre 2026
- **Demo publico**: https://chat-perfil-ferney.streamlit.app/
- **Codigo fuente**: https://github.com/ferquintero2013/rag-perfil-profesional

### 2. Asistente de documentacion tecnica con LangGraph — PUBLICO
- **Descripcion**: Asistente que responde preguntas sobre la documentacion de una API y muestra el razonamiento que siguio para llegar a cada respuesta. A diferencia de un RAG lineal, la orquestacion es un grafo de LangGraph con decisiones y ciclos: evalua si lo que encontro responde de verdad, reformula la busqueda y reintenta si no, y verifica la respuesta contra las fuentes antes de entregarla. Si no queda respaldada, la descarta.
- **Rol**: Arquitecto y desarrollador unico (100% del codigo, diseno y deploy)
- **Tecnologias**: Python, LangGraph (estado tipado, aristas condicionales, ciclos, checkpointers, reducers), OpenAI (GPT-4o + GPT-4o-mini + text-embedding-3-small), rank-bm25, numpy, BeautifulSoup, Streamlit. Construido con Claude Code.
- **Decisiones tecnicas destacadas**:
  - **La verificacion es una compuerta del grafo, no una instruccion del prompt**: pedirle a un modelo que no invente es una sugerencia; un nodo que compara la respuesta contra las fuentes y la descarta es un control.
  - **Chunking contextual**: cada fragmento se prefija con su pagina y su endpoint antes del embedding, porque cortar por encabezados deja treinta secciones tituladas igual e indistinguibles entre si. Medido: fragmentos que no aparecian en ninguna busqueda pasaron a ser el primer resultado.
  - **Ausencia de evidencia no es evidencia de ausencia**: afirmar que un endpoint "no requiere parametros" cuando lo cierto es que no se encontraron es la forma mas danina de fallar para quien esta integrando una API. Es una regla explicita del redactor y del verificador.
  - **Ciclo de autocorreccion** con tope de dos intentos: una arista hacia atras en el grafo, no un reintento ciego.
  - **Memoria del lado del servidor** con checkpointer por `thread_id` y reducer en el historial.
- **Corpus**: 503 fragmentos de 64 paginas de documentacion publica
- **Periodo**: Septiembre 2026
- **Codigo fuente**: https://github.com/ferquintero2013/langgraph-doc-assistant
- **Nota**: es una demostracion tecnica independiente sobre documentacion publica de terceros, sin afiliacion con la empresa cuya documentacion se uso.

### 3. MVP de Validacion Inteligente de Documentos con IA (UTEL) — PUBLICO
- **Descripcion**: Sistema de hiperautomatizacion que valida expedientes de admision universitaria. Extrae datos de documentos con GPT-4o Vision, aplica reglas de negocio auditables, hace cross-check de identidad entre documentos para detectar posibles suplantaciones, y genera notificaciones personalizadas al aspirante con IA.
- **Rol**: Arquitecto y desarrollador unico (100% del codigo, diseno y deploy)
- **Tecnologias**: Python 3.14, Streamlit, OpenAI GPT-4o Vision + GPT-4o-mini, GitHub API, reglas deterministas de negocio, deploy en Streamlit Community Cloud. Construido usando Claude Code como companero de desarrollo.
- **Impacto/Resultados**: Reduccion de ~14 minutos a ~5 segundos por documento (99% menos tiempo). Cross-check de identidad = capacidad nueva que no existia en el proceso manual. Notificacion al aspirante 100% automatizada. Trazabilidad completa para auditoria.
- **Arquitectura**: 6 modulos Python con separacion de responsabilidades — ingesta, extraccion con Vision AI, validacion por reglas de negocio, analisis de expediente con cross-check, generacion de notificacion, UI.
- **Decisiones de diseno destacadas**: hibrido IA + reglas deterministas (la IA extrae, las reglas deciden), anti-alucinacion via auto-declaracion de confianza del modelo, jerarquia de decision por severidad, modelos distintos por caso de uso (GPT-4o para extraccion critica, GPT-4o-mini 10x mas barato para redaccion).
- **Periodo**: Agosto - Septiembre 2026
- **Demo publico**: https://postulaciones-mvp.streamlit.app/
- **Codigo fuente**: https://github.com/ferquintero2013/postulaciones-mvp-utel

### 4. Implementacion ERP Cross-Country (cliente de manufactura y retail de moda)
- **Descripcion**: Implementacion de Odoo ERP para operaciones en US, Colombia y Mexico con sincronizacion multi-plataforma (TikTok Shop, Amazon, Shopify)
- **Rol**: Lider de desarrollo de software, IA y automatizacion, como independiente
- **Tecnologias**: Odoo, integraciones e-commerce, herramientas IA
- **Impacto/Resultados**: Eliminacion de inconsistencias de datos entre plataformas, frameworks de gobernanza de producto, documentacion acelerada 3x con IA
- **Periodo**: Marzo 2026 - Presente
- **Link**: _(privado)_

### 5. Automatizaciones CRM y motor de atribucion UTM (Onest Vision) — Cliente real
- **Descripcion**: Cuatro flujos en produccion sobre n8n autoalojado contra la API REST de GoHighLevel, implementando logica que el motor nativo de GHL no podia expresar: division de oportunidades por propiedad, clonado completo entre embudos con mas de 40 campos personalizados, enrutamiento de respuestas de encuesta a la oportunidad correcta sin duplicar, y un motor de atribucion UTM de unas 300 lineas de JavaScript
- **Rol**: Independent Contractor (cliente pagante)
- **Tecnologias**: n8n autoalojado, JavaScript, API REST de GoHighLevel, webhooks. **No Zapier**
- **Impacto/Resultados**: 4 flujos activos, 6 endpoints de API integrados, 12 campos UTM calculados por evento (primer contacto y ultima interaccion), mas de 10 tipos de origen de trafico normalizados. La atribucion paso de ser un dato no confiable a una taxonomia consistente sobre la que el equipo de marketing puede asignar presupuesto
- **Periodo**: Enero - Marzo 2026
- **Link**: _(trabajo de cliente, no publico)_

### 6. Hackathon EmprendIA LATAM - 1er Lugar
- **Descripcion**: Proyecto ganador del primer lugar en la categoria Best AI Automation usando n8n
- **Rol**: Participante / Desarrollador
- **Tecnologias**: n8n
- **Impacto/Resultados**: 1er puesto en Best AI Automation
- **Periodo**: 2025
- **Link**: _(agregar si disponible)_

### 7. Agentes IA de Soporte de Ventas (Lambda AI) — Proyecto propio
- **Descripcion**: Prototipo de agentes IA de soporte de ventas construido con Meta APIs y ManyChat, integrando multiples repositorios de datos para automatizar captura, calificacion y gestion de leads. Iniciativa propia con el objetivo de lanzar un negocio de chatbots.
- **Rol**: Creador y desarrollador unico (proyecto personal, no cliente)
- **Tecnologias**: Meta APIs, ManyChat, n8n, integraciones de datos
- **Impacto/Resultados**: Arquitectura completa del pipeline de ventas construida y funcional (captura → calificacion → gestion de leads). El mismo patron tecnico gano 1er lugar en el hackathon EmprendIA LATAM. No llego a clientes pagantes.
- **Periodo**: Agosto - Diciembre 2025
- **Link**: _(prototipo propio, codigo privado)_

### 8. QA Lead - Proyecto Mayor de BVC
- **Descripcion**: Liderazgo del equipo de QA para uno de los proyectos mas grandes en la historia reciente de la Bolsa de Valores de Colombia
- **Rol**: Senior Software QA Analyst - Team Leader
- **Tecnologias**: Scala, Java, herramientas QA
- **Impacto/Resultados**: Aseguramiento de calidad exitoso en proyecto de alta criticidad financiera
- **Periodo**: 2015 - 2018
- **Link**: _(confidencial)_

### 9. Transformacion Agil - Nequi
- **Descripcion**: Mejora de productividad en la cadena de valor de desarrollo de producto de software de Nequi (fintech lider en Colombia)
- **Rol**: Agile Leader
- **Tecnologias**: Frameworks agiles, metricas de productividad
- **Impacto/Resultados**: Implementacion de enfoques innovadores para eficiencia y colaboracion en equipos de desarrollo
- **Periodo**: Marzo 2024 - Julio 2025
- **Link**: _(interno)_

## Portafolio web

- **Sitio publico**: https://ferney-portfolio.vercel.app/
- **GitHub**: https://github.com/ferquintero2013

## Certificaciones y formacion

**IA y datos:** Bootcamp 2027: Comprender y Crear Agentes IA Profesionales (Udemy, 50.5 h, septiembre 2026) — enfocado en LangGraph, sistemas multi-agente, memoria de largo plazo y human-in-the-loop; sin CrewAI, modulo omitido a proposito · 1er Lugar Best AI Automation, hackathon n8n EmprendIA LATAM (2025) · Claude Code: Software Engineering with Generative AI Agents (Vanderbilt University) · n8n: Agentes y automatizaciones de IA (Udemy) · Generative AI for Business Leaders (LinkedIn) · Inteligencia Artificial: ChatGPT, DALL-E y Hugging Face (Platzi) · Analisis de Datos con Power BI (Platzi)

**Ingenieria y cloud:** AWS Certified Cloud Practitioner (AWS) · Arquitectura de Software (Platzi) · Curso Practico de Frontend Developer (Platzi) · Experto en Zapier

**Gestion (complementaria al rol tecnico):** Lean Portfolio Management ICP-LPM (ICAgile) · Certified SAFe 5 Scrum Master
