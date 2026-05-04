"""
logger.py — Registro de consultas en SQLite.
Guarda pregunta, respuesta, chunks recuperados, scores y latencias por componente.
El archivo .db vive en data/logs/ que ya esta montado como volumen en Docker.
"""
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.getenv("LOGS_DB_PATH", "data/logs/mbe_logs.db")


def init_db():
    """Crea la tabla de logs si no existe. Llamar una vez al arrancar la app."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS consultas (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp          DATETIME DEFAULT CURRENT_TIMESTAMP,
            usuario            TEXT,
            session_id         TEXT,
            pregunta           TEXT,
            chunks_extraidos   TEXT,
            scores_similitud   TEXT,
            respuesta          TEXT,
            latencia_embedding REAL,
            latencia_retrieval REAL,
            latencia_llm       REAL,
            latencia_total     REAL
        )
    """)
    conn.commit()
    conn.close()


def log_consulta(
    usuario: str,
    session_id: str,
    pregunta: str,
    chunks: list,
    scores: list,
    respuesta: str,
    latencia_embedding: float,
    latencia_retrieval: float,
    latencia_llm: float,
    latencia_total: float,
):
    """Inserta una fila de log. Falla silenciosamente para no interrumpir al usuario."""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.execute("""
            INSERT INTO consultas
            (usuario, session_id, pregunta, chunks_extraidos, scores_similitud,
             respuesta, latencia_embedding, latencia_retrieval, latencia_llm, latencia_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            usuario,
            session_id,
            pregunta,
            json.dumps(chunks, ensure_ascii=False),
            json.dumps([round(float(s), 4) for s in scores]),
            respuesta,
            round(latencia_embedding, 3),
            round(latencia_retrieval, 3),
            round(latencia_llm, 3),
            round(latencia_total, 3),
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        # Log silencioso: nunca interrumpir la experiencia del usuario
        print(f"[logger] Error al guardar log: {e}")
