from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.dependencies import get_current_user
from backend.services import auth_service

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


@router.post("/auth/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    try:
        datos = auth_service.autenticar(payload.username, payload.password)
    except auth_service.CredencialesInvalidas:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )
    token = auth_service.crear_token(datos["username"], datos["role"], datos["name"])
    return {"access_token": token, "role": datos["role"]}


@router.get("/auth/me")
async def me(usuario: dict = Depends(get_current_user)):
    return {"user_id": usuario["username"], "role": usuario["role"], "name": usuario["name"]}
