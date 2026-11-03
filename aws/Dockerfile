# Imagen base oficial de AWS para Lambda con Python.
#
# Esta linea resuelve sola el problema que motivo usar contenedores: las
# dependencias se compilan aqui dentro, sobre Amazon Linux, que es el mismo
# sistema donde va a correr la funcion. Instalar numpy en Windows y subir ese
# resultado a Lambda falla al importar, porque trae extensiones en C
# compiladas para otro sistema operativo.
FROM public.ecr.aws/lambda/python:3.12

# LAMBDA_TASK_ROOT es una variable que define la propia imagen base, y apunta
# a /var/task, que es donde Lambda busca el codigo al arrancar. Se usa la
# variable en vez de la ruta literal porque es el contrato de la imagen y
# podria cambiar.

# Las dependencias van antes que el codigo, y no es un detalle de estilo.
# Docker cachea cada instruccion por separado: si el codigo cambia pero
# requirements.txt no, esta capa se reutiliza y el build tarda segundos en
# vez de minutos. Al reves, cualquier cambio en el codigo invalidaria la
# instalacion entera.
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Ahora si el codigo: el motor del RAG y el adaptador para Lambda.
COPY _rag.py _retriever.py _log.py ${LAMBDA_TASK_ROOT}/
COPY handler.py ${LAMBDA_TASK_ROOT}/

# El indice ya NO viaja dentro de la imagen: vive en S3 y se baja en el
# arranque en frio. Eso es lo que permite reindexar el perfil subiendo un
# archivo, sin reconstruir la imagen ni volver a desplegar.
#
# De donde lo baja lo dice la variable INDEX_BUCKET, que se define al
# desplegar y no aqui: la imagen no debe saber contra que bucket corre.

# Que funcion invocar: el archivo handler.py, la funcion handler.
# Esto es el equivalente de decirle a Vercel cual es el endpoint, solo que
# aqui es explicito.
CMD [ "handler.handler" ]
