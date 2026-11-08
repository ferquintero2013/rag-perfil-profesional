# Proyecto: migracion de un sistema RAG en produccion a AWS

> Periodo: octubre y noviembre de 2026. Proyecto propio, codigo abierto.
> Repositorio: https://github.com/ferquintero2013/rag-perfil-profesional
> El Terraform completo esta en la carpeta `aws/terraform/` de ese repositorio.

## Que hizo

Movio a AWS el chatbot RAG de su portafolio, que ya estaba funcionando en Vercel, y dejo toda la infraestructura declarada en Terraform.

El sistema corre hoy en los dos sitios a la vez, con el mismo motor y sin duplicar logica. Vercel sigue siendo el despliegue oficial del portafolio; AWS es el mismo codigo sobre Lambda.

El punto de partida fue un diagnostico, no una curiosidad: al revisar las ofertas senior de IA a las que estaba aplicando, el requisito que se repetia no era LLMs ni RAG, que ya tenia construidos, sino cloud e infraestructura. En lugar de empezar un proyecto nuevo, migro uno que ya estaba en produccion, porque eso deja algo que un proyecto de ejercicio no deja: una comparacion entre el antes y el despues.

## Arquitectura en AWS

| Servicio | Para que |
|---|---|
| Lambda | Ejecuta el motor, desplegado desde imagen de contenedor y no desde zip |
| ECR | Guarda la imagen, con politica de ciclo de vida que conserva solo las 3 ultimas |
| S3 | Guarda el indice de embeddings, con acceso publico bloqueado |
| IAM | Rol propio de la funcion, con permiso de lectura sobre un solo prefijo |
| CloudWatch | Logs con 14 dias de retencion |
| Terraform | Los 8 recursos, declarados y versionados |

## Decisiones tecnicas destacadas

**Imagen de contenedor en vez de zip.** numpy trae extensiones compiladas en C. Instalado en Windows y subido a Lambda, falla al importar, porque el binario es para otro sistema operativo. El contenedor resuelve eso compilando las dependencias sobre Amazon Linux, que es donde la funcion va a correr de verdad.

**El indice fuera del despliegue.** El indice son 593 KB y cabria dentro de la imagen. Se puso en S3 para separar los datos del codigo: asi, actualizar el perfil es subir un archivo, y no reconstruir una imagen de 225 MB y volver a desplegar.

**Un solo archivo para las dos plataformas.** El modulo de recuperacion decide de donde lee el indice segun exista la variable `INDEX_BUCKET`: de S3 si esta, del disco si no. Lo que cambia entre Vercel y Lambda no es la logica, es donde viven los datos. Dos copias del archivo se habrian desincronizado a la primera correccion.

**Menor privilegio de verdad.** El rol no dice "puede usar S3". Dice que puede ejecutar `s3:GetObject`, solo bajo el prefijo del indice, solo en ese bucket. Si la funcion se viera comprometida, eso es todo lo que se obtiene.

**Rol en vez de credenciales.** La funcion no lleva llaves de acceso. Asume un rol al arrancar y AWS le entrega credenciales temporales que rota solo. Este concepto se entendio fallando: el contenedor corriendo en local dio `NoCredentialsError` con el codigo correcto y el archivo en su sitio, porque le faltaba identidad.

**Terraform sobre infraestructura que ya existia.** El bucket y el repositorio de ECR se habian creado antes por linea de comandos. En vez de borrarlos y recrearlos, se importaron al estado de Terraform, que es lo normal cuando una infraestructura empieza a mano y se formaliza despues.

**Sin API Gateway.** Aporta autenticacion, limites de tasa y dominios propios, y aqui no hacia falta nada de eso. Se uso una Function URL. Agregar un servicio solo para poder decir que se uso es sobreingenieria, y un buen entrevistador lo pregunta.

## Lo que midio, y lo que la medicion desmintio

La migracion se cerro midiendola, no declarandola terminada.

**La latencia no mejoro.** Vercel responde en 2266 ms en caliente y AWS en 3004 ms. Entre dos y tres segundos de cada respuesta son las llamadas a OpenAI, identicas en cualquier plataforma. El README lo dice con esas palabras, porque afirmar que la migracion gano velocidad seria falso y se cae a la primera repregunta.

**La configuracion de memoria estaba justificada con una creencia, no con un dato.** Se habia puesto 1024 MB con el argumento, muy repetido, de que en Lambda la memoria asigna CPU y por tanto acelera el arranque. Al medir cuatro arranques en frio por tamano, la diferencia entre 512 y 2048 MB fue de 35 ms, mientras la dispersion dentro de un mismo tamano era de 617 ms. El arranque de este sistema es espera de disco y red, no calculo, y la CPU de mas no acelera una espera. Se bajo a 512 MB: la mitad de costo, el mismo rendimiento.

## Dos problemas que costaron tiempo, y como se resolvieron

**Un 403 sin rastro en los logs.** Una Function URL publica necesita dos permisos de Lambda, no uno: `lambda:InvokeFunctionUrl` con la condicion del tipo de autenticacion, y `lambda:InvokeFunction` sin ella. Con solo el primero, la URL devuelve `403 AccessDeniedException` a todo el mundo y la funcion ni se entera, porque la peticion muere en el borde sin dejar una linea en CloudWatch. La documentacion describe el primero y la consola crea los dos en silencio, de donde sale el clasico "desde la consola funciona pero por codigo no".

Antes de encontrarlo se descartaron, con evidencia, seis hipotesis: politica corrupta, URL en mal estado, SCP de organizacion, qualifier desalineado, concurrencia en cero y problema del cliente HTTP. La causa se demostro quitando el permiso y viendo volver el error, no suponiendo.

**Una copia desactualizada que funcionaba.** Al revisar antes de documentar, aparecio que el modulo de recuperacion desplegado en Vercel llevaba dias 62 lineas por detras de la fuente. No fallaba, y por eso nadie lo habia notado: la version vieja leia del disco, que es justo lo que Vercel necesita. El script de distribucion cubria Vercel pero no AWS, asi que la copia de AWS se habia hecho a mano y quedo huerfana.

La leccion, que es la que importa: anadir un despliegue sin extender el mecanismo de distribucion crea una copia huerfana, y una copia huerfana que funciona es peor que una que falla, porque nadie la revisa. El script ahora distribuye a los dos destinos desde un solo origen.

## Higiene de la cuenta

Antes de crear nada se reviso la cuenta. Habia un usuario IAM sin usar desde hacia 604 dias con permisos de administrador y acceso a consola sin segundo factor. Se elimino. Se activo MFA en la raiz, se creo un usuario de solo linea de comandos para el trabajo diario y se puso un presupuesto mensual con alerta antes de desplegar el primer recurso.

## Que demuestra este proyecto

- Despliegue en AWS de un sistema real, no de un ejercicio
- Infraestructura como codigo, que era el requisito literal de varias ofertas
- Contenedores aplicados a un problema concreto y explicable
- Permisos disenados con menor privilegio, no copiados de un tutorial
- Observabilidad con retencion y control de costo definidos desde el principio
- Capacidad de depurar un fallo que no deja logs, descartando hipotesis con evidencia
- Disposicion a medir una decision propia y a corregirla cuando el dato la contradice

## Tecnologias

AWS Lambda, Amazon ECR, Amazon S3, AWS IAM, Amazon CloudWatch, Terraform, Docker, Python, boto3, numpy.
