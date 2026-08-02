"""Autenticación contra streamlit_app/users.yaml (mismo archivo que usa
streamlit-authenticator hoy) + emisión/verificación de JWT.

No se migra ningún esquema: las contraseñas ya están hasheadas en bcrypt
en users.yaml, tal cual las valida Streamlit.
"""
import os
import time

import bcrypt
import jwt
import yaml
from dotenv import load_dotenv

from backend import bootstrap
from report_generator.modules.roles import rol_de_usuario

load_dotenv()  # no depender de que algún otro módulo lo haya cargado antes

USERS_YAML_PATH = os.path.join(bootstrap.STREAMLIT_APP_DIR, "users.yaml")

JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_SECONDS = 24 * 60 * 60  # 24h, igual que cookie.expiry_days en users.yaml


def _cargar_credenciales() -> dict:
    with open(USERS_YAML_PATH) as f:
        config = yaml.safe_load(f)
    return config["credentials"]["usernames"]

class CredencialesInvalidas(Exception):
    pass


def autenticar(username: str, password: str) -> dict:
    """Valida usuario/contraseña contra users.yaml. Devuelve {username, role}
    o lanza CredencialesInvalidas."""
    usuarios = _cargar_credenciales()
    datos = usuarios.get(username)
    if datos is None:
        raise CredencialesInvalidas()

    hash_guardado = datos["password"].encode()
    if not bcrypt.checkpw(password.encode(), hash_guardado):
        raise CredencialesInvalidas()

    return {"username": username, "role": rol_de_usuario(username)}


def crear_token(username: str, role: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "exp": int(time.time()) + JWT_EXPIRY_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decodificar_token(token: str) -> dict:
    """Devuelve {username, role} o lanza jwt.PyJWTError si el token es
    inválido o expiró."""
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    return {"username": payload["sub"], "role": payload["role"]}
