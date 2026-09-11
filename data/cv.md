# CV de Ferney Quintero

## Datos de contacto
- **Nombre**: Ferney Quintero
- **Titulo**: Ingeniero de IA (AI Engineer)
- **Perfil complementario**: Software Engineer · Analista de negocio · Gerencia de proyectos de IA
- **Email**: ferquintero2013@gmail.com
- **LinkedIn**: linkedin.com/in/ferneyquintero-7301b547
- **Ubicacion**: Bogota, Colombia
- **Disponibilidad**: Inmediata (trabaja actualmente en Fajas Forma Tu Cuerpo + consultoria independiente)

## Resumen profesional
Ingeniero de IA. Construye sistemas con inteligencia artificial de punta a punta: agentes, asistentes sobre documentos (RAG), extraccion estructurada con modelos de vision y automatizacion de procesos entre sistemas.

Llega a la IA despues de trece anos recorriendo el ciclo completo de desarrollo de software — desarrollador, QA lead, analista de negocio, project manager y Agile Coach. Esa trayectoria es lo que le permite leer un proceso antes de automatizarlo y dimensionar una solucion a su escala real, en vez de aplicar la herramienta de moda a cualquier problema.

**Sobre su perfil profesional:** su rol primario es Ingeniero de IA. La experiencia en gerencia de proyectos y agilismo es complementaria, no su profesion actual: aporta la capacidad de mapear procesos, alinear stakeholders y estimar alcance, que es lo que suele faltarle a un perfil puramente tecnico. Los proyectos que lidera son de inteligencia artificial, agentes y automatizacion; no busca ni ejerce roles de PM o Scrum Master puros.

## Experiencia laboral

### Fajas Forma Tu Cuerpo Shapewear | Software Development Lead - AI & Process Automation | Marzo 2026 - Presente
- **Tecnologias**: Odoo ERP, TikTok Shop, Amazon, Shopify, herramientas IA
- **Logros clave**:
  - Liderando implementacion de ERP cross-country (US, Colombia, Mexico)
  - Diseno de frameworks de gobernanza de producto para eliminar inconsistencias de datos
  - Aplicacion de IA para acelerar toma de decisiones: analisis de reuniones, extraccion de requerimientos, identificacion de riesgos a 3x velocidad
- **Responsabilidades**: Alineacion de stakeholders (Operaciones, Contabilidad, Tecnologia), orquestacion de equipos de desarrollo, control de inventario, facturacion, sincronizacion multi-plataforma

### Independiente (Self-Employed) | AI Automation Consultant | Julio 2025 - Marzo 2026 (9 meses)
- **Tecnologias**: n8n, Zapier, Meta APIs, ManyChat, GoHighLevel CRM
- **Logros clave**:
  - **Onest Vision (cliente pagante, Ene-Mar 2026)**: Automatizaciones CRM en GoHighLevel para gestion de contactos, atribucion UTM y reporting. Contrato como contractor.
  - **Lambda AI (proyecto propio, Ago-Dic 2025)**: Prototipo de agentes de soporte de ventas con Meta APIs y ManyChat, automatizando captura, calificacion y gestion de leads. Iniciativa propia para lanzar negocio de chatbots; arquitectura completa construida, no llego a clientes pagantes. El mismo patron tecnico gano 1er lugar en el hackathon EmprendIA LATAM.
  - **Hackathon EmprendIA LATAM (2025)**: 1er lugar en la categoria Best AI Automation con solucion construida en n8n.
- **Responsabilidades**: Consultoria independiente en automatizaciones IA y sistemas multi-agente, optimizacion de workflows, integracion de asistentes IA

### Nequi | Agile Leader | Marzo 2024 - Julio 2025 (1 ano 5 meses)
- **Tecnologias**: Herramientas agiles, metricas de productividad
- **Logros clave**:
  - Mejora de productividad en la cadena de valor de desarrollo de producto de software
  - Implementacion de enfoques innovadores para eficiencia y colaboracion
- **Responsabilidades**: Liderazgo de equipos, tacticas y estrategias agiles

### Imagemaker | Scrum Master | Mayo 2022 - Julio 2023 (1 ano 3 meses)
- **Tecnologias**: Herramientas agiles, gestion de proyectos
- **Logros clave**:
  - Liderazgo de equipos multiculturales
  - Colaboracion con gerentes de ventas en propuestas de proyectos (estimaciones y alcance)
  - Sesiones de descubrimiento colaborativo con stakeholders
- **Responsabilidades**: Coaching agil, gestion de proyectos end-to-end, evaluacion de factibilidad tecnica y comercial

### Sophos Solutions S.A.S. | Scrum Master / Agile Consultant | Enero 2021 - Mayo 2022 (1 ano 5 meses)
- **Logros clave**:
  - Implementacion de metodologia agil mejorando eficiencia y adaptabilidad de proyectos
  - Remocion proactiva de impedimentos
- **Responsabilidades**: Coaching agil, facilitacion, gestion de dinamicas de equipo

