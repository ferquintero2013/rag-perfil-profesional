# Lo que cambia entre entornos o no debe estar escrito en el repositorio.

variable "region" {
  description = "Region de AWS"
  type        = string
  default     = "us-east-1"
}

variable "nombre_proyecto" {
  description = "Prefijo para nombrar los recursos"
  type        = string
  default     = "rag-portafolio"
}

variable "bucket_indice" {
  description = "Bucket donde vive el indice. El nombre es unico en todo AWS, no solo en la cuenta"
  type        = string
}

variable "prefijo_indice" {
  description = "Carpeta dentro del bucket"
  type        = string
  default     = "indice"
}

variable "origenes_permitidos" {
  description = "Dominios que pueden llamar a la funcion desde un navegador"
  type        = list(string)
  default     = ["https://ferney-portfolio.vercel.app"]
}

# --- Secretos ---
#
# sensitive = true evita que Terraform los imprima en la salida de plan y
# apply. No los cifra: siguen en claro en el archivo de estado, que por eso
# tambien esta en .gitignore.
#
# Para un proyecto de verdad esto iria en Secrets Manager o en Parameter
# Store, y la funcion los leeria al arrancar. Aqui se deja asi a proposito
# para que se vea la diferencia cuando toque mejorarlo.

variable "openai_api_key" {
  description = "Clave de OpenAI"
  type        = string
  sensitive   = true
}

variable "supabase_url" {
  description = "URL del proyecto de Supabase para el registro de consultas"
  type        = string
  sensitive   = true
  default     = ""
}

variable "supabase_key" {
  description = "Clave publicable de Supabase, con permiso de INSERT unicamente"
  type        = string
  sensitive   = true
  default     = ""
}
