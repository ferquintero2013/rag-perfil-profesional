from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag import answer

app = FastAPI(
    title="Ferney's profile assistant",
    description="RAG sobre CV y portafolio. Responde solo desde documentos indexados.",
    version="1.0.0"
)

# CORS: por defecto el navegador prohibe que una pagina de un dominio
# llame a una API de otro. Aqui se declara quien SI tiene permiso.
# Sin esto, el fetch desde el portafolio falla en silencio.
ORIGINS = [
    "https://ferney-portfolio.vercel.app",
    "http://localhost:4321",
    "http://127.0.0.1:4321",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------- forma de los datos ----------

class Turn(BaseModel):
    """Un turno del historial de conversacion."""
    rol: str
    texto: str


class AskRequest(BaseModel):
    """Lo que el frontend envia."""
    question: str = Field(min_length=1, max_length=500)
    history: List[Turn] = Field(default_factory=list, max_length=6)


class Source(BaseModel):
    source: str
    section: str


class AskResponse(BaseModel):
    """Lo que la API devuelve."""
    answer: str
    mood: str
    cited: List[Source]
    query_used: str


# ---------- endpoints ----------

@app.get("/health")
def health():
    """Comprobacion de vida. La usan los servicios de hosting."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """Responde una pregunta sobre el perfil."""
    historial = [{"rol": t.rol, "texto": t.texto} for t in req.history]

    resultado = answer(req.question, history=historial)

    return {
        "answer": resultado["answer"],
        "mood": resultado["mood"],
        "cited": resultado["cited"],
        "query_used": resultado["query_used"],
    }
