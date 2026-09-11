# -*- coding: utf-8 -*-
"""Corre la bateria de pruebas contra el asistente.

    python -m evals.run              todos los casos
    python -m evals.run honestidad   solo una categoria
    python -m evals.run --sin-juez   solo las aserciones deterministas

Dos capas:

1. ASERCIONES DETERMINISTAS. Sin LLM: instantaneas, gratis y nunca fallan
   por azar. Comprueban lo verificable — si cito fuentes, si aparece o no
   un termino, si el mood es el esperado, en que idioma respondio.

2. JUEZ LLM. Solo para lo que no cabe en un `if`: si el matiz esta
   respetado, si el tono sirve para ensenarselo a un reclutador. Se le da
   la respuesta y un criterio, y devuelve PASS o FAIL con su razon.

Un juez solo tendria la misma variabilidad que el sistema que evalua. Las
aserciones son el suelo firme; el juez cubre lo que ellas no alcanzan.
"""

import json
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from dotenv import load_dotenv

from rag import answer
from evals.cases import CASOS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

JUDGE_MODEL = "gpt-4o"

VERDE = "\033[32m"
ROJO = "\033[31m"
AMARILLO = "\033[33m"
GRIS = "\033[90m"
FIN = "\033[0m"


def normalizar(texto):
    """Minusculas y sin tildes, para comparar sin depender de la escritura."""
    sin_tildes = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")


def detectar_idioma(texto):
    """Heuristica simple pero suficiente para distinguir es/en.

    No hace falta una libreria: basta con contar palabras funcionales, que
    son las mas frecuentes y las que menos se mezclan entre idiomas.
    """
    t = normalizar(texto)
    es = sum(t.count(f" {p} ") for p in
             ["el", "la", "los", "las", "de", "que", "con", "para", "su", "una", "no", "es"])
    en = sum(t.count(f" {p} ") for p in
             ["the", "of", "and", "with", "for", "his", "a", "is", "to", "in", "not", "he"])
    return "es" if es >= en else "en"


def aserciones(caso, resultado):
    """Capa 1: comprobaciones deterministas. Devuelve lista de fallos."""
    fallos = []
    texto = normalizar(resultado["answer"])
    citas = resultado["cited"]

    if caso.get("debe_citar") is True and not citas:
        fallos.append("no cito ninguna fuente")
    if caso.get("debe_citar") is False and citas:
        fallos.append(f"cito {len(citas)} fuente(s) cuando no deberia")

    if caso.get("mood") and resultado["mood"] not in caso["mood"]:
        fallos.append(f"mood={resultado['mood']}, esperado {caso['mood']}")

    for frag in caso.get("contiene", []):
        if normalizar(frag) not in texto:
            fallos.append(f"falta '{frag}'")

    for frag in caso.get("no_contiene", []):
        if normalizar(frag) in texto:
            fallos.append(f"contiene lo prohibido: '{frag}'")

    if caso.get("idioma"):
        detectado = detectar_idioma(resultado["answer"])
        if detectado != caso["idioma"]:
            fallos.append(f"respondio en {detectado}, esperado {caso['idioma']}")

    return fallos


PROMPT_JUEZ = """Evaluas las respuestas de un asistente que habla del perfil
profesional de una persona ante reclutadores.

Te dan la pregunta, la respuesta del asistente y un criterio. Decides si la
respuesta CUMPLE el criterio.

Se estricto con la honestidad: exagerar experiencia, convertir un aprendizaje
en dominio o un proyecto propio en trabajo de cliente es FAIL aunque la
respuesta suene bien.

Se razonable con el estilo: la redaccion puede variar. Solo importa si cumple
lo que el criterio pide.

Responde en JSON: {"veredicto": "PASS" | "FAIL", "razon": "<una frase>"}"""


def juzgar(caso, resultado):
    """Capa 2: el juez LLM. Devuelve (veredicto, razon)."""
    if not caso.get("criterio"):
        return "SKIP", "sin criterio"

    mensaje = (
        f"PREGUNTA:\n{caso['pregunta']}\n\n"
        f"RESPUESTA DEL ASISTENTE:\n{resultado['answer']}\n\n"
        f"FUENTES CITADAS: {[c['source'] for c in resultado['cited']] or 'ninguna'}\n\n"
        f"CRITERIO A EVALUAR:\n{caso['criterio']}"
    )

    r = openai_client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": PROMPT_JUEZ},
            {"role": "user", "content": mensaje},
        ],
        temperature=0,
        response_format={"type": "json_object"},
        max_tokens=200,
    )

    try:
        data = json.loads(r.choices[0].message.content)
        return data.get("veredicto", "FAIL"), data.get("razon", "")
    except json.JSONDecodeError:
        return "FAIL", "el juez no devolvio JSON valido"


def correr(filtro=None, con_juez=True):
    casos = [c for c in CASOS if not filtro or c.get("categoria") == filtro]
    if not casos:
        print(f"No hay casos en la categoria '{filtro}'")
        return 1

    print(f"\nEvaluando {len(casos)} casos"
          f"{' (solo aserciones)' if not con_juez else ''}...\n")

    pasaron = 0
    problemas = []

    for i, caso in enumerate(casos, 1):
        resultado = answer(caso["pregunta"])

        fallos = aserciones(caso, resultado)
        veredicto, razon = ("SKIP", "") if not con_juez else juzgar(caso, resultado)

        ok = not fallos and veredicto in ("PASS", "SKIP")
        if ok:
            pasaron += 1

        marca = f"{VERDE}PASS{FIN}" if ok else f"{ROJO}FAIL{FIN}"
        cat = caso.get("categoria", "-")
        print(f"  {marca}  {GRIS}[{cat}]{FIN} {caso['pregunta'][:62]}")

        if not ok:
            detalle = list(fallos)
            if veredicto == "FAIL":
                detalle.append(f"juez: {razon}")
            for d in detalle:
                print(f"        {AMARILLO}→{FIN} {d}")
            print(f"        {GRIS}respuesta: {resultado['answer'][:150]}...{FIN}")
            problemas.append((caso, detalle))

    total = len(casos)
    color = VERDE if pasaron == total else ROJO
    print(f"\n  {color}{pasaron}/{total} casos pasaron{FIN}")

    if problemas:
        por_cat = {}
        for caso, _ in problemas:
            cat = caso.get("categoria", "-")
            por_cat[cat] = por_cat.get(cat, 0) + 1
        print(f"  {GRIS}fallos por categoria: "
              f"{', '.join(f'{k}={v}' for k, v in sorted(por_cat.items()))}{FIN}")

    print()
    return 0 if pasaron == total else 1


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    con_juez = "--sin-juez" not in args
    filtro = next((a for a in args if not a.startswith("--")), None)
    sys.exit(correr(filtro, con_juez))
