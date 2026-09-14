# Proyecto: ERP Odoo en tres paises y diagnostico de catalogo

> Periodo: marzo - septiembre de 2026 (7 meses). Trabajo independiente bajo contrato.
> Cliente: empresa de manufactura y retail de moda con operacion en Colombia, Estados Unidos y Mexico. El nombre del cliente no se publica en descripciones de proyecto.

## Que hizo Ferney Quintero en este proyecto

Ferney Quintero **dirigio el proyecto y construyo las herramientas con las que lo dirigio**. Las dos cosas, no una sola.

Del lado de direccion: modelo procesos antes de automatizarlos, priorizo el desarrollo, documento los sistemas, coordino a las areas de negocio y llevo el seguimiento de los frentes de trabajo hasta su cierre.

Del lado de ingenieria: construyo en Python el sistema de diagnostico que sostuvo el programa de mantenimiento de catalogo, y el agente de analisis de reuniones con su servidor MCP (documentado aparte) que mantuvo el estado del proyecto actualizado.

Al terminar el contrato el proyecto quedo en punto de continuidad autonoma, con informe final de traspaso y documentacion entregada.

## Es trabajo para un cliente real, en produccion

Conviene dejarlo explicito porque el nombre del cliente no aparece en este documento:
**este proyecto es trabajo pagado para un cliente real, bajo contrato, no un proyecto personal ni un prototipo.**

El sistema de diagnostico en Python descrito aqui corrio en produccion cada dos dias durante meses, sobre datos reales de una operacion en tres paises, y sus hallazgos derivaron en decisiones de negocio y en dinero recuperado. Es codigo Python escrito para un cliente real, con consecuencias operativas.

Si alguien pregunta si Ferney ha construido software en Python para clientes reales, o si su experiencia en Python es solo de proyectos propios, la respuesta es que **si tiene trabajo en Python para cliente real**: este sistema de diagnostico. Los otros trabajos de cliente son las automatizaciones de CRM para Onest Vision (GoHighLevel, no Python). Los proyectos propios — el chatbot RAG y el MVP de validacion documental — son adicionales a esto, no un sustituto.

## El entorno tecnico

Odoo 19 Enterprise en tres instancias productivas independientes, una por pais, con alrededor de veintiseis modulos personalizados. Canales de venta conectados: Shopify, Amazon, TikTok Shop y Mercado Libre. Alrededor conviven sistemas satelite de comercio electronico, datos y produccion, y varios sistemas legados en retiro. La infraestructura corre en un servidor en la nube que fue migrado durante el proyecto.

Una restriccion determino buena parte de las decisiones: **el proyecto contaba con un solo desarrollador para los tres paises**. Todo lo que exigia desarrollo competia por el mismo recurso, asi que la principal palanca de gestion no era pedir mas codigo sino evitar el codigo innecesario.

## El problema real

La empresa tenia talento, herramientas y datos, pero carecia de procesos formales, direccion de proyecto y seguimiento. El ERP estaba instalado en los tres paises y aun asi la operacion tomaba decisiones sobre informacion que el sistema no reflejaba bien: saldos de inventario que no eran reales, pedidos que no entraban, catalogos desalineados entre el ERP y la tienda en linea, y conciliaciones contables sin plan ni responsable.

El diagnostico de fondo es el mismo que Ferney ha visto repetirse durante trece anos: **los proyectos de automatizacion rara vez fallan por la herramienta, fallan porque nadie modelo bien el proceso antes de construir encima**.

## El sistema de diagnostico que construyo (Python)

Un script de diagnostico en Python que audita, cada dos dias y en menos de tres minutos, el estado de la integracion entre Odoo y Shopify, y produce un informe accionable para quien debe corregir los casos.

**Como esta construido**: se conecta a Odoo por XML-RPC y a la API de administracion de Shopify. Genera informes en Excel con openpyxl, lleva bitacora de cambios en JSONL y degrada a CSV si falta la libreria de Excel, en vez de fallar.

**Que revisa**: once verificaciones ordenadas por urgencia — pedidos que ya fallaron al entrar al ERP, referencias de la tienda que no existen en el ERP, variantes sin referencia, referencias duplicadas en dos fichas distintas, codigos de barras duplicados o divergentes entre sistemas, productos no publicados en el canal de punto de venta, productos activos en la tienda pero dados de baja en el ERP, mapeos rotos hacia registros de inventario inexistentes, y variantes sin inventario activo en todas las bodegas.

**Como entrega el resultado**: un libro de calculo con una hoja por verificacion. Cada fila trae una columna de accion escrita en lenguaje llano — que hay que hacer, no que esta mal — y un enlace directo al registro exacto a corregir. Una hoja adicional asigna cada caso a un responsable con nombre. Lo puede ejecutar una persona no tecnica.

