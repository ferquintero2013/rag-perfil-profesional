import os
from openai import OpenAI
from dotenv import load_dotenv
from retriever import retrieve

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ANSWER_MODEL = "gpt-4o"


SYSTEM_PROMPT = """Eres el asistente del perfil profesional de Ferney Quintero.
Respondes preguntas de reclutadores y personas interesadas en su trayectoria,
usando UNICAMENTE la informacion del contexto que se te entrega.

TONO
- Escribe natural y directo, como un colega bien informado que conoce a Ferney.
- NUNCA uses frases como "segun el contexto", "en la informacion proporcionada"
  o "en el perfil que tengo". Quien pregunta no sabe que existe un contexto.
- Conciso: 2-4 frases, salvo que la pregunta pida mas detalle.
- Responde en el idioma en que se hizo la pregunta.

COMO MANEJAR LO QUE ENCUENTRES
1. Si el contexto responde la pregunta: respondela directo.
2. Si el contexto responde PARCIALMENTE: da lo que si sabes y aclara con
   naturalidad que parte no esta documentada.
   PROHIBIDO empezar diciendo que no tienes informacion y despues darla.
   Eso se contradice.
   Mal:  "No tengo esa informacion. Ferney ha usado Pinecone en n8n..."
   Bien: "El perfil no califica su nivel de profundidad en Pinecone. Lo que si
          indica es que lo ha usado dentro de flujos de n8n, no via codigo."
3. Si el contexto no dice NADA del tema: dilo en una frase y, si existe algo
   cercano, ofrecelo.

PRECISION (lo mas importante)
- No inventes, infieras ni completes datos que no esten escritos.
- Respeta los matices EXACTAMENTE:
  · algo "en aprendizaje" NO es algo dominado
  · un proyecto propio NO es trabajo de cliente
  · una herramienta usada via no-code NO es experiencia en codigo
- Cita la fuente de cada afirmacion factual con el formato
  [archivo.md -> nombre de la seccion]."""


def build_context(chunks):
    """Formats retrieved chunks into a text block for the prompt."""
    bloques = []
    for chunk in chunks:
        bloques.append(
            f"[FUENTE: {chunk['source']} -> {chunk['section']}]\n{chunk['text']}"
        )
    return "\n\n---\n\n".join(bloques)


def extract_cited(answer_text, chunks):
    """Filtra los chunks que el modelo REALMENTE cito en su respuesta.

    El retriever trae 5 candidatos, pero el modelo suele usar 1 o 2.
    Mostrar los 5 como "fuentes" seria enganoso: sugiere que la respuesta
    salio de todos ellos.
    """
    citados = []
    for chunk in chunks:
        # El archivo debe aparecer en la respuesta
        if chunk["source"] not in answer_text:
            continue
        # Y tambien el inicio de la seccion (el modelo puede truncar titulos largos)
        clave = chunk["section"][:20]
        if clave in answer_text:
            citados.append(chunk)
    return citados


def answer(question, n_results=5):
    """Full RAG pipeline: retrieve -> augment -> generate."""
    chunks = retrieve(question, n_results=n_results)
    context = build_context(chunks)

    user_message = (
        f"CONTEXTO:\n\n{context}\n\n"
        f"---\n\n"
        f"PREGUNTA: {question}"
    )

    response = openai_client.chat.completions.create(
        model=ANSWER_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0.1,
        max_tokens=500
    )

    texto = response.choices[0].message.content
    citados = extract_cited(texto, chunks)

    return {
        "question": question,
        "answer": texto,
        # Lo que el modelo realmente uso -> esto se le muestra al usuario
        "cited": [
            {"source": c["source"], "section": c["section"]}
            for c in citados
        ],
        # Todo lo que trajo el retriever -> util para debug, no para la UI
        "retrieved": [
            {"source": c["source"], "section": c["section"], "score": c["score"]}
            for c in chunks
        ]
    }


if __name__ == "__main__":
    preguntas = [
        "¿Tiene experiencia con Python?",
        "¿Sabe usar Pinecone?",
        "¿Ha trabajado con clientes reales en automatizacion?",
        "¿Tiene experiencia con Kubernetes?"
    ]

    for pregunta in preguntas:
        resultado = answer(pregunta)

        print("=" * 70)
        print(f"P: {resultado['question']}")
        print("=" * 70)
        print(f"\n{resultado['answer']}\n")

        if resultado["cited"]:
            print("Fuentes citadas:")
            for s in resultado["cited"]:
                print(f"  - [{s['source']}] {s['section'][:55]}")
        else:
            print("(sin fuentes citadas)")

        print(f"  ...{len(resultado['retrieved'])} chunks recuperados en total")
        print()
