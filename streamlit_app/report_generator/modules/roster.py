import os
import sys

import pandas as pd
import yaml
from yaml.loader import SafeLoader

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from .roles import ROL_ESTUDIANTE, rol_de_usuario


def cargar_roster(users_yaml_path: str = None) -> dict:
    """
    Lee users.yaml (única fuente disponible de cuentas con acceso; no existe un
    roster académico separado) y retorna {usuario_en_minusculas: nombre_display}
    solo para las cuentas con rol Estudiante (las cuentas Docente no son parte
    del roster de estudiantes matriculados).

    Normaliza a minúsculas porque los usernames en users.yaml (ej. 'Estudiante1')
    no coinciden en mayúsculas con los guardados en la tabla consultas
    (ej. 'estudiante1').
    """
    path = users_yaml_path or config.USERS_YAML_PATH
    with open(path) as f:
        cfg = yaml.load(f, Loader=SafeLoader)

    usernames = (cfg or {}).get("credentials", {}).get("usernames", {})
    return {
        u.lower(): (info.get("name") or u)
        for u, info in usernames.items()
        if rol_de_usuario(u) == ROL_ESTUDIANTE
    }


def _usuarios_normalizados(df_historico: pd.DataFrame) -> set:
    if df_historico.empty:
        return set()
    return set(df_historico["usuario"].astype(str).str.lower().unique())


def nunca_usado(df_historico: pd.DataFrame, roster: dict) -> list:
    """
    Cuentas del roster que jamás han hecho una pregunta (en todo el histórico,
    no solo en el rango de fechas seleccionado).

    Retorna: [{"usuario": str, "nombre": str}, ...]
    """
    usados = _usuarios_normalizados(df_historico)
    return [
        {"usuario": u, "nombre": nombre}
        for u, nombre in roster.items()
        if u not in usados
    ]


def silenciosos(df_historico: pd.DataFrame, roster: dict, dias: int = None) -> list:
    """
    Cuentas del roster que SÍ han usado la herramienta antes, pero llevan
    `dias` (default config.SILENCIO_DIAS) o más sin actividad, contado desde
    hoy (no desde el rango de fechas seleccionado: es una señal operativa
    de "quién necesita seguimiento ahora").

    Retorna: [{"usuario": str, "nombre": str, "ultima_actividad": Timestamp,
               "dias_inactivo": int}, ...] ordenado de más a menos inactivo.
    """
    dias = dias if dias is not None else config.SILENCIO_DIAS
    if df_historico.empty:
        return []

    hoy = pd.Timestamp.now().normalize()
    ultima_actividad = (
        df_historico.assign(usuario_norm=df_historico["usuario"].astype(str).str.lower())
        .groupby("usuario_norm")["timestamp"]
        .max()
    )

    resultado = []
    for u, nombre in roster.items():
        if u not in ultima_actividad.index:
            continue
        ultima = ultima_actividad[u]
        dias_inactivo = (hoy - ultima.normalize()).days
        if dias_inactivo >= dias:
            resultado.append({
                "usuario": u,
                "nombre": nombre,
                "ultima_actividad": ultima,
                "dias_inactivo": int(dias_inactivo),
            })

    resultado.sort(key=lambda x: x["dias_inactivo"], reverse=True)
    return resultado
