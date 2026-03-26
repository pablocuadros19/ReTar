"""Tokens de diseño y CSS centralizado — Sistema NyPer."""

import streamlit as st

# Tokens de diseño
COLORS = {
    "primary": "#00A651",
    "primary_dark": "#00a34d",
    "secondary": "#00B8D4",
    "bg_primary": "#ffffff",
    "bg_secondary": "#f7f9fc",
    "bg_accent": "#f0f9f4",
    "text_primary": "#1a1a2e",
    "text_secondary": "#555555",
    "text_muted": "#666666",
    "text_very_muted": "#999999",
    "border_default": "#e0e5ec",
    "border_light": "#d0d5dd",
    "border_green": "#c8e6d5",
    "tag_bg": "#e8f5ee",
    "tag_text": "#00A651",
    "hover_bg": "#f0f9f4",
}


def inject_css():
    """Inyecta CSS global con estilo NyPer."""
    st.markdown("""
    <style>
    /* Fuente Montserrat */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Header con gradiente */
    .header-gradient {
        background: linear-gradient(90deg, #ffffff 0%, #00A651 25%, #00B8D4 100%);
        border-radius: 12px;
        padding: 2rem 2rem;
        margin-bottom: 1.5rem;
        color: white;
        text-shadow: 0 1px 3px rgba(0,0,0,.15);
        text-align: center;
    }
    .header-gradient h1 {
        font-weight: 900;
        font-size: 2.8rem;
        margin: 0;
        color: white !important;
    }
    .header-gradient p {
        font-weight: 400;
        font-size: 1rem;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }

    /* Cards */
    .nyper-card {
        background: #f7f9fc;
        border: 1px solid #e0e5ec;
        border-radius: 14px;
        padding: 1.2rem;
        transition: all 0.2s ease;
    }
    .nyper-card:hover {
        border-color: #00A651;
        box-shadow: 0 4px 20px rgba(0,132,61,.1);
    }

    /* Metric card */
    .metric-card {
        background: #f7f9fc;
        border: 1px solid #e0e5ec;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #00A651;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #666666;
        margin-top: 0.3rem;
    }

    /* Sección destacada */
    .section-highlight {
        background: #f0f9f4;
        border: 1px solid #c8e6d5;
        border-left: 4px solid #00A651;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin: 0.8rem 0;
    }

    /* Badge / Tag */
    .nyper-badge {
        background: #e8f5ee;
        color: #00A651;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        display: inline-block;
    }
    .nyper-badge.urgente {
        background: #fff3e0;
        color: #e65100;
    }
    .nyper-badge.prioridad {
        background: #fce4ec;
        color: #c62828;
    }
    .nyper-badge.sin-contacto {
        background: #f5f5f5;
        color: #999999;
    }

    /* Divider decorativo */
    .nyper-divider {
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, #00A651, #00B8D4);
        border-radius: 2px;
        margin: 0.8rem 0;
    }

    /* Section label */
    .section-label {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #999999;
        margin-bottom: 0.5rem;
    }

    /* Contacto card */
    .contacto-card {
        background: #ffffff;
        border: 2px solid #e0e5ec;
        border-radius: 14px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .contacto-card.activo {
        border-color: #00A651;
        box-shadow: 0 4px 20px rgba(0,132,61,.15);
    }

    /* Mensaje preview */
    .msg-preview {
        background: #f0f9f4;
        border: 1px solid #c8e6d5;
        border-radius: 12px;
        padding: 1rem;
        font-size: 0.85rem;
        line-height: 1.6;
        white-space: pre-wrap;
        color: #1a1a2e;
    }

    /* Progress bar custom */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #00A651, #00B8D4) !important;
    }

    /* Botones Streamlit override */
    .stButton > button {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        box-shadow: 0 4px 15px rgba(0,132,61,.25);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00A651, #00a34d);
        color: white;
        border: none;
    }

    /* Tabs Streamlit override */
    .stTabs [data-baseweb="tab-list"] {
        background: white;
        border-bottom: 2px solid #e0e5ec;
        gap: 0;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Montserrat', sans-serif !important;
        font-size: 0.9rem;
        font-weight: 600;
        color: #666666;
        padding: 0.75rem 1.2rem;
    }
    .stTabs [aria-selected="true"] {
        color: #00A651 !important;
        border-bottom: 3px solid #00A651;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #00A651;
    }

    /* Sidebar logo */
    .sidebar-logo {
        text-align: center;
        padding: 1rem 0;
    }
    .sidebar-logo img {
        max-width: 225px;
    }

    /* Loader perrito */
    @keyframes olfatear {
        0% { transform: translateX(-80px) scaleX(-1); }
        45% { transform: translateX(80px) scaleX(-1); }
        50% { transform: translateX(80px) scaleX(1); }
        95% { transform: translateX(-80px) scaleX(1); }
        100% { transform: translateX(-80px) scaleX(-1); }
    }
    .perrito-loader {
        text-align: center;
        padding: 2rem;
        overflow: hidden;
    }
    .perrito-loader img {
        width: 120px;
        animation: olfatear 3s ease-in-out infinite;
    }
    .perrito-loader p {
        color: #666666;
        font-size: 0.85rem;
        margin-top: 0.8rem;
    }

    /* Scrollable table */
    .dataframe-container {
        max-height: 500px;
        overflow-y: auto;
        border-radius: 10px;
        border: 1px solid #e0e5ec;
    }

    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* File uploader — estilo NyPer */
    [data-testid="stFileUploaderDropzone"] {
        border: 2px dashed #c8e6d5 !important;
        border-radius: 12px !important;
        background: #f0f9f4 !important;
        transition: all 0.2s ease;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #00A651 !important;
        background: #e8f5ee !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        font-size: 0 !important;
    }
    [data-testid="stFileUploaderDropzone"] button::after {
        content: "Buscar archivo";
        font-size: 0.875rem;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .header-gradient h1 { font-size: 1.5rem; }
        .metric-value { font-size: 1.3rem; }
        .nyper-card { padding: 0.8rem; }
    }
    </style>
    """, unsafe_allow_html=True)


def inject_uploader_translation():
    """Traduce el file uploader de Streamlit al español via JS en el parent frame."""
    import streamlit.components.v1 as components
    components.html("""
    <script>
    const doc = window.parent.document;
    function traducir() {
        doc.querySelectorAll('[data-testid="stFileUploaderDropzone"]').forEach(dz => {
            dz.querySelectorAll('span').forEach(s => {
                if (s.textContent.includes('Drag and drop')) {
                    s.textContent = 'Arrastrá y soltá tu Excel acá';
                }
            });
            dz.querySelectorAll('small').forEach(s => {
                if (s.textContent.includes('Limit')) {
                    s.textContent = 'Límite 200MB por archivo';
                }
            });
        });
    }
    const obs = new MutationObserver(traducir);
    obs.observe(doc.body, {childList: true, subtree: true});
    traducir();
    </script>
    """, height=0)
