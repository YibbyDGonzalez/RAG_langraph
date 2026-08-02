"""
Router de navegación del reporte docente, basado en st.query_params.

Los 3 niveles agregados (Pulso, Temas, Estudiantes) son pestañas de nivel
superior. El Nivel 4 (estudiante individual) NO es una pestaña: solo se
alcanza fijando el parámetro "estudiante" desde una fila de Nivel 3 (o desde
una alerta de Nivel 1 que apunte a un estudiante puntual), y se sale de él
volviendo explícitamente a Estudiantes.
"""
import streamlit as st

VISTA_DEFAULT = "pulso"
VISTAS_VALIDAS = {"pulso", "temas", "estudiantes"}


def vista_actual() -> str:
    v = st.query_params.get("vista", VISTA_DEFAULT)
    return v if v in VISTAS_VALIDAS else VISTA_DEFAULT


def estudiante_seleccionado():
    """Usuario (normalizado, minúsculas) en Nivel 4, o None si no se ha entrado a ningún detalle."""
    return st.query_params.get("estudiante") or None


def filtro_actual(clave: str, default=None):
    return st.query_params.get(clave, default)


def ir_a_vista(vista: str, **filtro):
    """Navega a un nivel agregado (1-3), limpiando cualquier estudiante seleccionado."""
    st.query_params["vista"] = vista
    st.query_params.pop("estudiante", None)
    for k in list(st.query_params.keys()):
        if k not in ("vista",) and k not in filtro:
            st.query_params.pop(k, None)
    for k, v in filtro.items():
        st.query_params[k] = str(v)
    st.rerun()


def ir_a_estudiante(usuario_norm: str):
    """Entra al Nivel 4 para un estudiante específico. Solo debe llamarse desde Nivel 3."""
    st.query_params["estudiante"] = usuario_norm
    st.rerun()


def volver_a_estudiantes():
    st.query_params.pop("estudiante", None)
    st.query_params["vista"] = "estudiantes"
    st.rerun()
