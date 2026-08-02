"""
Página de reporte docente del Asistente MBE.

Navegación en 4 niveles de zoom (overview-first, details-on-demand):
  Nivel 1 Pulso, Nivel 2 Temas, Nivel 3 Estudiantes — pestañas agregadas.
  Nivel 4 Estudiante individual — NO es pestaña, solo se llega por click
  desde una fila de Nivel 3 (o desde una alerta de Nivel 1).

El análisis de temas (embeddings + clustering + Groq) sigue siendo bajo
demanda (botón en la pestaña Temas): puede tardar 1-3 minutos y por eso
Nivel 1 no depende de él para responder rápido.
"""
import sys
import os
import sqlite3
from datetime import date

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# No basta con "insertar si no está": PYTHONPATH=/app ya lo agrega a sys.path,
# pero Streamlit inserta antes /app/app (carpeta de app/app.py). Como ahí existe
# un archivo app.py, 'app' se resuelve como ese módulo suelto y no como paquete.
# Hay que forzar _project_root a la posición 0 siempre.
if _project_root in sys.path:
    sys.path.remove(_project_root)
sys.path.insert(0, _project_root)

import pandas as pd
import streamlit as st

from app.report_views import router, nivel1_pulso, nivel2_temas, nivel3_estudiantes, nivel4_individual
from report_generator.modules.alerts import detectar_tema_en_alza, generar_alertas
from report_generator.modules.data_loader import load_data_con_periodo_anterior, load_data_historico
from report_generator.modules.deltas import kpis_con_delta, sparkline_semanal
from report_generator.modules.retrieval_quality import temas_con_retrieval_debil
from report_generator.modules.roles import ROL_DOCENTE, ROL_ESTUDIANTE, rol_de_usuario
from report_generator.modules.roster import cargar_roster, nunca_usado as calcular_nunca_usado, silenciosos as calcular_silenciosos
from report_generator.modules.temporal_analysis import compute_temporal_stats
from report_generator.modules.topic_analysis import evolucion_semanal_por_tema

DB_PATH = os.getenv("LOGS_DB_PATH", os.path.join(_project_root, "data", "logs", "mbe_logs.db"))

# La configuración de página (st.set_page_config) y el CSS que oculta el
# header nativo de Streamlit ya se aplicaron una sola vez en app.py, que
# corre siempre antes de esta página vía st.navigation().

# ── Autenticación ──────────────────────────────────────────────────────────────
if not st.session_state.get("authentication_status"):
    st.error("Debes iniciar sesión primero.")
    st.markdown("← Usa el menú lateral para volver al **Asistente MBE** e iniciar sesión.")
    st.stop()

username = st.session_state.get("username", "")
nombre_usuario = st.session_state.get("name", username)

# ── Autorización: el Reporte de Monitoreo es exclusivo del rol Docente ────────
if rol_de_usuario(username) != ROL_DOCENTE:
    st.error("No tienes permisos para acceder al Reporte de Monitoreo. Esta sección es exclusiva para Docentes.")
    st.markdown("← Usa el menú lateral para volver al **Asistente MBE**.")
    st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    logo_path = os.path.join(_project_root, "Javeriana.png")
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)

    st.markdown(f"👤 **{nombre_usuario}**")

    st.session_state["authenticator"].logout("Cerrar sesión", "sidebar")

    st.markdown("---")
    st.markdown("### 📅 Período de análisis")

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

    st.markdown("### 👥 Quién pregunta")
    rol_filtro = st.radio(
        "Quién pregunta",
        options=["Todos", "Solo Docentes", "Solo Estudiantes"],
        index=0,
        key="filtro_rol_preguntas",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.75em; color:gray; line-height:1.6;'>"
        "<b>Autores</b><br>Yibby Gonzalez - Juan Ruiz<br><br>"
        "<b>Profesores</b><br>Juan Pablo Pajaro - Fabian Gil"
        "</div>",
        unsafe_allow_html=True,
    )

# ── Validar rango ──────────────────────────────────────────────────────────────
if desde > hasta:
    st.error("La fecha 'Desde' no puede ser posterior a 'Hasta'.")
    st.stop()

desde_str = desde.strftime("%Y-%m-%d")
hasta_str = hasta.strftime("%Y-%m-%d")

if not os.path.exists(DB_PATH):
    st.error(f"No se encontró la base de datos: `{DB_PATH}`")
    st.stop()

