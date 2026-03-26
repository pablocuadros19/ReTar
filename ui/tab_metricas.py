"""Pestaña de métricas mensuales — tasa de entrega, objetivo diario, movimientos."""

import streamlit as st
import pandas as pd
from ui.components import render_metric_card, render_divider, render_section_label, render_section_highlight
from services.metrics import calc_tasa_entrega, calc_gap_40, get_diagnostico, calcular_objetivo_diario
from services.stock_manager import cargar_stock, cargar_movimientos, registrar_entregas_manuales
from services.contact_history import cargar_historial


def render_tab_metricas():
    """Renderiza el módulo de métricas mensuales."""

    st.markdown("### 📈 Métricas mensuales")
    render_divider()

    stock = cargar_stock()

    if stock is None:
        st.info("Cargá un Excel en la pestaña de Carga para empezar a acumular métricas.")
        return

    metricas = stock.get("metricas_mes", {})
    stock_inicial = metricas.get("stock_inicial", 0)
    ingresos = metricas.get("ingresos", 0)
    entregadas = metricas.get("entregadas", 0)
    derivadas = metricas.get("derivadas", 0)
    depuradas = metricas.get("depuradas", 0)
    contactadas_entregadas = metricas.get("contactadas_entregadas", 0)

    universo = stock_inicial + ingresos
    if universo == 0:
        st.info("No hay datos suficientes para calcular métricas.")
        return

    # === Sección A: Resumen del mes ===
    _render_resumen_mes(stock_inicial, ingresos, entregadas, derivadas, depuradas)

    # === Sección B: Registrar entregas manuales ===
    _render_registro_manual()

    # === Sección C: Conversión por contacto ===
    _render_conversion(contactadas_entregadas)

    # === Sección D: Objetivo diario ===
    _render_objetivo_diario(stock_inicial, ingresos, entregadas, derivadas)

    # === Sección E: Movimientos diarios ===
    _render_movimientos()

    # === Ajuste completo (colapsado) ===
    _render_ajuste_manual(stock)


def _render_resumen_mes(stock_inicial, ingresos, entregadas, derivadas, depuradas):
    """Cards con resumen del mes y progreso."""
    render_section_label("Resumen del mes")

    tasa = calc_tasa_entrega(stock_inicial, ingresos, entregadas, derivadas)
    gap = calc_gap_40(stock_inicial, ingresos, entregadas, derivadas)

    c1, c2, c3, c4 = st.columns(4)
    render_metric_card(f"{gap['tasa_actual']}%", "Tasa actual", c1)
    render_metric_card(f"{gap['objetivo_pct']}%", "Objetivo", c2)
    render_metric_card(f"{gap['faltan']}", "Faltan entregas", c3)

    stock_actual = stock_inicial + ingresos - entregadas - derivadas - depuradas
    render_metric_card(f"{stock_actual}", "Stock actual", c4)

    # Desglose en segunda fila
    c5, c6, c7, c8 = st.columns(4)
    render_metric_card(f"{stock_inicial}", "Stock inicial", c5)
    render_metric_card(f"{ingresos}", "Ingresos", c6)
    render_metric_card(f"{entregadas}", "Entregadas", c7)
    render_metric_card(f"{derivadas + depuradas}", f"Derivadas ({derivadas}) + Depuradas ({depuradas})", c8)

    # Progress bar
    st.markdown("<br>", unsafe_allow_html=True)
    progress_val = min(tasa / 0.40, 1.0) if tasa > 0 else 0
    st.progress(progress_val)

    if gap["alcanzado"]:
        st.success(f"🎯 Objetivo alcanzado. Tasa: {gap['tasa_actual']}%")
    elif gap["tasa_actual"] >= 30:
        st.info(f"📈 Cerca del objetivo. Faltan {gap['faltan']} entregas/derivaciones.")
    elif gap["tasa_actual"] >= 20:
        st.warning(f"⚠️ Hay que intensificar. Faltan {gap['faltan']} entregas/derivaciones.")
    else:
        st.error(f"🚨 Lejos del objetivo. Faltan {gap['faltan']} entregas/derivaciones.")

    # Diagnóstico
    diagnostico = get_diagnostico(gap, depuradas)
    render_section_highlight(diagnostico)


