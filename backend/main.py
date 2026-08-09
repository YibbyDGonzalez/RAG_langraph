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

    from report_generator.modules.topic_store import init_db as init_temas_db

    from backend.services.report_service import DB_PATH as TEMAS_DB_PATH

    init_temas_db(TEMAS_DB_PATH)

    app.state.resources = rag_service.cargar_recursos()

    yield

    app.state.resources = {}


app = FastAPI(title="Asistente MBE API", lifespan=lifespan)

app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(conversations.router, prefix="/api", tags=["conversations"])
app.include_router(report.router, prefix="/api", tags=["report"])
