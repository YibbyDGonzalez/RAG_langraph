import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend import bootstrap
from backend.routers import auth, chat, conversations, report
from backend.services import rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # core.py y logger.py (streamlit_app/app/) resuelven sus rutas de datos
    # ("data/...", "data/logs/mbe_logs.db") relativas al cwd, tal como corre
    # hoy Streamlit lanzado desde streamlit_app/. Nos paramos ahí para
    # reusar ese código sin tocarlo.
    os.chdir(bootstrap.STREAMLIT_APP_DIR)

    from logger import init_db

    init_db()
    app.state.resources = rag_service.cargar_recursos()
    # Caché del análisis de temas (embeddings + Groq, 1-3 min), llave
    # (desde, hasta, rol) — bajo demanda, igual que en Streamlit.
    app.state.temas_cache = {}

    yield

    app.state.resources = {}
    app.state.temas_cache = {}


app = FastAPI(title="Asistente MBE API", lifespan=lifespan)

app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(conversations.router, prefix="/api", tags=["conversations"])
app.include_router(report.router, prefix="/api", tags=["report"])
