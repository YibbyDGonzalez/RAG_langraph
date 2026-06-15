"""
Página de reporte de uso del Asistente MBE.
Secciones 1 y 2 se calculan automáticamente al cambiar el filtro de fechas.
La sección 3 (embeddings + clustering + Groq) solo se ejecuta al hacer clic.
"""
import sys
import os
import sqlite3
from datetime import date

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
import plotly.graph_objects as go
import yaml
from yaml.loader import SafeLoader

from report_generator.modules.data_loader import load_data
from report_generator.modules.usage_stats import compute_usage_stats
from report_generator.modules.temporal_analysis import compute_temporal_stats
from report_generator.modules.topic_analysis import compute_topics

# ── Constantes visuales ────────────────────────────────────────────────────────
DIAS_ES   = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
_AZUL_OSC = "#1B4F72"
_AZUL_MED = "#2E86AB"
_VERDE    = "#17A589"
_GRID     = "#eef2f7"

DB_PATH    = os.getenv("LOGS_DB_PATH", os.path.join(_project_root, "data", "logs", "mbe_logs.db"))
USERS_PATH = os.path.join(_project_root, "users.yaml")

# ── Configuración de página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Reporte MBE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Autenticación ──────────────────────────────────────────────────────────────
if not st.session_state.get("authentication_status"):
    st.error("Debes iniciar sesión primero.")
    st.markdown("← Usa el menú lateral para volver al **Asistente MBE** e iniciar sesión.")
    st.stop()

username = st.session_state.get("username", "")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    logo_path = os.path.join(_project_root, "Javeriana.png")
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)

    nombre_usuario = st.session_state.get("name", username)
    st.markdown(f"👤 **{nombre_usuario}**")

    with open(USERS_PATH) as f:
        _cfg = yaml.load(f, Loader=SafeLoader)
    _auth = stauth.Authenticate(
        _cfg["credentials"],
        _cfg["cookie"]["name"],
        _cfg["cookie"]["key"],
        _cfg["cookie"]["expiry_days"],
        _cfg.get("preauthorized", {"emails": [""]}),
    )
    _auth.logout("Cerrar sesión", "sidebar")

    st.markdown("---")
    st.markdown("### 📅 Período de análisis")

    # Detectar rango disponible en la DB
    try:
        _conn = sqlite3.connect(DB_PATH)
        _row = pd.read_sql_query(
            "SELECT MIN(timestamp) as mn, MAX(timestamp) as mx FROM consultas", _conn
        ).iloc[0]
        _conn.close()
        _min_ts = pd.to_datetime(_row["mn"]).date()
        _max_ts = pd.to_datetime(_row["mx"]).date()
    except Exception:
        _min_ts = date(2025, 1, 1)
        _max_ts = date.today()

    desde = st.date_input("Desde", value=_min_ts, min_value=_min_ts, max_value=_max_ts)
    hasta = st.date_input("Hasta", value=_max_ts, min_value=_min_ts, max_value=_max_ts)

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.75em; color:gray; line-height:1.6;'>"
        "<b>Autores</b><br>Yibby Gonzalez - Juan Ruiz<br><br>"
        "<b>Profesores</b><br>Juan Pablo Paramo - Fabian Gil"
        "</div>",
        unsafe_allow_html=True,
    )

# ── Validar rango ──────────────────────────────────────────────────────────────
if desde > hasta:
    st.error("La fecha 'Desde' no puede ser posterior a 'Hasta'.")
    st.stop()

desde_str = desde.strftime("%Y-%m-%d")
hasta_str = hasta.strftime("%Y-%m-%d")

# ── Cargar datos ───────────────────────────────────────────────────────────────
if not os.path.exists(DB_PATH):
    st.error(f"No se encontró la base de datos: `{DB_PATH}`")
    st.stop()

df = load_data(DB_PATH, desde_str, hasta_str)

# ── Título ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<h2 style='text-align:center; margin-bottom:0;'>📊 Reporte de Uso — Asistente MBE</h2>"
    f"<p style='text-align:center; color:gray; margin-top:4px;'>Período: {desde_str} → {hasta_str}</p>",
    unsafe_allow_html=True,
)
st.divider()

