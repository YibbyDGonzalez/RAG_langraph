import os
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import ollama
from typing import Generator

ARTICLES_PATH = "data/processed/articulos_total.csv"
EMBEDDINGS_PATH = "data/processed/models/embeddings_total.npy"
FAISS_PATH = "data/processed/models/faiss_index_total.bin"

EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OLLAMA_MODEL = "llama3.2:1b"   # 1b: ~3x mas rapido en CPU que 3b, suficiente para RAG
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

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
    ollama_client = ollama.Client(host=OLLAMA_HOST)
    return df, embeddings, index, encoder, ollama_client


def buscar_articulos(query, top_k=3, *, encoder, index, df):
    """Recupera los top_k articulos mas relevantes para la query."""
    q_emb = encoder.encode([query], normalize_embeddings=True)
    scores, idxs = index.search(np.array(q_emb).astype("float32"), top_k)
    resultados = df.iloc[idxs[0]].copy()
    resultados["score"] = scores[0]
    return resultados


def call_ollama(prompt: str, *, ollama_client) -> str:
    """Llamada sincronica — devuelve el texto completo al terminar."""
    response = ollama_client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        options={"temperature": 0.2, "num_predict": 1300, "num_ctx": 1024},
    )
    return response["message"]["content"]


def call_ollama_stream(prompt: str, *, ollama_client) -> Generator[str, None, None]:
    """Llamada con streaming — hace yield de cada token al generarse.
    Usar con st.write_stream() para que el usuario vea la respuesta en tiempo real."""
    stream = ollama_client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        options={"temperature": 0.2, "num_predict": 300,"num_ctx": 1024},
        stream=True,
    )
    for chunk in stream:
        token = chunk["message"]["content"]
        if token:
            yield token
