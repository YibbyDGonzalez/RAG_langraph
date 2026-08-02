import uuid

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_current_user
from backend.models.schemas import ConversationDetail, ConversationOut
from backend.services import history_service

router = APIRouter()


@router.get("/conversations", response_model=list[ConversationOut])
async def listar_conversaciones(usuario: dict = Depends(get_current_user)):
    return history_service.listar_conversaciones(usuario["username"])


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def obtener_conversacion(conversation_id: str, usuario: dict = Depends(get_current_user)):
    conversacion = history_service.obtener_conversacion(usuario["username"], conversation_id)
    if conversacion is None:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return conversacion


@router.post("/conversations", response_model=ConversationDetail)
async def crear_conversacion(usuario: dict = Depends(get_current_user)):
    # Solo vive en el cliente hasta la primera pregunta, igual que
    # crear_chat() en Streamlit (no escribe en la DB todavía).
    return {"id": str(uuid.uuid4()), "title": "Nueva conversacion", "messages": []}
