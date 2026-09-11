# Portafolio de Proyectos - Ferney Quintero

## Proyectos destacados

### 1. Chatbot RAG sobre CV y portafolio — PUBLICO
- **Descripcion**: Sistema RAG que responde preguntas sobre mi trayectoria profesional usando unicamente mi CV y portafolio como fuente. Cada afirmacion cita el archivo y la seccion de donde salio, de modo que la respuesta es verificable y no una opinion del modelo.
- **Rol**: Arquitecto y desarrollador unico (100% del codigo, diseno y deploy)
- **Tecnologias**: Python, Streamlit, ChromaDB, rank-bm25, OpenAI (text-embedding-3-small + GPT-4o + GPT-4o-mini). Construido con Claude Code.
- **Decisiones tecnicas destacadas**:
  - **Busqueda hibrida**: BM25 + embeddings, fusionados con Reciprocal Rank Fusion. La busqueda puramente vectorial fallaba en preguntas sobre entidades nombradas por dilucion semantica en chunks tematicamente mixtos.
  - **HyDE probado y descartado con datos**: mejoraba las distancias de similitud (1.13 -> 0.77) mientras empeoraba la relevancia real, porque la metrica media parecido con la respuesta hipotetica y no con la pregunta.
  - **Query rewriting previo al retrieval** para soportar preguntas de seguimiento: el historial no sirve si se le pasa solo al generador, porque la busqueda ya ocurrio.
  - **Grounding estricto**: si el dato no esta en el corpus, lo dice; respeta matices (una habilidad en aprendizaje no se presenta como dominada).
  - **Curacion por allowlist**: el corpus publico es un subconjunto declarado explicitamente; lo nuevo es privado por defecto.
- **Periodo**: Septiembre 2026
- **Demo publico**: https://chat-perfil-ferney.streamlit.app/
- **Codigo fuente**: https://github.com/ferquintero2013/rag-perfil-profesional

### 2. MVP de Validacion Inteligente de Documentos con IA (UTEL) — PUBLICO
- **Descripcion**: Sistema de hiperautomatizacion que valida expedientes de admision universitaria. Extrae datos de documentos con GPT-4o Vision, aplica reglas de negocio auditables, hace cross-check de identidad entre documentos para detectar posibles suplantaciones, y genera notificaciones personalizadas al aspirante con IA.
- **Rol**: Arquitecto y desarrollador unico (100% del codigo, diseno y deploy)
- **Tecnologias**: Python 3.14, Streamlit, OpenAI GPT-4o Vision + GPT-4o-mini, GitHub API, ChromaDB-free (reglas deterministas), deploy en Streamlit Community Cloud. Construido usando Claude Code como companero de desarrollo.
- **Impacto/Resultados**: Reduccion de ~14 minutos a ~5 segundos por documento (99% menos tiempo). Cross-check de identidad = capacidad nueva que no existia en el proceso manual. Notificacion al aspirante 100% automatizada. Trazabilidad completa para auditoria.
- **Arquitectura**: 6 modulos Python con separacion de responsabilidades — ingesta, extraccion con Vision AI, validacion por reglas de negocio, analisis de expediente con cross-check, generacion de notificacion, UI.
- **Decisiones de diseno destacadas**: hibrido IA + reglas deterministas (la IA extrae, las reglas deciden), anti-alucinacion via auto-declaracion de confianza del modelo, jerarquia de decision por severidad, modelos distintos por caso de uso (GPT-4o para extraccion critica, GPT-4o-mini 10x mas barato para redaccion).
- **Periodo**: Agosto - Septiembre 2026
- **Demo publico**: https://postulaciones-mvp.streamlit.app/
- **Codigo fuente**: https://github.com/ferquintero2013/postulaciones-mvp-utel

