import os
import re
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Path relativo AL ARCHIVO, no al directorio de trabajo: en Streamlit Cloud
# el cwd no es necesariamente la raiz del proyecto.
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "perfil_ferney"
EMBEDDING_MODEL = "text-embedding-3-small"

# --- Load index once at import ---
_chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

try:
    _collection = _chroma_client.get_collection(name=COLLECTION_NAME)
except Exception as e:
    raise RuntimeError(
        f"No se encontro el indice '{COLLECTION_NAME}' en {CHROMA_PATH}. "
        "Construyelo con: python sync_data.py && python indexer.py"
    ) from e

_all = _collection.get(include=["documents", "metadatas"])
_ids = _all["ids"]
_docs = _all["documents"]
_metas = _all["metadatas"]

_by_id = {
    _ids[i]: {
        "text": _docs[i],
        "source": _metas[i]["source"],
        "section": _metas[i]["section"]
    }
    for i in range(len(_ids))
}


def tokenize(text):
    """Splits text into lowercase words for keyword matching."""
    return re.findall(r"[a-z0-9aeiouñ]+", text.lower())


_bm25 = BM25Okapi([tokenize(d) for d in _docs])


def get_embedding(text):
    """Converts a text into a vector of 1536 dimensions."""
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


def search_semantic(question, n=10):
    """Vector search: finds chunks with similar MEANING."""
    results = _collection.query(
        query_embeddings=[get_embedding(question)],
        n_results=n
    )
    return results["ids"][0]


def search_keyword(question, n=10):
    """BM25 search: finds chunks with matching WORDS."""
    scores = _bm25.get_scores(tokenize(question))
    ranked = sorted(zip(_ids, scores), key=lambda pair: -pair[1])
    return [chunk_id for chunk_id, score in ranked[:n] if score > 0]


def reciprocal_rank_fusion(rankings, k=60):
    """Merges several rankings into one.

    A chunk that appears high in MULTIPLE rankings beats a chunk that
    appears very high in only one. k=60 is the standard damping constant.
    """
    scores = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking):
            scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda pair: -pair[1])


def retrieve(question, n_results=5):
    """Hybrid retrieval: semantic + keyword, merged with RRF."""
    semantic_ids = search_semantic(question, n=10)
    keyword_ids = search_keyword(question, n=10)

    fused = reciprocal_rank_fusion([semantic_ids, keyword_ids])

    chunks = []
    for chunk_id, score in fused[:n_results]:
        chunk = _by_id[chunk_id]
        chunks.append({
            "text": chunk["text"],
            "source": chunk["source"],
            "section": chunk["section"],
            "score": score
        })

    return chunks


if __name__ == "__main__":
    preguntas = [
        "¿Tiene experiencia con Python?",
        "¿Sabe usar Pinecone?",
        "¿Que sabe de Odoo?",
        "¿Ha liderado equipos?"
    ]

    for pregunta in preguntas:
        print("=" * 70)
        print(f"PREGUNTA: {pregunta}")
        print("=" * 70)

        for i, chunk in enumerate(retrieve(pregunta, n_results=4)):
            print(f"{i + 1}. rrf={chunk['score']:.4f}  "
                  f"[{chunk['source']}] {chunk['section'][:50]}")
        print()
