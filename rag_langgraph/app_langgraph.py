from app.app import load_resources, buscar_articulos, call_groq

from typing import TypedDict
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

df, embeddings, index, encoder, groq_client = load_resources()

class GraphState(TypedDict):
    query: str
    context: str
    response: str

def retrieval_node(state: GraphState):
    query = state["query"]
    articulos = buscar_articulos(query, top_k=4)

    contexto = ""
    for _, row in articulos.iterrows():
        contexto += f"ARTÍCULO {row['id_articulo']} - {row['titulo']}\n{row['texto']}\n\n"

    return {"context": contexto}

def generation_node(state: GraphState):
    query = state["query"]
    contexto = state["context"]

    prompt = f"""
PREGUNTA:
{query}

CONTEXTO:
{contexto}

Responde claro, cita páginas y no inventes.
"""

    respuesta = call_groq(prompt)
    return {"response": respuesta}

builder = StateGraph(GraphState)

builder.add_node("retrieve", retrieval_node)
builder.add_node("generate", generation_node)

builder.set_entry_point("retrieve")
builder.add_edge("retrieve", "generate")

memory = MemorySaver()

graph = builder.compile(checkpointer=memory)

def responder(query: str):
    result = graph.invoke(
    {"query": query},
    config={"configurable": {"thread_id": "1"}}
)
    return result["response"]