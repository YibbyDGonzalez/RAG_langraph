import sqlite3
from datetime import timedelta

import pandas as pd

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def load_data(db_path: str, desde: str = None, hasta: str = None) -> pd.DataFrame:
    """
    Lee la tabla 'consultas' del SQLite, aplica offset de zona horaria
    y filtra por el rango de fechas indicado.
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        "SELECT id, timestamp, usuario, session_id, pregunta, scores_similitud "
        "FROM consultas ORDER BY timestamp",
        conn,
    )
    conn.close()

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])

    if config.TIMEZONE_OFFSET_HOURS != 0:
        df["timestamp"] = df["timestamp"] + timedelta(hours=config.TIMEZONE_OFFSET_HOURS)

    if desde:
        df = df[df["timestamp"] >= pd.Timestamp(desde)]
    if hasta:
        df = df[df["timestamp"] < pd.Timestamp(hasta) + timedelta(days=1)]

    df = df.dropna(subset=["pregunta"])
    df = df[df["pregunta"].str.strip() != ""]

    return df.reset_index(drop=True)


def load_data_con_periodo_anterior(db_path: str, desde: str, hasta: str):
    """
    Carga el rango seleccionado y el periodo inmediatamente anterior de igual
    longitud (para calcular deltas de KPI), en una sola lectura a la DB.

    Retorna (df_actual, df_anterior).
    """
    desde_ts = pd.Timestamp(desde)
    hasta_ts = pd.Timestamp(hasta)
    dias = (hasta_ts - desde_ts).days + 1

    anterior_desde = desde_ts - timedelta(days=dias)

    df_total = load_data(db_path, anterior_desde.strftime("%Y-%m-%d"), hasta_ts.strftime("%Y-%m-%d"))

    df_actual = df_total[df_total["timestamp"] >= desde_ts].reset_index(drop=True)
    df_anterior = df_total[df_total["timestamp"] < desde_ts].reset_index(drop=True)

    return df_actual, df_anterior


def load_data_historico(db_path: str) -> pd.DataFrame:
    """Carga todo el histórico sin filtrar por fecha (para roster: 'nunca ha usado' y 'silencioso')."""
    return load_data(db_path)
