import json
import os
from datetime import date

import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

from loader import build_corpus

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

META_PATH = os.path.join(BASE_DIR, "index_meta.json")
VECTORS_PATH = os.path.join(BASE_DIR, "index_vectors.npy")
EMBEDDING_MODEL = "text-embedding-3-small"

# La API acepta varios textos por llamada. Agrupar evita 37 viajes de red
# donde basta con uno, y deja el indexado igual de barato cuando el corpus
# crezca a cientos o miles de chunks.
BATCH_SIZE = 100


def embed_batch(textos):
    """Genera los embeddings de varios textos en una sola llamada."""
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=textos
    )
    # La API devuelve el indice de cada entrada: ordenar por el es gratis
    # y elimina la suposicion de que el orden se conserva.
    return [d.embedding for d in sorted(response.data, key=lambda d: d.index)]


def build_index():
    """Construye el indice desde data/ y lo guarda en dos archivos planos.

    No se usa base de datos vectorial: a esta escala los embeddings caben
    en memoria y la busqueda es una multiplicacion de matriz (ver
    retriever.py). El umbral para replantearlo esta en torno a los 10.000
    chunks, cuando el .npy pase de unas decenas de MB.
    """
    corpus = build_corpus()
    print(f"\nGenerando embeddings para {len(corpus)} chunks...")

    vectores = []
    for inicio in range(0, len(corpus), BATCH_SIZE):
        lote = corpus[inicio:inicio + BATCH_SIZE]
        print(f"  [{inicio + 1}-{inicio + len(lote)}/{len(corpus)}]")
        vectores.extend(embed_batch([c["text"] for c in lote]))

    matriz = np.array(vectores, dtype=np.float32)

    # Se normaliza aqui, una vez. Con vectores de norma 1 la similitud
    # coseno es exactamente el producto punto, asi que el retriever no
    # tiene que normalizar en cada consulta.
    matriz /= np.linalg.norm(matriz, axis=1, keepdims=True)

    meta = {
        "model": EMBEDDING_MODEL,
        "dimensions": int(matriz.shape[1]),
        "count": len(corpus),
        "normalized": True,
        "exported": date.today().isoformat(),
        "chunks": [
            {
                "id": f"chunk_{i:03d}",
                "source": c["source"],
                "section": c["section"],
                "text": c["text"],
            }
            for i, c in enumerate(corpus)
        ],
    }

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    np.save(VECTORS_PATH, matriz)

    def kb(path):
        return os.path.getsize(path) / 1024

    print("\nIndice construido:")
    print(f"  {len(corpus)} chunks, {matriz.shape[1]} dimensiones")
    print(f"  {os.path.basename(META_PATH):22} {kb(META_PATH):7.0f} KB")
    print(f"  {os.path.basename(VECTORS_PATH):22} {kb(VECTORS_PATH):7.0f} KB")


if __name__ == "__main__":
    build_index()

    print("\n" + "=" * 60)
    print("PRUEBA DE BUSQUEDA")
    print("=" * 60)

    from retriever import retrieve

    pregunta = "¿Tiene experiencia con Python?"
    print(f"\n{pregunta}\n")
    for i, c in enumerate(retrieve(pregunta, n_results=3)):
        print(f"{i + 1}. [{c['source']}] {c['section'][:52]}")
