"""
Página del chatbot del Asistente MBE.

Disponible para ambos roles (Docente y Estudiante). La autenticación y la
construcción del menú de navegación (qué páginas ve cada rol) ocurren en
app/app.py, el punto de entrada que llama a st.navigation() antes de
delegar en esta página.
"""
import sys
import os
import uuid
import time

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root in sys.path:
    sys.path.remove(_project_root)
sys.path.insert(0, _project_root)

_app_dir = os.path.join(_project_root, "app")
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

import streamlit as st

from core import load_resources
from rag_langgraph.app_langgraph import responder_stream_logged
from logger import init_db, log_consulta, load_user_sessions
from report_generator.modules.roles import ROL_DOCENTE


# ============================
# SESION AUTENTICADA (ya validada en app.py)
# ============================

username = st.session_state.get("username", "")
nombre_usuario = st.session_state.get("name", username)

authenticator = st.session_state["authenticator"]


# ============================
# INICIALIZAR LOGS DB
# ============================

init_db()


# ============================
# CARGA DE RECURSOS
# ============================

@st.cache_resource
def _load_resources():
    return load_resources()

df, embeddings, index, encoder, ollama_client = _load_resources()


# ============================
# ESTADO DE SESION
# ============================

def crear_chat():
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {"title": "Nueva conversacion", "messages": []}
    st.session_state.active_chat = chat_id

if "chats" not in st.session_state:
    historial = load_user_sessions(username)
    if historial:
        st.session_state.chats = historial
        st.session_state.active_chat = list(historial.keys())[-1]
    else:
        st.session_state.chats = {}
        crear_chat()

if "active_chat" not in st.session_state or \
   st.session_state.active_chat not in st.session_state.chats:
    crear_chat()


# ============================
# SIDEBAR
# ============================

with st.sidebar:
    logo_path = os.path.join(_project_root, "Javeriana.png")
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("## Javeriana")

    st.markdown(f"👤 **{nombre_usuario}**")
    authenticator.logout("Cerrar sesion", "sidebar")

    st.markdown("---")

    if st.button("＋  Nueva conversacion", use_container_width=True, type="primary"):
        crear_chat()
        st.rerun()

    st.markdown("---")
    st.caption("CONVERSACIONES")

    for chat_id, chat_data in reversed(list(st.session_state.chats.items())):
        es_activo = chat_id == st.session_state.active_chat
        icono = "💬" if es_activo else "🗨️"
        if st.button(
            f"{icono}  {chat_data['title']}",
            key=f"btn_{chat_id}",
            use_container_width=True,
        ):
            st.session_state.active_chat = chat_id
            st.rerun()

    if st.session_state.get("role") == ROL_DOCENTE:
        st.markdown("---")
        db_path = os.path.join(_project_root, "data", "logs", "mbe_logs.db")
        if os.path.exists(db_path):
            with open(db_path, "rb") as f:
                st.download_button(
                    label="⬇️ Descargar logs (.db)",
                    data=f,
                    file_name="mbe_logs.db",
                    mime="application/octet-stream",
                    use_container_width=True,
                )

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.75em; color:gray; line-height:1.6;'>"
        "<b>Autores</b><br>Yibby Gonzalez - Juan Ruiz<br><br>"
        "<b>Profesores</b><br>Juan Pablo Pajaro - Fabian Gil"
        "</div>",
        unsafe_allow_html=True,
    )


# ============================
# TOGGLE MENU LATERAL (mostrar / ocultar)
# ============================

if "menu_visible" not in st.session_state:
    st.session_state.menu_visible = True

if not st.session_state.menu_visible:
    st.markdown(
        "<style>section[data-testid='stSidebar'] {display: none;}</style>",
        unsafe_allow_html=True,
    )

texto_toggle = "☰  Mostrar menu" if not st.session_state.menu_visible else "‹  Ocultar menu"
if st.button(texto_toggle, key="toggle_menu_btn"):
    st.session_state.menu_visible = not st.session_state.menu_visible
    st.rerun()


# ============================
# AREA PRINCIPAL
# ============================

chat_activo = st.session_state.chats[st.session_state.active_chat]
mensajes    = chat_activo["messages"]

st.markdown(
    "<h2 style='text-align:center; margin-bottom:0;'>🔬 Asistente MBE</h2>"
    "<p style='text-align:center; color:gray; margin-top:4px;'>"
    "Facultad de Medicina - Pontificia Universidad Javeriana</p>",
    unsafe_allow_html=True,
)
st.divider()

# Pantalla de bienvenida
if not mensajes:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; color:#555; font-size:1.05rem;'>"
        "Hola 👋 Soy tu asistente de Medicina Basada en la Evidencia.<br>"
        "Puedes hacerme preguntas o elegir una de las sugerencias:</p>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    sugerencias = [
        "Que es la medicina basada en la evidencia y cuales son sus pasos principales?",
        "Cual es la diferencia entre un estudio observacional y un ensayo clinico aleatorizado?",
        "Que significa el nivel de evidencia de un estudio y como se clasifica?",
    ]
    for col, sug in zip(st.columns(3), sugerencias):
        with col:
            if st.button(sug, use_container_width=True, key=f"sug_{sug[:20]}"):
                st.session_state["pending_question"] = sug
                st.rerun()

# Historial de mensajes
for msg in mensajes:
    avatar = "🧑" if msg["role"] == "user" else "🔬"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Input
pregunta = st.chat_input("Escribe tu pregunta sobre MBE, tratamientos, estudios...")

if "pending_question" in st.session_state:
    pregunta = st.session_state.pop("pending_question")


# ============================
# PROCESAR PREGUNTA + LOGGING
# ============================

if pregunta:
    t_total_start = time.time()

    if not mensajes:
        titulo = pregunta[:45] + "..." if len(pregunta) > 45 else pregunta
        st.session_state.chats[st.session_state.active_chat]["title"] = titulo

    mensajes.append({"role": "user", "content": pregunta})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(pregunta)

    # Primer yield del stream es el dict de metadata
    stream = responder_stream_logged(
        pregunta,
        df=df,
        index=index,
        encoder=encoder,
        ollama_client=ollama_client,
    )
    meta = next(stream)

    # Stream manual con cursor de escritura en tiempo real
    with st.chat_message("assistant", avatar="🔬"):
        placeholder = st.empty()
        respuesta_completa = ""
        for token in stream:
            respuesta_completa += token
            placeholder.markdown(respuesta_completa + "▌")
        placeholder.markdown(respuesta_completa)

    # Latencias finales
    lat_llm   = time.time() - meta["llm_start"]
    lat_total = time.time() - t_total_start

    # Guardar en SQLite
    log_consulta(
        usuario            = username,
        session_id         = st.session_state.active_chat,
        pregunta           = pregunta,
        chunks             = meta["chunks"],
        scores             = meta["scores"],
        respuesta          = respuesta_completa,
        latencia_embedding = meta["lat_embedding"],
        latencia_retrieval = meta["lat_retrieval"],
        latencia_llm       = lat_llm,
        latencia_total     = lat_total,
    )

    mensajes.append({"role": "assistant", "content": respuesta_completa})
    st.rerun()
