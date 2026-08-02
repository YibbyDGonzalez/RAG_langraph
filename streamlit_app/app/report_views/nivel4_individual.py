"""
Nivel 4 — Estudiante individual.
Solo alcanzable por click desde el Nivel 3 (no es una pestaña). Aplica el
criterio "mínimo suficiente": datos básicos, últimas 3-5 preguntas (no todo
el historial), timeline simple y perfil temático corto.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.report_views import router
from report_generator.modules.student_detail import detalle_estudiante

_AZUL_MED = "#2E86AB"


def render(db_path: str, usuario_norm: str, nombre_display: str, tema_por_pregunta: dict):
    if st.button("‹ Volver a Estudiantes"):
        router.volver_a_estudiantes()

    st.caption("🔒 Vista individual — uso exclusivo para tutoría docente")

    detalle = detalle_estudiante(db_path, usuario_norm, tema_por_pregunta)

    ultima_fmt = (
        pd.to_datetime(detalle["ultima_actividad"]).strftime("%d/%m/%Y")
        if detalle["ultima_actividad"] else "—"
    )
    st.markdown(f"### {nombre_display}")
    st.markdown(f"{detalle['n_preguntas']} preguntas · {detalle['n_sesiones']} sesiones · última actividad: {ultima_fmt}")

    st.markdown("---")
    st.markdown("##### Últimas preguntas")
    if not detalle["ultimas_preguntas"]:
        st.caption("Sin preguntas registradas.")
    else:
        for fila in detalle["ultimas_preguntas"]:
            fecha = pd.to_datetime(fila["timestamp"]).strftime("%d/%m")
            st.markdown(f'- **{fecha}** — "{fila["pregunta"]}"')

    st.markdown("---")
    st.markdown("##### Actividad")
    timeline = detalle["timeline"]
    if not timeline:
        st.caption("Sin actividad registrada.")
    else:
        fig = go.Figure(go.Scatter(
            x=[t["dia"] for t in timeline],
            y=[t["n"] for t in timeline],
            mode="lines+markers",
            line=dict(color=_AZUL_MED),
        ))
        fig.update_layout(
            height=180,
            margin=dict(l=10, r=10, t=10, b=30),
            yaxis_title="Preguntas",
            plot_bgcolor="white", paper_bgcolor="white",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("##### Perfil temático")
    if tema_por_pregunta:
        tocados = ", ".join(detalle["temas_tocados"]) if detalle["temas_tocados"] else "Ninguno"
        no_tocados = ", ".join(detalle["temas_no_tocados"]) if detalle["temas_no_tocados"] else "Ninguno"
        st.markdown(f"**Ha tocado:** {tocados}")
        st.markdown(f"**No ha tocado:** {no_tocados}")
    else:
        st.caption("Genera el análisis de temas en la pestaña Temas para ver el perfil temático.")
