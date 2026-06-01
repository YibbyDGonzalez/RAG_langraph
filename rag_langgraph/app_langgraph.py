import sys
import os

# /app/app debe estar en sys.path para importar core directamente
_app_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

from core import load_resources, buscar_articulos, call_ollama, call_ollama_stream

from typing import TypedDict, Generator
from langgraph.graph import StateGraph


class InputState(TypedDict):
    query: str

class OutputState(TypedDict):
    response: str

class GraphState(InputState, OutputState):
    context: str


def build_graph(df, index, encoder, ollama_client):
    """Construye el grafo LangGraph con los recursos ya cargados."""

    def retrieval_node(state: GraphState):
        query = state["query"]
        articulos = buscar_articulos(query, top_k=3, encoder=encoder, index=index, df=df)
        contexto = ""
        for _, row in articulos.iterrows():
            contexto += f"ARTÍCULO {row['id_articulo']} - {row['titulo']}\n{row['texto']}\n\n"
        return {"context": contexto}

    def generation_node(state: GraphState):
        query = state["query"]
        contexto = state["context"]
        prompt = f"PREGUNTA:\n{query}\n\nCONTEXTO:\n{contexto}\n\nResponde claro, cita paginas y no inventes."
        respuesta = call_ollama(prompt, ollama_client=ollama_client)
        return {"response": respuesta}

    builder = StateGraph(GraphState, input=InputState, output=OutputState)
    builder.add_node("retrieve", retrieval_node)
    builder.add_node("generate", generation_node)
    builder.set_entry_point("retrieve")
    builder.add_edge("retrieve", "generate")
    return builder.compile()


def responder(query: str, *, df, index, encoder, ollama_client) -> str:
    """Pipeline RAG sincrono — devuelve respuesta completa."""
    graph = build_graph(df, index, encoder, ollama_client)
    result = graph.invoke({"query": query})
    return result["response"]


def responder_stream(query: str, *, df, index, encoder, ollama_client) -> Generator[str, None, None]:
    """Pipeline RAG con streaming — hace yield de tokens en tiempo real.
    La recuperacion FAISS ocurre primero (sincrona), luego genera en streaming."""
    # Paso 1: recuperacion (rapido, ~1 seg)
    articulos = buscar_articulos(query, top_k=3, encoder=encoder, index=index, df=df)
    contexto = ""
    for _, row in articulos.iterrows():
        contexto += f"ARTÍCULO {row['id_articulo']} - {row['titulo']}\n{row['texto']}\n\n"

    # Paso 2: generacion en streaming (el usuario ve tokens desde el primer segundo)
    prompt = f"PREGUNTA:\n{query}\n\nCONTEXTO:\n{contexto}\n\nResponde claro, cita paginas y no inventes."
    yield from call_ollama_stream(prompt, ollama_client=ollama_client)


def responder_stream_logged(query: str, *, df, index, encoder, ollama_client) -> Generator:
    """Pipeline RAG con streaming Y captura de metadata para logging.
    Primer yield: dict con chunks, scores y latencias de embedding+retrieval.
    Yields siguientes: tokens de texto del LLM en tiempo real."""
    import time
    import numpy as np

    meta = {}

    # Paso 1: Embedding — tiempo aislado
    t0 = time.time()
    q_emb = encoder.encode([query], normalize_embeddings=True)
    meta["lat_embedding"] = time.time() - t0

    # Paso 2: Busqueda FAISS — tiempo aislado
    t1 = time.time()
    scores, idxs = index.search(np.array(q_emb).astype("float32"), 3)
    meta["lat_retrieval"] = time.time() - t1

    articulos = df.iloc[idxs[0]].copy()
    articulos["score"] = scores[0]

    meta["chunks"] = articulos[["id_articulo", "titulo", "texto"]].to_dict("records")
    meta["scores"] = scores[0].tolist()

    # Paso 3: Construir contexto y prompt
    contexto = ""
    for _, row in articulos.iterrows():
        contexto += f"ARTÍCULO {row['id_articulo']} - {row['titulo']}\n{row['texto']}\n\n"

    prompt = (
        f"PREGUNTA:\n{query}\n\n"
        f"CONTEXTO:\n{contexto}\n\n"
        f"Responde claro, cita paginas y no inventes."
    )

    meta["llm_start"] = time.time()

    # Primer yield: metadata (capturado en app.py antes de iniciar el stream)
    yield meta

    # Yields siguientes: tokens del LLM
    yield from call_ollama_stream(prompt, ollama_client=ollama_client)
