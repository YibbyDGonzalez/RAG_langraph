"""
Punto de entrada: autenticación y menú de navegación por rol.

El Estudiante solo ve la página del chatbot. El Docente ve además el
Reporte de Monitoreo. El menú de navegación (barra lateral con las páginas)
usa el comportamiento nativo de Streamlit. La flecha nativa para
plegar/desplegar la barra lateral se oculta a propósito: el navegador
guarda ese estado en localStorage, así que si un usuario la usaba para
colapsar el menú, quedaba colapsado en futuras sesiones.
"""
import sys
import os

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import yaml
import streamlit as st
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader

from report_generator.modules.roles import ROL_DOCENTE, rol_de_usuario


# ============================
# CONFIGURACION DE PAGINA
# ============================

st.set_page_config(
    page_title="Asistente MBE - Javeriana",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* Se oculta la flecha nativa de plegar/desplegar la barra lateral:
       su estado se guarda en el localStorage del navegador, por lo que
       si el usuario la usaba para ocultar el menu, quedaba oculto
       permanentemente en ese navegador, sin importar la sesion. */
    [data-testid="stSidebarCollapsedControl"] {
        visibility: hidden !important;
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================
# AUTENTICACION
# ============================

USERS_PATH = os.path.join(_project_root, "users.yaml")

with open(USERS_PATH) as f:
    config = yaml.load(f, Loader=SafeLoader)

if "authenticator" not in st.session_state:
    st.session_state["authenticator"] = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
        config.get("preauthorized", {"emails": [""]}),
    )
authenticator = st.session_state["authenticator"]

name, auth_status, username = authenticator.login("Iniciar sesion", "main")

if auth_status is False:
    st.error("Usuario o contrasena incorrectos.")
    st.stop()

if auth_status is None:
    logo_path = os.path.join(_project_root, "Javeriana.png")
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        st.markdown(
            "<h3 style='text-align:center;'>Asistente MBE</h3>"
            "<p style='text-align:center; color:gray;'>Facultad de Medicina - Javeriana</p>",
            unsafe_allow_html=True,
        )
    st.stop()


# ============================
# NAVEGACION SEGUN ROL
# ============================

rol_usuario = rol_de_usuario(username)
st.session_state["role"] = rol_usuario

paginas = [st.Page("pages/chat.py", title="Asistente MBE", icon="🔬", default=True)]
if rol_usuario == ROL_DOCENTE:
    paginas.append(st.Page("pages/reporte.py", title="Reporte", icon="📊"))

pg = st.navigation(paginas)
pg.run()
