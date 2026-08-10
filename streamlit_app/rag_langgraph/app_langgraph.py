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


def _preparar_historial(historial: list[dict] | None) -> list[dict]:
    """Recorta a los últimos 3 intercambios (6 mensajes) para no inflar el
    prompt sin límite en conversaciones largas."""
    if not historial:
        return []
    return historial[-6:]


def _query_retrieval(historial: list[dict], query: str) -> str:
    """El embedding de FAISS no entiende pronombres ni elipsis ('sus',
    'el segundo', ...) si solo ve la pregunta nueva — por eso el retrieval de
    un seguimiento aislado puede traer chunks irrelevantes aunque el LLM sí
    tenga el historial en el prompt. Se arma la query de búsqueda con la
    última pregunta del usuario + la pregunta actual.

    Ojo: sumar también la última RESPUESTA del asistente empeora el
    retrieval en la práctica — un párrafo largo de respuesta diluye el
    embedding y desplaza el vector lejos del tema puntual del seguimiento."""
    if not historial:
        return query
    ultima_pregunta = next((m["content"] for m in reversed(historial) if m["role"] == "user"), None)
    if not ultima_pregunta:
        return query
    return f"{ultima_pregunta} {query}"


def _bloque_historial(historial: list[dict]) -> str:
    if not historial:
        return ""
    lineas = [f"{'Usuario' if m['role'] == 'user' else 'Asistente'}: {m['content']}" for m in historial]
    return "HISTORIAL RECIENTE DE LA CONVERSACIÓN:\n" + "\n".join(lineas) + "\n\n"


def build_graph(df, index, encoder, ollama_client):
    """Construye el grafo LangGraph con los recursos ya cargados."""

    def retrieval_node(state: GraphState):
        query = state["query"]
        articulos = buscar_articulos(query, top_k=3, encoder=encoder, index=index, df=df)
        contexto = ""
        for _, row in articulos.iterrows():
            contexto += f"FUENTE: ({row['referencia']} — pág. {row['pagina']})\n{row['texto']}\n\n"
        return {"context": contexto}

    def generation_node(state: GraphState):
        query = state["query"]
        contexto = state["context"]
        prompt = (
            f"PREGUNTA:\n{query}\n\nCONTEXTO:\n{contexto}\n\n"
            f"Responde claro y, al citar, usa exactamente el texto entre paréntesis de cada "
            f"FUENTE que uses (autor, título, año y página), y no inventes."
        )
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
        contexto += f"FUENTE: ({row['referencia']} — pág. {row['pagina']})\n{row['texto']}\n\n"

    # Paso 2: generacion en streaming (el usuario ve tokens desde el primer segundo)
    prompt = (
        f"PREGUNTA:\n{query}\n\nCONTEXTO:\n{contexto}\n\n"
        f"Responde claro y, al citar, usa exactamente el texto entre paréntesis de cada "
        f"FUENTE que uses (autor, título, año y página), y no inventes."
    )
    yield from call_ollama_stream(prompt, ollama_client=ollama_client)


def responder_stream_logged(
    query: str, *, df, index, encoder, ollama_client, trace_id: str | None = None,
    historial: list[dict] | None = None,
) -> Generator:
    """Pipeline RAG con streaming Y captura de metadata para logging.
    Primer yield: dict con chunks, scores y latencias de embedding+retrieval.
    Yields siguientes: tokens de texto del LLM en tiempo real.

    `historial`: mensajes previos de la conversación ([{"role": "user"/
    "assistant", "content": str}, ...], más antiguo primero). Sin esto cada
    pregunta se resuelve aislada y los seguimientos ("cuáles son sus 3
    componentes") fallan tanto en retrieval como en generación.

    Todas las líneas impresas llevan el mismo `trace_id` para poder seguir
    una consulta de punta a punta en `docker logs` aunque haya requests
    concurrentes intercalados."""
    import time
    import uuid
    import numpy as np

    trace_id = trace_id or uuid.uuid4().hex[:8]
    meta = {"trace_id": trace_id}
    historial = _preparar_historial(historial)

    # Paso 1: Embedding — tiempo aislado. Se embebe la query "enriquecida"
    # con el turno anterior, no la pregunta cruda, para que el retrieval
    # entienda seguimientos.
    query_retrieval = _query_retrieval(historial, query)
    print(f"🧠 [{trace_id}] Generando embedding de la pregunta...")
    if query_retrieval != query:
        print(f"   💬 [{trace_id}] query retrieval (con historial): {query_retrieval!r}")
    t0 = time.time()
    q_emb = encoder.encode([query_retrieval], normalize_embeddings=True)
    meta["lat_embedding"] = time.time() - t0
    print(f"✅ [{trace_id}] Embedding listo en {meta['lat_embedding']:.3f}s")

    # Paso 2: Busqueda FAISS — tiempo aislado
    print(f"🔍 [{trace_id}] Buscando en FAISS (top_k=3)...")
    t1 = time.time()
    scores, idxs = index.search(np.array(q_emb).astype("float32"), 3)
    meta["lat_retrieval"] = time.time() - t1

    articulos = df.iloc[idxs[0]].copy()
    articulos["score"] = scores[0]

    print(f"📚 [{trace_id}] {len(articulos)} documentos recuperados en {meta['lat_retrieval']:.3f}s:")
    for _, row in articulos.iterrows():
        print(
            f"   📄 [{trace_id}] fuente={row['fuente_pdf']!r} "
            f"pág={row['pagina']} score={row['score']:.4f}"
        )

    meta["chunks"] = articulos[["chunk_id", "fuente_pdf", "referencia", "pagina", "texto"]].to_dict("records")
    meta["scores"] = scores[0].tolist()

    # Paso 3: Construir contexto y prompt
    contexto = ""
    for _, row in articulos.iterrows():
        contexto += f"FUENTE: ({row['referencia']} — pág. {row['pagina']})\n{row['texto']}\n\n"

    prompt = (
        f"{_bloque_historial(historial)}"
        f"PREGUNTA:\n{query}\n\n"
        f"CONTEXTO:\n{contexto}\n\n"
        f"Responde claro y, al citar, usa exactamente el texto entre paréntesis de cada "
        f"FUENTE que uses (autor, título, año y página), y no inventes. Usa el historial de la "
        f"conversación solo si la pregunta es un seguimiento que lo necesita. Ve directo a la "
        f"respuesta: no expliques ni menciones si la pregunta se relaciona o no con el historial. "
        f"Si la pregunta no es de Medicina Basada en la Evidencia (MBE), NO digas que no tienes "
        f"información ni menciones el contexto o los textos: en 1-2 frases, amable y directo, di "
        f"que esa pregunta está fuera de tu alcance como asistente de MBE, y ofrece ayudar con "
        f"temas como niveles y calidad de la evidencia, diseño de estudios, sesgos, formulación de "
        f"preguntas clínicas, interpretación de resultados o revisiones sistemáticas."
    )
    print(f"✍️  [{trace_id}] Prompt listo ({len(prompt)} caracteres) — iniciando generación...")

    meta["llm_start"] = time.time()

    # Primer yield: metadata (capturado en chat.py antes de iniciar el stream)
    yield meta

    # Yields siguientes: tokens del LLM
    print(f"🤖 [{trace_id}] Generando respuesta (streaming)...")
    yield from call_ollama_stream(prompt, ollama_client=ollama_client)
