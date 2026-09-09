import os
import re


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERFIL_DIR = os.path.join(BASE_DIR, "data")


def load_markdown_files(directory):
    """Reads all .md files in a directory. Returns list of (filename, content)."""
    documents = []

    for filename in sorted(os.listdir(directory)):
        if not filename.endswith(".md"):
            continue

        path = os.path.join(directory, filename)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        documents.append((filename, content))

    return documents


def chunk_by_headers(filename, content):
    """Splits markdown content into chunks by ## and ### headers."""
    chunks = []

    # Split keeping the header with its content
    parts = re.split(r"\n(?=#{2,3} )", content)

    for part in parts:
        part = part.strip()
        if len(part) < 50:          # skip near-empty fragments
            continue

        # First line is the header (or the first content line)
        lines = part.split("\n")
        header = lines[0].lstrip("#").strip()

        chunks.append({
            "source": filename,
            "section": header,
            "text": part
        })

    return chunks


def build_corpus(directory=PERFIL_DIR):
    """Loads all files and returns the full list of chunks."""
    all_chunks = []

    for filename, content in load_markdown_files(directory):
        chunks = chunk_by_headers(filename, content)
        all_chunks.extend(chunks)
        print(f"  {filename}: {len(chunks)} chunks")

    return all_chunks


if __name__ == "__main__":
    print("Cargando corpus del perfil...\n")
    corpus = build_corpus()

    print(f"\nTotal: {len(corpus)} chunks\n")
    print("=" * 60)
    print("MUESTRA DE LOS PRIMEROS 3 CHUNKS")
    print("=" * 60)

    for chunk in corpus[:3]:
        print(f"\n[{chunk['source']}] -> {chunk['section']}")
        print(f"  {len(chunk['text'])} caracteres")
        print(f"  {chunk['text'][:200]}...")
