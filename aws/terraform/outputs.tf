# Lo que hay que saber despues de desplegar.

output "url_funcion" {
  description = "La direccion publica del asistente. Esto es lo que consume el portafolio"
  value       = aws_lambda_function_url.publica.function_url
}

output "repositorio_ecr" {
  description = "Donde subir la imagen cuando cambie el codigo"
  value       = aws_ecr_repository.imagen.repository_url
}

output "bucket_indice" {
  description = "Donde subir el indice cuando se reindexe el perfil"
  value       = aws_s3_bucket.indice.id
}

output "grupo_logs" {
  description = "Donde mirar cuando algo falle"
  value       = aws_cloudwatch_log_group.lambda.name
}
