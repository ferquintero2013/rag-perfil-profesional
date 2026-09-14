# Proyecto: automatizaciones de CRM y motor de atribucion UTM (Onest Vision)

> Periodo: enero - marzo de 2026. Cliente pagante, contrato como contractor.
> Cliente final: un proyecto inmobiliario en Medellin, Colombia. El nombre del proyecto no se publica.
> **Importante**: todo este trabajo se construyo en **n8n autoalojado (self-hosted)** contra la API REST de GoHighLevel, **no en Zapier**.

## Que construyo

Cuatro flujos en produccion sobre n8n autoalojado, que se comunican con la API REST de GoHighLevel (GHL) para implementar logica de negocio que el constructor de flujos nativo de GHL no podia expresar.

El punto de partida fue una limitacion concreta: el motor nativo de GHL no puede dividir oportunidades con varias propiedades, no copia campos personalizados entre embudos, y crea oportunidades duplicadas cada vez que llega una respuesta de encuesta. Nada de eso se podia desactivar desde la configuracion.

## Flujo 1: dividir oportunidades por propiedad

**Problema**: en el embudo comercial, una misma oportunidad podia estar ligada a varios apartamentos. El embudo administrativo necesitaba una oportunidad por unidad para seguimiento, gestion documental y cierre. GHL no tiene forma nativa de dividir una oportunidad multiple.

**Solucion**: un flujo n8n disparado por webhook que recibe el ID de la oportunidad, consulta sus campos personalizados via API, identifica la lista de apartamentos, asigna el primero a la oportunidad original con un PUT, y despues itera sobre los restantes con un nodo Split Out creando una oportunidad nueva por cada uno via POST, con sus campos correspondientes.

## Flujo 2: clonado completo de oportunidades entre embudos

**Problema**: al mover una oportunidad del embudo comercial al administrativo habia que recrearla con **todos** sus campos personalizados — texto, telefonos, valores monetarios, desplegables y archivos adjuntos. La accion nativa "Create Opportunity" de GHL solo copia nombre, contacto y etapa, e ignora los campos personalizados. Ademas fallaba por permisos cuando el usuario asignado no tenia acceso al embudo destino.

**Solucion**: un flujo que trae la oportunidad origen con sus **mas de 40 campos personalizados**, la serializa como JSON en un nodo Edit Fields para evitar errores de referencia entre nodos, crea la oportunidad destino via POST, recorre con un nodo Code todos los campos mapeando ID y valor al formato de la API, y envia un unico PUT con el arreglo completo usando JSON.stringify para que arreglos y objetos anidados se serialicen bien.

## Flujo 3: respuesta de encuesta hacia la oportunidad correcta

**Problema**: una encuesta de varios pasos recogia la documentacion del comprador (cedula, certificados bancarios, declaraciones de renta, datos financieros). La encuesta colgaba de un contacto que podia tener varias oportunidades, una por apartamento. Habia que llevar cada respuesta a la oportunidad correcta **sin crear duplicados**, y el comportamiento por defecto de GHL era crear una oportunidad nueva en cada envio.

**Solucion**: un flujo con emparejamiento inteligente. Recibe el envio por webhook extrayendo **mas de 16 campos**, consulta todas las oportunidades del contacto con la API de busqueda, y un nodo Code hace coincidencia sin distincion de mayusculas entre el apartamento de la encuesta y el campo de la oportunidad. Solo actualiza la que coincide, filtrando campos vacios para no sobrescribir datos existentes con blancos.

## Flujo 4: motor de atribucion UTM

Es la pieza mas compleja de las cuatro y la mas interesante tecnicamente.

**Problema**: GHL captura datos de atribucion desde muchas entradas — anuncios de Meta, Google Ads, busqueda organica, trafico directo, cargas de CSV, enlaces de seguimiento, encuestas, calendarios, referidos, WhatsApp y codigos QR de vallas fisicas. Cada fuente manda el dato en un formato distinto y con distinto nivel de completitud, y **el mismo valor de origen puede significar canales completamente diferentes** segun que otros campos vengan llenos:

- Meta Ads llega como "Social media" con medio "form", sin utm_source ni utm_medium explicitos: hay que inferir que es pago a partir de senales de contexto.
- El trafico organico y el pagado de Instagram llegan identicos; solo se distinguen mirando adId, adSetId o campaignId.
- Entradas manuales del CRM e importaciones de CSV comparten origen pero necesitan clasificaciones distintas.
- Los escaneos de QR de vallas fisicas llegan sin parametros UTM, solo con un identificador propio enterrado en la URL.

