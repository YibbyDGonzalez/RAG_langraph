"""
Nivel 2 — Temas (qué se pregunta).
El análisis de temas (embeddings + clustering + Groq) se genera bajo demanda
(botón), igual que en el reporte anterior, porque puede tardar 1-3 minutos.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.report_views import router
from report_generator.modules.topic_analysis import compute_topics_detallado, evolucion_semanal_por_tema

_VERDE = "#17A589"


def _generar_si_hace_falta(df: pd.DataFrame, groq_key: str, desde_str: str, hasta_str: str):
    if st.session_state.get("temas_rango") != (desde_str, hasta_str):
        st.session_state.pop("temas_detallado", None)

    if not groq_key:
        st.warning(
            "Variable de entorno `GROQ_API_KEY` no encontrada. El análisis de temas no está disponible.",
            icon="⚠️",
        )
        return

    n_preguntas = len(df)
    if n_preguntas < 5:
        st.warning(f"Se necesitan al menos 5 preguntas para el análisis (periodo actual: {n_preguntas}).")
        return

    if "temas_detallado" not in st.session_state:
        st.info(
            "Este análisis agrupa las preguntas por significado usando embeddings semánticos, "
            "clustering automático y un LLM (Groq). Puede tardar 1-3 minutos.",
            icon="ℹ️",
        )
        if st.button(f"🔍 Generar mapa temático ({n_preguntas} preguntas)", type="primary"):
            with st.spinner("Ejecutando embeddings → UMAP → clustering → Groq..."):
                try:
                    resultado = compute_topics_detallado(list(df["pregunta"]), groq_key)
                    st.session_state["temas_detallado"] = resultado
                    st.session_state["temas_rango"] = (desde_str, hasta_str)
                except Exception as e:
                    st.error(f"Error durante el análisis: {e}")


def render(df: pd.DataFrame, groq_key: str, desde_str: str, hasta_str: str):
    filtro_tema = router.filtro_actual("tema")
    if filtro_tema:
        c1, c2 = st.columns([5, 1])
        c1.info(f"Mostrando con foco en: **{filtro_tema}**")
        if c2.button("Quitar filtro"):
            router.ir_a_vista("temas")

    _generar_si_hace_falta(df, groq_key, desde_str, hasta_str)

    resultado = st.session_state.get("temas_detallado")
    if not resultado:
        return

    temas = resultado["temas"]
    mapeo = resultado["mapeo_pregunta_tema"]

    if not temas:
        st.info("No se encontraron grupos temáticos con los datos del periodo seleccionado.")
        return

    st.success(f"{len(temas)} grupos temáticos identificados.")

    nombres = [t["nombre"] for t in reversed(temas)]
    conteos = [t["n_preguntas"] for t in reversed(temas)]
    fig_temas = go.Figure(go.Bar(
        x=conteos, y=nombres, orientation="h",
        marker_color=_VERDE,
        text=[f"  {c}" for c in conteos], textposition="outside",
        hovertemplate="%{y}: %{x} preguntas<extra></extra>",
    ))
    fig_temas.update_layout(
        height=max(250, len(temas) * 52),
        margin=dict(l=10, r=70, t=10, b=20),
        xaxis_title="Número de preguntas",
        plot_bgcolor="white", paper_bgcolor="white",
    )
    st.plotly_chart(fig_temas, use_container_width=True)

    st.markdown("#### Preguntas de ejemplo por tema")
    for tema in temas:
        expandido = filtro_tema == tema["nombre"]
        with st.expander(
            f"**{tema['nombre']}** — {tema['n_preguntas']} preguntas ({tema['pct']}%)",
            expanded=expandido,
        ):
            for ej in tema["ejemplos"]:
                st.markdown(f"- {ej}")

    st.markdown("---")
    st.markdown("#### Evolución semana a semana")
    evolucion = evolucion_semanal_por_tema(df, mapeo)
    if evolucion.empty or len(evolucion.index) < 2:
        st.caption("No hay suficientes semanas en el rango seleccionado para mostrar una tendencia.")
    else:
        fig_evol = go.Figure()
        for tema in evolucion.columns:
            fig_evol.add_trace(go.Scatter(
                x=[str(i) for i in evolucion.index],
                y=evolucion[tema],
                mode="lines+markers",
                name=tema,
            ))
        fig_evol.update_layout(
            height=340,
            margin=dict(l=10, r=10, t=20, b=40),
            xaxis_title="Semana",
            yaxis_title="Preguntas",
            plot_bgcolor="white", paper_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_evol, use_container_width=True)