### 3. Implementacion ERP Cross-Country (Fajas Forma Tu Cuerpo)
- **Descripcion**: Implementacion de Odoo ERP para operaciones en US, Colombia y Mexico con sincronizacion multi-plataforma (TikTok Shop, Amazon, Shopify)
- **Rol**: Software Development Lead
- **Tecnologias**: Odoo, integraciones e-commerce, herramientas IA
- **Impacto/Resultados**: Eliminacion de inconsistencias de datos entre plataformas, frameworks de gobernanza de producto, documentacion acelerada 3x con IA
- **Periodo**: Marzo 2026 - Presente
- **Link**: _(privado)_

### 4. Automatizaciones CRM (Onest Vision) — Cliente real
- **Descripcion**: Desarrollo y mantenimiento de automatizaciones CRM en GoHighLevel para gestion de contactos, atribucion UTM automatizada y reporting
- **Rol**: Independent Contractor (cliente pagante)
- **Tecnologias**: GoHighLevel CRM, Zapier, automatizaciones de datos
- **Impacto/Resultados**: Gestion de contactos y oportunidades optimizada, atribucion de datos UTM automatizada, insights de reporting confiables
- **Periodo**: Enero - Marzo 2026
- **Link**: _(trabajo de cliente, no publico)_

### 5. Hackathon EmprendIA LATAM - 1er Lugar
- **Descripcion**: Proyecto ganador del primer lugar en la categoria Best AI Automation usando n8n
- **Rol**: Participante / Desarrollador
- **Tecnologias**: n8n
- **Impacto/Resultados**: 1er puesto en Best AI Automation
- **Periodo**: 2025
- **Link**: _(agregar si disponible)_

### 6. Agentes IA de Soporte de Ventas (Lambda AI) — Proyecto propio
- **Descripcion**: Prototipo de agentes IA de soporte de ventas construido con Meta APIs y ManyChat, integrando multiples repositorios de datos para automatizar captura, calificacion y gestion de leads. Iniciativa propia con el objetivo de lanzar un negocio de chatbots.
- **Rol**: Creador y desarrollador unico (proyecto personal, no cliente)
- **Tecnologias**: Meta APIs, ManyChat, n8n, integraciones de datos
- **Impacto/Resultados**: Arquitectura completa del pipeline de ventas construida y funcional (captura → calificacion → gestion de leads). El mismo patron tecnico gano 1er lugar en el hackathon EmprendIA LATAM. No llego a clientes pagantes.
- **Periodo**: Agosto - Diciembre 2025
- **Link**: _(prototipo propio, codigo privado)_

### 7. QA Lead - Proyecto Mayor de BVC
- **Descripcion**: Liderazgo del equipo de QA para uno de los proyectos mas grandes en la historia reciente de la Bolsa de Valores de Colombia
- **Rol**: Senior Software QA Analyst - Team Leader
- **Tecnologias**: Scala, Java, herramientas QA
- **Impacto/Resultados**: Aseguramiento de calidad exitoso en proyecto de alta criticidad financiera
- **Periodo**: 2015 - 2018
- **Link**: _(confidencial)_

### 8. Transformacion Agil - Nequi
- **Descripcion**: Mejora de productividad en la cadena de valor de desarrollo de producto de software de Nequi (fintech lider en Colombia)
- **Rol**: Agile Leader
- **Tecnologias**: Frameworks agiles, metricas de productividad
- **Impacto/Resultados**: Implementacion de enfoques innovadores para eficiencia y colaboracion en equipos de desarrollo
- **Periodo**: Marzo 2024 - Julio 2025
- **Link**: _(interno)_

## Portafolio web

- **Sitio publico**: https://ferney-portfolio.vercel.app/
- **GitHub**: https://github.com/ferquintero2013

## Certificaciones

- 1er Lugar — Best AI Automation, n8n EmprendIA LATAM Hackathon (2025)
- Claude Code: Software Engineering with Generative AI Agents (Anthropic)
- n8n: Agentes y automatizaciones de IA
- AWS Certified Cloud Practitioner
- Certified SAFe 5 Scrum Master
- Lean Portfolio Management (ICP-LPM)