if df.empty:
    st.warning("No hay datos registrados para el período seleccionado.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — Estadísticas de uso
# ══════════════════════════════════════════════════════════════════════════════
uso = compute_usage_stats(df)

st.subheader("1. Estadísticas de uso")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Preguntas totales",         uso["n_preguntas"])
c2.metric("Usuarios únicos",           uso["n_usuarios"])
c3.metric("Sesiones",                  uso["n_sesiones"])
c4.metric("Preguntas / sesión (prom)", uso["promedio_preguntas_por_sesion"])

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — Análisis temporal
# ══════════════════════════════════════════════════════════════════════════════
temporal = compute_temporal_stats(df)

st.markdown("---")
st.subheader("2. Análisis temporal")

# Duración promedio formateada
dur = temporal["duracion_promedio_min"]
if dur < 1:
    dur_str = "< 1 minuto"
elif dur < 60:
    dur_str = f"{dur:.0f} min"
else:
    dur_str = f"{int(dur // 60)}h {int(dur % 60)}min"

m1, m2 = st.columns(2)
m1.metric("Duración promedio de sesión", dur_str)
m2.metric(
    f"Uso en top-2 días ({', '.join(temporal['top2_dias'])})",
    f"{temporal['top2_dias_pct']}%",
    delta="Uso concentrado" if temporal["top2_dias_pct"] >= 40 else None,
    delta_color="off",
)

# Heatmap día × hora
hm = temporal["heatmap"]
fig_hm = go.Figure(go.Heatmap(
    z=[[hm[dia].get(h, 0) for h in range(24)] for dia in DIAS_ES],
    x=[f"{h:02d}:00" for h in range(24)],
    y=DIAS_ES,
    colorscale=[[0, "#EBF5FB"], [1, _AZUL_OSC]],
    showscale=True,
    colorbar=dict(title="Preguntas", thickness=12),
    hovertemplate="%{y} a las %{x}: %{z} preguntas<extra></extra>",
))
fig_hm.update_layout(
    title="Actividad por día y hora",
    height=300,
    margin=dict(l=10, r=10, t=40, b=45),
    plot_bgcolor="white",
    paper_bgcolor="white",
    xaxis=dict(title="Hora del día", tickangle=-45),
)
st.plotly_chart(fig_hm, use_container_width=True)

col_h, col_d = st.columns(2)

# Distribución por hora
ph = temporal["por_hora"]
fig_hora = go.Figure(go.Bar(
    x=[f"{h:02d}:00" for h in range(24)],
    y=[ph.get(h, 0) for h in range(24)],
    marker_color=_AZUL_MED,
    hovertemplate="%{x}: %{y} preguntas<extra></extra>",
))
fig_hora.update_layout(
    title="Distribución por hora",
    height=280,
    margin=dict(l=10, r=10, t=40, b=50),
    xaxis=dict(title="Hora", tickangle=-45),
    yaxis=dict(title="Preguntas", gridcolor=_GRID),
    plot_bgcolor="white",
    paper_bgcolor="white",
)
col_h.plotly_chart(fig_hora, use_container_width=True)

# Distribución por día de semana
pd_ = temporal["por_dia"]
fig_dia = go.Figure(go.Bar(
    x=DIAS_ES,
    y=[pd_.get(dia, 0) for dia in DIAS_ES],
    marker_color=_AZUL_OSC,
    hovertemplate="%{x}: %{y} preguntas<extra></extra>",
))
fig_dia.update_layout(
    title="Distribución por día de semana",
    height=280,
    margin=dict(l=10, r=10, t=40, b=40),
    xaxis=dict(title="Día"),
    yaxis=dict(title="Preguntas", gridcolor=_GRID),
    plot_bgcolor="white",
    paper_bgcolor="white",
)
col_d.plotly_chart(fig_dia, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — Análisis de temas (bajo demanda)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("3. Análisis de temas")

st.info(
    "Este análisis agrupa las preguntas por significado usando embeddings semánticos, "
    "clustering automático y un LLM (Groq). Puede tardar 1-3 minutos. "
    "Solo se ejecuta al presionar el botón.",
    icon="ℹ️",
)

groq_key = os.environ.get("GROQ_API_KEY")

if not groq_key:
    st.warning(
        "Variable de entorno `GROQ_API_KEY` no encontrada. "
        "El análisis de temas no está disponible.",
        icon="⚠️",
    )
else:
    n_preguntas = len(df)

    # Limpiar resultado cacheado si el período cambió
    if st.session_state.get("temas_rango") != (desde_str, hasta_str):
        st.session_state.pop("temas_resultado", None)

    if n_preguntas < 5:
        st.warning(f"Se necesitan al menos 5 preguntas para el análisis (período actual: {n_preguntas}).")
    else:
        if st.button(
            f"🔍 Generar análisis de temas  ({n_preguntas} preguntas)",
            type="primary",
        ):
            with st.spinner("Ejecutando embeddings → UMAP → clustering → Groq..."):
                try:
                    temas = compute_topics(list(df["pregunta"]), groq_key)
                    st.session_state["temas_resultado"] = temas
                    st.session_state["temas_rango"] = (desde_str, hasta_str)
                except Exception as e:
                    st.error(f"Error durante el análisis: {e}")

        # Mostrar resultados si existen en session_state
        if "temas_resultado" in st.session_state:
            temas = st.session_state["temas_resultado"]

            if not temas:
                st.info("No se encontraron grupos temáticos con los datos del período seleccionado.")
            else:
                st.success(f"{len(temas)} grupos temáticos identificados.")

                # Gráfico de barras horizontal
                nombres = [t["nombre"] for t in reversed(temas)]
                conteos = [t["n_preguntas"] for t in reversed(temas)]
                fig_temas = go.Figure(go.Bar(
                    x=conteos,
                    y=nombres,
                    orientation="h",
                    marker_color=_VERDE,
                    text=[f"  {c}" for c in conteos],
                    textposition="outside",
                    hovertemplate="%{y}: %{x} preguntas<extra></extra>",
                ))
                fig_temas.update_layout(
                    height=max(250, len(temas) * 52),
                    margin=dict(l=10, r=70, t=10, b=20),
                    xaxis_title="Número de preguntas",
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                )
                st.plotly_chart(fig_temas, use_container_width=True)

                # Detalle por tema con ejemplos de preguntas
                st.markdown("#### Preguntas de ejemplo por tema")
                for tema in temas:
                    with st.expander(
                        f"**{tema['nombre']}** — {tema['n_preguntas']} preguntas ({tema['pct']}%)"
                    ):
                        for ej in tema["ejemplos"]:
                            st.markdown(f"- {ej}")
