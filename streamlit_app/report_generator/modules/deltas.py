import pandas as pd

from .temporal_analysis import compute_temporal_stats
from .usage_stats import compute_usage_stats


def _uso_seguro(df: pd.DataFrame) -> dict:
    """compute_usage_stats(), pero tolera un dataframe vacío (periodo sin datos)."""
    if df.empty:
        return {"n_preguntas": 0, "n_usuarios": 0, "n_sesiones": 0, "promedio_preguntas_por_sesion": 0.0}
    return compute_usage_stats(df)


def _duracion_segura(df: pd.DataFrame) -> float:
    """duracion_promedio_min de compute_temporal_stats(), tolerando dataframe vacío."""
    if df.empty:
        return 0.0
    return compute_temporal_stats(df)["duracion_promedio_min"]


def _delta_pct(actual: float, anterior: float):
    """Retorna % de cambio, o None si no hay dato del periodo anterior para comparar."""
    if anterior == 0:
        return None
    return round((actual - anterior) / anterior * 100, 0)


def kpis_con_delta(df_actual: pd.DataFrame, df_anterior: pd.DataFrame) -> dict:
    """
    KPIs de Nivel 1 (preguntas, estudiantes activos, sesiones, preguntas por
    estudiante, tiempo promedio de sesión) con su delta porcentual contra el
    periodo inmediatamente anterior de igual longitud.

    Retorna: {
      "preguntas":               {"valor": int, "delta_pct": float|None},
      "estudiantes":             {"valor": int, "delta_pct": float|None},
      "sesiones":                {"valor": int, "delta_pct": float|None},
      "preguntas_por_estudiante": {"valor": float, "delta_pct": float|None},
      "tiempo_promedio_sesion":  {"valor": float (minutos), "delta_pct": float|None},
    }
    delta_pct es None cuando no hay datos del periodo anterior para comparar.
    """
    actual = _uso_seguro(df_actual)
    anterior = _uso_seguro(df_anterior)

    preg_por_est_actual = (
        round(actual["n_preguntas"] / actual["n_usuarios"], 1) if actual["n_usuarios"] else 0.0
    )
    preg_por_est_anterior = (
        round(anterior["n_preguntas"] / anterior["n_usuarios"], 1) if anterior["n_usuarios"] else 0.0
    )

    dur_actual = _duracion_segura(df_actual)
    dur_anterior = _duracion_segura(df_anterior)

    return {
        "preguntas": {
            "valor": actual["n_preguntas"],
            "delta_pct": _delta_pct(actual["n_preguntas"], anterior["n_preguntas"]),
        },
        "estudiantes": {
            "valor": actual["n_usuarios"],
            "delta_pct": _delta_pct(actual["n_usuarios"], anterior["n_usuarios"]),
        },
        "sesiones": {
            "valor": actual["n_sesiones"],
            "delta_pct": _delta_pct(actual["n_sesiones"], anterior["n_sesiones"]),
        },
        "preguntas_por_estudiante": {
            "valor": preg_por_est_actual,
            "delta_pct": _delta_pct(preg_por_est_actual, preg_por_est_anterior),
        },
        "tiempo_promedio_sesion": {
            "valor": dur_actual,
            "delta_pct": _delta_pct(dur_actual, dur_anterior),
        },
    }


def sparkline_semanal(df_historico: pd.DataFrame, hasta, semanas: int = 4) -> list:
    """
    Conteo de preguntas por semana en las `semanas` semanas terminando en `hasta`,
    tomado del histórico completo (independiente del rango seleccionado por el
    docente): da siempre contexto de tendencia reciente.

    Retorna: [{"semana": "YYYY-MM-DD", "n_preguntas": int}, ...] (orden cronológico)
    """
    hasta_ts = pd.Timestamp(hasta) + pd.Timedelta(days=1)
    desde_ts = hasta_ts - pd.Timedelta(weeks=semanas)

    ventana = df_historico[
        (df_historico["timestamp"] >= desde_ts) & (df_historico["timestamp"] < hasta_ts)
    ]

    if ventana.empty:
        conteo = pd.Series(dtype=int)
    else:
        conteo = ventana.set_index("timestamp").resample("W")["id"].count()

    rango_semanas = pd.date_range(end=hasta_ts, periods=semanas, freq="W")
    conteo = conteo.reindex(rango_semanas, fill_value=0)

    return [{"semana": str(idx.date()), "n_preguntas": int(v)} for idx, v in conteo.items()]
