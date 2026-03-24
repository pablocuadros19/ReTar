"""Pestaña de rescate — registros sin datos de contacto."""

import streamlit as st
import pandas as pd
from ui.components import render_divider, render_section_label, render_section_highlight, require_data
from services.campaign_export import export_to_csv, export_to_xlsx


def render_tab_rescate():
    """Renderiza la bandeja de rescate para registros sin contacto."""

    st.markdown("### 🔍 Rescate")
    render_divider()

    if not require_data():
        return

    df = st.session_state.df

    # Filtrar solo registros sin contacto
    df_rescate = df[df["_contactabilidad"] == "sin_contacto"].copy()

    if len(df_rescate) == 0:
        st.success("🎉 Todos los registros tienen al menos un canal de contacto. No hay nada que rescatar.")
        return

    render_section_highlight(
        f"<b>{len(df_rescate)}</b> registros sin teléfono ni mail. "
        "Podés buscar estos DNIs en otros sistemas internos para recuperar datos de contacto."
    )

    # --- Tabla de rescate ---
    render_section_label("Registros sin contacto")

    display_cols = {
        "_nombre": "Nombre",
        "_documento": "DNI",
        "_tipo_tarjeta": "Tipo tarjeta",
        "_dias_guarda": "Días guarda",
        "_urgencia_label": "Urgencia",
        "_estado_gestion": "Estado",
    }
    existing = {k: v for k, v in display_cols.items() if k in df_rescate.columns}

    # Búsqueda
    search = st.text_input("🔍 Buscar por nombre o DNI", key="rescate_search")
    if search.strip():
        search_lower = search.strip().lower()
        df_rescate = df_rescate[
            df_rescate["_nombre"].str.lower().str.contains(search_lower, na=False)
            | df_rescate["_documento"].str.lower().str.contains(search_lower, na=False)
        ]

    st.dataframe(
        df_rescate[list(existing.keys())].rename(columns=existing),
        use_container_width=True,
        hide_index=True,
        height=350,
    )

    # --- Acciones ---
    st.markdown("---")
    action_cols = st.columns(3)

    with action_cols[0]:
        # Marcar todos como pendiente de rescate manual
        if st.button("🔧 Marcar todos como rescate manual", use_container_width=True):
            for idx in df_rescate.index:
                st.session_state.estados[idx] = "rescate manual"
                st.session_state.df.at[idx, "_estado_gestion"] = "rescate manual"
            st.success(f"✅ {len(df_rescate)} registros marcados como rescate manual")
            st.rerun()

    with action_cols[1]:
        # Exportar listado para buscar manualmente
        rescue_export = df_rescate[list(existing.keys())].rename(columns=existing)
        csv_data = rescue_export.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ Exportar CSV para rescate",
            data=csv_data,
            file_name="rescate_retar.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with action_cols[2]:
        st.write(f"📊 {len(df_rescate)} registros sin contacto")

    # --- Info adicional ---
    st.markdown("<br>", unsafe_allow_html=True)
    render_section_highlight(
        "<b>Tip:</b> Exportá este listado, buscá los DNIs en los sistemas internos (ej. Bantotal, Banca Internet), "
        "y después podés agregar los datos de contacto recuperados manualmente."
    )