**La decision de diseno que importa**: el modo de correccion asistida tiene topes deliberadamente bajos. Puede aplicar correcciones, pero solo sobre la tienda en linea, nunca sobre el ERP, con un maximo de diez cambios por ejecucion y tres por producto. El razonamiento esta escrito en el propio codigo: la referencia es la llave que une un pedido con su factura, y en la tienda una referencia repetida no produce error, se sobrescribe en silencio. Si un lote supera esos topes no es un conjunto de erratas sueltas sino un problema de catalogo, y eso debe mirarlo una persona. **El tope no es una limitacion del script: es el punto donde la automatizacion se detiene y escala en vez de propagar un error a escala.** Antes de tocar nada guarda copia de seguridad de las referencias y registra cada cambio en una bitacora, de modo que toda correccion es reversible y auditable.

**La verificacion que busca la causa y no el sintoma**: la primera hoja del informe no lista errores del sistema, sino lineas de pedido escritas a mano en el punto de venta. Esa verificacion existe porque el indicador de casos abiertos no bajaba aunque el equipo trabajara: entraban casos nuevos al mismo ritmo al que se cerraban los viejos. El script se diseno para hacer visible esa causa de entrada, no solo para contar pendientes.

## Resultados concretos y verificables

- **Falla de sincronizacion detectada**: el mecanismo de contraste de reportes encontro una falla del conector que llevaba **una semana sin que nadie la notara**, y que afectaba a decenas de pedidos ya facturados y no entregados, por un valor de decenas de miles de dolares.
- **Mantenimiento de catalogo**: en un periodo de **tres semanas el equipo cerro cuarenta y ocho referencias**, el mapeo roto entre sistemas quedo en cero y los productos sin punto de venta asignado bajaron a un unico caso.
- **Conciliacion contable**: estaba estimada en **dos meses**. Al conseguir que el recurso contable quedara dedicado en exclusiva y no compartido, y al acordar una franja diaria de trabajo conjunto con el consultor senior, la estimacion bajo a **aproximadamente tres semanas**.
- **Desarrollo evitado en manufactura**: corrio el ejercicio completo de produccion de punta a punta y valido que el modulo no requeria desarrollo, solo parametrizacion. Esto libero al unico desarrollador del proyecto en el mes de mayor competencia por su tiempo.
- **Causa raiz separada del sintoma**: un grupo de referencias llevaba **veintidos dias** sin movimiento pese al trabajo de mantenimiento. Al contrastar tres reportes de fechas distintas demostro que no era atraso operativo: el mismo codigo estaba asignado a dos fichas de producto activas y el ERP no permite reutilizar codigos, asi que el caso requeria una decision de negocio, no mas trabajo.
- **Inventario disponible no confiable**: descubrio que cada cotizacion abierta reserva inventario, de modo que un backlog de cotizaciones sin cerrar distorsionaba el saldo disponible de toda la operacion. Dirigio la depuracion por canal y detecto ademas cotizaciones sin confirmar que ya tenian factura y movimiento de inventario, donde confirmarlas habria duplicado el movimiento. Se trato caso por caso en lugar de aplicar una correccion masiva.
- **Decision irreversible identificada a tiempo**: en la operacion de Mexico el requisito aduanero exige que cada unidad de inventario exista individualmente con su numero de pedimento, algo que va contra la logica de unidades agregadas del ERP. Senalo que el cambio debia decidirse antes de cargar el inventario inicial, porque despues no habria vuelta atras y la base todavia estaba limpia.

## Como reporta un hallazgo grave

Al encontrar el grupo de pedidos sin registro de entrada en el ERP, Ferney **no afirmo la causa, porque no la tenia**. Planteo las dos hipotesis posibles — el conector dejo de importar, o el script quedo descalibrado tras la migracion de servidores — y propuso una prueba unica que las distinguia: revisar un pedido especifico en el ERP. Si estaba, el problema era del reporte; si no estaba, el problema era mayor.

Esa forma de reportar convierte una alarma en una verificacion de quince minutos, y protege la credibilidad del reporte: si el hallazgo hubiera sido un falso positivo del script, el correo ya lo contemplaba.

## Los principios de trabajo que confirmo el proyecto

1. **No automatizar errores**: depurar el proceso antes de construir encima. Varios requerimientos se cerraron sin escribir una linea de codigo.
2. **La adopcion vale mas que la construccion**: ningun desarrollo subio a produccion sin capacitacion previa.
3. **Orquestar en lugar de programar**: la direccion define el que y protege el tiempo de quien ejecuta el como, sobre todo cuando ese recurso es uno solo.
4. **Documentar todo**: si el unico que entiende el sistema es quien lo monto, el trabajo no esta terminado.
5. **El punto de madurez no es corregir mas rapido, sino que las correcciones sean minimas**: evitar que se escriban productos a mano resuelve el problema de raiz; corregir el resultado solo lo administra.

## Tecnologias

Odoo 19 Enterprise (inventario, manufactura, facturacion, contabilidad, punto de venta); conectores de comercio electronico con Shopify, Amazon, TikTok Shop y Mercado Libre; facturacion electronica con requisitos fiscales de Colombia y Mexico (CFDI 4.0 y timbrado); migracion de servidor en la nube; y desarrollo propio en Python — Odoo XML-RPC, Shopify Admin API, openpyxl, bitacora JSONL, respaldo CSV.
