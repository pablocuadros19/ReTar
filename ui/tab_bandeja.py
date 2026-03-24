"""Pestaña de bandeja — tabla filtrable con todos los registros."""

import streamlit as st
import pandas as pd
from ui.components import render_divider, render_section_label, require_data
from services.campaign_export import prepare_campaign_df, export_to_csv, export_to_xlsx


def render_tab_bandeja():
    """Renderiza la bandeja filtrable de registros."""

    st.markdown("### 📋 Bandeja")
    render_divider()

    if not require_data():
        return

    df = st.session_state.df
    column_map = st.session_state.get("column_map", {})
    operador = st.session_state.get("operador", "")
    sucursal = st.session_state.get("sucursal", "")

    # --- Filtros ---
    render_section_label("Filtros")
    fc1, fc2, fc3, fc4 = st.columns(4)

    with fc1:
        f_contact = st.multiselect(
            "Contactabilidad",
            options=["ambos", "solo_telefono", "solo_mail", "sin_contacto"],
            default=["ambos", "solo_telefono", "solo_mail", "sin_contacto"],
            format_func=lambda x: {
                "ambos": "📱✉️ Ambos",
                "solo_telefono": "📱 Teléfono",
                "solo_mail": "✉️ Mail",
                "sin_contacto": "❌ Sin contacto",
            }.get(x, x),
            key="bandeja_f_contact",
        )

    with fc2:
        tipos = df["_tipo_tarjeta"].unique().tolist()
        f_tipo = st.multiselect("Tipo tarjeta", options=tipos, default=tipos, key="bandeja_f_tipo")

    with fc3:
        f_urgencia = st.multiselect(
            "Urgencia",
            options=df["_urgencia_code"].unique().tolist(),
            default=df["_urgencia_code"].unique().tolist(),
            format_func=lambda x: {
                "informativo": "🟢 Informativo",
                "recordatorio": "🟡 Recordatorio",
                "urgente": "🟠 Urgente",
                "prioridad_alta": "🔴 Prioridad alta",
                "sin_fecha": "⚪ Sin fecha",
            }.get(x, x),
            key="bandeja_f_urgencia",
        )

    with fc4:
        # Rango de días de guarda
        dias_min = int(df["_dias_guarda"].min()) if df["_dias_guarda"].notna().any() else 0
        dias_max = int(df["_dias_guarda"].max()) if df["_dias_guarda"].notna().any() else 100
        if dias_min == dias_max:
            dias_max = dias_min + 1
        f_dias = st.slider("Días de guarda", dias_min, dias_max, (dias_min, dias_max), key="bandeja_f_dias")

    # Búsqueda por texto
    search = st.text_input("🔍 Buscar por nombre o DNI", key="bandeja_search")

    # Aplicar filtros
    mask = pd.Series(True, index=df.index)
    mask &= df["_contactabilidad"].isin(f_contact)
    mask &= df["_tipo_tarjeta"].isin(f_tipo)
    mask &= df["_urgencia_code"].isin(f_urgencia)

    if df["_dias_guarda"].notna().any():
        dias_mask = (df["_dias_guarda"].isna()) | (
            (df["_dias_guarda"] >= f_dias[0]) & (df["_dias_guarda"] <= f_dias[1])
        )
        mask &= dias_mask

    if search.strip():
        search_lower = search.strip().lower()
        mask &= (
            df["_nombre"].str.lower().str.contains(search_lower, na=False)
            | df["_documento"].str.lower().str.contains(search_lower, na=False)
        )

    df_filtered = df[mask]

    # --- Info de resultados ---
    st.markdown(f"**{len(df_filtered)}** registros encontrados de {len(df)} totales")

    # --- Tabla ---
    display_cols = {
        "_nombre": "Nombre",
        "_documento": "DNI",
        "_telefono_norm": "Teléfono",
        "_mail_norm": "Mail",
        "_tipo_tarjeta": "Tipo",
        "_dias_guarda": "Días",
        "_urgencia_label": "Urgencia",
        "_canal_sugerido": "Canal",
        "_estado_gestion": "Estado",
    }
    existing = {k: v for k, v in display_cols.items() if k in df_filtered.columns}

    st.dataframe(
        df_filtered[list(existing.keys())].rename(columns=existing),
        use_container_width=True,
        hide_index=True,
        height=400,
    )

    # --- Exportación ---
    st.markdown("---")
    render_section_label("Exportar campaña")

    exp_cols = st.columns(3)
    with exp_cols[0]:
        st.write(f"📦 {len(df_filtered)} registros para exportar")
    with exp_cols[1]:
        campaign_df = prepare_campaign_df(df_filtered, column_map, operador, sucursal)
        csv_data = export_to_csv(campaign_df)
        st.download_button(
            "⬇️ Descargar CSV",
            data=csv_data,
            file_name="campaña_retar.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with exp_cols[2]:
        xlsx_data = export_to_xlsx(campaign_df)
        st.download_button(
            "⬇️ Descargar Excel",
            data=xlsx_data,
            file_name="campaña_retar.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
