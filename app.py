"""ReTar — Gestión de campañas de retiro de tarjetas.

Streamlit app para gestionar contacto con clientes que tienen
tarjetas pendientes de retiro en sucursal bancaria.
"""

from pathlib import Path
import streamlit as st
from ui.theme import inject_css
from ui.components import render_header, render_sidebar_logo, render_footer

# Favicon desde archivo
_favicon = Path("assets/retarlogo.png")
_page_icon = str(_favicon) if _favicon.exists() else "💳"
from ui.tab_carga import render_tab_carga
from ui.tab_resumen import render_tab_resumen
from ui.tab_contacto import render_tab_contacto
from ui.tab_bandeja import render_tab_bandeja
from ui.tab_rescate import render_tab_rescate
from ui.tab_metricas import render_tab_metricas


# --- Configuración de página ---
st.set_page_config(
    page_title="ReTar — Gestión de Tarjetas",
    page_icon=_page_icon,
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS NyPer ---
inject_css()

# --- Inicializar session_state ---
defaults = {
    "df": None,
    "df_raw": None,
    "column_map": {},
    "operador": "",
    "sucursal": "",
    "cargo": "",
    "estados": {},
    "indice_contacto": 0,
    "_filename": "",
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Recuperar datos desde stock en disco si la sesión está vacía (nuevo browser, celu, F5)
if st.session_state.df is None:
    from services.stock_manager import cargar_stock, reconstruir_df_desde_stock
    if cargar_stock():
        df_rec, estados_rec = reconstruir_df_desde_stock()
        if df_rec is not None:
            st.session_state.df = df_rec
            st.session_state.estados = estados_rec
            st.session_state.indice_contacto = 0


# --- Sidebar: logo + config operador ---
render_sidebar_logo()

st.sidebar.markdown("---")
st.sidebar.markdown("#### 👤 Operador")

st.session_state.operador = st.sidebar.text_input(
    "Nombre",
    value=st.session_state.operador,
    placeholder="Ej: Pablo",
    key="input_operador",
)

st.session_state.sucursal = st.sidebar.text_input(
    "Sucursal",
    value=st.session_state.sucursal,
    placeholder="Ej: Villa Ballester",
    key="input_sucursal",
)

st.session_state.cargo = st.sidebar.text_input(
    "Cargo (opcional)",
    value=st.session_state.cargo,
    placeholder="Ej: Oficial de cuentas",
    key="input_cargo",
)

# Info del archivo cargado
if st.session_state.df is not None:
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 📄 Archivo cargado")
    st.sidebar.success(f"**{st.session_state._filename}**")
    st.sidebar.caption(f"{len(st.session_state.df)} registros")

    # Resumen rápido de estados
    estados = st.session_state.estados
    if estados:
        pendientes = sum(1 for v in estados.values() if v == "pendiente")
        gestionados = len(estados) - pendientes
        st.sidebar.metric("Gestionados", f"{gestionados}/{len(estados)}")


# --- Header principal ---
render_header()

# --- Tabs ---
tab_carga, tab_resumen, tab_contacto, tab_bandeja, tab_rescate, tab_metricas = st.tabs([
    "📂 Carga",
    "📊 Resumen",
    "📞 Contacto guiado",
    "📋 Bandeja",
    "🔍 Rescate",
    "📈 Métricas",
])

with tab_carga:
    render_tab_carga()

with tab_resumen:
    render_tab_resumen()

with tab_contacto:
    render_tab_contacto()

with tab_bandeja:
    render_tab_bandeja()

with tab_rescate:
    render_tab_rescate()

with tab_metricas:
    render_tab_metricas()

# --- Footer con firma ---
render_footer()
