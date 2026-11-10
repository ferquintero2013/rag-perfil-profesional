# Quien puede desplegar, y desde donde.
#
# El problema a resolver: GitHub necesita permiso para subir una imagen a ECR
# y actualizar la funcion. La forma facil es crear un usuario de IAM, sacarle
# una clave de acceso y pegarla en los secretos del repositorio. Funciona, y
# es exactamente lo que no se hace, por dos razones:
#
#   1. Esa clave no caduca. Vive ahi hasta que alguien se acuerde de rotarla,
#      y nadie se acuerda.
#   2. Cualquiera con acceso al repositorio puede usarla fuera de GitHub.
#
# La alternativa es OIDC, y es el mismo principio que ya aplica la funcion
# Lambda unas lineas mas abajo en main.tf: identidades que asumen un rol, no
# credenciales permanentes.
#
# Como funciona: en cada ejecucion GitHub emite un token firmado por el que
# dice quien es, que repositorio es y que rama. AWS verifica la firma contra
# este proveedor, comprueba que coincida con lo que dice la condicion de
# abajo, y entrega credenciales temporales que duran lo que dure el job.
# No hay nada guardado que robar.

resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  # A quien va dirigido el token. Es el valor que usa la accion oficial de AWS.
  client_id_list = ["sts.amazonaws.com"]

  # Huellas del certificado de GitHub. Desde 2023 AWS valida la cadena por su
  # cuenta y en la practica las ignora, pero el recurso las sigue aceptando y
  # se dejan las dos conocidas por si cambia.
  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd",
  ]
}

# -----------------------------------------------------------------------
# El rol que asume el pipeline
# -----------------------------------------------------------------------

resource "aws_iam_role" "github_actions" {
  name        = "${var.nombre_proyecto}-github-actions"
  description = "Lo asume GitHub Actions para desplegar. Solo desde main de un repositorio"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"

      # Esta condicion es el cierre de verdad. Sin ella, CUALQUIER repositorio
      # de GitHub, de cualquier persona del mundo, podria asumir este rol:
      # todos reciben tokens del mismo emisor.
      #
      # El campo sub lo escribe GitHub, no quien ejecuta el workflow, y dice
      # literalmente de que repositorio y de que rama viene. Al exigirlo exacto,
      # un fork no sirve, una rama distinta no sirve, y un pull request tampoco,
      # porque su sub tiene otra forma (pull_request en vez de ref).
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          "token.actions.githubusercontent.com:sub" = "repo:${var.repositorio_github}:ref:refs/heads/main"
        }
      }
    }]
  })
}

# Que puede hacer, y nada mas.
#
# Un repositorio ECR, una funcion Lambda. No puede crear recursos, no puede
# leer el bucket del indice, no puede tocar otra funcion ni otro repositorio.
# Si manana alguien se cuela en el pipeline, el radio de dano es: publicar una
# imagen y cambiar el codigo de esta funcion. Que ya es bastante, y por eso la
# condicion de arriba importa tanto.
resource "aws_iam_role_policy" "desplegar" {
  name = "desplegar"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Pedir el token de sesion de ECR. Es la unica accion de las tres que
        # no admite recurso concreto: AWS la define sobre toda la cuenta.
        Sid      = "AutenticarEnECR"
        Effect   = "Allow"
        Action   = "ecr:GetAuthorizationToken"
        Resource = "*"
      },
      {
        Sid    = "SubirLaImagen"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
        ]
        Resource = aws_ecr_repository.imagen.arn
      },
      {
        Sid    = "ActualizarYProbarLaFuncion"
        Effect = "Allow"
        Action = [
          "lambda:UpdateFunctionCode",
          "lambda:GetFunction",
          "lambda:GetFunctionConfiguration",
          "lambda:InvokeFunction",
        ]
        Resource = aws_lambda_function.asistente.arn
      },
    ]
  })
}
