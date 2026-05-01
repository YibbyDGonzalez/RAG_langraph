import streamlit as st
from app.core import load_resources, buscar_articulos, call_ollama
from rag_langgraph.app_langgraph import responder


# ============================
# 1. CARGA DE MODELOS Y DATOS
# ============================

@st.cache_resource
def _load_resources():
    return load_resources()


df, embeddings, index, encoder, ollama_client = _load_resources()


# ============================
# 3. INTERFAZ STREAMLIT
# ============================

st.set_page_config(page_title="Asistente educativo Javeriana", page_icon="🧪")

st.title("🔬 Asistente MBE • Facultad de medicina PUJ")

# --- Párrafo objetivo ---
with st.expander("ℹ️ ¿Qué es este asistente?", expanded=False):
    st.markdown(
        """
        Este asistente ha sido diseñado como una herramienta de apoyo académico para estudiantes
        de medicina que cursan la materia de Medicina Basada en la Evidencia. A través de un sistema
        de recuperación de información, permite consultar conceptos, metodologías y principios
        fundamentales de la MBE, facilitando la comprensión y aplicación de sus herramientas
        en el contexto clínico y académico.

        Este asistente se basa en literatura académica reconocida en Medicina Basada en la Evidencia, incluyendo:

        🔹Painless Evidence-Based Medicine — Antonio L. Dans, Leonila F. Dans, Maria Asuncion A. Silvestre
        🔹Users' Guides to the Medical Literature: A Manual for Evidence-Based Medicine — Gordon Guyatt, Drummond Rennie, Maureen O. Meade, Deborah J. Cook
        """
    )

st.divider()

# --- Preguntas sugeridas ---
st.subheader("Preguntas sugeridas:")
col1, col2, col3 = st.columns(3)

q1 = "¿Qué es la medicina basada en la evidencia y cuáles son sus pasos principales?"
q2 = "¿Cuál es la diferencia entre un estudio observacional y un ensayo clínico aleatorizado?"
q3 = "¿Qué significa el nivel de evidencia de un estudio y cómo se clasifica?"

if col1.button(q1):
    st.session_state["pregunta"] = q1

if col2.button(q2):
    st.session_state["pregunta"] = q2

if col3.button(q3):
    st.session_state["pregunta"] = q3

# --- Input de pregunta ---
pregunta = st.text_input(
    "Haz una pregunta sobre tratamientos, estudios, diagnósticos, etc:",
    value=st.session_state.get("pregunta", "")
)

if st.button("Consultar"):
    if pregunta.strip() == "":
        st.warning("Por favor ingresa una pregunta.")
    else:
        with st.spinner("Generando respuesta..."):
            respuesta = responder(pregunta)

        st.subheader("📌 Respuesta")
        st.write(respuesta)

# --- Créditos al pie ---
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.82em; padding: 10px 0'>
        <b>Autores:</b> Yibby Gonzalez · Juan Ruiz &nbsp;|&nbsp;
        <b>Profesores:</b> Juan Pablo Páramo · Fabián Gil <br>
        📧 Comentarios, mejoras o sugerencia a: <a href='mailto:gonzalez_yibby@javeriana.edu.co' style='color: gray;'>gonzalez_yibby@javeriana.edu.co</a>
    </div>
    """,
    unsafe_allow_html=True
)