### Softgic | Project Manager | Agosto 2018 - Diciembre 2020 (2 anos 5 meses)
- **Tecnologias**: Framework PMI
- **Logros clave**:
  - Entregas a tiempo y dentro del alcance
- **Responsabilidades**: Gestion de proyectos bajo PMI, analisis de contratos, seguimiento de entregables

### BVC - Bolsa de Valores de Colombia | Senior Software QA Analyst - Team Leader | 2015 - Agosto 2018 (3 anos)
- **Tecnologias**: Scala, Java, herramientas QA
- **Logros clave**:
  - Lider de QA para uno de los proyectos mas grandes en la historia reciente de la empresa
- **Responsabilidades**: Planificacion, control y aseguramiento de calidad en proyectos de software

### BVC - Bolsa de Valores de Colombia | Software Developer Scrum Team | Junio 2015 - Diciembre 2016 (1 ano 7 meses)
- **Tecnologias**: Scala, Java
- **Responsabilidades**: Desarrollo de software en equipo Scrum

### DIIT Consultores SAS | Development and Consulting Engineer | Febrero 2013 - Marzo 2015 (2 anos 2 meses)
- **Tecnologias**: Microsoft Dynamics AX ERP
- **Responsabilidades**: Desarrollo y consultoria en ERP, analisis de negocio, documentacion funcional y tecnica

## Proyectos tecnicos publicos

### Chatbot RAG sobre CV y portafolio | Septiembre 2026
Sistema RAG que responde preguntas sobre mi trayectoria profesional usando unicamente mi CV y portafolio como fuente, con citacion obligatoria de la fuente de cada afirmacion.
- **Stack**: Python, Streamlit, ChromaDB, BM25 (rank-bm25), OpenAI (text-embedding-3-small + GPT-4o). Desarrollado con Claude Code.
- **Decision tecnica clave**: busqueda hibrida (BM25 + embeddings fusionados con Reciprocal Rank Fusion). La busqueda puramente vectorial fallaba en preguntas sobre entidades nombradas ("¿sabe X?") por dilucion semantica en chunks tematicamente mixtos. HyDE se probo y se descarto con datos: mejoraba las distancias mientras empeoraba la relevancia.
- **Otras piezas**: query rewriting previo al retrieval para soportar preguntas de seguimiento, grounding estricto anti-alucinacion, y curacion del corpus por allowlist explicita.
- **Demo publico**: https://chat-perfil-ferney.streamlit.app/
- **Codigo**: https://github.com/ferquintero2013/rag-perfil-profesional

### MVP de Validacion Inteligente de Documentos con IA | Agosto - Septiembre 2026
Sistema end-to-end de validacion automatizada de expedientes de admision universitaria, construido integramente en Python. Extrae datos de documentos con GPT-4o Vision, aplica reglas de negocio auditables, hace cross-check de identidad entre documentos para detectar posibles suplantaciones, y genera notificaciones personalizadas con IA.
- **Stack**: Python 3.14, Streamlit, OpenAI GPT-4o Vision + GPT-4o-mini, GitHub API. Desarrollado con Claude Code.
- **Resultado**: reduccion de ~14 min a ~5 seg por documento (99%). Cross-check de identidad como capacidad nueva. 100% de notificaciones automatizadas.
- **Demo publico**: https://postulaciones-mvp.streamlit.app/
- **Codigo**: https://github.com/ferquintero2013/postulaciones-mvp-utel

## Educacion

### Universidad del Rosario | Especialista en Gerencia de Proyectos de Sistemas | 2015 - 2016

### Universidad Catolica de Colombia | Ingeniero de Sistemas | 2007 - 2012

## Certificaciones y formacion

### Inteligencia artificial y datos
- **1er Lugar — Best AI Automation**, hackathon n8n EmprendIA LATAM (2025)
- **Claude Code: Software Engineering with Generative AI Agents** — Vanderbilt University
- **n8n: Agentes y automatizaciones de IA** — Udemy
- **Generative AI for Business Leaders** — LinkedIn
- **Inteligencia Artificial: ChatGPT, DALL-E y Hugging Face** — Platzi
- **Analisis de Datos con Power BI** — Platzi

### Ingenieria y cloud
- **AWS Certified Cloud Practitioner** — Amazon Web Services (AWS)
- **Arquitectura de Software** — Platzi
- **Curso Practico de Frontend Developer** — Platzi
- **Experto en Zapier** — Zapier

### Gestion (formacion complementaria, no rol primario)
- **Lean Portfolio Management ICP-LPM** — ICAgile
- **Certified SAFe 5 Scrum Master** — Scaled Agile
- **Becoming an Agile Coach**

## Idiomas
- Espanol: Nativo
- Ingles: Full Professional

## Top Skills (destacados en LinkedIn)
- Claude Skills
- Anthropic Claude
- Vibe Coding
- n8n
- software development
- Business analysis
- Project management
- Agile methodologiest
