"""Componentes reutilizables — cards, badges, loader perrito, copy buttons."""

import base64
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path


def render_header():
    """Renderiza el header con gradiente NyPer."""
    st.markdown("""
    <div class="header-gradient">
        <h1>ReTar</h1>
        <p>Gestión de campañas de retiro de tarjetas</p>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(value, label, col=None):
    """Renderiza una card de métrica."""
    html = f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """
    target = col if col else st
    target.markdown(html, unsafe_allow_html=True)


def render_badge(text, badge_type="default"):
    """Renderiza un badge/tag estilo píldora."""
    extra_class = ""
    if badge_type == "urgente":
        extra_class = " urgente"
    elif badge_type == "prioridad":
        extra_class = " prioridad"
    elif badge_type == "sin-contacto":
        extra_class = " sin-contacto"

    return f'<span class="nyper-badge{extra_class}">{text}</span>'


def render_section_highlight(content):
    """Renderiza una sección destacada con borde verde."""
    st.markdown(f'<div class="section-highlight">{content}</div>', unsafe_allow_html=True)


def render_divider():
    """Renderiza un divider decorativo con gradiente."""
    st.markdown('<div class="nyper-divider"></div>', unsafe_allow_html=True)


def render_section_label(text):
    """Renderiza un label de sección."""
    st.markdown(f'<div class="section-label">{text}</div>', unsafe_allow_html=True)


def render_perrito_loader(message="Olfateando datos..."):
    """Renderiza el loader del perrito con animación."""
    perrito_path = Path("assets/perrito_bp.png")

    if perrito_path.exists():
        img_bytes = perrito_path.read_bytes()
        img_b64 = base64.b64encode(img_bytes).decode()
        img_tag = f'<img src="data:image/png;base64,{img_b64}" alt="Cargando...">'
    else:
        # Fallback si no existe la imagen
        img_tag = '<div style="font-size:3rem;">🐕</div>'

    st.markdown(f"""
    <div class="perrito-loader">
        {img_tag}
        <p>{message}</p>
    </div>
    """, unsafe_allow_html=True)


def render_copy_button(text, label="📋 Copiar", key=None):
    """Renderiza un botón que copia texto al portapapeles."""
    escaped = text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    btn_id = key or f"copy_{hash(text) % 100000}"

    components.html(f"""
    <button id="{btn_id}" onclick="
        navigator.clipboard.writeText(`{escaped}`).then(() => {{
            this.innerHTML = '✅ Copiado';
            setTimeout(() => this.innerHTML = '{label}', 2000);
        }}).catch(() => {{
            const ta = document.createElement('textarea');
            ta.value = `{escaped}`;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            this.innerHTML = '✅ Copiado';
            setTimeout(() => this.innerHTML = '{label}', 2000);
        }})
    " style="
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.5rem 1.2rem;
        border-radius: 8px;
        border: 2px solid #00A651;
        background: white;
        color: #00A651;
        cursor: pointer;
        transition: all 0.2s ease;
    " onmouseover="this.style.background='#f0f9f4'"
      onmouseout="this.style.background='white'"
    >{label}</button>
    """, height=50)


def render_msg_preview(message, label=""):
    """Renderiza un preview de mensaje con estilo."""
    if label:
        st.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="msg-preview">{message}</div>', unsafe_allow_html=True)


def render_sidebar_logo():
    """Renderiza el logo ReTar en el sidebar."""
    logo_path = Path("assets/retar.png")
    if logo_path.exists():
        img_bytes = logo_path.read_bytes()
        img_b64 = base64.b64encode(img_bytes).decode()
        st.sidebar.markdown(f"""
        <div class="sidebar-logo">
            <img src="data:image/png;base64,{img_b64}" alt="ReTar">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown("""
        <div style="text-align:center; padding:1rem 0;">
            <span style="font-size:1.5rem; font-weight:900; color:#00A651;">ReTar</span>
        </div>
        """, unsafe_allow_html=True)


def render_footer():
    """Renderiza el footer con la firma de Pablo."""
    firma_path = Path("assets/firma_pablo.png")

    if firma_path.exists():
        img_bytes = firma_path.read_bytes()
        img_b64 = base64.b64encode(img_bytes).decode()
        firma_tag = f'<img src="data:image/png;base64,{img_b64}" alt="@Pablocuadros19" style="max-width:180px; opacity:0.85;">'
    else:
        firma_tag = '<span style="font-style:italic; color:#999;">@Pablocuadros19</span>'

    st.markdown(f"""
    <div style="text-align:center; padding:2rem 0 1rem; margin-top:3rem;
                border-top:1px solid #e0e5ec;">
        {firma_tag}
        <p style="font-size:0.7rem; color:#999; margin-top:0.5rem;">
            ReTar — Banco Provincia
        </p>
    </div>
    """, unsafe_allow_html=True)


def require_data():
    """Muestra mensaje si no hay datos cargados. Devuelve True si hay datos."""
    if st.session_state.get("df") is None:
        st.info("📂 Primero cargá un archivo en la pestaña **Carga**.")
        return False
    return True
