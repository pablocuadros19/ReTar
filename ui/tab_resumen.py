"""Pestaña de resumen — cards de métricas + distribuciones."""

import streamlit as st
from ui.components import render_metric_card, render_divider, render_section_label, require_data
from services.classifier import get_summary


def render_tab_resumen():
    """Renderiza la pestaña de resumen con cards y distribuciones."""

    st.markdown("### 📊 Resumen")
    render_divider()

    if not require_data():
        return

    df = st.session_state.df
    summary = get_summary(df)

    # --- Fila 1: métricas principales ---
    render_section_label("Indicadores generales")
    c1, c2, c3, c4 = st.columns(4)
    render_metric_card(summary["total"], "Total registros", c1)
    render_metric_card(summary["contactables"], "Contactables", c2)
    render_metric_card(summary["sin_contacto"], "Sin contacto", c3)
    promedio = summary["promedio_dias_guarda"] if summary["promedio_dias_guarda"] else "—"
    render_metric_card(f"{promedio}", "Promedio días guarda", c4)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Fila 2: canales ---
    render_section_label("Canales de contacto")
    c1, c2, c3, c4 = st.columns(4)
    render_metric_card(summary["con_telefono"], "Con teléfono", c1)
    render_metric_card(summary["con_mail"], "Con mail", c2)
    render_metric_card(summary["con_ambos"], "Con ambos", c3)
    render_metric_card(summary["criticos_30_dias"], "Críticos (+30 días)", c4)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Distribución por tipo de tarjeta ---
    col_left, col_right = st.columns(2)

    with col_left:
        render_section_label("Por tipo de tarjeta")
        if summary["por_tipo"]:
            for tipo, count in sorted(summary["por_tipo"].items(), key=lambda x: -x[1]):
                pct = round(count / summary["total"] * 100, 1)
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center;
                            padding:0.4rem 0.8rem; margin:0.2rem 0; background:#f7f9fc;
                            border-radius:8px; border:1px solid #e0e5ec;">
                    <span style="font-weight:600; font-size:0.85rem;">{tipo}</span>
                    <span style="color:#00A651; font-weight:700;">{count} <span style="color:#999; font-weight:400;">({pct}%)</span></span>
                </div>
                """, unsafe_allow_html=True)

    with col_right:
        render_section_label("Por urgencia")
        if summary["por_urgencia"]:
            for urgencia, count in sorted(summary["por_urgencia"].items(), key=lambda x: -x[1]):
                pct = round(count / summary["total"] * 100, 1)
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center;
                            padding:0.4rem 0.8rem; margin:0.2rem 0; background:#f7f9fc;
                            border-radius:8px; border:1px solid #e0e5ec;">
                    <span style="font-weight:600; font-size:0.85rem;">{urgencia}</span>
                    <span style="color:#00A651; font-weight:700;">{count} <span style="color:#999; font-weight:400;">({pct}%)</span></span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Distribución por contactabilidad ---
    render_section_label("Por contactabilidad")
    contact_labels = {
        "ambos": "📱✉️ Teléfono + Mail",
        "solo_telefono": "📱 Solo teléfono",
        "solo_mail": "✉️ Solo mail",
        "sin_contacto": "❌ Sin contacto",
    }
    if summary["por_contactabilidad"]:
        cols = st.columns(len(summary["por_contactabilidad"]))
        for i, (key, count) in enumerate(summary["por_contactabilidad"].items()):
            label = contact_labels.get(key, key)
            pct = round(count / summary["total"] * 100, 1)
            render_metric_card(f"{count}", f"{label} ({pct}%)", cols[i])

    # --- Barra de progreso contactabilidad ---
    st.markdown("<br>", unsafe_allow_html=True)
    render_section_label("Cobertura de contacto")
    if summary["total"] > 0:
        coverage = summary["contactables"] / summary["total"]
        st.progress(coverage)
        st.caption(f"{summary['contactables']} de {summary['total']} registros son contactables ({round(coverage*100,1)}%)")
