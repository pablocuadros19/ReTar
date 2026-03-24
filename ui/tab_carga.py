"""Pestaña de carga de archivo — subida, mapeo de columnas, preview."""

import streamlit as st
from services.file_loader import load_file, detect_columns, validate_data, COLUMN_PATTERNS
from services.normalizer import normalize_dataframe
from services.classifier import classify_dataframe
from ui.components import render_perrito_loader, render_section_highlight, render_divider


def render_tab_carga():
    """Renderiza la pestaña de carga de archivo."""

    st.markdown("### 📂 Carga de archivo")
    render_divider()

    st.markdown(
        "Subí el Excel o CSV exportado desde TAR. "
        "ReTar detecta las columnas automáticamente — podés ajustar el mapeo si hace falta."
    )

    uploaded = st.file_uploader(
        "Elegí un archivo",
        type=["xlsx", "xls", "csv"],
        key="file_uploader",
    )

    if uploaded is not None:
        _process_upload(uploaded)

    elif st.session_state.get("df") is not None:
        st.success(f"✅ Archivo cargado: **{st.session_state.get('_filename', '')}** — "
                   f"{len(st.session_state.df)} registros procesados.")


def _process_upload(uploaded):
    """Procesa el archivo subido."""
    # Si ya se procesó este archivo, no reprocesar
    if st.session_state.get("_filename") == uploaded.name and st.session_state.get("df") is not None:
        st.success(f"✅ **{uploaded.name}** — {len(st.session_state.df)} registros procesados.")
        _show_preview()
        return

    # Cargar archivo
    try:
        with st.spinner(""):
            render_perrito_loader("Leyendo archivo...")
            df_raw = load_file(uploaded)
    except ValueError as e:
        st.error(f"❌ {e}")
        return

    st.session_state.df_raw = df_raw
    st.session_state._filename = uploaded.name

    st.success(f"📄 **{uploaded.name}** — {len(df_raw)} registros, {len(df_raw.columns)} columnas detectadas.")

    # Detección automática de columnas
    auto_map = detect_columns(df_raw)

    st.markdown("#### Mapeo de columnas")
    render_section_highlight(
        "Revisá que cada campo interno apunte a la columna correcta del archivo. "
        "Si alguno no se detectó, seleccionalo manualmente."
    )

    # UI de mapeo
    column_map = _render_column_mapping(df_raw, auto_map)

    # Validar
    warnings = validate_data(df_raw, column_map)
    if warnings:
        with st.expander(f"⚠️ {len(warnings)} advertencia(s)", expanded=False):
            for w in warnings:
                st.warning(w)

    # Botón de procesar
    st.markdown("---")
    if st.button("🚀 Procesar archivo", type="primary", use_container_width=True):
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

    # Guardar mapeo en session_state
    st.session_state.column_map = column_map
    return column_map


def _run_processing(df_raw, column_map):
    """Ejecuta normalización y clasificación."""
    with st.spinner(""):
        render_perrito_loader("Procesando datos...")

        # Normalizar
        df = normalize_dataframe(df_raw, column_map)

        # Clasificar
        df = classify_dataframe(df)

        # Inicializar estados de gestión
        df["_estado_gestion"] = "pendiente"

        # Guardar en session_state
        st.session_state.df = df
        st.session_state.column_map = column_map
        st.session_state.estados = {i: "pendiente" for i in df.index}
        st.session_state.indice_contacto = 0

    st.success(f"✅ **{len(df)} registros** procesados correctamente.")
    _show_preview()


def _show_preview():
    """Muestra preview de los datos procesados."""
    df = st.session_state.df
    if df is None:
        return

    with st.expander("👀 Preview de datos procesados", expanded=False):
        # Mostrar columnas internas relevantes
        preview_cols = ["_nombre", "_documento", "_telefono_norm", "_mail_norm",
                       "_tipo_tarjeta", "_dias_guarda", "_contactabilidad",
                       "_urgencia_label", "_canal_sugerido"]
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
        }

        st.dataframe(
            df[existing].rename(columns=rename).head(20),
            use_container_width=True,
            hide_index=True,
        )
        if len(df) > 20:
            st.caption(f"Mostrando 20 de {len(df)} registros.")
