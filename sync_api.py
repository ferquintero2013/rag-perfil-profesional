"""Copia el motor del RAG al repositorio del portafolio.

La API vive dentro del portafolio para compartir dominio con el sitio y
ahorrarse el CORS por completo. Pero la fuente de verdad del codigo sigue
siendo ESTE repositorio: aqui se desarrolla y se prueba, y desde aqui se
copia.

Vercel convierte en endpoint cualquier .py dentro de /api/, salvo los que
empiezan por guion bajo. Por eso los modulos viajan renombrados a
_rag.py y _retriever.py: si no, cada uno seria una ruta publica.

Uso:  python sync_api.py
"""

import os
import re
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DESTINO = r"C:\proyectos_portafolio\Porfolio\api"

# origen -> nombre en destino
ARCHIVOS = {
    "rag.py": "_rag.py",
    "retriever.py": "_retriever.py",
    "index_meta.json": "_index_meta.json",
    "index_vectors.npy": "_index_vectors.npy",
}

# Los imports entre modulos hay que reescribirlos al renombrarlos.
REEMPLAZOS = [
    (r"\bfrom retriever import\b", "from _retriever import"),
    (r"\bimport retriever\b", "import _retriever"),
    (r'"index_meta\.json"', '"_index_meta.json"'),
    (r'"index_vectors\.npy"', '"_index_vectors.npy"'),
]


def sync():
    os.makedirs(DESTINO, exist_ok=True)

    for origen, nombre_destino in ARCHIVOS.items():
        ruta_origen = os.path.join(BASE_DIR, origen)
        ruta_destino = os.path.join(DESTINO, nombre_destino)

        if not os.path.exists(ruta_origen):
            print(f"  FALTA  {origen}")
            continue

        if origen.endswith(".py"):
            with open(ruta_origen, encoding="utf-8") as f:
                contenido = f.read()

            for patron, reemplazo in REEMPLAZOS:
                contenido = re.sub(patron, reemplazo, contenido)

            cabecera = (
                "# GENERADO POR sync_api.py — NO EDITAR A MANO.\n"
                "# La fuente esta en el repositorio rag-perfil-profesional:\n"
                f"#   {origen}\n\n"
            )

            with open(ruta_destino, "w", encoding="utf-8") as f:
                f.write(cabecera + contenido)
        else:
            shutil.copy2(ruta_origen, ruta_destino)

        kb = os.path.getsize(ruta_destino) / 1024
        print(f"  OK     {origen:22} -> {nombre_destino:24} {kb:7.0f} KB")


if __name__ == "__main__":
    print(f"Sincronizando motor del RAG hacia:\n  {DESTINO}\n")
    sync()
    print("\nRecuerda: en el portafolio, 'git add api/' y push.")
