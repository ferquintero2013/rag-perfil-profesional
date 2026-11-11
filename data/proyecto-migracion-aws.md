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
| GitHub Actions | Despliega en cada push a `main` que toque el codigo de la funcion |
| IAM / OIDC | GitHub se autentica sin llaves guardadas, asumiendo un rol con permisos acotados al despliegue |
| Terraform | Los 11 recursos, declarados y versionados |

## Decisiones tecnicas destacadas

**Imagen de contenedor en vez de zip.** numpy trae extensiones compiladas en C. Instalado en Windows y subido a Lambda, falla al importar, porque el binario es para otro sistema operativo. El contenedor resuelve eso compilando las dependencias sobre Amazon Linux, que es donde la funcion va a correr de verdad.

**El indice fuera del despliegue.** El indice son 593 KB y cabria dentro de la imagen. Se puso en S3 para separar los datos del codigo: asi, actualizar el perfil es subir un archivo, y no reconstruir una imagen de 225 MB y volver a desplegar.

**Un solo archivo para las dos plataformas.** El modulo de recuperacion decide de donde lee el indice segun exista la variable `INDEX_BUCKET`: de S3 si esta, del disco si no. Lo que cambia entre Vercel y Lambda no es la logica, es donde viven los datos. Dos copias del archivo se habrian desincronizado a la primera correccion.

**Menor privilegio de verdad.** El rol no dice "puede usar S3". Dice que puede ejecutar `s3:GetObject`, solo bajo el prefijo del indice, solo en ese bucket. Si la funcion se viera comprometida, eso es todo lo que se obtiene.

**Rol en vez de credenciales.** La funcion no lleva llaves de acceso. Asume un rol al arrancar y AWS le entrega credenciales temporales que rota solo. Este concepto se entendio fallando: el contenedor corriendo en local dio `NoCredentialsError` con el codigo correcto y el archivo en su sitio, porque le faltaba identidad.

**Terraform sobre infraestructura que ya existia.** El bucket y el repositorio de ECR se habian creado antes por linea de comandos. En vez de borrarlos y recrearlos, se importaron al estado de Terraform, que es lo normal cuando una infraestructura empieza a mano y se formaliza despues.

**Sin API Gateway.** Aporta autenticacion, limites de tasa y dominios propios, y aqui no hacia falta nada de eso. Se uso una Function URL. Agregar un servicio solo para poder decir que se uso es sobreingenieria, y un buen entrevistador lo pregunta.

## Despliegue automatico

Hasta noviembre el despliegue era manual: construir la imagen, subirla a ECR y correr `update-function-code` a mano. Eso se automatizo con GitHub Actions. El pipeline se dispara en cada push a `main` que toque el codigo de la funcion, y tambien a mano cuando hace falta. Los cambios de Terraform estan excluidos del disparador a proposito: la infraestructura se aplica deliberadamente, no por empujar un commit.

**Primero la entrega, no la validacion.** Lo que hay montado hoy es la parte de entrega. No hay suite de pruebas corriendo sobre cada pull request, y conviene decirlo asi en vez de llamarlo "CI/CD" sin matices. Lo que sustituye a las pruebas por ahora es una prueba de humo al final del despliegue.

**Sin llaves guardadas, con OIDC.** La alternativa habitual es crear un usuario IAM, generar una clave de acceso y pegarla en los secretos del repositorio. Esa clave no expira y sirve desde cualquier parte: si se filtra, sigue funcionando. En vez de eso, GitHub firma un token en cada ejecucion que declara de que repositorio y de que rama viene. AWS verifica la firma contra un proveedor OIDC registrado, comprueba esa declaracion contra la condicion del rol, y entrega credenciales que caducan con el trabajo. Es un pase de visitante, no una copia de la llave.

Son tres piezas distintas, y confundirlas es el error tipico: el proveedor OIDC dice "confia en lo que firme GitHub"; la politica de confianza del rol dice "pero solo desde este repositorio y esta rama"; y la politica de permisos dice "y esto es todo lo que puede hacer". La condicion es la cerradura de verdad. Sin ella, cualquier repositorio de GitHub podria asumir el rol.

**Permisos acotados al trabajo.** El rol del pipeline no es administrador. Puede pedir el token de ECR, empujar y leer imagenes en un unico repositorio, y actualizar el codigo de una unica funcion. No puede crear infraestructura, ni borrar nada, ni tocar otra funcion.

**La frontera de propiedad entre Terraform y el pipeline.** Terraform declara que la funcion existe y como esta configurada. El pipeline decide que version del codigo corre dentro. Si no se marca `image_uri` como ignorado en el ciclo de vida del recurso, el siguiente `terraform apply` revierte en silencio el ultimo despliegue, porque para Terraform la etiqueta de imagen que tiene escrita es la verdad. Terraform es dueno de los recursos; el pipeline es dueno de la version del codigo.

**Una prueba de humo que no cuesta nada.** Al terminar, el pipeline invoca la funcion con un cuerpo vacio. El handler devuelve 400 antes de llamar a OpenAI, asi que no gasta un solo token. Pero para llegar a ese 400 la funcion ya tuvo que arrancar la imagen nueva, importar numpy y bajar el indice desde S3, porque el indice se carga al importar el modulo y no dentro del handler. Si cualquiera de esas tres cosas falla, el trabajo falla. Es la verificacion mas barata que cubre el arranque completo.

## Lo que midio, y lo que la medicion desmintio

La migracion se cerro midiendola, no declarandola terminada.

