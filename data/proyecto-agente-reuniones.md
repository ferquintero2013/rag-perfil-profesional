# Proyecto: agente de analisis de reuniones con servidor MCP propio

> Periodo: 2026. Herramienta propia construida durante la direccion del proyecto de ERP Odoo en tres paises.

## Que es

Un sistema propio que convierte las reuniones grabadas de un proyecto en estado de gestion actualizado, sin transcripcion manual. El agente obtiene el transcript completo desde Fathom, la plataforma de grabacion; lo analiza bajo un protocolo estricto; lo contrasta contra el estado vigente del proyecto; y escribe el resultado en un tablero de gestion a traves de un servidor MCP construido para ese proposito.

**Ferney Quintero construyo las tres piezas**: el agente y su protocolo de analisis, el servidor MCP que expone las operaciones de escritura, y el tablero de gestion que consume esa informacion.

## Por que construirlo en vez de usar el resumen automatico

Porque el resumen automatico de la plataforma no era una fuente confiable para tomar decisiones de gestion, y ese hallazgo origino el proyecto.

Al contrastar resumenes automaticos contra transcripts completos aparecieron tres problemas recurrentes:

1. **Los rotulos de hablante vienen cruzados.** Bloques largos atribuidos a una persona contenian intervenciones de otras dos, de modo que un compromiso podia quedar asignado a quien no lo asumio.
2. **El resumen conserva la conclusion y pierde la condicion.** Un acuerdo que en la reunion quedo condicionado — "se hace si el recurso queda dedicado, no compartido" — se resume como acuerdo cerrado, y esa diferencia es exactamente la que determina si el compromiso se cumple.
3. **Lo mas valioso suele mencionarse de pasada.** El cierre de un pendiente abierto hacia tres semanas aparece en una frase incidental que ningun resumen conserva, porque no fue el tema de la reunion.

La conclusion de diseno: el resumen automatico sirve para ubicar una reunion, no para analizarla. El agente trabaja siempre sobre el transcript completo.

## Como funciona

**Uno, obtencion.** El agente consulta Fathom y recupera el transcript integro, no su resumen. La fuente es la plataforma en vivo, no archivos exportados, de modo que siempre lee la version actual.

**Dos, analisis con protocolo.** Un protocolo formalizado fija como se lee y que se puede afirmar. Las reglas principales: leer el cien por ciento del transcript, en bloques si es largo; no analizar nunca desde el resumen automatico; no delegar la lectura a un subproceso que devuelva un resumen, porque eso reintroduce el problema que el sistema existe para resolver; reconstruir la atribucion de hablantes por contenido y por rol cuando los rotulos vienen cruzados; registrar como compromiso lo acordado al final de la discusion y no una propuesta intermedia; y asignar cada compromiso a quien lo asumio textualmente, nunca por inferencia.

**Tres, contraste contra el estado vigente.** Antes de escribir nada, el agente compara lo analizado con el estado actual del proyecto y busca cuatro cosas: contradicciones con lo documentado, compromisos nuevos, cambios de prioridad y personas involucradas que no estaban mapeadas. Tambien barre la lista de pendientes abiertos para ver si la reunion cierra o desbloquea alguno.

**Cuatro, escritura a traves del MCP.** El agente escribe en el tablero invocando las herramientas que expone el servidor MCP. La escritura no es texto libre: cada pendiente queda con responsable, fecha concreta y una etiqueta de estado de un vocabulario cerrado — completado, en progreso, verificar estado, bloqueado por, cancelado, sin cerrar. Si algo no quedo cerrado en la reunion se marca *sin cerrar*; si no se sabe, *verificar estado*. Nunca se asume.

## Las decisiones de diseno

**El sistema escala en vez de resolver.** Cuando el agente encuentra una contradiccion entre lo dicho en la reunion y lo documentado, no la resuelve por su cuenta ni elige la version mas probable: la senala y la deja marcada para decision humana. La razon es directa: quien usa el tablero le dedica poco tiempo al detalle y confia en lo que el sistema entrega, asi que un error silencioso no se detecta, se convierte en una decision mal informada semanas despues.

Es el mismo criterio que Ferney aplica en el resto de sus sistemas: **una automatizacion que falla en silencio es peor que no tener ninguna**. El agente esta disenado para que el fallo sea visible en el punto donde ocurre, no para prometer que no va a fallar.

**El vocabulario cerrado de estados es lo que lo hace auditable.** Prohibir expresiones ambiguas — "esta semana", "hoy", "pronto" — y obligar a fecha concreta y estado explicito convierte el tablero en algo que se puede revisar sin releer la reunion. Un pendiente marcado *verificar estado* comunica algo distinto de uno marcado *bloqueado por*, y esa diferencia permite preparar una reunion en minutos en lugar de una hora.

**La regla de atribucion protege la credibilidad del sistema.** Asignar un compromiso a la persona equivocada destruye la confianza en todo el tablero de una sola vez. Por eso la atribucion se reconstruye por contenido, y ante la duda se guarda la cita textual en lugar de una interpretacion.

## Resultados

El sistema sostuvo la direccion de un proyecto de ERP con operacion en tres paises durante siete meses, con multiples reuniones semanales y mas de veinte personas involucradas entre areas de negocio, desarrollo y direccion. El estado del proyecto — frentes de trabajo, pendientes, decisiones y responsables — se mantuvo actualizado despues de cada reunion sin transcripcion manual, y sirvio tanto para preparar las reuniones siguientes como para producir el informe final de traspaso al cierre del contrato.

El efecto practico: la documentacion de gestion dejo de ser una tarea que se hace al final, cuando ya se olvido el detalle, y paso a ser una consecuencia automatica de que la reunion ocurriera.

## Relacion con el asistente del portafolio

Los dos resuelven el mismo problema con la misma filosofia: **un sistema de IA que trabaja sobre documentos debe poder decir de donde saco cada afirmacion y reconocer cuando no la tiene**. En el asistente del portafolio eso se ve en las citas a la fuente y en el estado de grounding visible en la interfaz. En el agente de reuniones se ve en la cita textual ante duda de atribucion y en las etiquetas de estado que distinguen lo confirmado de lo que falta verificar.

La diferencia esta en el destinatario del error. En un portafolio, una afirmacion sin respaldo es una molestia. En la direccion de un proyecto de ERP en tres paises, es una decision operativa tomada sobre un dato falso.

## Tecnologias

Servidor MCP propio, API de Fathom para obtencion de transcripts, agentes de IA con protocolo de analisis formalizado, tablero de gestion propio.
