import pandas as pd


def compute_usage_stats(df: pd.DataFrame) -> dict:
    """Calcula métricas de uso agregadas sin exponer datos individuales."""
    preguntas_por_sesion = df.groupby("session_id").size()
    return {
        "n_preguntas": int(len(df)),
        "n_usuarios": int(df["usuario"].nunique()),
        "n_sesiones": int(df["session_id"].nunique()),
        "promedio_preguntas_por_sesion": round(float(preguntas_por_sesion.mean()), 1),
    }
