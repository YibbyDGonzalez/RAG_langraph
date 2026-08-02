import json
import math
import re
import sys
import os

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import umap
from groq import Groq
from sklearn.cluster import KMeans

# sklearn ≥1.3 incluye HDBSCAN; si no, usar el paquete standalone
try:
    from sklearn.cluster import HDBSCAN
except ImportError:
    from hdbscan import HDBSCAN

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def _deduplicar(preguntas: list) -> list:
    """Deduplica preguntas preservando el orden de aparición."""
    seen = set()
    preguntas_unicas = []
    for p in preguntas:
        p_norm = p.strip()
        if p_norm and p_norm not in seen:
            seen.add(p_norm)
            preguntas_unicas.append(p_norm)
    return preguntas_unicas


def _clusterizar(preguntas_unicas: list) -> np.ndarray:
    """
    Embeddings multilingües → UMAP → HDBSCAN (KMeans como fallback).
    Retorna un array de labels alineado por índice con preguntas_unicas.
    """
    print("    Cargando modelo de embeddings...")
    model = SentenceTransformer(config.EMBEDDING_MODEL)
    print("    Generando embeddings (puede tardar un momento)...")
    embeddings = model.encode(preguntas_unicas, show_progress_bar=True, batch_size=32)

    n = len(preguntas_unicas)
    n_neighbors = min(15, n - 1)
    n_components = min(config.UMAP_N_COMPONENTS, n - 2)
    print(f"    Reduciendo dimensiones con UMAP ({n_components}D)...")
    reducer = umap.UMAP(
        n_neighbors=n_neighbors,
        n_components=n_components,
        metric="cosine",
        random_state=42,
        low_memory=False,
    )
    reduced = reducer.fit_transform(embeddings)

    min_cluster = max(2, min(config.HDBSCAN_MIN_CLUSTER_SIZE, n // 8))
    print(f"    Agrupando con HDBSCAN (min_cluster_size={min_cluster})...")
    clusterer = HDBSCAN(
        min_cluster_size=min_cluster,
        min_samples=config.HDBSCAN_MIN_SAMPLES,
    )
    labels = clusterer.fit_predict(reduced)

    n_clusters_validos = len(set(labels) - {-1})
    if n_clusters_validos < 2:
        k = max(2, min(8, int(math.sqrt(n / 2))))
        print(f"    HDBSCAN sin grupos suficientes → usando KMeans (k={k})...")
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(reduced)

    return labels


def compute_topics(preguntas: list, groq_api_key: str) -> list:
    """
    Agrupa las preguntas por significado mediante:
      1. Embeddings multilingües (sentence-transformers)
      2. Reducción de dimensiones con UMAP
      3. Clustering con HDBSCAN (KMeans como fallback)
      4. Nombre de cada grupo generado por Groq

    Retorna lista de dicts ordenada de mayor a menor grupo:
      [{"nombre": str, "n_preguntas": int, "pct": float, "ejemplos": list[str]}]

    Usado por el generador de reporte HTML standalone (generate_report.py).
    Para la vista interactiva de Nivel 2 (Temas), que necesita además el
    tema asignado a cada pregunta y las preguntas destacadas, usar
    compute_topics_detallado().
    """
    preguntas_unicas = _deduplicar(preguntas)
    if len(preguntas_unicas) < 5:
        return []

    labels = _clusterizar(preguntas_unicas)

    groq_client = Groq(api_key=groq_api_key)
    temas = []
    labels_validos = sorted(set(labels) - {-1})

    clusters_para_llm = [
        (label, [preguntas_unicas[i] for i in np.where(labels == label)[0]][:8])
        for label in labels_validos
    ]

    print(f"    Nombrando {len(clusters_para_llm)} grupos en una sola llamada a Groq...")
    nombres_map = _nombrar_clusters(clusters_para_llm, groq_client)

    for label in labels_validos:
        indices = np.where(labels == label)[0]
        cluster_qs = [preguntas_unicas[i] for i in indices]
        nombre = nombres_map.get(label) or f"Tema {label + 1}"
        temas.append({
            "nombre": nombre,
            "n_preguntas": len(cluster_qs),
            "pct": 0.0,
            "ejemplos": cluster_qs[-config.MAX_EJEMPLOS_POR_TEMA:],
        })

    n_ruido = int(np.sum(labels == -1))
    if n_ruido > 0:
        indices_ruido = np.where(labels == -1)[0]
        temas.append({
            "nombre": "Preguntas variadas",
            "n_preguntas": n_ruido,
            "pct": 0.0,
            "ejemplos": [preguntas_unicas[i] for i in indices_ruido[-config.MAX_EJEMPLOS_POR_TEMA:]],
        })

    total = len(preguntas_unicas)
    for t in temas:
        t["pct"] = round(t["n_preguntas"] / total * 100, 1)

    temas.sort(key=lambda x: x["n_preguntas"], reverse=True)
    return temas


def compute_topics_detallado(preguntas: list, groq_api_key: str) -> dict:
    """
    Igual que compute_topics(), pero pensado para el Nivel 2 (Temas) de la
    app interactiva. Retorna además:
      - mapeo_pregunta_tema: {pregunta_normalizada (str.strip()): {"cluster_id": int,
        "nombre_tema": str}}, para poder asignar tema a TODAS las filas originales
        (no solo a los ejemplos deduplicados) y así construir la evolución
        temporal por tema y el cruce con scores de retrieval débil.
      - preguntas_destacadas: hasta config.MAX_PREGUNTAS_DESTACADAS preguntas bien
        formuladas, elegidas en la MISMA llamada a Groq que nombra los clusters.

    Retorna: {"temas": list, "mapeo_pregunta_tema": dict, "preguntas_destacadas": list[str]}
    """
    preguntas_unicas = _deduplicar(preguntas)
    if len(preguntas_unicas) < 5:
        return {"temas": [], "mapeo_pregunta_tema": {}, "preguntas_destacadas": []}

    labels = _clusterizar(preguntas_unicas)

    groq_client = Groq(api_key=groq_api_key)
    labels_validos = sorted(set(labels) - {-1})
    clusters_para_llm = [
        (label, [preguntas_unicas[i] for i in np.where(labels == label)[0]][:8])
        for label in labels_validos
    ]

    print(f"    Nombrando {len(clusters_para_llm)} grupos y eligiendo preguntas destacadas...")
    nombres_map, destacadas = _nombrar_clusters_y_destacar(clusters_para_llm, preguntas_unicas, groq_client)

    temas = []
    label_a_nombre = {}
    for label in labels_validos:
        indices = np.where(labels == label)[0]
        cluster_qs = [preguntas_unicas[i] for i in indices]
        nombre = nombres_map.get(label) or f"Tema {label + 1}"
        label_a_nombre[label] = nombre
        temas.append({
            "nombre": nombre,
            "n_preguntas": len(cluster_qs),
            "pct": 0.0,
            "ejemplos": cluster_qs[-config.MAX_EJEMPLOS_POR_TEMA:],
        })

    n_ruido = int(np.sum(labels == -1))
    if n_ruido > 0:
        indices_ruido = np.where(labels == -1)[0]
        label_a_nombre[-1] = "Preguntas variadas"
        temas.append({
            "nombre": "Preguntas variadas",
            "n_preguntas": n_ruido,
            "pct": 0.0,
            "ejemplos": [preguntas_unicas[i] for i in indices_ruido[-config.MAX_EJEMPLOS_POR_TEMA:]],
        })

    total = len(preguntas_unicas)
    for t in temas:
        t["pct"] = round(t["n_preguntas"] / total * 100, 1)
    temas.sort(key=lambda x: x["n_preguntas"], reverse=True)

    mapeo_pregunta_tema = {
        preguntas_unicas[i]: {
            "cluster_id": int(labels[i]),
            "nombre_tema": label_a_nombre[labels[i]],
        }
        for i in range(len(preguntas_unicas))
    }

    return {
        "temas": temas,
        "mapeo_pregunta_tema": mapeo_pregunta_tema,
        "preguntas_destacadas": destacadas,
    }


def _bloques_clusters(clusters: list) -> str:
    bloques = []
    for cid, preguntas in clusters:
        lista = "\n".join(f"  - {p}" for p in preguntas)
        bloques.append(f"Grupo {cid}:\n{lista}")
    return "\n\n".join(bloques)


def _nombrar_clusters(clusters: list, groq_client: Groq) -> dict:
    """
    Una sola llamada al LLM con todos los clusters en contexto para que
    genere títulos diferenciados entre sí.

    clusters: [(id, [preguntas...]), ...]
    Retorna: {id: titulo}
    """
    prompt = (
        "Eres un asistente académico. A continuación se presentan los grupos de preguntas "
        "formuladas por estudiantes de medicina.\n"
        "El dominio completo es 'Medicina Basada en la Evidencia', por lo que ese término "
        "tiene PROHIBIDO aparecer como nombre de ningún grupo.\n\n"
        "Tu tarea: asigna a CADA grupo un título corto en español (máximo 4 palabras) "
        "que capture el SUBTEMA ESPECÍFICO que distingue ese grupo de los demás. "
        "NO reorganices las preguntas entre grupos; los grupos son fijos, solo ponles nombre.\n\n"
        "Devuelve ÚNICAMENTE un JSON sin texto adicional ni bloques de markdown:\n"
        '[{"id": 0, "titulo": "..."}, {"id": 1, "titulo": "..."}, ...]\n\n'
        + _bloques_clusters(clusters)
    )
    try:
        resp = groq_client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
        data = json.loads(raw)
        return {
            int(item["id"]): str(item.get("titulo", "")).strip().capitalize()
            for item in data
            if str(item.get("titulo", "")).strip()
        }
    except Exception as e:
        print(f"    Advertencia al nombrar clusters: {e}")
        return {}


def _nombrar_clusters_y_destacar(clusters: list, preguntas_unicas: list, groq_client: Groq):
    """
    Una sola llamada al LLM que (a) nombra cada cluster igual que
    _nombrar_clusters(), y (b) selecciona hasta config.MAX_PREGUNTAS_DESTACADAS
    preguntas bien formuladas de todo el conjunto, útiles como ejemplo en clase.

    Retorna: (nombres_map: {id: titulo}, destacadas: list[str])
    """
    muestra_destacar = preguntas_unicas[:80]
    lista_muestra = "\n".join(f"  - {p}" for p in muestra_destacar)

    prompt = (
        "Eres un asistente académico. A continuación se presentan los grupos de preguntas "
        "formuladas por estudiantes de medicina.\n"
        "El dominio completo es 'Medicina Basada en la Evidencia', por lo que ese término "
        "tiene PROHIBIDO aparecer como nombre de ningún grupo.\n\n"
        "Tarea 1: asigna a CADA grupo un título corto en español (máximo 4 palabras) "
        "que capture el SUBTEMA ESPECÍFICO que distingue ese grupo de los demás. "
        "NO reorganices las preguntas entre grupos; los grupos son fijos, solo ponles nombre.\n\n"
        f"Tarea 2: de la siguiente lista completa de preguntas del curso, selecciona hasta "
        f"{config.MAX_PREGUNTAS_DESTACADAS} que estén especialmente bien formuladas (claras, "
        "específicas, que reflejen buen razonamiento clínico) para que el docente las use "
        "como ejemplo en clase. Cítalas EXACTAMENTE como aparecen, sin modificarlas.\n\n"
        f"Preguntas del curso:\n{lista_muestra}\n\n"
        "Devuelve ÚNICAMENTE un JSON sin texto adicional ni bloques de markdown, con esta forma:\n"
        '{"clusters": [{"id": 0, "titulo": "..."}, ...], "destacadas": ["...", "..."]}\n\n'
        + _bloques_clusters(clusters)
    )
    try:
        resp = groq_client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
        data = json.loads(raw)
        nombres_map = {
            int(item["id"]): str(item.get("titulo", "")).strip().capitalize()
            for item in data.get("clusters", [])
            if str(item.get("titulo", "")).strip()
        }
        destacadas = [
            str(d).strip() for d in data.get("destacadas", []) if str(d).strip()
        ][: config.MAX_PREGUNTAS_DESTACADAS]
        return nombres_map, destacadas
    except Exception as e:
        print(f"    Advertencia al nombrar clusters y elegir destacadas: {e}")
        return {}, []


def evolucion_semanal_por_tema(df: pd.DataFrame, tema_por_pregunta: dict) -> pd.DataFrame:
    """
    Conteo de preguntas por semana y por tema (Nivel 2), usando el mapeo
    pregunta -> tema que retorna compute_topics_detallado(). Permite ver, por
    ejemplo, si "Qué es MBE" sigue dominando en semanas donde ya no debería.

    Retorna un DataFrame ancho: índice = fecha de inicio de semana,
    columnas = nombre de tema, valores = número de preguntas. Vacío si no
    hay datos o no hay mapeo de temas todavía.
    """
    if df.empty or not tema_por_pregunta:
        return pd.DataFrame()

    df = df.copy()
    df["tema"] = df["pregunta"].str.strip().map(
        lambda p: tema_por_pregunta.get(p, {}).get("nombre_tema")
    )
    df = df.dropna(subset=["tema"])
    if df.empty:
        return pd.DataFrame()

    df["semana"] = df["timestamp"].dt.to_period("W").apply(lambda r: r.start_time.date())
    tabla = df.groupby(["semana", "tema"]).size().unstack(fill_value=0)
    return tabla.sort_index()
