import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.services import auth_service

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """Reemplaza el header X-User-Id de Fase 1: exige 'Authorization: Bearer <jwt>'."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return auth_service.decodificar_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(role: str):
    """Factory de dependencia para gatear endpoints por rol (p.ej. el
    reporte docente en Fase 4): Depends(require_role(ROL_DOCENTE))."""

    def _checker(usuario: dict = Depends(get_current_user)) -> dict:
        if usuario["role"] != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requiere rol {role}",
            )
        return usuario

    return _checker
