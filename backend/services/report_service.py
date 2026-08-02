"""Wrapea streamlit_app/report_generator/modules/* para el reporte docente.

No reimplementa el análisis (KPIs, alertas, temas, roster): lo importa tal
cual corre hoy en Streamlit (app/pages/reporte.py). La única diferencia de
comportamiento a propósito es que la caché de temas se invalida por
(desde, hasta, rol) — en Streamlit no incluía el rol en la llave.
"""
import os
import sqlite3

import pandas as pd

from backend import bootstrap  # noqa: F401

from report_generator.modules.alerts import detectar_tema_en_alza, generar_alertas
from report_generator.modules.data_loader import load_data_con_periodo_anterior, load_data_historico
from report_generator.modules.deltas import kpis_con_delta, sparkline_semanal
from report_generator.modules.retrieval_quality import temas_con_retrieval_debil
from report_generator.modules.roles import ROL_DOCENTE, ROL_ESTUDIANTE, rol_de_usuario
from report_generator.modules.roster import (
    cargar_roster,
    nunca_usado as calcular_nunca_usado,
    silenciosos as calcular_silenciosos,
)
from report_generator.modules.student_detail import detalle_estudiante as _detalle_estudiante
from report_generator.modules.students import histograma_esfuerzo, tabla_estudiantes
from report_generator.modules.temporal_analysis import compute_temporal_stats, formatear_duracion
from report_generator.modules.topic_analysis import compute_topics_detallado, evolucion_semanal_por_tema

DB_PATH = os.getenv("LOGS_DB_PATH", "data/logs/mbe_logs.db")

ROL_QUERY_A_ROL = {"docentes": ROL_DOCENTE, "estudiantes": ROL_ESTUDIANTE}


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


def _filtrar_por_rol(df: pd.DataFrame, rol: str) -> pd.DataFrame:
    rol_objetivo = ROL_QUERY_A_ROL.get(rol)
    if rol_objetivo is None or df.empty:
        return df
    mascara = df["usuario"].astype(str).map(rol_de_usuario) == rol_objetivo
    return df[mascara].reset_index(drop=True)


def _cargar(desde: str, hasta: str, rol: str):
    df_actual, df_anterior = load_data_con_periodo_anterior(DB_PATH, desde, hasta)
    df_historico = load_data_historico(DB_PATH)
    return (
        _filtrar_por_rol(df_actual, rol),
        _filtrar_por_rol(df_anterior, rol),
        _filtrar_por_rol(df_historico, rol),
    )


def pulso(desde: str, hasta: str, rol: str, temas_cache: dict) -> dict:
    df_actual, df_anterior, df_historico = _cargar(desde, hasta, rol)
    roster = cargar_roster()

    kpis_delta = kpis_con_delta(df_actual, df_anterior)
    kpis_delta["tiempo_promedio_sesion"]["valor_fmt"] = formatear_duracion(
        kpis_delta["tiempo_promedio_sesion"]["valor"]
    )

    sparkline_data = sparkline_semanal(df_historico, hasta, semanas=4)

    resultado = temas_cache.get((desde, hasta, rol))
    mapeo_temas = resultado["mapeo_pregunta_tema"] if resultado else {}

    tema_en_alza = None
    temas_debiles = []
    if resultado and resultado["temas"]:
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
        "temas_generados": bool(resultado),
        "total_estudiantes": len(roster),
    }


def generar_temas(desde: str, hasta: str, rol: str, groq_api_key: str, temas_cache: dict) -> dict:
    df_actual, _, _ = _cargar(desde, hasta, rol)
    if len(df_actual) < 5:
        raise DatosInsuficientes(len(df_actual))
    resultado = compute_topics_detallado(list(df_actual["pregunta"]), groq_api_key)
    temas_cache[(desde, hasta, rol)] = resultado
    return resultado


def estado_temas(desde: str, hasta: str, rol: str, temas_cache: dict) -> dict:
    resultado = temas_cache.get((desde, hasta, rol))
    if not resultado:
        return {"status": "idle"}

    df_actual, _, _ = _cargar(desde, hasta, rol)
    evolucion = evolucion_semanal_por_tema(df_actual, resultado["mapeo_pregunta_tema"])
    evolucion_json = [
        {"semana": str(idx), **{str(col): int(v) for col, v in row.items()}}
        for idx, row in evolucion.iterrows()
    ]

    return {
        "status": "generado",
        "temas": resultado["temas"],
        "preguntas_destacadas": resultado["preguntas_destacadas"],
        "evolucion_semanal": evolucion_json,
    }


def estudiantes(desde: str, hasta: str, rol: str, temas_cache: dict) -> dict:
    df_actual, _, df_historico = _cargar(desde, hasta, rol)
    roster = cargar_roster()
    resultado = temas_cache.get((desde, hasta, rol))
    mapeo_temas = resultado["mapeo_pregunta_tema"] if resultado else {}

    tabla = tabla_estudiantes(df_actual, mapeo_temas, roster)

    return {
        "tabla": tabla,
        "histograma": histograma_esfuerzo(tabla),
        "nunca_usado": calcular_nunca_usado(df_historico, roster),
        "silenciosos": _serializar_silenciosos(calcular_silenciosos(df_historico, roster)),
    }


def estudiante_detalle(usuario: str, desde: str, hasta: str, rol: str, temas_cache: dict) -> dict:
    resultado = temas_cache.get((desde, hasta, rol))
    mapeo_temas = resultado["mapeo_pregunta_tema"] if resultado else {}

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
