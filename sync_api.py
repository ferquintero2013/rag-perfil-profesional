"""Copia el motor del RAG a los dos despliegues.

La fuente de verdad del codigo es ESTE repositorio. Aqui se desarrolla y se
prueba, y desde aqui se distribuye. Los destinos no se editan a mano.

    Vercel   la API vive dentro del repositorio del portafolio, para
             compartir dominio con el sitio y ahorrarse el CORS. Vercel
             convierte en endpoint cualquier .py dentro de /api/ salvo los
             que empiezan por guion bajo, de ahi el renombrado a _rag.py.

    AWS      aws/ es el contexto de build de Docker, asi que los modulos
             tienen que estar fisicamente dentro de esa carpeta para entrar
             en la imagen. Se mantiene el mismo prefijo para que el handler
             importe igual en los dos sitios.

Por que este script existe y no bastaba con uno de los dos destinos: cuando
solo sincronizaba Vercel, la copia de aws/ se hizo a mano y las dos se
separaron en la primera correccion. El retriever de Vercel se quedo sin la
rama de S3 durante dias. Un motor en tres copias sin un solo origen produce,
antes o despues, dos asistentes que responden distinto a la misma pregunta.

Que va a cada destino no es lo mismo: Vercel necesita el indice al lado del
codigo, y AWS no, porque lo baja de S3 al arrancar.

Uso:  python sync_api.py
"""

import os
import re
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Los imports entre modulos hay que reescribirlos al renombrarlos.
RENOMBRAR_IMPORTS = [
    (r"\bfrom retriever import\b", "from _retriever import"),
    (r"\bimport retriever\b", "import _retriever"),
    (r"\bfrom log import\b", "from _log import"),
    (r"\bimport log\b", "import _log"),
]

# Y en Vercel tambien el nombre de los archivos del indice, que viajan
# renombrados por la misma regla del guion bajo.
RENOMBRAR_INDICE = [
    (r'"index_meta\.json"', '"_index_meta.json"'),
    (r'"index_vectors\.npy"', '"_index_vectors.npy"'),
]

DESTINOS = {
    "Vercel": {
        "ruta": r"C:\proyectos_portafolio\Porfolio\api",
        "archivos": {
            "rag.py": "_rag.py",
            "retriever.py": "_retriever.py",
            "log.py": "_log.py",
            "index_meta.json": "_index_meta.json",
            "index_vectors.npy": "_index_vectors.npy",
        },
        "reemplazos": RENOMBRAR_IMPORTS + RENOMBRAR_INDICE,
    },
    "AWS": {
        "ruta": os.path.join(BASE_DIR, "aws"),
        # Sin los archivos del indice: en Lambda vienen de S3, y meterlos en
        # la imagen anularia la razon de haberlos sacado.
        "archivos": {
            "rag.py": "_rag.py",
            "retriever.py": "_retriever.py",
            "log.py": "_log.py",
        },
        "reemplazos": RENOMBRAR_IMPORTS,
    },
}

CABECERA = (
    "# GENERADO POR sync_api.py. NO EDITAR A MANO.\n"
    "# La fuente esta en el repositorio rag-perfil-profesional:\n"
    "#   {origen}\n\n"
)


def sincronizar(nombre, destino):
    ruta = destino["ruta"]
    os.makedirs(ruta, exist_ok=True)
    print(f"{nombre}\n  {ruta}\n")

    problemas = 0
    for origen, nombre_destino in destino["archivos"].items():
        ruta_origen = os.path.join(BASE_DIR, origen)
        ruta_destino = os.path.join(ruta, nombre_destino)

        if not os.path.exists(ruta_origen):
            print(f"  FALTA  {origen}")
            problemas += 1
            continue

        if origen.endswith(".py"):
            with open(ruta_origen, encoding="utf-8") as f:
                contenido = f.read()

            for patron, reemplazo in destino["reemplazos"]:
                contenido = re.sub(patron, reemplazo, contenido)

            with open(ruta_destino, "w", encoding="utf-8") as f:
                f.write(CABECERA.format(origen=origen) + contenido)
        else:
            shutil.copy2(ruta_origen, ruta_destino)

        kb = os.path.getsize(ruta_destino) / 1024
        print(f"  OK     {origen:20} -> {nombre_destino:22} {kb:7.0f} KB")

    print()
    return problemas


if __name__ == "__main__":
    print("Sincronizando el motor del RAG\n")
    fallos = sum(sincronizar(n, d) for n, d in DESTINOS.items())

    if fallos:
        print(f"{fallos} archivo(s) sin copiar. Revisa antes de desplegar.")
    else:
        # Este mensaje decia que para AWS habia que reconstruir la imagen
        # y correr update-function-code a mano. Dejo de ser verdad el
        # 10 de noviembre de 2026, cuando el despliegue paso a GitHub
        # Actions, y siguio impreso una semana mas. Un mensaje
        # desactualizado es peor que no tener mensaje: se obedece.
        print("Para que el cambio llegue a produccion:")
        print("  Vercel  en el repositorio del portafolio: git add api/ y push")
        print("  AWS     el codigo lo despliega el pipeline al hacer push")
        print("          a main. El indice no va en la imagen: se sube")
        print("          con publicar_indice.py y no necesita redespliegue.")