def _render_registro_manual():
    """Permite corregir stock inicial y registrar entregas que no pasaron por el Excel."""
    from services.stock_manager import guardar_stock

    st.markdown("---")
    render_section_label("Ajuste manual")

    stock = cargar_stock()
    metricas = stock.get("metricas_mes", {}) if stock else {}

    # Stock inicial — corregir si el mes no arrancó con este Excel
    stock_ini_actual = metricas.get("stock_inicial", 0)
    nuevo_stock_ini = st.number_input(
        "Stock inicial del mes",
        min_value=0,
        value=stock_ini_actual,
        help="Corregí si el stock inicial real del mes es diferente al que cargó ReTar.",
        key="input_stock_inicial",
    )
    if nuevo_stock_ini != stock_ini_actual:
        if st.button("💾 Actualizar stock inicial", key="btn_stock_inicial"):
            metricas["stock_inicial"] = nuevo_stock_ini
            stock["metricas_mes"] = metricas
            guardar_stock(stock)
            st.success(f"Stock inicial actualizado a **{nuevo_stock_ini}**.")
            st.rerun()

    st.markdown("")

    # Ajustes manuales — sumar al acumulado sin tocar stock
    st.caption("¿Hubo movimientos que no pasaron por el Excel? Sumalos acá.")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        add_ing = st.number_input("+ Ingresos", min_value=0, value=0, key="add_ingresos")
    with c2:
        add_ent = st.number_input("+ Entregadas", min_value=0, value=0, key="add_entregadas")
    with c3:
        add_der = st.number_input("+ Derivadas", min_value=0, value=0, key="add_derivadas")
    with c4:
        add_dep = st.number_input("+ Depuradas", min_value=0, value=0, key="add_depuradas")

    if st.button("✅ Registrar ajuste", type="primary", key="btn_registro_manual"):
        total = add_ent + add_der + add_dep + add_ing
        if total > 0:
            registrar_entregas_manuales(add_ent, add_der, add_dep, ingresos=add_ing)
            partes = []
            if add_ing: partes.append(f"+{add_ing} ingresos")
            if add_ent: partes.append(f"+{add_ent} entregadas")
            if add_der: partes.append(f"+{add_der} derivadas")
            if add_dep: partes.append(f"+{add_dep} depuradas")
            st.success(", ".join(partes) + ".")
            st.rerun()
        else:
            st.warning("Ingresá al menos un valor.")


def _render_conversion(contactadas_entregadas):
    """Muestra tasa de conversión por contacto."""
    st.markdown("---")
    render_section_label("Conversión por contacto")

    historial = cargar_historial()
    total_contactados = len([d for d, v in historial.items() if v.get("contactos")])

    c1, c2, c3 = st.columns(3)
    render_metric_card(f"{total_contactados}", "Clientes contactados", c1)
    render_metric_card(f"{contactadas_entregadas}", "Retiraron tras contacto", c2)

    if total_contactados > 0:
        tasa_conv = round((contactadas_entregadas / total_contactados) * 100, 1)
        render_metric_card(f"{tasa_conv}%", "Tasa de conversión", c3)
    else:
        render_metric_card("—", "Tasa de conversión", c3)

    if contactadas_entregadas > 0:
        st.markdown(
            f"De **{total_contactados}** clientes contactados, **{contactadas_entregadas}** "
            f"retiraron su tarjeta. El contacto funciona."
        )


