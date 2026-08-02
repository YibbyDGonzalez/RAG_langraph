"""
Nivel 3 — Estudiantes (vista de grupo).
Cada fila del listado es clickeable y lleva al Nivel 4 (solo alcanzable desde aquí).
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.report_views import router
from report_generator.modules.students import histograma_esfuerzo, tabla_estudiantes

_AZUL_OSC = "#1B4F72"
_GRID = "#eef2f7"


def render(df: pd.DataFrame, roster: dict, tema_por_pregunta: dict, nunca_usado: list, silenciosos: list):
    tabla = tabla_estudiantes(df, tema_por_pregunta, roster)
    hist = histograma_esfuerzo(tabla)

    st.markdown("##### Histograma de esfuerzo")
    fig_hist = go.Figure(go.Bar(
        x=["0", "1-5", "6-20", "20+"],
        y=[hist["0"], hist["1-5"], hist["6-20"], hist["20+"]],
        marker_color=_AZUL_OSC,
        hovertemplate="%{x} preguntas: %{y} estudiantes<extra></extra>",
    ))
    fig_hist.update_layout(
        height=220,
        margin=dict(l=10, r=10, t=10, b=30),
        xaxis_title="Preguntas en el periodo",
        yaxis=dict(title="Nº estudiantes", gridcolor=_GRID),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")
    st.markdown("##### 😴 Estudiantes silenciosos (sin actividad hace 2+ semanas)")
    if not silenciosos and not nunca_usado:
        st.caption("Todos los estudiantes del roster han tenido actividad reciente.")
    else:
        for s in silenciosos:
            st.markdown(f"- **{s['nombre']}** — última actividad hace {s['dias_inactivo']} días")
        if nunca_usado:
            nombres = ", ".join(n["nombre"] for n in nunca_usado)
            st.markdown(f"- **Nunca han usado la herramienta:** {nombres}")

    st.markdown("---")
    st.markdown("##### Listado completo de estudiantes")
    st.caption("Orden por defecto: quién menos ha usado la herramienta primero (no alfabético).")

    h1, h2, h3, h4, h5 = st.columns([3, 1, 1, 3, 1])
    h1.markdown("**Estudiante**")
    h2.markdown("**Preguntas**")
    h3.markdown("**Sesiones**")
    h4.markdown("**Últimos temas**")
    h5.markdown("")

    for fila in tabla:
        c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 3, 1])
        c1.markdown(fila["nombre"])
        c2.markdown(str(fila["n_preguntas"]))
        c3.markdown(str(fila["n_sesiones"]))
        c4.markdown(", ".join(fila["ultimos_temas"]) if fila["ultimos_temas"] else "—")
        if c5.button("Ver →", key=f"estudiante_{fila['usuario']}"):
            router.ir_a_estudiante(fila["usuario"])
