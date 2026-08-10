"""Wrapea streamlit_app/report_generator/modules/* para el reporte docente.

No reimplementa el análisis (KPIs, alertas, roster): lo importa tal cual corre
hoy en Streamlit (app/pages/reporte.py). Los "Temas" son la excepción: usan
topic_store.py, una taxonomía persistente en SQLite por rol (no por rango de
fechas) en vez de recalcular el clustering en cada request.
"""
import os
import sqlite3

import pandas as pd

from backend import bootstrap  # noqa: F401

from report_generator.config import TEMAS_MIN_PREGUNTAS_NUEVAS
from report_generator.modules import topic_store
from report_generator.modules.alerts import detectar_tema_en_alza, generar_alertas
from report_generator.modules.data_loader import load_data_con_periodo_anterior, load_data_historico
from report_generator.modules.deltas import kpis_con_delta, sparkline_semanal
from report_generator.modules.retrieval_quality import temas_con_retrieval_debil
from report_generator.modules.roles import filtrar_por_rol
from report_generator.modules.roster import (
    cargar_roster,
    nunca_usado as calcular_nunca_usado,
    silenciosos as calcular_silenciosos,
)
from report_generator.modules.student_detail import detalle_estudiante as _detalle_estudiante
from report_generator.modules.students import histograma_esfuerzo, tabla_estudiantes
from report_generator.modules.temporal_analysis import compute_temporal_stats, formatear_duracion
from report_generator.modules.topic_analysis import evolucion_semanal_por_tema, resumen_temas

DB_PATH = os.getenv("LOGS_DB_PATH", "data/logs/mbe_logs.db")

# El reporte docente analiza únicamente lo que preguntan los estudiantes;
# "docentes"/"todos" eran opciones ilustrativas del filtro que ya no se exponen.
ROL_REPORTE = "estudiantes"


class DatosInsuficientes(Exception):
    def __init__(self, n: int):
        self.n = n
        super().__init__(f"Se necesitan al menos 5 preguntas, hay {n}.")


def groq_disponible() -> str | None:
    return os.environ.get("GROQ_API_KEY")


def rango_fechas() -> dict:
    conn = sqlite3.connect(DB_PATH)
    try:
        row = pd.read_sql_query(
            "SELECT MIN(timestamp) as mn, MAX(timestamp) as mx FROM consultas", conn
        ).iloc[0]
    finally:
        conn.close()
    if row["mn"] is None:
        return {"min_date": None, "max_date": None}
    return {
        "min_date": str(pd.to_datetime(row["mn"]).date()),
        "max_date": str(pd.to_datetime(row["mx"]).date()),
    }


def _cargar(desde: str, hasta: str):
    df_actual, df_anterior = load_data_con_periodo_anterior(DB_PATH, desde, hasta)
    df_historico = load_data_historico(DB_PATH)
    return (
        filtrar_por_rol(df_actual, ROL_REPORTE),
        filtrar_por_rol(df_anterior, ROL_REPORTE),
        filtrar_por_rol(df_historico, ROL_REPORTE),
    )


def pulso(desde: str, hasta: str) -> dict:
    df_actual, df_anterior, df_historico = _cargar(desde, hasta)
    roster = cargar_roster()

    kpis_delta = kpis_con_delta(df_actual, df_anterior)
    kpis_delta["tiempo_promedio_sesion"]["valor_fmt"] = formatear_duracion(
        kpis_delta["tiempo_promedio_sesion"]["valor"]
    )

    sparkline_data = sparkline_semanal(df_historico, hasta, semanas=4)

    scope = topic_store.estado_scope(ROL_REPORTE, DB_PATH)
    mapeo_temas = topic_store.mapeo_pregunta_tema(ROL_REPORTE, DB_PATH) if scope["existe"] else {}

    tema_en_alza = None
    temas_debiles = []
    if mapeo_temas:
        evolucion = evolucion_semanal_por_tema(df_actual, mapeo_temas)
        tema_en_alza = detectar_tema_en_alza(evolucion)
        temas_debiles = temas_con_retrieval_debil(df_actual, mapeo_temas)

    temporal_actual = compute_temporal_stats(df_actual) if not df_actual.empty else None
    concentracion = None
    if temporal_actual and temporal_actual["top2_dias_pct"] >= 40:
        concentracion = {"pct": temporal_actual["top2_dias_pct"], "dias": temporal_actual["top2_dias"]}

    nunca_usado_list = calcular_nunca_usado(df_historico, roster)
    silenciosos_list = _serializar_silenciosos(calcular_silenciosos(df_historico, roster))

    alertas = generar_alertas(tema_en_alza, temas_debiles, nunca_usado_list, silenciosos_list, concentracion)

    return {
        "kpis": kpis_delta,
        "sparkline": sparkline_data,
        "temporal": temporal_actual,
        "alertas": alertas,
        "temas_generados": scope["existe"],
        "total_estudiantes": len(roster),
    }


