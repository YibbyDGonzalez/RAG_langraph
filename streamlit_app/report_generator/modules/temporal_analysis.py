import pandas as pd

DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


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

    # Duración promedio de sesión (tiempo entre primera y última pregunta del session_id)
    sesion_ts = df.groupby("session_id")["timestamp"].agg(["min", "max"])
    sesion_ts["duracion_min"] = (
        (sesion_ts["max"] - sesion_ts["min"]).dt.total_seconds() / 60
    )
    sesiones_validas = sesion_ts[sesion_ts["duracion_min"] > 0]
    duracion_promedio = (
        float(sesiones_validas["duracion_min"].mean())
        if len(sesiones_validas) > 0
        else 0.0
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
