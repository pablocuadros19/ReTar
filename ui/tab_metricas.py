"""Pestaña de métricas mensuales — tasa de entrega y proyecciones."""

import streamlit as st
from ui.components import render_metric_card, render_divider, render_section_label, render_section_highlight
from services.metrics import calc_tasa_entrega, calc_gap_40, get_diagnostico


def render_tab_metricas():
    """Renderiza el módulo de métricas mensuales."""

    st.markdown("### 📈 Métricas mensuales")
    render_divider()

    st.markdown(
        "Ingresá los datos mensuales de tu sucursal para calcular la tasa de entrega "
        "y ver cuánto falta para el objetivo del 40%."
    )

    # --- Inputs manuales ---
    render_section_label("Datos del mes")

    col1, col2 = st.columns(2)
    with col1:
        stock_inicial = st.number_input("Stock inicial (tarjetas al inicio del mes)",
                                        min_value=0, value=0, step=1, key="met_stock")
        ingresos = st.number_input("Ingresos del mes (tarjetas nuevas recibidas)",
                                   min_value=0, value=0, step=1, key="met_ingresos")
        depuradas = st.number_input("Depuradas (descartadas/vencidas)",
                                    min_value=0, value=0, step=1, key="met_depuradas")

    with col2:
        entregadas = st.number_input("Entregadas (retiradas por el cliente)",
                                     min_value=0, value=0, step=1, key="met_entregadas")
        derivadas = st.number_input("Derivadas (enviadas a otra sucursal)",
                                    min_value=0, value=0, step=1, key="met_derivadas")

    # Validar que haya datos
    denominador = stock_inicial + ingresos
    if denominador == 0:
        st.info("Completá al menos stock inicial o ingresos para ver los cálculos.")
        return

    # --- Cálculos ---
    st.markdown("---")
    render_section_label("Resultados")

    tasa = calc_tasa_entrega(stock_inicial, ingresos, entregadas, derivadas)
    gap = calc_gap_40(stock_inicial, ingresos, entregadas, derivadas)

    # Métricas principales
    c1, c2, c3, c4 = st.columns(4)
    render_metric_card(f"{gap['tasa_actual']}%", "Tasa actual", c1)
    render_metric_card(f"{gap['objetivo_pct']}%", "Objetivo", c2)
    render_metric_card(f"{gap['faltan']}", "Faltan entregas", c3)

    # Stock actual estimado
    stock_actual = stock_inicial + ingresos - entregadas - derivadas - depuradas
    render_metric_card(f"{stock_actual}", "Stock actual estimado", c4)

    # --- Barra de progreso hacia el 40% ---
    st.markdown("<br>", unsafe_allow_html=True)
    render_section_label("Progreso hacia el objetivo")

    progress_val = min(tasa / 0.40, 1.0) if tasa > 0 else 0
    st.progress(progress_val)

    # Colores según nivel
    if gap["alcanzado"]:
        st.success(f"🎯 ¡Objetivo alcanzado! Tasa: {gap['tasa_actual']}%")
    elif gap["tasa_actual"] >= 30:
        st.info(f"📈 Cerca del objetivo. Faltan {gap['faltan']} entregas/derivaciones.")
    elif gap["tasa_actual"] >= 20:
        st.warning(f"⚠️ Hay que intensificar. Faltan {gap['faltan']} entregas/derivaciones.")
    else:
        st.error(f"🚨 Lejos del objetivo. Faltan {gap['faltan']} entregas/derivaciones.")

    # --- Diagnóstico ---
    st.markdown("<br>", unsafe_allow_html=True)
    render_section_label("Diagnóstico")
    diagnostico = get_diagnostico(gap, depuradas)
    render_section_highlight(diagnostico)

    # --- Desglose ---
    st.markdown("<br>", unsafe_allow_html=True)
    render_section_label("Desglose")

    desglose_data = {
        "Concepto": [
            "Stock inicial",
            "Ingresos del mes",
            "Total universo (denominador)",
            "Entregadas",
            "Derivadas",
            "Total positivas (numerador)",
            "Depuradas",
            "Stock actual estimado",
        ],
        "Cantidad": [
            stock_inicial,
            ingresos,
            denominador,
            entregadas,
            derivadas,
            entregadas + derivadas,
            depuradas,
            stock_actual,
        ],
    }

    st.table(desglose_data)

    # --- Comparación con promedio ---
    st.markdown("<br>", unsafe_allow_html=True)
    render_section_label("Comparación")

    comp_cols = st.columns(3)
    promedio_banco = 35.0
    diff = round(gap["tasa_actual"] - promedio_banco, 1)

    render_metric_card(f"{promedio_banco}%", "Promedio del banco", comp_cols[0])
    render_metric_card(f"{gap['tasa_actual']}%", "Tu sucursal", comp_cols[1])

    diff_text = f"+{diff}%" if diff >= 0 else f"{diff}%"
    diff_color = "#00A651" if diff >= 0 else "#c62828"
    comp_cols[2].markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color:{diff_color};">{diff_text}</div>
        <div class="metric-label">Diferencia</div>
    </div>
    """, unsafe_allow_html=True)
