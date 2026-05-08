import os
from dotenv import load_dotenv
load_dotenv()
from typing import Generator

import faiss
import numpy as np
import pandas as pd
from groq import Groq
from sentence_transformers import SentenceTransformer

ARTICLES_PATH = "data/processed/articulos_total.csv"
EMBEDDINGS_PATH = "data/processed/models/embeddings_total.npy"
FAISS_PATH = "data/processed/models/faiss_index_total.bin"

EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
GROQ_MODEL = "llama-3.1-8b-instant"

_SYSTEM_PROMPT = (
    "Eres un experto en Medicina Basada en la Evidencia (MBE). "
    "Tu tarea es responder preguntas clinicas de manera clara, precisa y concisa, "
    "utilizando UNICAMENTE la informacion proporcionada en los textos de contexto. "
    "Reglas estrictas: "
    "- No uses conocimiento externo. "
    "- No inventes informacion. "
    "- Si la respuesta no esta en el contexto, responde: "
    "'No hay suficiente informacion en los textos proporcionados para responder la pregunta.' "
    "- Prioriza informacion relevante y directamente relacionada con la pregunta. "
    "- Resume y sintetiza, no copies textualmente a menos que sea necesario. "
    "Formato de respuesta: "
    "- Respuesta clara y directa. "
    "- Si aplica, incluye un breve soporte citando el fragmento del texto."
)


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
    """Llamada sincronica via Groq — interfaz compatible con rama main."""
    completion = ollama_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=1300,
    )
    return completion.choices[0].message.content


def call_ollama_stream(prompt: str, *, ollama_client) -> Generator[str, None, None]:
    """Streaming via Groq — interfaz compatible con rama main."""
    stream = ollama_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=1300,
        stream=True,
    )
    for chunk in stream:
        token = chunk.choices[0].delta.content
        if token:
            yield token
