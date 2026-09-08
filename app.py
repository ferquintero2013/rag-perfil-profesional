import streamlit as st
from rag import answer

st.set_page_config(
    page_title="Chat con el perfil de Ferney Quintero",
    page_icon="💬",
    layout="centered"
)


# ============= HEADER =============
st.title("💬 Chat con mi perfil profesional")
st.caption(
    "Preguntale lo que quieras sobre la experiencia, proyectos y habilidades "
    "de Ferney Quintero. Las respuestas salen unicamente de su CV y portafolio, "
    "con la fuente citada."
)


# ============= SIDEBAR =============
with st.sidebar:
    st.header("Como funciona")
    st.markdown("""
    Este chatbot usa **RAG** (Retrieval-Augmented Generation):

    1. Tu pregunta se busca en el perfil por **significado** (embeddings)
       y por **palabras exactas** (BM25)
    2. Los dos rankings se combinan con **Reciprocal Rank Fusion**
    3. Los fragmentos relevantes se pasan a **GPT-4o** como contexto
    4. El modelo responde **solo** con esa informacion y cita la fuente

    Si algo no esta en el perfil, lo dice. No inventa.
    """)

    st.divider()
    st.subheader("Preguntas de ejemplo")
    ejemplos = [
        "¿Tiene experiencia con Python?",
        "¿Ha trabajado con clientes reales?",
        "¿Que sabe de Odoo y ERPs?",
        "¿Ha liderado equipos?",
        "¿Cual es su proyecto mas reciente?",
    ]
    for ej in ejemplos:
        st.markdown(f"- {ej}")

    st.divider()
    st.caption("**Stack**: Python · Streamlit · OpenAI · ChromaDB · BM25")
    st.markdown("[Portafolio](https://ferney-portfolio.vercel.app/)")
    st.markdown("[Codigo de este proyecto](https://github.com/ferquintero2013)")


# ============= HISTORIAL =============
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# Repintar todo el historial en cada rerun
for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["rol"]):
        st.markdown(mensaje["texto"])

        if mensaje.get("fuentes"):
            with st.expander("Ver fuentes"):
                for f in mensaje["fuentes"]:
                    st.caption(f"**{f['source']}** → {f['section']}")


# ============= INPUT =============
pregunta = st.chat_input("Escribe tu pregunta...")

if pregunta:
    # El historial ANTES de esta pregunta (se usa para resolver referencias)
    historial_previo = list(st.session_state.mensajes)

    # 1. Pintar y guardar la pregunta del usuario
    st.session_state.mensajes.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    # 2. Generar y pintar la respuesta
    with st.chat_message("assistant"):
        with st.spinner("Buscando en el perfil..."):
            try:
                resultado = answer(pregunta, history=historial_previo)
            except Exception as e:
                st.error(f"Error al procesar la pregunta: {e}")
                st.stop()

        st.markdown(resultado["answer"])

        # Solo mostramos las fuentes que el modelo realmente cito
        if resultado["cited"]:
            with st.expander("Ver fuentes"):
                for f in resultado["cited"]:
                    st.caption(f"**{f['source']}** → {f['section']}")

                # Si la pregunta se reescribio, mostrarlo (transparencia)
                if resultado["query_used"] != resultado["question"]:
                    st.divider()
                    st.caption(f"_Pregunta interpretada como:_ {resultado['query_used']}")

    # 3. Guardar la respuesta en el historial
    st.session_state.mensajes.append({
        "rol": "assistant",
        "texto": resultado["answer"],
        "fuentes": resultado["cited"]
    })
