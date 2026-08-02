"""Wrapea streamlit_app/app/logger.py para exponer historial y logging vía HTTP.

Misma tabla SQLite que usa Streamlit (data/logs/mbe_logs.db) — no se migra
esquema ni se reimplementa el logging.
"""
from backend import bootstrap  # noqa: F401  (deja logger.py importable)

from logger import load_user_sessions, log_consulta


def listar_conversaciones(usuario: str) -> list[dict]:
    """Más reciente primero, igual que el sidebar de Streamlit."""
    sesiones = load_user_sessions(usuario)
    return [
        {"id": chat_id, "title": data["title"]}
        for chat_id, data in reversed(list(sesiones.items()))
    ]


def obtener_conversacion(usuario: str, conversation_id: str) -> dict | None:
    sesiones = load_user_sessions(usuario)
    data = sesiones.get(conversation_id)
    if data is None:
        return None
    return {"id": conversation_id, "title": data["title"], "messages": data["messages"]}


def registrar_intercambio(
    *, usuario: str, session_id: str, pregunta: str, meta: dict,
    respuesta: str, lat_llm: float, lat_total: float,
):
    log_consulta(
        usuario=usuario,
        session_id=session_id,
        pregunta=pregunta,
        chunks=meta["chunks"],
        scores=meta["scores"],
        respuesta=respuesta,
        latencia_embedding=meta["lat_embedding"],
        latencia_retrieval=meta["lat_retrieval"],
        latencia_llm=lat_llm,
        latencia_total=lat_total,
    )
