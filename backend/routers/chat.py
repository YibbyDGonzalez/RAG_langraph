import json
import time

from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse

from backend.models.schemas import ChatRequest
from backend.services import history_service, rag_service

router = APIRouter()


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(payload: ChatRequest, request: Request, x_user_id: str = Header(...)):
    recursos = request.app.state.resources

    def event_stream():
        t_total_start = time.time()

        stream = rag_service.responder(payload.pregunta, recursos=recursos)
        meta = next(stream)  # primer yield: chunks/scores/latencias (no se envía al cliente)

        respuesta_completa = ""
        for token in stream:
            respuesta_completa += token
            yield _sse("token", {"token": token})

        lat_llm = time.time() - meta["llm_start"]
        lat_total = time.time() - t_total_start

        history_service.registrar_intercambio(
            usuario=x_user_id,
            session_id=payload.conversation_id,
            pregunta=payload.pregunta,
            meta=meta,
            respuesta=respuesta_completa,
            lat_llm=lat_llm,
            lat_total=lat_total,
        )

        yield _sse("done", {"content": respuesta_completa})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
