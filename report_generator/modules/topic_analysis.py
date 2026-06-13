import math
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

    for label in sorted(set(labels) - {-1}):
        indices = np.where(labels == label)[0]
        cluster_qs = [preguntas[i] for i in indices]
        print(f"    Nombrando grupo {label + 1}/{len(set(labels) - {-1})} ({len(cluster_qs)} preguntas)...")
        nombre = _nombre_cluster(cluster_qs[:8], groq_client)
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


def _nombre_cluster(ejemplos: list, groq_client: Groq) -> str:
    """Pide a Groq un nombre corto (≤5 palabras) para el grupo."""
    lista = "\n".join(f"- {q}" for q in ejemplos)
    prompt = (
        "Analiza estas preguntas de estudiantes de medicina sobre Medicina Basada en la Evidencia:\n\n"
        f"{lista}\n\n"
        "Genera un nombre descriptivo MUY CORTO (máximo 5 palabras) en español "
        "que capture el tema central del grupo.\n"
        "Responde SOLO con el nombre, sin explicaciones, sin comillas, sin puntuación final."
    )
    try:
        resp = groq_client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"    Advertencia al nombrar grupo: {e}")
        return f"Grupo de {len(ejemplos)} preguntas"