def generar_temas(desde: str, hasta: str, groq_api_key: str) -> dict:
    if not topic_store.estado_scope(ROL_REPORTE, DB_PATH)["existe"]:
        n = topic_store.contar_pendientes(ROL_REPORTE, DB_PATH)
        if n < TEMAS_MIN_PREGUNTAS_NUEVAS:
            raise DatosInsuficientes(n)
    topic_store.actualizar_scope(ROL_REPORTE, groq_api_key, DB_PATH)
    return estado_temas(desde, hasta)


def estado_temas(desde: str, hasta: str) -> dict:
    scope = topic_store.estado_scope(ROL_REPORTE, DB_PATH)
    if not scope["existe"]:
        return {"status": "idle"}

    mapeo = topic_store.mapeo_pregunta_tema(ROL_REPORTE, DB_PATH)
    df_actual, _, _ = _cargar(desde, hasta)
    temas = resumen_temas(df_actual, mapeo)
    evolucion = evolucion_semanal_por_tema(df_actual, mapeo)
    evolucion_json = [
        {"semana": str(idx), **{str(col): int(v) for col, v in row.items()}}
        for idx, row in evolucion.iterrows()
    ]

    return {
        "status": "generado",
        "temas": temas,
        "preguntas_destacadas": scope["destacadas"],
        "evolucion_semanal": evolucion_json,
    }


def estudiantes(desde: str, hasta: str) -> dict:
    df_actual, _, df_historico = _cargar(desde, hasta)
    roster = cargar_roster()
    mapeo_temas = topic_store.mapeo_pregunta_tema(ROL_REPORTE, DB_PATH)

    tabla = tabla_estudiantes(df_actual, mapeo_temas, roster)

    return {
        "tabla": tabla,
        "histograma": histograma_esfuerzo(tabla),
        "nunca_usado": calcular_nunca_usado(df_historico, roster),
        "silenciosos": _serializar_silenciosos(calcular_silenciosos(df_historico, roster)),
    }


def estudiante_detalle(usuario: str, desde: str, hasta: str) -> dict:
    mapeo_temas = topic_store.mapeo_pregunta_tema(ROL_REPORTE, DB_PATH)

    usuario_norm = usuario.lower()
    roster = cargar_roster()
    detalle = _detalle_estudiante(DB_PATH, usuario_norm, mapeo_temas)

    detalle["usuario"] = usuario_norm
    detalle["nombre"] = roster.get(usuario_norm, usuario_norm)
    detalle["primera_actividad"] = _iso_o_none(detalle["primera_actividad"])
    detalle["ultima_actividad"] = _iso_o_none(detalle["ultima_actividad"])
    for fila in detalle["ultimas_preguntas"]:
        fila["timestamp"] = _iso_o_none(fila["timestamp"])

    return detalle


def _iso_o_none(valor):
    return str(valor) if pd.notna(valor) else None


def _serializar_silenciosos(silenciosos: list) -> list:
    return [
        {**s, "ultima_actividad": _iso_o_none(s["ultima_actividad"])}
        for s in silenciosos
    ]
