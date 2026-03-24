"""Pestaña de contacto guiado — experiencia caso por caso tipo maratón."""

import streamlit as st
import pandas as pd
from ui.components import (render_divider, render_section_label, render_badge,
                           render_msg_preview, render_copy_button, require_data)
from services.message_engine import get_message_wa, get_message_mail, get_wa_url, get_mailto_url


def render_tab_contacto():
    """Renderiza la pestaña de contacto guiado."""

    st.markdown("### 📞 Contacto guiado")
    render_divider()

    if not require_data():
        return

    df = st.session_state.df
    operador = st.session_state.get("operador", "")
    sucursal = st.session_state.get("sucursal", "")

    # --- Filtros de trabajo ---
    render_section_label("Filtros de trabajo")
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        filtro_estado = st.selectbox(
            "Estado",
            ["pendiente", "todos", "enviado WhatsApp", "enviado Mail", "enviado ambos"],
            key="contacto_filtro_estado",
        )
    with col_f2:
        filtro_canal = st.selectbox(
            "Canal disponible",
            ["todos", "solo_telefono", "solo_mail", "ambos"],
            key="contacto_filtro_canal",
        )
    with col_f3:
        filtro_urgencia = st.selectbox(
            "Urgencia",
            ["todas", "prioridad_alta", "urgente", "recordatorio", "informativo"],
            key="contacto_filtro_urgencia",
        )

    # Aplicar filtros
    df_work = _apply_filters(df, filtro_estado, filtro_canal, filtro_urgencia)

    if len(df_work) == 0:
        st.info("No hay registros que coincidan con los filtros seleccionados.")
        return

    # --- Navegación ---
    idx = st.session_state.get("indice_contacto", 0)
    if idx >= len(df_work):
        idx = 0
        st.session_state.indice_contacto = 0

    total = len(df_work)

    # Progress
    completados = sum(1 for i in df_work.index
                      if st.session_state.get("estados", {}).get(i, "pendiente") != "pendiente")
    st.progress(completados / total if total > 0 else 0)
    st.caption(f"Caso **{idx + 1}** de **{total}** — {completados} gestionados")

    # --- Card del caso actual ---
    row = df_work.iloc[idx]
    real_idx = df_work.index[idx]

    _render_contact_card(row, real_idx, operador, sucursal)

    # --- Navegación inferior ---
    st.markdown("---")
    nav_cols = st.columns([1, 1, 1, 2])

    with nav_cols[0]:
        if st.button("⬅️ Anterior", use_container_width=True, disabled=(idx == 0)):
            st.session_state.indice_contacto = idx - 1
            st.rerun()

    with nav_cols[1]:
        if st.button("➡️ Siguiente", use_container_width=True, disabled=(idx >= total - 1)):
            st.session_state.indice_contacto = idx + 1
            st.rerun()

    with nav_cols[2]:
        if st.button("⏭️ Saltar a pendiente", use_container_width=True):
            next_pending = _find_next_pending(df_work, idx)
            if next_pending is not None:
                st.session_state.indice_contacto = next_pending
                st.rerun()
            else:
                st.toast("No hay más pendientes")

    with nav_cols[3]:
        go_to = st.number_input("Ir a caso #", min_value=1, max_value=total,
                                value=idx + 1, key="goto_case")
        if go_to != idx + 1:
            st.session_state.indice_contacto = go_to - 1
            st.rerun()


def _apply_filters(df, estado, canal, urgencia):
    """Aplica filtros al DataFrame para la sesión de contacto."""
    mask = pd.Series(True, index=df.index)

    # Filtro por estado de gestión
    if estado != "todos":
        estados = st.session_state.get("estados", {})
        mask &= df.index.map(lambda i: estados.get(i, "pendiente") == estado)

    # Filtro por canal
    if canal != "todos":
        mask &= df["_contactabilidad"] == canal

    # Filtro por urgencia
    if urgencia != "todas":
        mask &= df["_urgencia_code"] == urgencia

    # Excluir sin contacto (no tiene sentido en contacto guiado)
    mask &= df["_contactabilidad"] != "sin_contacto"

    return df[mask].reset_index(drop=False)


