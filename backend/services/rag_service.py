"""Wrapea streamlit_app/app/core.py y streamlit_app/rag_langgraph/app_langgraph.py.

No reimplementa el pipeline RAG: lo importa tal cual corre hoy en Streamlit.
"""
from backend import bootstrap  # noqa: F401  (deja core/rag_langgraph importables)

from core import load_resources
from rag_langgraph.app_langgraph import responder_stream_logged


def cargar_recursos() -> dict:
    df, embeddings, index, encoder, groq_client = load_resources()
    return {"df": df, "index": index, "encoder": encoder, "groq_client": groq_client}


def responder(pregunta: str, *, recursos: dict, trace_id: str | None = None):
    """Generator: primer yield es dict de metadata (chunks/scores/latencias),
    los siguientes son tokens de texto de la respuesta."""
    return responder_stream_logged(
        pregunta,
        df=recursos["df"],
        index=recursos["index"],
        encoder=recursos["encoder"],
        ollama_client=recursos["groq_client"],
        trace_id=trace_id,
    )
