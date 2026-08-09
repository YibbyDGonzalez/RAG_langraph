import json
import time
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from backend.dependencies import get_current_user
from backend.models.schemas import ChatRequest
from backend.services import history_service, rag_service

router = APIRouter()


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(payload: ChatRequest, request: Request, usuario: dict = Depends(get_current_user)):
    recursos = request.app.state.resources
    # Un id corto por request: agrupa todas las líneas de esta consulta en
    # `docker logs`, incluso si hay varias peticiones concurrentes.
    trace_id = uuid.uuid4().hex[:8]

    def event_stream():
        t_total_start = time.time()

        print(
            f"📥 [{trace_id}] POST /chat | usuario={usuario['username']!r} "
            f"session={payload.conversation_id!r} pregunta={payload.pregunta!r}"
        )

        stream = rag_service.responder(payload.pregunta, recursos=recursos, trace_id=trace_id)
        meta = next(stream)  # primer yield: chunks/scores/latencias (no se envía al cliente)

        respuesta_completa = ""
        for token in stream:
            respuesta_completa += token
            yield _sse("token", {"token": token})

        lat_llm = time.time() - meta["llm_start"]
        lat_total = time.time() - t_total_start

        print(
            f"✅ [{trace_id}] Respuesta generada en {lat_llm:.2f}s "
            f"({len(respuesta_completa)} caracteres)"
        )

        db_id = history_service.registrar_intercambio(
            usuario=usuario["username"],
            session_id=payload.conversation_id,
            pregunta=payload.pregunta,
            meta=meta,
            respuesta=respuesta_completa,
            lat_llm=lat_llm,
            lat_total=lat_total,
        )

        print(
            f"🏁 [{trace_id}] Fin | fila DB #{db_id} | "
            f"embedding={meta['lat_embedding']:.2f}s retrieval={meta['lat_retrieval']:.2f}s "
            f"llm={lat_llm:.2f}s total={lat_total:.2f}s"
        )

        yield _sse("done", {"content": respuesta_completa})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
