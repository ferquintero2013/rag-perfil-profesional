import os
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
from loader import build_corpus

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "perfil_ferney"
EMBEDDING_MODEL = "text-embedding-3-small"


def get_embedding(text):
    """Converts a text into a vector of 1536 dimensions."""
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


def build_index():
    """Generates embeddings for all chunks and stores them in ChromaDB."""
    corpus = build_corpus()
    print(f"\nGenerando embeddings para {len(corpus)} chunks...\n")

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Rebuild from scratch each run
    try:
        chroma_client.delete_collection(name=COLLECTION_NAME)
        print("  (coleccion anterior eliminada)\n")
    except Exception:
        pass

    collection = chroma_client.create_collection(name=COLLECTION_NAME)

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for idx, chunk in enumerate(corpus):
        print(f"  [{idx + 1}/{len(corpus)}] {chunk['section'][:60]}")

        ids.append(f"chunk_{idx:03d}")
        documents.append(chunk["text"])
        embeddings.append(get_embedding(chunk["text"]))
        metadatas.append({
            "source": chunk["source"],
            "section": chunk["section"]
        })

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(f"\nIndice creado: {collection.count()} chunks guardados en '{CHROMA_PATH}'")
    return collection


if __name__ == "__main__":
    collection = build_index()

    # Quick smoke test: does semantic search actually work?
    print("\n" + "=" * 60)
    print("PRUEBA DE BUSQUEDA SEMANTICA")
    print("=" * 60)

    pregunta = "¿Tiene experiencia con Python?"
    print(f"\nPregunta: {pregunta}\n")

    resultados = collection.query(
        query_embeddings=[get_embedding(pregunta)],
        n_results=3
    )

    for i, doc in enumerate(resultados["documents"][0]):
        meta = resultados["metadatas"][0][i]
        distancia = resultados["distances"][0][i]
        print(f"{i + 1}. [{meta['source']}] {meta['section']}")
        print(f"   distancia: {distancia:.4f}")
        print(f"   {doc[:150]}...\n")