def _render_objetivo_diario(stock_inicial, ingresos, entregadas, derivadas):
    """Calcula y muestra el objetivo diario de entregas."""
    st.markdown("---")
    render_section_label("Objetivo diario")

    tasa_deseada = st.slider(
        "Tasa de entrega deseada",
        min_value=20, max_value=60, value=40, step=5,
        format="%d%%",
        key="tasa_deseada_slider",
    )

    objetivo = calcular_objetivo_diario(
        stock_inicial, ingresos, entregadas, derivadas,
        tasa_deseada=tasa_deseada / 100,
    )

    c1, c2, c3 = st.columns(3)
    render_metric_card(f"{objetivo['entregas_necesarias']}", "Entregas que faltan", c1)
    render_metric_card(f"{objetivo['dias_habiles_restantes']}", "Días hábiles restantes", c2)
    render_metric_card(f"{objetivo['objetivo_diario']}", "Entregas por día", c3)

    if objetivo["alcanzado"]:
        st.success(f"🎯 Ya alcanzaste el {tasa_deseada}%. Mantener el ritmo.")
    elif objetivo["objetivo_diario"] > 10:
        st.error(
            f"🚨 Necesitás **{objetivo['objetivo_diario']} entregas por día hábil** "
            f"para llegar al {tasa_deseada}%. Es un ritmo muy alto — "
            f"considerá ajustar el objetivo o intensificar el contacto."
        )
    elif objetivo["objetivo_diario"] > 5:
        st.warning(
            f"⚠️ Necesitás **{objetivo['objetivo_diario']} entregas por día hábil** "
            f"para llegar al {tasa_deseada}%. Ritmo exigente pero alcanzable."
        )
    else:
        st.info(
            f"📈 Necesitás **{objetivo['objetivo_diario']} entregas por día hábil** "
            f"para llegar al {tasa_deseada}%. Ritmo razonable."
        )


def _render_movimientos():
    """Muestra la tabla de movimientos diarios."""
    st.markdown("---")
    render_section_label("Registro de movimientos")

    movimientos = cargar_movimientos()

    if not movimientos:
        st.info("Los movimientos se registran con cada carga de Excel.")
        return

    df_mov = pd.DataFrame(movimientos)

    # Renombrar columnas
    rename = {
        "fecha": "Fecha",
        "ingresaron": "Ingresaron",
        "desaparecieron": "Salieron",
        "entregadas": "Entregadas",
        "depuradas": "Depuradas",
        "derivadas": "Derivadas",
        "stock_al_cierre": "Stock",
    }
    cols_mostrar = [c for c in rename.keys() if c in df_mov.columns]
    df_mostrar = df_mov[cols_mostrar].rename(columns=rename)

    # Más reciente primero
    df_mostrar = df_mostrar.iloc[::-1]

    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)


def _render_ajuste_manual(stock):
    """Permite ajustar manualmente las métricas si no coinciden."""
    st.markdown("---")
    with st.expander("🔧 Ajustar métricas manualmente"):
        st.caption("Usá esto solo si los números automáticos no coinciden con tu control.")

        metricas = stock.get("metricas_mes", {})
        col1, col2 = st.columns(2)

        with col1:
            adj_stock = st.number_input("Stock inicial", value=metricas.get("stock_inicial", 0),
                                        min_value=0, key="adj_stock")
            adj_ingresos = st.number_input("Ingresos", value=metricas.get("ingresos", 0),
                                           min_value=0, key="adj_ingresos")
            adj_depuradas = st.number_input("Depuradas", value=metricas.get("depuradas", 0),
                                            min_value=0, key="adj_depuradas")

        with col2:
            adj_entregadas = st.number_input("Entregadas", value=metricas.get("entregadas", 0),
                                              min_value=0, key="adj_entregadas")
            adj_derivadas = st.number_input("Derivadas", value=metricas.get("derivadas", 0),
                                             min_value=0, key="adj_derivadas")

        if st.button("💾 Guardar ajustes", key="guardar_ajustes"):
            from services.stock_manager import guardar_stock
            stock["metricas_mes"] = {
                "stock_inicial": adj_stock,
                "ingresos": adj_ingresos,
                "entregadas": adj_entregadas,
                "derivadas": adj_derivadas,
                "depuradas": adj_depuradas,
                "contactadas_entregadas": metricas.get("contactadas_entregadas", 0),
            }
            guardar_stock(stock)
            st.success("✅ Métricas ajustadas.")
            st.rerun()
