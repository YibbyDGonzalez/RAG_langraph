"""
Nivel 1 — Pulso del curso (vista de entrada).
Debe caber en una pantalla y responder en 10 segundos "¿cómo va la semana?".
Por eso NO depende del análisis de temas (embeddings + Groq, 1-3 min): las
alertas de contenido (tema en alza, retrieval débil) solo aparecen si ya se
generó el mapa temático en la pestaña Temas; si no, se avisa explícitamente.
"""
import plotly.graph_objects as go
import streamlit as st

from app.report_views import router
from report_generator.modules.temporal_analysis import DIAS_ES, formatear_duracion

_AZUL_OSC = "#1B4F72"
_AZUL_MED = "#2E86AB"
_GRID = "#eef2f7"


def _fmt_delta(pct):
    if pct is None:
        return None
    signo = "+" if pct >= 0 else ""
    return f"{signo}{int(pct)}% vs periodo anterior"


def render(kpis_delta: dict, sparkline_data: list, alertas: list, temas_generados: bool, total_estudiantes: int,
           temporal: dict = None):
    c1, c2, c3 = st.columns(3)
    c1.metric("🧑‍🎓 Total de estudiantes", total_estudiantes)
    c2.metric("👥 Estudiantes activos", kpis_delta["estudiantes"]["valor"], _fmt_delta(kpis_delta["estudiantes"]["delta_pct"]))
    c3.metric("💬 Total de chats", kpis_delta["sesiones"]["valor"], _fmt_delta(kpis_delta["sesiones"]["delta_pct"]))

    c4, c5, c6 = st.columns(3)
    c4.metric("📨 Total de preguntas", kpis_delta["preguntas"]["valor"], _fmt_delta(kpis_delta["preguntas"]["delta_pct"]))
    c5.metric(
        "❓ Pregunta por estudiante",
        kpis_delta["preguntas_por_estudiante"]["valor"],
        _fmt_delta(kpis_delta["preguntas_por_estudiante"]["delta_pct"]),
    )
    c6.metric(
        "⏱️ Tiempo por sesión promedio",
        formatear_duracion(kpis_delta["tiempo_promedio_sesion"]["valor"]),
        _fmt_delta(kpis_delta["tiempo_promedio_sesion"]["delta_pct"]),
    )

    st.markdown("##### Actividad (últimas 4 semanas)")
    fig = go.Figure(go.Bar(
        x=[d["semana"] for d in sparkline_data],
        y=[d["n_preguntas"] for d in sparkline_data],
        marker_color=_AZUL_MED,
        hovertemplate="Semana del %{x}: %{y} preguntas<extra></extra>",
    ))
    fig.update_layout(
        height=140,
        margin=dict(l=10, r=10, t=10, b=30),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False, showticklabels=False),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("##### Comportamiento diario")
    if not temporal:
        st.caption("No hay datos suficientes en el periodo seleccionado.")
    else:
        por_dia = temporal["por_dia"]
        fig_dia = go.Figure(go.Bar(
            x=DIAS_ES,
            y=[por_dia.get(dia, 0) for dia in DIAS_ES],
            marker_color=_AZUL_OSC,
            hovertemplate="%{x}: %{y} preguntas<extra></extra>",
        ))
        fig_dia.update_layout(
            height=240,
            margin=dict(l=10, r=10, t=10, b=40),
            xaxis=dict(title="Día de la semana"),
            yaxis=dict(title="Preguntas", gridcolor=_GRID),
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig_dia, use_container_width=True)

        st.markdown("###### Mapa de calor por hora")
        heatmap = temporal["heatmap"]
        z = [[heatmap[dia].get(h, 0) for h in range(24)] for dia in DIAS_ES]
        fig_heatmap = go.Figure(go.Heatmap(
            z=z,
            x=[f"{h:02d}:00" for h in range(24)],
            y=DIAS_ES,
            colorscale=[[0, "#EBF5FB"], [1, _AZUL_OSC]],
            showscale=True,
            colorbar=dict(title="Preguntas", thickness=12, len=0.85),
            hovertemplate="%{y} a las %{x}: %{z} preguntas<extra></extra>",
        ))
        fig_heatmap.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=10, b=45),
            xaxis=dict(title="Hora del día", tickangle=-45),
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)

        with st.expander("▸ Detalle: patrones de horario (opcional)"):
            dur_str = formatear_duracion(temporal["duracion_promedio_min"])
            m1, m2 = st.columns(2)
            m1.metric("Duración promedio de sesión", dur_str)
            m2.metric(
                f"Uso en top-2 días ({', '.join(temporal['top2_dias'])})",
                f"{temporal['top2_dias_pct']}%",
                delta="Uso concentrado" if temporal["top2_dias_pct"] >= 40 else None,
                delta_color="off",
            )

    st.markdown("##### Qué necesita tu atención esta semana")

    if not alertas:
        st.info("No hay alertas para el periodo seleccionado.", icon="✅")
    else:
        cols = st.columns(len(alertas))
        for i, (col, alerta) in enumerate(zip(cols, alertas)):
            with col:
                with st.container(border=True):
                    st.markdown(f"{alerta['icono']} {alerta['texto']}")
                    if st.button("Ver más →", key=f"alerta_{i}"):
                        router.ir_a_vista(alerta["nivel_destino"], **(alerta["filtro"] or {}))

    if not temas_generados:
        st.caption(
            "🔍 Genera el análisis de temas en la pestaña **Temas** para ver también "
            "alertas de contenido (tema en alza, retrieval débil)."
        )
