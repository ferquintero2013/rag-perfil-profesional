# -*- coding: utf-8 -*-
"""Sube el indice a S3, que es de donde lo lee Lambda.

Este es el eslabon que faltaba. `actualizar.py` decia existir "para que no
haya que acordarse de los cinco", y tenia cuatro pasos: copiar el perfil,
reconstruir el indice, evaluar y distribuir el motor. El indice llegaba a
Vercel, porque `sync_api.py` lo copia dentro del repositorio del
portafolio, pero a AWS no llegaba nunca: en Lambda el indice no viaja en
la imagen, vive en S3, y nadie lo subia.

Lo peor de ese hueco no era que fallara, era que no fallaba. El
despliegue terminaba en verde y Lambda seguia respondiendo con el perfil
viejo, sin una sola linea de error. Es el mismo error que ya esta
documentado en el README con otra victima: anadir un destino de
despliegue sin extender el mecanismo de distribucion. Se cometio dos
veces, la segunda sobre el aviso escrito de la primera.

Los nombres cambian al subir, igual que al copiar a Vercel:

    index_meta.json     ->  indice/_index_meta.json
    index_vectors.npy   ->  indice/_index_vectors.npy

El guion bajo no es decorativo. En Vercel, cualquier archivo de la carpeta
`api/` que no empiece por guion bajo se interpreta como una funcion
desplegable, y un .json no lo es. El prefijo lo excluye. En S3 no haria
falta, pero se mantiene el mismo nombre en los dos destinos: dos
convenciones para el mismo archivo es una trampa esperando.

El nombre del bucket NO esta escrito aqui. Sale de la variable de entorno
INDEX_BUCKET o, si no esta, de la salida de Terraform, que es donde vive
la verdad sobre que infraestructura existe. Escribirlo a mano en un
script seria una tercera copia que se desincroniza.
"""

import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TERRAFORM_DIR = os.path.join(BASE_DIR, "aws", "terraform")

PREFIJO = os.getenv("INDEX_PREFIX", "indice")

# origen local -> nombre en S3
ARCHIVOS = {
    "index_meta.json": "_index_meta.json",
    "index_vectors.npy": "_index_vectors.npy",
}


def bucket_desde_terraform():
    """Pregunta a Terraform como se llama el bucket.

    Es la fuente de verdad: Terraform es quien lo creo. Si no responde se
    devuelve None y el error lo explica arriba, en vez de reventar aqui
    con un mensaje de subproceso que no dice nada.
    """
    try:
        r = subprocess.run(
            ["terraform", "output", "-raw", "bucket_indice"],
            cwd=TERRAFORM_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    if r.returncode != 0:
        return None

    nombre = r.stdout.strip()
    return nombre or None


def resolver_bucket():
    desde_entorno = os.getenv("INDEX_BUCKET")
    if desde_entorno:
        return desde_entorno, "variable de entorno INDEX_BUCKET"

    desde_terraform = bucket_desde_terraform()
    if desde_terraform:
        return desde_terraform, "salida de Terraform"

    return None, None


def publicar():
    bucket, origen = resolver_bucket()

    if not bucket:
        print("  No se pudo determinar el bucket del indice.\n")
        print("  Define INDEX_BUCKET, o corre esto desde una maquina donde")
        print("  `terraform output` funcione:\n")
        print(f"    cd {TERRAFORM_DIR}")
        print("    terraform output -raw bucket_indice\n")
        return 1

    print(f"  bucket  {bucket}")
    print(f"  origen  {origen}")
    print(f"  prefijo {PREFIJO}/\n")

    # boto3 se importa aqui y no arriba: si falta el paquete, el mensaje
    # tiene que llegar despues de haber explicado que se iba a hacer.
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:
        print("  Falta boto3. Instalalo con: pip install boto3\n")
        return 1

    s3 = boto3.client("s3")

    for local, remoto in ARCHIVOS.items():
        ruta = os.path.join(BASE_DIR, local)

        if not os.path.exists(ruta):
            print(f"  FALTA   {local} no existe. Corre indexer.py primero.\n")
            return 1

        clave = f"{PREFIJO}/{remoto}"
        kb = os.path.getsize(ruta) / 1024

        try:
            s3.upload_file(ruta, bucket, clave)
        except (BotoCoreError, ClientError) as e:
            print(f"  FALLO   {local} -> s3://{bucket}/{clave}")
            print(f"          {type(e).__name__}: {e}\n")
            return 1

        print(f"  OK      {local:20} -> {clave:28} {kb:6.1f} KB")

    print("""
  Lambda lo lee al arrancar en frio, no en la siguiente invocacion: el
  indice queda en memoria mientras el contenedor viva. Si hay uno
  caliente va a seguir respondiendo con el indice anterior hasta que se
  recicle, unos minutos. No hay que redesplegar nada.""")

    return 0


if __name__ == "__main__":
    print("\nPublicando el indice en S3...\n")
    sys.exit(publicar())
