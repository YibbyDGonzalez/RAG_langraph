import os
from dotenv import load_dotenv
load_dotenv()
from typing import Generator
# Algo
import faiss
import numpy as np
import pandas as pd
from groq import Groq
from sentence_transformers import SentenceTransformer

ARTICLES_PATH = "data/processed/articulos_total.csv"
EMBEDDINGS_PATH = "data/processed/models/embeddings_total.npy"
FAISS_PATH = "data/processed/models/faiss_index_total.bin"

EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
GROQ_MODEL = "openai/gpt-oss-20b"

# gpt-oss: Groq recomienda NO usar mensaje "system" con estos modelos (lo tratan
# como "developer", de menor prioridad que un "system" oculto que el propio modelo
# inyecta) y meter todas las instrucciones en el mensaje "user". Por eso ya no hay
# un _SYSTEM_PROMPT separado: las reglas viven todas en el prompt que arma
# app_langgraph.py y se envian como un unico mensaje "user".


def load_resources():
    df = pd.read_csv(ARTICLES_PATH)
    embeddings = np.load(EMBEDDINGS_PATH)
    index = faiss.read_index(FAISS_PATH)
    encoder = SentenceTransformer(EMBED_MODEL_NAME)

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY no encontrada en variables de entorno.")
    groq_client = Groq(api_key=api_key)

    return df, embeddings, index, encoder, groq_client


def buscar_articulos(query, top_k=3, *, encoder, index, df):
    """Recupera los top_k articulos mas relevantes para la query."""
    q_emb = encoder.encode([query], normalize_embeddings=True)
    scores, idxs = index.search(np.array(q_emb).astype("float32"), top_k)
    resultados = df.iloc[idxs[0]].copy()
    resultados["score"] = scores[0]
    return resultados


def call_ollama(prompt: str, *, ollama_client) -> str:
    """Llamada sincronica via Groq — interfaz compatible con rama main.

    reasoning_effort="low": esto es QA extractivo sobre 3 chunks, no requiere
    razonamiento multi-paso, y con gpt-oss los tokens de razonamiento salen del
    mismo presupuesto que max_tokens — en "medium" (default) se comian el budget
    y la respuesta final quedaba truncada o el modelo devolvia el fallback corto
    en vez de la respuesta completa."""
    completion = ollama_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=2048,
        reasoning_effort="low",
        include_reasoning=False,
    )
    return completion.choices[0].message.content


def call_ollama_stream(prompt: str, *, ollama_client) -> Generator[str, None, None]:
    """Streaming via Groq — interfaz compatible con rama main."""
    stream = ollama_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=2048,
        reasoning_effort="low",
        include_reasoning=False,
        stream=True,
    )
    for chunk in stream:
        token = chunk.choices[0].delta.content
        if token:
            yield token
