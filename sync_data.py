import os
import shutil

PERFIL_DIR = r"c:\Users\Usuario\Documents\Estudio claude\Agente personal\perfil"
DATA_DIR = "./data"

# ALLOWLIST: solo estos archivos se publican.
# Cualquier archivo nuevo en perfil/ es PRIVADO por defecto.
ARCHIVOS_PUBLICOS = [
    "cv.md",
    "portafolio.md",
    "habilidades.md",
    "resumen-ejecutivo.md",
]


def sync():
    """Copia solo los archivos de la allowlist a data/."""
    os.makedirs(DATA_DIR, exist_ok=True)

    # Limpiar data/ para que no queden archivos huerfanos
    for existente in os.listdir(DATA_DIR):
        if existente.endswith(".md"):
            os.remove(os.path.join(DATA_DIR, existente))

    copiados = []
    for nombre in ARCHIVOS_PUBLICOS:
        origen = os.path.join(PERFIL_DIR, nombre)

        if not os.path.exists(origen):
            print(f"  AVISO: {nombre} no existe en perfil/, se omite")
            continue

        destino = os.path.join(DATA_DIR, nombre)
        shutil.copy2(origen, destino)
        tam = os.path.getsize(destino)
        copiados.append(nombre)
        print(f"  OK  {nombre}  ({tam} bytes)")

    # Reportar lo que NO se copio, para revision consciente
    todos = [f for f in os.listdir(PERFIL_DIR) if f.endswith(".md")]
    excluidos = [f for f in todos if f not in ARCHIVOS_PUBLICOS]

    if excluidos:
        print(f"\n  Excluidos (privados): {', '.join(excluidos)}")

    return copiados


if __name__ == "__main__":
    print("Sincronizando corpus publico desde perfil/...\n")
    copiados = sync()
    print(f"\n{len(copiados)} archivos sincronizados a {DATA_DIR}")
    print("\nSiguiente paso: python indexer.py")
