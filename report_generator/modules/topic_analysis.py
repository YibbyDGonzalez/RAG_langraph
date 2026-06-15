import json
import math
import re
import sys
import os

import numpy as np
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


def compute_topics(preguntas: list, groq_api_key: str) -> list:
    """
    Agrupa las preguntas por significado mediante:
      1. Embeddings multilingües (sentence-transformers)
      2. Reducción de dimensiones con UMAP
      3. Clustering con HDBSCAN (KMeans como fallback)
      4. Nombre de cada grupo generado por Groq

    Retorna lista de dicts ordenada de mayor a menor grupo:
      [{"nombre": str, "n_preguntas": int, "pct": float, "ejemplos": list[str]}]
    """
    # Deduplicar preservando orden
    seen = set()
    preguntas_unicas = []
    for p in preguntas:
        p_norm = p.strip()
        if p_norm and p_norm not in seen:
            seen.add(p_norm)
            preguntas_unicas.append(p_norm)
    preguntas = preguntas_unicas

    if len(preguntas) < 5:
        return []

    # ── 1. Embeddings ────────────────────────────────────────────────────────
    print("    Cargando modelo de embeddings...")
    model = SentenceTransformer(config.EMBEDDING_MODEL)
    print("    Generando embeddings (puede tardar un momento)...")
    embeddings = model.encode(preguntas, show_progress_bar=True, batch_size=32)

    # ── 2. Reducción UMAP ────────────────────────────────────────────────────
    n = len(preguntas)
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

    # ── 3. Clustering HDBSCAN ────────────────────────────────────────────────
    min_cluster = max(2, min(config.HDBSCAN_MIN_CLUSTER_SIZE, n // 8))
    print(f"    Agrupando con HDBSCAN (min_cluster_size={min_cluster})...")
    clusterer = HDBSCAN(
        min_cluster_size=min_cluster,
        min_samples=config.HDBSCAN_MIN_SAMPLES,
    )
    labels = clusterer.fit_predict(reduced)

    # Fallback a KMeans si HDBSCAN clasifica todo como ruido
    n_clusters_validos = len(set(labels) - {-1})
    if n_clusters_validos < 2:
        k = max(2, min(8, int(math.sqrt(n / 2))))
        print(f"    HDBSCAN sin grupos suficientes → usando KMeans (k={k})...")
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(reduced)

    # ── 4. Construir grupos y nombrarlos con Groq ────────────────────────────
    groq_client = Groq(api_key=groq_api_key)
    temas = []
    labels_validos = sorted(set(labels) - {-1})

    # Recopilar preguntas representativas de cada cluster
    clusters_para_llm = [
        (label, [preguntas[i] for i in np.where(labels == label)[0]][:8])
        for label in labels_validos
    ]

    # Una sola llamada al LLM con todos los clusters en contexto
    print(f"    Nombrando {len(clusters_para_llm)} grupos en una sola llamada a Groq...")
    nombres_map = _nombrar_clusters(clusters_para_llm, groq_client)

    # Construir temas con el nombre asignado (o fallback "Tema N")
    for label in labels_validos:
        indices = np.where(labels == label)[0]
        cluster_qs = [preguntas[i] for i in indices]
        nombre = nombres_map.get(label) or f"Tema {label + 1}"
        temas.append({
            "nombre": nombre,
            "n_preguntas": len(cluster_qs),
            "pct": 0.0,
            "ejemplos": cluster_qs[: config.MAX_EJEMPLOS_POR_TEMA],
        })

    # Puntos de ruido (HDBSCAN) → grupo "Preguntas variadas"
    n_ruido = int(np.sum(labels == -1))
    if n_ruido > 0:
        indices_ruido = np.where(labels == -1)[0]
        temas.append({
            "nombre": "Preguntas variadas",
            "n_preguntas": n_ruido,
            "pct": 0.0,
            "ejemplos": [preguntas[i] for i in indices_ruido[: config.MAX_EJEMPLOS_POR_TEMA]],
        })

    # Calcular porcentajes y ordenar
    total = len(preguntas)
    for t in temas:
        t["pct"] = round(t["n_preguntas"] / total * 100, 1)

    temas.sort(key=lambda x: x["n_preguntas"], reverse=True)
    return temas


def _nombrar_clusters(clusters: list, groq_client: Groq) -> dict:
    """
    Una sola llamada al LLM con todos los clusters en contexto para que
    genere títulos diferenciados entre sí.

    clusters: [(id, [preguntas...]), ...]
    Retorna: {id: titulo}
    """
    bloques = []
    for cid, preguntas in clusters:
        lista = "\n".join(f"  - {p}" for p in preguntas)
        bloques.append(f"Grupo {cid}:\n{lista}")

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
        + "\n\n".join(bloques)
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
