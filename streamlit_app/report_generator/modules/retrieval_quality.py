import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def _score_representativo(scores_json: str):
    """
    Parsea scores_similitud (guardado como JSON, lista de floats) y retorna el
    score del mejor chunk recuperado (máximo de la lista). None si no se puede
    parsear o la lista viene vacía.
    """
    try:
        scores = json.loads(scores_json)
        if not scores:
            return None
        return max(float(s) for s in scores)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def temas_con_retrieval_debil(
    df: pd.DataFrame,
    tema_por_pregunta: dict,
    min_preguntas: int = None,
    umbral_score: float = None,
) -> list:
    """
    Cruza la frecuencia de cada tema con la calidad de retrieval (scores de
    similitud ya guardados en los logs). Un tema entra en la alerta si tiene
    al menos `min_preguntas` preguntas Y su score medio representativo es
    <= `umbral_score` (retrieval trayendo chunks poco relevantes).

    Retorna: [{"tema": str, "n_preguntas": int, "score_medio": float}, ...]
    ordenado del score más débil al menos débil.
    """
    min_preguntas = min_preguntas if min_preguntas is not None else config.RETRIEVAL_DEBIL_MIN_PREGUNTAS
    umbral_score = umbral_score if umbral_score is not None else config.RETRIEVAL_DEBIL_UMBRAL_SCORE

    if df.empty or not tema_por_pregunta:
        return []

    df = df.copy()
    df["tema"] = df["pregunta"].str.strip().map(
        lambda p: tema_por_pregunta.get(p, {}).get("nombre_tema")
    )
    df["score_max"] = df["scores_similitud"].map(_score_representativo)
    df = df.dropna(subset=["tema", "score_max"])

    if df.empty:
        return []

    agrupado = (
        df.groupby("tema")
        .agg(n_preguntas=("pregunta", "size"), score_medio=("score_max", "mean"))
        .reset_index()
    )
    debiles = agrupado[
        (agrupado["n_preguntas"] >= min_preguntas) & (agrupado["score_medio"] <= umbral_score)
    ].sort_values("score_medio")

    return [
        {
            "tema": row["tema"],
            "n_preguntas": int(row["n_preguntas"]),
            "score_medio": round(float(row["score_medio"]), 2),
        }
        for _, row in debiles.iterrows()
    ]
