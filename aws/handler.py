# -*- coding: utf-8 -*-
"""Adaptador de Lambda para el asistente del portafolio.

Es el equivalente de `api/ask.py`, que esta escrito para Vercel. La logica
del RAG no cambia ni una linea: `_rag.py`, `_retriever.py` y `_log.py` son
los mismos archivos. Lo unico que cambia es el borde, porque cada plataforma
tiene su propio contrato.

    Vercel   una clase con do_POST, que lee de self.rfile y escribe
             cabeceras a mano en self.wfile.

    Lambda   una funcion que recibe (event, context) y devuelve un dict con
             statusCode y body. La peticion ya viene parseada.

Que el motor sea portable entre las dos no es suerte: es consecuencia de que
la logica nunca supo quien la invocaba.
"""

import json
import time
import traceback

from _rag import answer
import _log

MAX_PREGUNTA = 500
MAX_TURNOS = 6
MAX_CARACTERES_TURNO = 2000


def _respuesta(codigo, cuerpo):
    """Arma lo que Lambda espera de vuelta.

    El body va como texto, no como objeto: Lambda no serializa por uno. Y
    ensure_ascii=False para que las tildes viajen como tildes y no como
    secuencias de escape.
    """
    return {
        "statusCode": codigo,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(cuerpo, ensure_ascii=False),
    }


def _limpiar_historial(bruto):
    """Recorta el historial que manda el navegador.

    Es entrada no confiable y acaba dentro de un prompt, asi que se limita
    el numero de turnos y el largo de cada uno antes de tocar el modelo.
    """
    if not isinstance(bruto, list):
        return []

    limpio = []
    for turno in bruto[-MAX_TURNOS:]:
        if not isinstance(turno, dict):
            continue
        rol = "user" if turno.get("rol") == "user" else "assistant"
        texto = str(turno.get("texto") or "")[:MAX_CARACTERES_TURNO]
        if texto:
            limpio.append({"rol": rol, "texto": texto})
    return limpio


def handler(event, context):
    """Punto de entrada. Lambda llama aqui en cada peticion."""
    pregunta = ""
    inicio = time.monotonic()

    try:
        # Con una Function URL, el cuerpo llega como texto dentro de event.
        # Puede venir en base64 si el cliente lo marco asi, aunque con JSON
        # plano no suele pasar.
        cuerpo_bruto = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            import base64
            cuerpo_bruto = base64.b64decode(cuerpo_bruto).decode("utf-8")

        cuerpo = json.loads(cuerpo_bruto)

        pregunta = str(cuerpo.get("question") or "").strip()
        if not pregunta:
            return _respuesta(400, {"error": "A question is required."})
        if len(pregunta) > MAX_PREGUNTA:
            return _respuesta(400, {
                "error": f"Question too long (max {MAX_PREGUNTA} characters)."
            })

        historial = _limpiar_historial(cuerpo.get("history"))
        resultado = answer(pregunta, history=historial)
        ms = int((time.monotonic() - inicio) * 1000)

        # A diferencia de Vercel, aqui el registro va ANTES de devolver. En
        # Vercel se respondia primero porque la funcion seguia viva despues
        # de escribir la respuesta. Lambda congela el proceso en cuanto
        # retorna el handler, asi que lo que se deje para despues no corre.
        _log.registrar(
            pregunta=pregunta,
            respuesta=resultado["answer"],
            mood=resultado["mood"],
            fuentes=resultado["cited"],
            query_usada=resultado["query_used"],
            ms=ms,
        )

        return _respuesta(200, {
            "answer": resultado["answer"],
            "mood": resultado["mood"],
            "cited": resultado["cited"],
            "query_used": resultado["query_used"],
        })

    except json.JSONDecodeError:
        return _respuesta(400, {"error": "Malformed JSON."})

    except Exception as e:
        # El detalle va a CloudWatch, nunca al cliente: un stack trace en la
        # respuesta filtra rutas y estructura interna.
        print(traceback.format_exc())

        # Y tambien a Supabase, con el mismo criterio que en Vercel: un log
        # que solo escribe cuando todo va bien es inutil justo para lo unico
        # que importa, que es enterarse cuando no.
        _log.registrar(
            pregunta=pregunta or "(no se alcanzo a leer la pregunta)",
            respuesta=f"{type(e).__name__}: {str(e)[:300]}",
            mood="error",
            fuentes=[],
            ms=int((time.monotonic() - inicio) * 1000),
        )
        return _respuesta(500, {"error": "Something went wrong on my side."})
