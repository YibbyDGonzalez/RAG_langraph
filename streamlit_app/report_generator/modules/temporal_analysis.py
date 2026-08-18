import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def _duraciones_por_sesion(
    df: pd.DataFrame, gap_min: int = config.SESION_GAP_INACTIVIDAD_MIN
) -> pd.Series:
    """
    Duración (en minutos) de cada sesión real dentro de cada session_id.

    session_id identifica una conversación (se conserva mientras el
    estudiante no inicie un chat nuevo, incluso entre logins distintos), no
    una sesión de uso. Por eso una sesión real termina cuando pasan más de
    `gap_min` minutos sin preguntas: la siguiente pregunta del mismo
    session_id arranca una sesión nueva en vez de sumarse a la anterior.
    """
    ordenado = df.sort_values(["session_id", "timestamp"])
    delta = ordenado.groupby("session_id")["timestamp"].diff()
    nueva_sesion = delta.isna() | (delta > pd.Timedelta(minutes=gap_min))
    sesion_real = nueva_sesion.groupby(ordenado["session_id"]).cumsum()

    grupo = ordenado.groupby([ordenado["session_id"], sesion_real])["timestamp"]
    duraciones = (grupo.max() - grupo.min()).dt.total_seconds() / 60
    return duraciones[duraciones > 0]


def compute_temporal_stats(df: pd.DataFrame) -> dict:
    """
    Calcula distribución por hora y día, duración promedio de sesión,
    y detecta si el uso está concentrado en pocos días.
    """
    df = df.copy()
    df["hora"] = df["timestamp"].dt.hour
    df["dia_semana"] = df["timestamp"].dt.dayofweek  # 0=lunes, 6=domingo

    # Distribución por hora (0-23)
    por_hora_serie = df.groupby("hora").size().reindex(range(24), fill_value=0)
    por_hora = {int(h): int(por_hora_serie[h]) for h in range(24)}

    # Distribución por día de semana (nombres en español)
    por_dia_idx = df.groupby("dia_semana").size().reindex(range(7), fill_value=0)
    por_dia = {DIAS_ES[i]: int(por_dia_idx[i]) for i in range(7)}

    # Heatmap: día × hora → conteo
    hm_raw = df.groupby(["dia_semana", "hora"]).size().unstack(fill_value=0)
    hm_raw = hm_raw.reindex(index=range(7), fill_value=0)
    hm_raw = hm_raw.reindex(columns=range(24), fill_value=0)
    heatmap = {
        DIAS_ES[dia]: {int(h): int(hm_raw.loc[dia, h]) for h in range(24)}
        for dia in range(7)
    }

    # Duración promedio de sesión, partiendo cada session_id en sesiones reales
    # por huecos de inactividad (ver _duraciones_por_sesion)
    duraciones_validas = _duraciones_por_sesion(df)
    duracion_promedio = (
        float(duraciones_validas.mean()) if len(duraciones_validas) > 0 else 0.0
    )

    # Detección de concentración: ¿los 2 días más activos acumulan ≥40% del uso?
    total = sum(por_dia.values())
    top2_dias = sorted(por_dia, key=por_dia.get, reverse=True)[:2]
    top2_pct = (
        round(sum(por_dia[d] for d in top2_dias) / total * 100, 1)
        if total > 0
        else 0.0
    )

    return {
        "por_hora": por_hora,
        "por_dia": por_dia,
        "heatmap": heatmap,
        "duracion_promedio_min": round(duracion_promedio, 1),
        "top2_dias_pct": top2_pct,
        "top2_dias": top2_dias,
    }


def formatear_duracion(minutos: float) -> str:
    """Formatea minutos como '< 1 minuto', 'N min' o 'Hh Mmin' según magnitud."""
    if minutos < 1:
        return "< 1 minuto"
    if minutos < 60:
        return f"{minutos:.0f} min"
    return f"{int(minutos // 60)}h {int(minutos % 60)}min"
