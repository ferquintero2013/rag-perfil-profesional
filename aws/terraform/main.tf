# Infraestructura del asistente del portafolio en AWS.
#
# Todo lo que existe en la cuenta para este proyecto esta descrito aqui. Eso
# es lo que significa infraestructura como codigo: no "hice unos clics y
# funciono", sino un archivo que cualquiera puede leer para saber que hay, y
# ejecutar para recrearlo desde cero.

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# -----------------------------------------------------------------------
# Donde vive el indice
# -----------------------------------------------------------------------

# Este bucket ya existia: se creo por CLI antes de escribir esto, y despues
# se importo al estado de Terraform. Importar en vez de recrear es lo normal
# cuando una infraestructura empieza a mano y se formaliza despues.
resource "aws_s3_bucket" "indice" {
  bucket = var.bucket_indice
}

# Nada de este bucket es publico. El unico que lo lee es la funcion, y lo
# hace con el rol de abajo.
resource "aws_s3_bucket_public_access_block" "indice" {
  bucket = aws_s3_bucket.indice.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# -----------------------------------------------------------------------
# Donde vive la imagen
# -----------------------------------------------------------------------

resource "aws_ecr_repository" "imagen" {
  name = var.nombre_proyecto

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Sin esto, cada despliegue deja atras la imagen anterior y el repositorio
# crece para siempre pagando almacenamiento por imagenes que nadie usa.
resource "aws_ecr_lifecycle_policy" "limpieza" {
  repository = aws_ecr_repository.imagen.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Conservar solo las 3 imagenes mas recientes"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 3
      }
      action = { type = "expire" }
    }]
  })
}

# -----------------------------------------------------------------------
# Quien es la funcion: el rol
# -----------------------------------------------------------------------
#
# Aqui esta la diferencia que vimos fallar en local. A la funcion no se le
# dan llaves: se le da un ROL que ella asume al arrancar. AWS le entrega
# credenciales temporales que rota solo y que nadie escribe en ningun lado.
#
# Un rol tiene dos partes y conviene no confundirlas:
#
#   quien puede asumirlo   -> assume_role_policy, abajo
#   que puede hacer        -> las policies que se le adjuntan

resource "aws_iam_role" "lambda" {
  name = "${var.nombre_proyecto}-lambda"

  # "El servicio Lambda, y solo el, puede asumir este rol."
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Permiso para escribir en CloudWatch. Sin esto la funcion corre pero no
# deja rastro, y depurar a ciegas en la nube es imposible.
resource "aws_iam_role_policy_attachment" "logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Y el permiso que de verdad importa: leer el indice.
#
# Fijate en lo estrecho que es. No dice "puede usar S3": dice que puede
# LEER objetos, y solo los que esten bajo el prefijo del indice, y solo en
# este bucket. Si manana la funcion se ve comprometida, eso es todo lo que
# el atacante consigue.
#
# Eso es el principio de menor privilegio, y es la diferencia entre decir
# que se sabe de cloud y demostrarlo.
resource "aws_iam_role_policy" "leer_indice" {
  name = "leer-indice"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject"]
      Resource = "${aws_s3_bucket.indice.arn}/${var.prefijo_indice}/*"
    }]
  })
}

# -----------------------------------------------------------------------
# La funcion
# -----------------------------------------------------------------------

