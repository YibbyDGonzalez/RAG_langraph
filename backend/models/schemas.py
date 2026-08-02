from pydantic import BaseModel


class ChatRequest(BaseModel):
    conversation_id: str
    pregunta: str


class MessageOut(BaseModel):
    role: str
    content: str


class ConversationOut(BaseModel):
    id: str
    title: str


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]
