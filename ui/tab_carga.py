"""Pestaña de carga de archivo — subida, mapeo de columnas, reconciliación diaria."""

import streamlit as st
from datetime import date
from services.file_loader import load_file, detect_columns, validate_data, COLUMN_PATTERNS
from services.normalizer import normalize_dataframe
from services.classifier import classify_dataframe
from services.stock_manager import (
    cargar_stock, crear_stock_inicial, reconciliar,
    aplicar_reconciliacion, restaurar_estados, detectar_nuevo_mes, resetear_mes,
    reconstruir_df_desde_stock,
)
from services.contact_history import cargar_historial
from services.contact_sequence import resumen_pendientes_hoy
from services.metrics import calc_gap_40
from ui.components import render_perrito_loader, render_section_highlight, render_divider, render_metric_card
from ui.theme import inject_uploader_translation


def render_tab_carga():
    """Renderiza la pestaña de carga de archivo."""

    st.markdown("### 📂 Carga de archivo")
    render_divider()

    # Dashboard "Tu día de hoy"
    if st.session_state.get("df") is not None:
        _render_dashboard_hoy()

    # Detectar nuevo mes
    stock_existente = cargar_stock()
    if stock_existente and detectar_nuevo_mes(stock_existente):
        _render_nuevo_mes(stock_existente)

    st.markdown(
        "Subí el Excel o CSV exportado desde TAR. "
        "ReTar detecta las columnas automáticamente — podés ajustar el mapeo si hace falta."
    )

    uploaded = st.file_uploader(
        "Elegí un archivo",
        type=["xlsx", "xls", "csv"],
        key="file_uploader",
    )
    inject_uploader_translation()

    # Recuperar datos del stock si se perdió session_state (F5 / recarga)
    if st.session_state.get("df") is None and stock_existente:
        _recuperar_desde_stock()

    if uploaded is not None:
        _process_upload(uploaded)

    elif st.session_state.get("df") is not None:
        st.success(f"✅ **{len(st.session_state.df)} tarjetas** en gestión.")

    # Mostrar estado del stock si no hay nada cargado
    if stock_existente and st.session_state.get("df") is None:
        _render_stock_info(stock_existente)


def _recuperar_desde_stock():
    """Reconstruye session_state desde el stock en disco (tras F5 / recarga)."""
    df, estados = reconstruir_df_desde_stock()
    if df is not None:
        st.session_state.df = df
        st.session_state.estados = estados
        st.session_state.indice_contacto = 0


