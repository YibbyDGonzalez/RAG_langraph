"""
roles.py — Distingue Docente vs Estudiante a partir del username.

Desde que los usuarios pasaron a loguearse con su correo, el rol ya no se
puede inferir de un prefijo ('Docente3', 'Estudiante1'): se lee del campo
explícito "rol" en users.yaml. Para los usernames viejos que quedaron en el
histórico de `consultas` (de antes del cambio a correo), se cae al
heurístico anterior por prefijo, así el reporte no pierde su clasificación.
"""
import os
import sys

import pandas as pd
import yaml
from yaml.loader import SafeLoader

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

ROL_DOCENTE = "Docente"
ROL_ESTUDIANTE = "Estudiante"

ROL_QUERY_A_ROL = {"docentes": ROL_DOCENTE, "estudiantes": ROL_ESTUDIANTE}

_cache = {"mtime": None, "roles": {}}


def _roles_por_usuario() -> dict:
    """{usuario_en_minusculas: rol}, releído solo cuando cambia users.yaml."""
    try:
        mtime = os.path.getmtime(config.USERS_YAML_PATH)
    except OSError:
        return {}

    if _cache["mtime"] != mtime:
        with open(config.USERS_YAML_PATH) as f:
            cfg = yaml.load(f, Loader=SafeLoader) or {}
        usernames = cfg.get("credentials", {}).get("usernames", {})
        _cache["roles"] = {
            u.lower(): info.get("rol")
            for u, info in usernames.items()
        }
        _cache["mtime"] = mtime

    return _cache["roles"]


def rol_de_usuario(usuario: str) -> str:
    """Rol explícito de users.yaml si la cuenta existe hoy; si no (username
    histórico de antes del cambio a correo), infiere por prefijo 'docente'.
    Cualquier caso no reconocido cae a Estudiante (deny-by-default para
    secciones restringidas a Docente).
    """
    u = (usuario or "").strip().lower()

    rol = _roles_por_usuario().get(u)
    if rol in (ROL_DOCENTE, ROL_ESTUDIANTE):
        return rol

    if u.startswith("docente"):
        return ROL_DOCENTE
    return ROL_ESTUDIANTE


def filtrar_por_rol(df: pd.DataFrame, rol: str) -> pd.DataFrame:
    """Filtra un DataFrame de `consultas` por rol ('docentes'/'estudiantes'/'todos')."""
    rol_objetivo = ROL_QUERY_A_ROL.get(rol)
    if rol_objetivo is None or df.empty:
        return df
    mascara = df["usuario"].astype(str).map(rol_de_usuario) == rol_objetivo
    return df[mascara].reset_index(drop=True)