**La latencia no mejoro.** Vercel responde en 2266 ms en caliente y AWS en 3004 ms. Entre dos y tres segundos de cada respuesta son las llamadas a OpenAI, identicas en cualquier plataforma. El README lo dice con esas palabras, porque afirmar que la migracion gano velocidad seria falso y se cae a la primera repregunta.

**La configuracion de memoria estaba justificada con una creencia, no con un dato.** Se habia puesto 1024 MB con el argumento, muy repetido, de que en Lambda la memoria asigna CPU y por tanto acelera el arranque. Al medir cuatro arranques en frio por tamano, la diferencia entre 512 y 2048 MB fue de 35 ms, mientras la dispersion dentro de un mismo tamano era de 617 ms. El arranque de este sistema es espera de disco y red, no calculo, y la CPU de mas no acelera una espera. Se bajo a 512 MB: la mitad de costo, el mismo rendimiento.

## Problemas que costaron tiempo, y como se resolvieron

**Un 403 sin rastro en los logs.** Una Function URL publica necesita dos permisos de Lambda, no uno: `lambda:InvokeFunctionUrl` con la condicion del tipo de autenticacion, y `lambda:InvokeFunction` sin ella. Con solo el primero, la URL devuelve `403 AccessDeniedException` a todo el mundo y la funcion ni se entera, porque la peticion muere en el borde sin dejar una linea en CloudWatch. La documentacion describe el primero y la consola crea los dos en silencio, de donde sale el clasico "desde la consola funciona pero por codigo no".

Antes de encontrarlo se descartaron, con evidencia, seis hipotesis: politica corrupta, URL en mal estado, SCP de organizacion, qualifier desalineado, concurrencia en cero y problema del cliente HTTP. La causa se demostro quitando el permiso y viendo volver el error, no suponiendo.

**Una copia desactualizada que funcionaba.** Al revisar antes de documentar, aparecio que el modulo de recuperacion desplegado en Vercel llevaba dias 62 lineas por detras de la fuente. No fallaba, y por eso nadie lo habia notado: la version vieja leia del disco, que es justo lo que Vercel necesita. El script de distribucion cubria Vercel pero no AWS, asi que la copia de AWS se habia hecho a mano y quedo huerfana.

La leccion, que es la que importa: anadir un despliegue sin extender el mecanismo de distribucion crea una copia huerfana, y una copia huerfana que funciona es peor que una que falla, porque nadie la revisa. El script ahora distribuye a los dos destinos desde un solo origen.

**Un `AccessDenied` que el log no podia explicar.** El primer despliegue automatico fallo al asumir el rol. La politica de confianza desplegada coincidia exactamente con lo que se habia escrito, y el registro de GitHub solo decia que no estaba autorizado, sin mas. Esa parquedad es deliberada: explicar por que se rechaza un token seria filtrar informacion a traves de la frontera de confianza, asi que AWS no lo explica. El diagnostico estaba al otro lado, en el evento `AssumeRoleWithWebIdentity` de CloudTrail, que si guarda el sujeto que se presento de verdad.

La causa: GitHub ya no manda el nombre del repositorio en texto plano, sino identificadores inmutables, con la forma `repo:propietario@id/repositorio@id:ref:refs/heads/main`. La condicion estaba escrita con el nombre simple y nunca podia coincidir. El cambio no es un detalle burocratico: ata el permiso a una identidad y no a un nombre, de modo que un repositorio borrado y vuelto a crear con el mismo nombre no hereda el acceso.

**Una imagen que se construia bien y Lambda rechazaba.** Con el rol ya funcionando, el despliegue fallo al actualizar la funcion: el tipo de medio del manifiesto no era compatible. Lambda exige un manifiesto unico en formato Docker v2 esquema 2. BuildKit, que es el constructor por defecto hoy, emite tipos de medio OCI y adjunta ademas certificados de procedencia y un inventario de dependencias, lo que convierte la publicacion en una lista de manifiestos en vez de uno solo. Nada de eso se ve construyendo en local; aparece al desplegar. Se resolvio desactivando esos adjuntos y pidiendo explicitamente tipos de medio de Docker.

Las dos fallas comparten una leccion: el error aparece donde esta la frontera, y "funciona en mi maquina" no ejercita la frontera del despliegue. Produccion nunca se vio afectada, porque la actualizacion fallo y la imagen anterior siguio atendiendo.

## Higiene de la cuenta

Antes de crear nada se reviso la cuenta. Habia un usuario IAM sin usar desde hacia 604 dias con permisos de administrador y acceso a consola sin segundo factor. Se elimino. Se activo MFA en la raiz, se creo un usuario de solo linea de comandos para el trabajo diario y se puso un presupuesto mensual con alerta antes de desplegar el primer recurso.

## Que demuestra este proyecto

- Despliegue en AWS de un sistema real, no de un ejercicio
- Infraestructura como codigo, que era el requisito literal de varias ofertas
- Despliegue continuo real, con autenticacion federada sin llaves guardadas y permisos acotados al despliegue
- Criterio para separar lo que es dueno Terraform de lo que es dueno el pipeline
- Contenedores aplicados a un problema concreto y explicable
- Permisos disenados con menor privilegio, no copiados de un tutorial
- Observabilidad con retencion y control de costo definidos desde el principio
- Capacidad de depurar un fallo que no deja logs, descartando hipotesis con evidencia
- Disposicion a medir una decision propia y a corregirla cuando el dato la contradice

## Tecnologias

AWS Lambda, Amazon ECR, Amazon S3, AWS IAM, AWS STS, AWS CloudTrail, Amazon CloudWatch, Terraform, Docker, BuildKit, GitHub Actions, OIDC, Python, boto3, numpy.