def _render_contact_card(row, real_idx, operador, sucursal):
    """Renderiza la card de un caso de contacto."""
    estado_actual = st.session_state.get("estados", {}).get(real_idx, "pendiente")

    # Badge de urgencia
    urgencia_label = row.get("_urgencia_label", "")
    urgencia_code = row.get("_urgencia_code", "")
    badge_type = "default"
    if urgencia_code == "urgente":
        badge_type = "urgente"
    elif urgencia_code == "prioridad_alta":
        badge_type = "prioridad"

    # Header del caso
    st.markdown(f"""
    <div class="contacto-card activo">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
            <div>
                <span style="font-size:1.1rem; font-weight:700; color:#1a1a2e;">{row.get("_nombre", "Sin nombre")}</span>
                <br><span style="font-size:0.8rem; color:#666;">DNI: {row.get("_documento", "—")} · {row.get("_tipo_tarjeta", "—")}</span>
            </div>
            <div>
                {render_badge(urgencia_label, badge_type)}
                {render_badge(estado_actual)}
            </div>
        </div>
        <div style="display:flex; gap:2rem; font-size:0.85rem; color:#555;">
            <span>📱 {row.get("_telefono_norm", "—")}</span>
            <span>✉️ {row.get("_mail_norm", "—")}</span>
            <span>📅 Días guarda: <b>{row.get("_dias_guarda", "—")}</b></span>
            <span>📡 {row.get("_canal_sugerido", "—")}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Mensajes ---
    has_phone = pd.notna(row.get("_telefono_norm")) and row.get("_telefono_norm")
    has_mail = pd.notna(row.get("_mail_norm")) and row.get("_mail_norm")

    if has_phone:
        _render_wa_section(row, real_idx, operador, sucursal)

    if has_mail:
        _render_mail_section(row, real_idx, operador, sucursal)

    # --- Botones de estado ---
    st.markdown("---")
    render_section_label("Marcar estado")
    state_cols = st.columns(5)

    estados_opciones = [
        ("✅ Enviado WA", "enviado WhatsApp"),
        ("✅ Enviado Mail", "enviado Mail"),
        ("✅ Enviado ambos", "enviado ambos"),
        ("⏳ Pendiente", "pendiente"),
        ("🔧 Rescate manual", "rescate manual"),
    ]

    for i, (label, state_value) in enumerate(estados_opciones):
        with state_cols[i]:
            disabled = (estado_actual == state_value)
            if st.button(label, key=f"state_{real_idx}_{state_value}",
                        use_container_width=True, disabled=disabled):
                st.session_state.estados[real_idx] = state_value
                st.session_state.df.at[real_idx, "_estado_gestion"] = state_value
                st.rerun()


def _render_wa_section(row, real_idx, operador, sucursal):
    """Renderiza sección de WhatsApp con mensaje y acciones."""
    render_section_label("Mensaje WhatsApp")

    # Generar mensaje (con semilla para consistencia en la sesión)
    wa_key = f"_wa_msg_{real_idx}"
    if wa_key not in st.session_state:
        st.session_state[wa_key] = get_message_wa(row, operador, sucursal)
    wa_msg = st.session_state[wa_key]

    # Preview editable
    wa_msg_edited = st.text_area(
        "Mensaje (podés editar antes de copiar)",
        value=wa_msg,
        height=150,
        key=f"wa_text_{real_idx}",
        label_visibility="collapsed",
    )

    col_wa1, col_wa2, col_wa3 = st.columns(3)
    with col_wa1:
        render_copy_button(wa_msg_edited, "📋 Copiar mensaje WA", key=f"copy_wa_{real_idx}")
    with col_wa2:
        wa_url = get_wa_url(row.get("_telefono_norm"), wa_msg_edited)
        if wa_url:
            st.link_button("💬 Abrir WhatsApp Web", wa_url, use_container_width=True)
    with col_wa3:
        if st.button("🔄 Regenerar mensaje", key=f"regen_wa_{real_idx}", use_container_width=True):
            new_msg = get_message_wa(row, operador, sucursal)
            st.session_state[wa_key] = new_msg
            st.rerun()


def _render_mail_section(row, real_idx, operador, sucursal):
    """Renderiza sección de Mail con mensaje y acciones."""
    render_section_label("Mensaje Mail")

    mail_key = f"_mail_msg_{real_idx}"
    if mail_key not in st.session_state:
        st.session_state[mail_key] = get_message_mail(row, operador, sucursal)
    mail_subject, mail_body = st.session_state[mail_key]

    # Subject
    subject_edited = st.text_input(
        "Asunto",
        value=mail_subject,
        key=f"mail_subject_{real_idx}",
    )

    # Body editable
    body_edited = st.text_area(
        "Cuerpo del mail (podés editar)",
        value=mail_body,
        height=180,
        key=f"mail_body_{real_idx}",
        label_visibility="collapsed",
    )

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        full_mail = f"Asunto: {subject_edited}\n\n{body_edited}"
        render_copy_button(full_mail, "📋 Copiar mail completo", key=f"copy_mail_{real_idx}")
    with col_m2:
        mailto_url = get_mailto_url(row.get("_mail_norm"), subject_edited, body_edited)
        if mailto_url:
            st.link_button("✉️ Abrir cliente de mail", mailto_url, use_container_width=True)
    with col_m3:
        if st.button("🔄 Regenerar mail", key=f"regen_mail_{real_idx}", use_container_width=True):
            new_subject, new_body = get_message_mail(row, operador, sucursal)
            st.session_state[mail_key] = (new_subject, new_body)
            st.rerun()


def _find_next_pending(df_work, current_idx):
    """Busca el siguiente registro pendiente."""
    estados = st.session_state.get("estados", {})
    for i in range(current_idx + 1, len(df_work)):
        real_i = df_work.index[i]
        if estados.get(real_i, "pendiente") == "pendiente":
            return i
    # Wrap around
    for i in range(0, current_idx):
        real_i = df_work.index[i]
        if estados.get(real_i, "pendiente") == "pendiente":
            return i
    return None