resource "aws_lambda_function" "asistente" {
  function_name = var.nombre_proyecto
  role          = aws_iam_role.lambda.arn

  # Desde imagen de contenedor, no desde un zip. Por eso no hay runtime ni
  # handler aqui: los define el Dockerfile.
  package_type = "Image"
  image_uri    = "${aws_ecr_repository.imagen.repository_url}:latest"

  # El arranque en frio tiene que bajar el indice de S3, cargar numpy y
  # construir el indice BM25. 30 segundos da margen de sobra.
  timeout = 30

  # 512 MB, y el numero sale de medir, no de suponer.
  #
  # Es cierto que en Lambda la memoria tambien asigna CPU, asi que la
  # intuicion dice que subirla acelera el arranque. Aqui no pasa. Cuatro
  # arranques en frio por tamano, mediana del Init Duration:
  #
  #    512 MB   2267 ms
  #   1024 MB   2240 ms
  #   1769 MB   2249 ms     (el umbral de 1 vCPU completa)
  #   2048 MB   2232 ms
  #
  # 35 ms de diferencia entre el menor y el mayor, con el cuadruple de
  # memoria. La dispersion DENTRO de un mismo tamano fue de 617 ms, o sea
  # casi veinte veces mayor que el efecto que se buscaba.
  #
  # La razon es que este arranque no gasta CPU: baja una imagen, importa
  # numpy y trae 593 KB de S3. Es espera de entrada y salida, y la CPU de
  # mas no acelera una espera.
  #
  # Max Memory Used en produccion: 182 MB. Reservar 1024 era pagar por el
  # doble de GB-segundo sin recibir nada a cambio.
  #
  # Queda escrito porque la version anterior de este comentario afirmaba lo
  # contrario, sin una sola medicion detras. En una entrevista eso se cae
  # con una pregunta.
  memory_size = 512

  # Cuantas ejecuciones simultaneas se permiten como maximo.
  #
  # Esta funcion esta detras de una URL publica sin autenticacion, y cada
  # invocacion gasta tokens de OpenAI. Sin este tope, mil peticiones a la vez
  # son mil llamadas al modelo corriendo en paralelo, y la factura la paga
  # quien no la provoco.
  #
  # No impide que alguien insista: acota el dano. Lo que sobra se rechaza con
  # un 429 en vez de ejecutarse. Para un asistente que nadie usa en rafagas,
  # dos simultaneas son de sobra.
  #
  # Conviene no confundirlo con el limite por IP que tiene la version de
  # Vercel: aquel vive en la memoria del proceso y cada instancia lleva el
  # suyo, asi que frena el abuso accidental pero no uno decidido. Este seria
  # un techo real, impuesto por la plataforma.
  #
  # ESTA DESACTIVADO, y no por descuido. AWS exige que queden al menos 10
  # ejecuciones sin reservar en la cuenta, y esta cuenta tiene un limite
  # total de 10, que es lo que dan las cuentas nuevas hasta que se pide
  # ampliacion (el estandar son 1000). Reservar aunque fuera 1 dejaria 9 y
  # la llamada se rechaza:
  #
  #   InvalidParameterValueException: Specified ReservedConcurrentExecutions
  #   decreases account's UnreservedConcurrentExecution below its minimum
  #   value of [10]
  #
  # Lo util es que ese techo de 10 ya cumple la funcion: el peor caso son 10
  # llamadas simultaneas al modelo, no infinitas. Y el unico limite que de
  # verdad no se puede saltar vive en la cuenta de OpenAI, no aqui.
  #
  # Se reactiva el dia que la cuenta suba de los 10, pidiendo ampliacion de
  # cuota en Service Quotas.
  # reserved_concurrent_executions = 2

  environment {
    variables = {
      INDEX_BUCKET   = aws_s3_bucket.indice.id
      INDEX_PREFIX   = var.prefijo_indice
      OPENAI_API_KEY = var.openai_api_key
      SUPABASE_URL   = var.supabase_url
      SUPABASE_KEY   = var.supabase_key
    }
  }
}

# CloudWatch crea el grupo de logs solo la primera vez, pero sin retencion:
# los guarda para siempre y se paga por ellos. Declararlo aqui permite fijar
# cuanto tiempo se conservan.
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.asistente.function_name}"
  retention_in_days = 14
}

# -----------------------------------------------------------------------
# Como se llega desde internet
# -----------------------------------------------------------------------
#
# Una Function URL, no API Gateway. API Gateway aporta autenticacion,
# limites de tasa y dominios propios, y aqui no hace falta nada de eso.
# Agregarlo solo para poder decir que se uso es sobreingenieria, y un buen
# entrevistador lo cuestionaria.
# Una Function URL publica necesita DOS permisos, no uno. Esto costo seis
# intentos de depuracion y es de los errores que mas tiempo hacen perder,
# porque la documentacion de AWS solo documenta el primero.
#
#   InvokeFunctionUrl   permite usar el endpoint de la URL
#   InvokeFunction      permite ejecutar la funcion
#
# Con solo el primero, la URL responde 403 AccessDeniedException a todo el
# mundo y la funcion ni se entera: la peticion muere en el borde, sin dejar
# una sola linea en CloudWatch.
#
# La consola de AWS crea los dos en silencio cuando eliges auth type NONE.
# Por API, CLI o Terraform hay que declararlos. De ahi viene el clasico
# "desde la consola funciona pero por codigo no".
resource "aws_lambda_permission" "url_publica" {
  statement_id           = "AllowPublicFunctionUrl"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.asistente.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

# El segundo va SIN function_url_auth_type. No es un olvido: AWS rechaza la
# llamada con "FunctionUrlAuthType is only supported for
# lambda:InvokeFunctionUrl action" si se intenta ponerla aqui.
resource "aws_lambda_permission" "invocar" {
  statement_id  = "FunctionURLAllowInvokeAction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.asistente.function_name
  principal     = "*"
}

resource "aws_lambda_function_url" "publica" {
  function_name      = aws_lambda_function.asistente.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = var.origenes_permitidos
    allow_methods = ["POST"]
    allow_headers = ["content-type"]
  }
}