Sin normalizar, un mismo canal aparecia con cinco etiquetas distintas en los reportes y la agregacion era imposible.

**Solucion**: un flujo que intercepta la creacion de cada oportunidad, trae los datos de atribucion del contacto, los pasa por un **motor de clasificacion basado en reglas de unas 300 lineas de JavaScript** en un nodo Code, y escribe los valores normalizados de vuelta en el contacto y en la oportunidad.

El motor es un arbol de decision multidimensional que calcula **seis campos UTM** (source, medium, campaign, content, type, term) y lo hace **dos veces**: para el primer contacto (first touch) y para la ultima interaccion (last touch), **doce campos por evento**. Si no existe ultima interaccion, copia la primera, de modo que ningun campo queda en blanco.

Ramas de decision principales: deteccion de senales de pago, identificacion de QR de valla, distincion entre campanas de conversion y de consideracion, desambiguacion de redes sociales con prioridad en cascada, inferencia del tipo de creatividad a partir del texto de la URL (reel, carrusel, banner estatico), y clasificacion de la estrategia de audiencia (lookalike, remarketing, prospectos frios).

**Por que importa para el negocio**: la atribucion dejo de ser un dato en el que no se podia confiar. Con la taxonomia normalizada, el equipo de marketing puede calcular costo por lead por canal, distinguir que canal capto al lead de cual lo reactivo antes de cerrar — critico en un ciclo de venta inmobiliaria que dura semanas o meses — y mover presupuesto con datos en vez de intuicion.

## Retos tecnicos que resolvio

- **Formato JSON en n8n**: mezclar expresiones de n8n dentro de un cuerpo JSON crudo rompia la peticion. Se resolvio construyendo los objetos en nodos Code y serializando con JSON.stringify.
- **Errores de referencia entre nodos**: los nodos Code de n8n solo pueden referenciar nodos de su cadena directa de ejecucion. Cuando hacia falta el dato de un nodo no adyacente, implemento un patron de nodo intermedio que consolida datos de varias fuentes antes de pasarlos al Code.
- **Tipos de dato inconsistentes**: campos que llegaban como arreglos serializados en texto en vez de arreglos reales, y habia que parsearlos antes de procesarlos.
- **Limitaciones de campos de archivo**: el constructor de GHL no expone los campos de subida de archivo en su accion de actualizar oportunidad, y la API rechaza el formato completo que usa internamente. Requirio trabajar con URLs directas.
- **Errores de permisos silenciosos**: las oportunidades creadas por automatizacion heredaban los permisos del usuario que disparaba el flujo. Si ese usuario no tenia acceso al embudo destino, **la operacion fallaba en silencio** dentro de GHL. Se resolvio creando via API con una llave de nivel administrador.

Ese ultimo caso es un ejemplo del criterio que Ferney aplica en todos sus sistemas: **un fallo silencioso es peor que un error visible**, porque nadie lo detecta hasta que ya causo dano.

## Resultados

| Metrica | Valor |
|---------|-------|
| Flujos en produccion | 4 flujos n8n activos |
| Endpoints de API integrados | 6 (GET, POST, PUT, DELETE) |
| Campos personalizados mapeados | mas de 40 en el clonado; mas de 16 por oportunidad en la encuesta |
| Logica de clasificacion | ~300 lineas de JavaScript, 6 funciones de clasificacion |
| Tipos de origen manejados | mas de 10 |
| Campos UTM calculados | 12 por evento (6 de primer contacto + 6 de ultima interaccion) |
| Trabajo manual eliminado | division de oportunidades, duplicado entre embudos, enrutamiento de encuestas y limpieza de atribucion |

## Que demuestra este proyecto

Que Ferney **escribe codigo cuando la herramienta no da**: el valor no estuvo en configurar GHL sino en detectar donde su modelo se quedaba corto y construir por fuera lo que faltaba, con JavaScript y llamadas directas a la API. Es trabajo de cliente pagante, en produccion.

## Tecnologias

n8n autoalojado (webhooks, HTTP Request, nodos Code, logica condicional, Split Out); JavaScript (~300 lineas de logica de clasificacion basada en reglas); API REST de GoHighLevel (GET, POST, PUT, DELETE sobre oportunidades, contactos y campos personalizados); GoHighLevel como CRM y almacen de datos.
