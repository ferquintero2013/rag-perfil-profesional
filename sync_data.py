import os
import shutil

PERFIL_DIR = r"c:\Users\Usuario\Documents\Estudio claude\Agente personal\perfil"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# ALLOWLIST: de perfil/ solo se copian estos archivos.
# Cualquier archivo nuevo alli es PRIVADO por defecto — publicar tiene que
# ser un acto deliberado, no un descuido posible.
ARCHIVOS_PUBLICOS = [
    "cv.md",
    "portafolio.md",
    "habilidades.md",
    "resumen-ejecutivo.md",
]


def sync():
    """Copia los archivos de la allowlist, sin tocar el contenido propio.

    En data/ conviven dos origenes:

      - Copias de perfil/, que este script gestiona. Se sobrescriben en
        cada ejecucion, asi que editarlas aqui no sirve de nada: la fuente
        de verdad es perfil/.

      - Archivos propios del asistente, puestos a mano. Notas de proyecto,
        preguntas frecuentes, casos de estudio... contenido que pertenece
        al asistente y no al perfil de coaching. Estos NO se tocan.

    Solo se borran los que este script mismo copia. Borrar todo dejaria
    fuera el contenido propio en la siguiente ejecucion, y en silencio.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    # Se limpian solo las copias gestionadas, para que un archivo retirado
    # de la allowlist tampoco siga publicado.
    for nombre in ARCHIVOS_PUBLICOS:
        ruta = os.path.join(DATA_DIR, nombre)
        if os.path.exists(ruta):
            os.remove(ruta)

    copiados = []
    for nombre in ARCHIVOS_PUBLICOS:
        origen = os.path.join(PERFIL_DIR, nombre)

        if not os.path.exists(origen):
            print(f"  AVISO   {nombre} no existe en perfil/, se omite")
            continue

        destino = os.path.join(DATA_DIR, nombre)
        shutil.copy2(origen, destino)
        copiados.append(nombre)
        print(f"  perfil  {nombre:26} {os.path.getsize(destino) / 1024:6.1f} KB")

    # Lo que vive en data/ sin venir de perfil/: contenido propio.
    propios = sorted(
        f for f in os.listdir(DATA_DIR)
        if f.endswith(".md") and f not in ARCHIVOS_PUBLICOS
    )
    for nombre in propios:
        ruta = os.path.join(DATA_DIR, nombre)
        print(f"  propio  {nombre:26} {os.path.getsize(ruta) / 1024:6.1f} KB")

    # Lo que existe en perfil/ y NO se publica. Se lista siempre: un
    # control de privacidad que no se ve acaba olvidandose.
    todos = [f for f in os.listdir(PERFIL_DIR) if f.endswith(".md")]
    excluidos = sorted(f for f in todos if f not in ARCHIVOS_PUBLICOS)
    if excluidos:
        print(f"\n  Privados, no se publican: {', '.join(excluidos)}")

    return copiados, propios


if __name__ == "__main__":
    print("Sincronizando corpus del asistente...\n")
    copiados, propios = sync()
    total = len(copiados) + len(propios)
    print(f"\n  {total} archivos en el corpus "
          f"({len(copiados)} desde perfil/, {len(propios)} propios)")
    print("\n  Siguiente paso: python indexer.py")
