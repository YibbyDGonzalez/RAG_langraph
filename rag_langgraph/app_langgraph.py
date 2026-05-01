from app.core import load_resources, buscar_articulos, call_ollama

from typing import TypedDict
from langgraph.graph import StateGraph

df, embeddings, index, encoder, ollama_client = load_resources()

class InputState(TypedDict):
    query: str

class OutputState(TypedDict):
    response: str

class GraphState(InputState, OutputState):
    context: str

def retrieval_node(state: GraphState):
    query = state["query"]
    articulos = buscar_articulos(query, top_k=4, encoder=encoder, index=index, df=df)

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

    respuesta = call_ollama(prompt, ollama_client=ollama_client)
    return {"response": respuesta}

builder = StateGraph(GraphState, input=InputState, output=OutputState)

builder.add_node("retrieve", retrieval_node)
builder.add_node("generate", generation_node)

builder.set_entry_point("retrieve")
builder.add_edge("retrieve", "generate")

graph = builder.compile()

def responder(query: str):
    result = graph.invoke({"query": query})
    return result["response"]