# ── Título y mensaje transversal obligatorio ───────────────────────────────────
st.markdown(
    "<h2 style='text-align:center; margin-bottom:0;'>📊 Reporte de Uso — Asistente MBE</h2>"
    f"<p style='text-align:center; color:gray; margin-top:4px;'>Período: {desde_str} → {hasta_str}</p>",
    unsafe_allow_html=True,
)
st.info(
    "Datos agregados por defecto. La vista individual está disponible para tutoría docente.",
    icon="ℹ️",
)

# ── Carga de datos (una sola lectura por vista de rango) ───────────────────────
df_actual, df_anterior = load_data_con_periodo_anterior(DB_PATH, desde_str, hasta_str)
df_historico = load_data_historico(DB_PATH)


def _filtrar_por_rol(df: pd.DataFrame, rol_filtro: str) -> pd.DataFrame:
    """Filtra las preguntas según el rol de quien las hizo (Docente/Estudiante)."""
    if rol_filtro == "Todos" or df.empty:
        return df
    rol_objetivo = ROL_DOCENTE if rol_filtro == "Solo Docentes" else ROL_ESTUDIANTE
    mascara = df["usuario"].astype(str).map(rol_de_usuario) == rol_objetivo
    return df[mascara].reset_index(drop=True)


df_actual = _filtrar_por_rol(df_actual, rol_filtro)
df_anterior = _filtrar_por_rol(df_anterior, rol_filtro)
df_historico = _filtrar_por_rol(df_historico, rol_filtro)

roster = cargar_roster()
groq_key = os.environ.get("GROQ_API_KEY")

nunca_usado_list = calcular_nunca_usado(df_historico, roster)
silenciosos_list = calcular_silenciosos(df_historico, roster)

temas_detallado = None
if st.session_state.get("temas_rango") == (desde_str, hasta_str):
    temas_detallado = st.session_state.get("temas_detallado")
mapeo_temas = temas_detallado["mapeo_pregunta_tema"] if temas_detallado else {}

# ── Navegación (Nivel 4 no es pestaña: solo aparece si hay estudiante seleccionado) ──
estudiante_sel = router.estudiante_seleccionado()

if estudiante_sel:
    nivel4_individual.render(DB_PATH, estudiante_sel, roster.get(estudiante_sel, estudiante_sel), mapeo_temas)
else:
    vista = router.vista_actual()
    opciones = {"pulso": "🩺 General", "temas": "🗂️ Temas", "estudiantes": "🧑‍🎓 Estudiantes"}
    cols_nav = st.columns(3)
    for col, (clave, etiqueta) in zip(cols_nav, opciones.items()):
        with col:
            tipo = "primary" if clave == vista else "secondary"
            if st.button(etiqueta, key=f"nav_{clave}", type=tipo, use_container_width=True):
                if clave != vista:
                    router.ir_a_vista(clave)
    st.divider()

    if vista == "pulso":
        kpis_delta = kpis_con_delta(df_actual, df_anterior)
        sparkline_data = sparkline_semanal(df_historico, hasta, semanas=4)

        tema_en_alza = None
        temas_debiles = []
        if temas_detallado and temas_detallado["temas"]:
            evolucion = evolucion_semanal_por_tema(df_actual, mapeo_temas)
            tema_en_alza = detectar_tema_en_alza(evolucion)
            temas_debiles = temas_con_retrieval_debil(df_actual, mapeo_temas)

        temporal_actual = compute_temporal_stats(df_actual) if not df_actual.empty else None
        concentracion = None
        if temporal_actual and temporal_actual["top2_dias_pct"] >= 40:
            concentracion = {"pct": temporal_actual["top2_dias_pct"], "dias": temporal_actual["top2_dias"]}

        alertas = generar_alertas(tema_en_alza, temas_debiles, nunca_usado_list, silenciosos_list, concentracion)
        nivel1_pulso.render(
            kpis_delta, sparkline_data, alertas,
            temas_generados=bool(temas_detallado),
            total_estudiantes=len(roster),
            temporal=temporal_actual,
        )

    elif vista == "temas":
        nivel2_temas.render(df_actual, groq_key, desde_str, hasta_str)

    elif vista == "estudiantes":
        nivel3_estudiantes.render(df_actual, roster, mapeo_temas, nunca_usado_list, silenciosos_list)