def _render_dashboard_hoy():
    """Panel 'Tu día de hoy' con pendientes y métricas rápidas."""
    df = st.session_state.df
    stock = cargar_stock()
    if stock is None:
        return

    historial = cargar_historial()
    resumen = resumen_pendientes_hoy(df, historial)
    metricas = stock.get("metricas_mes", {})

    stock_inicial = metricas.get("stock_inicial", 0)
    ingresos = metricas.get("ingresos", 0)
    entregadas = metricas.get("entregadas", 0)
    derivadas = metricas.get("derivadas", 0)
    depuradas = metricas.get("depuradas", 0)

    gap = calc_gap_40(stock_inicial, ingresos, entregadas, derivadas)
    stock_actual = len(stock.get("tarjetas", {}))
    total_pendientes = resumen["total_mail"] + resumen["total_wa"]

    # Panel destacado
    st.markdown(f"""
    <div style="background:#f0f9f4; border:1px solid #c8e6d5; border-left:4px solid #00A651;
                border-radius:12px; padding:1rem 1.2rem; margin-bottom:1rem;">
        <div style="font-weight:700; color:#1a1a2e; font-size:1rem; margin-bottom:0.5rem;">
            📋 Tu día de hoy
        </div>
        <div style="font-size:0.85rem; color:#555;">
            {"<b>" + str(total_pendientes) + " contactos pendientes</b> — " +
             str(resumen["total_mail"]) + " mails + " +
             str(resumen["total_wa"]) + " WhatsApps"
             if total_pendientes > 0
             else "No hay contactos pendientes para hoy."}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Métricas rápidas
    c1, c2, c3, c4 = st.columns(4)
    render_metric_card(f"{stock_actual}", "Stock actual", c1)
    render_metric_card(f"{gap['tasa_actual']}%", "Tasa entrega", c2)
    render_metric_card(f"{gap['faltan']}", "Faltan entregas", c3)
    render_metric_card(f"{total_pendientes}", "Contactos hoy", c4)

    if total_pendientes > 0:
        st.caption("Andá a la pestaña **Contacto guiado** para gestionar los pendientes del día.")

    st.markdown("---")


def _render_nuevo_mes(stock):
    """Muestra aviso de nuevo mes y opción de resetear."""
    st.warning("📅 **Nuevo mes detectado.** Las métricas mensuales necesitan resetearse.")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Resetear métricas del mes", type="primary"):
            stock = resetear_mes(stock)
            st.success("✅ Métricas reseteadas. Stock inicial = stock actual.")
            st.rerun()
    with col2:
        st.caption(f"Stock actual: {len(stock.get('tarjetas', {}))} tarjetas")


def _render_stock_info(stock):
    """Muestra info del stock guardado cuando no hay Excel cargado."""
    fecha = stock.get("fecha_ultima_carga", "")
    total = len(stock.get("tarjetas", {}))
    metricas = stock.get("metricas_mes", {})

    st.info(
        f"📦 Stock guardado del **{fecha}**: {total} tarjetas en sucursal. "
        f"Este mes: {metricas.get('entregadas', 0)} entregadas, "
        f"{metricas.get('ingresos', 0)} ingresos."
    )


def _process_upload(uploaded):
    """Procesa el archivo subido."""
    # Si ya se procesó este archivo, no reprocesar
    if st.session_state.get("_filename") == uploaded.name and st.session_state.get("df") is not None:
        st.success(f"✅ **{len(st.session_state.df)} tarjetas** procesadas.")
        _show_preview()
        return

    # Cargar archivo
    try:
        df_raw = load_file(uploaded)
    except ValueError as e:
        st.error(f"❌ {e}")
        return

    st.session_state.df_raw = df_raw
    st.session_state._filename = uploaded.name

    # Detección automática y procesamiento directo
    auto_map = detect_columns(df_raw)
    _run_processing(df_raw, auto_map)

    # Mapeo colapsado (por si alguna vez falla la detección)
    with st.expander("🔧 Ajustar mapeo de columnas", expanded=False):
        column_map = _render_column_mapping(df_raw, auto_map)
        if st.button("🔄 Reprocesar con mapeo manual", use_container_width=True):
            _run_processing(df_raw, column_map)


def _render_column_mapping(df_raw, auto_map):
    """Renderiza la UI de mapeo de columnas y devuelve el mapeo final."""
    available_cols = ["(no mapear)"] + list(df_raw.columns)
    column_map = {}

    col1, col2 = st.columns(2)
    items = list(COLUMN_PATTERNS.keys())

    for i, internal_name in enumerate(items):
        target_col = col1 if i % 2 == 0 else col2
        labels = {
            "nombre": "👤 Nombre del cliente",
            "documento": "🪪 DNI / Documento",
            "telefono": "📱 Teléfono",
            "mail": "✉️ Email",
            "tipo_tarjeta": "💳 Tipo de tarjeta",
            "fecha_recepcion": "📅 Fecha de recepción",
            "numero_tarjeta": "🔢 Número de tarjeta",
            "estado": "📋 Estado",
        }
        label = labels.get(internal_name, internal_name)
        default_val = auto_map.get(internal_name, "(no mapear)")
        default_idx = available_cols.index(default_val) if default_val in available_cols else 0

        with target_col:
            selected = st.selectbox(
                label,
                options=available_cols,
                index=default_idx,
                key=f"colmap_{internal_name}",
            )
            if selected != "(no mapear)":
                column_map[internal_name] = selected

    st.session_state.column_map = column_map
    return column_map


def _run_processing(df_raw, column_map):
    """Ejecuta normalización, clasificación y reconciliación."""
    with st.spinner(""):
        render_perrito_loader("Procesando tarjetas...")

        # Normalizar y clasificar
        df = normalize_dataframe(df_raw, column_map)
        df = classify_dataframe(df)
        df["_estado_gestion"] = "pendiente"

    # Guardar en session_state
    st.session_state.df = df
    st.session_state.column_map = column_map

    # Reconciliar con stock anterior
    stock = cargar_stock()

    if stock is None:
        # Primera carga
        stock = crear_stock_inicial(df)
        st.session_state.estados = {i: "pendiente" for i in df.index}
        st.session_state.indice_contacto = 0
        st.success(f"✅ **{len(df)} tarjetas** procesadas. Stock inicial creado.")
        _show_preview()
    else:
        # Reconciliación
        resultado = reconciliar(df, stock)
        st.session_state._reconciliacion = resultado
        st.session_state._stock_pre = stock

        # Restaurar estados de gestión
        estados = restaurar_estados(df, stock)
        st.session_state.estados = estados
        for idx, estado in estados.items():
            df.at[idx, "_estado_gestion"] = estado
        st.session_state.df = df
        st.session_state.indice_contacto = 0

        # Mostrar resultado de reconciliación
        _render_reconciliacion(resultado, stock, df)


def _render_reconciliacion(resultado, stock, df):
    """Muestra el resultado de la reconciliación y permite ajustar."""
    nuevas = len(resultado["nuevas"])
    desaparecidas = len(resultado["desaparecidas"])
    contactadas = len(resultado["desaparecidas_contactadas"])
    actualizadas = resultado["actualizadas"]

    # Resumen
    st.markdown(f"""
    <div style="background:#f0f9f4; border:1px solid #c8e6d5; border-left:4px solid #00A651;
                border-radius:12px; padding:1rem 1.2rem; margin:1rem 0;">
        <div style="font-weight:700; color:#1a1a2e; margin-bottom:0.5rem;">
            📊 Reconciliación completada
        </div>
        <div style="display:flex; gap:2rem; font-size:0.9rem; color:#555;">
            <span>🆕 <b>{nuevas}</b> nuevas</span>
            <span>📤 <b>{desaparecidas}</b> salieron</span>
            <span>🔄 <b>{actualizadas}</b> actualizadas</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if desaparecidas > 0:
        if contactadas > 0:
            st.markdown(
                f"De las {desaparecidas} que salieron, **{contactadas} habían sido contactadas** "
                f"(posible conversión)."
            )

        # Por defecto todas son entregadas
        st.markdown(
            f"Se asumen las **{desaparecidas} como entregadas**. "
            f"Si hubo depuraciones o derivaciones, indicalo abajo."
        )

        # Form opcional para corregir (colapsado)
        with st.expander("¿Hubo depuraciones o derivaciones?", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                dep = st.number_input("Depuradas", min_value=0, max_value=desaparecidas,
                                      value=0, key="reconcil_dep")
            with col2:
                der = st.number_input("Derivadas", min_value=0,
                                      max_value=max(0, desaparecidas - dep),
                                      value=0, key="reconcil_der")

            if dep + der > desaparecidas:
                st.error("Depuradas + derivadas no puede superar las tarjetas que salieron.")

        # Usar los valores del expander (0 por defecto si no se tocó)
        dep_val = st.session_state.get("reconcil_dep", 0)
        der_val = st.session_state.get("reconcil_der", 0)

        if st.button("✅ Confirmar y actualizar", type="primary", use_container_width=True):
            stock_nuevo = aplicar_reconciliacion(
                stock, df, resultado, depuradas=dep_val, derivadas=der_val
            )
            ent = max(0, desaparecidas - dep_val - der_val)
            st.success(
                f"Stock actualizado: +{nuevas} ingresos, "
                f"+{ent} entregadas, +{dep_val} depuradas, +{der_val} derivadas."
            )
            st.rerun()
    else:
        # Sin desaparecidas, aplicar directo
        stock_nuevo = aplicar_reconciliacion(stock, df, resultado)
        if nuevas > 0:
            st.success(f"Stock actualizado: +{nuevas} tarjetas nuevas ingresaron.")
        else:
            st.success("Stock actualizado. Sin cambios en la composición.")

    _show_preview()


def _show_preview():
    """Muestra preview de los datos procesados."""
    df = st.session_state.df
    if df is None:
        return

    with st.expander("👀 Preview de datos procesados", expanded=False):
        preview_cols = ["_nombre", "_documento", "_telefono_norm", "_mail_norm",
                       "_tipo_tarjeta", "_dias_guarda", "_contactabilidad",
                       "_urgencia_label", "_canal_sugerido", "_estado_gestion"]
        existing = [c for c in preview_cols if c in df.columns]

        rename = {
            "_nombre": "Nombre",
            "_documento": "DNI",
            "_telefono_norm": "Teléfono",
            "_mail_norm": "Mail",
            "_tipo_tarjeta": "Tipo",
            "_dias_guarda": "Días",
            "_contactabilidad": "Contacto",
            "_urgencia_label": "Urgencia",
            "_canal_sugerido": "Canal",
            "_estado_gestion": "Estado",
        }

        st.dataframe(
            df[existing].rename(columns=rename).head(20),
            use_container_width=True,
            hide_index=True,
        )
        if len(df) > 20:
            st.caption(f"Mostrando 20 de {len(df)} registros.")
