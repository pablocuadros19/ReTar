"""Pestaña de contacto guiado — experiencia caso por caso con inteligencia de contacto."""

import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO

from ui.components import (render_divider, render_section_label, render_badge,
                           render_msg_preview, render_copy_button, require_data)
from services.message_engine import get_message_wa, get_message_mail, get_wa_url, get_wa_app_url, get_mailto_url
from services.normalizer import format_phone_display
from services.classifier import ordenar_cola_contacto
from services.contact_history import (
    cargar_historial, registrar_contacto, contar_contactos
)
from services.contact_sequence import (
    get_pendientes_mail_hoy, get_pendientes_wa_hoy, resumen_pendientes_hoy,
    determinar_accion_hoy,
)
from services.mail_sender import outlook_disponible, enviar_campana_mail, exportar_mails_csv
from services.stock_manager import actualizar_estado_tarjeta

# Límite diario de WhatsApp
WA_LIMITE_DIARIO = 20


def render_tab_contacto():
    """Renderiza la pestaña de contacto guiado."""

    st.markdown("### 📞 Contacto guiado")
    render_divider()

    if not require_data():
        return

    df = st.session_state.df
    operador = st.session_state.get("operador", "")
    sucursal = st.session_state.get("sucursal", "")
    historial = cargar_historial()

    # --- Panel de mails del día ---
    _render_panel_mails_dia(df, operador, sucursal, historial)

    st.markdown("---")

    # --- Contador WA del día ---
    _render_contador_wa()

    # --- Filtros de trabajo ---
    render_section_label("Filtros de trabajo")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

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
    with col_f4:
        filtro_orden = st.selectbox(
            "Orden",
            ["Por prioridad (reglas)", "Por días de guarda", "Por nombre"],
            key="contacto_filtro_orden",
        )

    # Aplicar filtros
    df_work = _apply_filters(df, filtro_estado, filtro_canal, filtro_urgencia)

    # Ordenar según selección
    if filtro_orden == "Por prioridad (reglas)":
        df_work = ordenar_cola_contacto(df_work, historial)
    elif filtro_orden == "Por días de guarda":
        df_work = df_work.sort_values("_dias_guarda", ascending=False, na_position="last")
    else:
        df_work = df_work.sort_values("_nombre", na_position="last")

    df_work = df_work.reset_index(drop=False)

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
    completados = sum(1 for i in df_work["index"]
                      if st.session_state.get("estados", {}).get(i, "pendiente") != "pendiente")
    st.progress(completados / total if total > 0 else 0)
    st.caption(f"Caso **{idx + 1}** de **{total}** — {completados} gestionados")

    # --- Card del caso actual ---
    row = df_work.iloc[idx]
    real_idx = row["index"] if "index" in df_work.columns else df_work.index[idx]

    _render_contact_card(row, real_idx, operador, sucursal, historial)

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


# ==================== PANEL MAILS DEL DÍA ====================

def _render_panel_mails_dia(df, operador, sucursal, historial):
    """Muestra el panel de mails pendientes del día con botón de envío."""
    pendientes_mail = get_pendientes_mail_hoy(df, historial)

    if len(pendientes_mail) == 0:
        st.success("No hay mails pendientes para hoy.")
        return

    # Resumen
    total_mails = len(pendientes_mail)
    bandas = pendientes_mail["banda"].value_counts()
    resumen_text = ", ".join(f"{v} {k}" for k, v in bandas.items())

    st.markdown(f"""
    <div style="background:#f0f9f4; border:1px solid #c8e6d5; border-left:4px solid #00A651;
                border-radius:12px; padding:1rem 1.2rem; margin-bottom:1rem;">
        <div style="font-weight:700; color:#1a1a2e; margin-bottom:0.3rem;">
            ✉️ Mails del día: {total_mails} pendientes
        </div>
        <div style="font-size:0.85rem; color:#555;">
            {resumen_text}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Lista expandible
    with st.expander(f"Ver {total_mails} destinatarios"):
        st.dataframe(
            pendientes_mail[["nombre", "tipo", "banda", "mail", "motivo"]],
            use_container_width=True,
            hide_index=True,
        )

    # Botones de acción
    col_a1, col_a2 = st.columns(2)

    with col_a1:
        if outlook_disponible():
            if st.button(f"📨 Enviar {total_mails} mails vía Outlook",
                        use_container_width=True, type="primary"):
                _ejecutar_envio_outlook(pendientes_mail, df, operador, sucursal, historial)
        else:
            st.info("Outlook no disponible — usá la exportación CSV")

    with col_a2:
        # Exportar como CSV (siempre disponible)
        csv_df = exportar_mails_csv(pendientes_mail, df, operador, sucursal)
        csv_bytes = csv_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Exportar mails del día (CSV)",
            data=csv_bytes,
            file_name=f"mails_dia_{date.today().isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )


def _ejecutar_envio_outlook(pendientes_mail, df, operador, sucursal, historial):
    """Ejecuta el envío masivo vía Outlook con progress bar."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(pendientes_mail)

    def progress_cb(i, tot, nombre):
        progress_bar.progress(i / tot)
        status_text.text(f"Enviando {i}/{tot} — {nombre}...")

    resultados = enviar_campana_mail(
        pendientes_mail, df, operador, sucursal,
        progress_callback=progress_cb,
        delay=2,
    )

    progress_bar.progress(1.0)

    # Registrar en historial
    for detalle in resultados["detalle"]:
        if detalle["enviado"]:
            # Buscar documento por mail
            match = pendientes_mail[pendientes_mail["mail"] == detalle["mail"]]
            if len(match) > 0:
                doc = match.iloc[0]["documento"]
                banda = match.iloc[0]["banda"]
                registrar_contacto(doc, "mail", banda, historial)

    # Mostrar resultado
    if resultados["fallidos"] == 0:
        st.success(f"✅ {resultados['enviados']} mails enviados correctamente")
    else:
        st.warning(
            f"Enviados: {resultados['enviados']} — Fallidos: {resultados['fallidos']}"
        )


# ==================== CONTADOR WA ====================

def _render_contador_wa():
    """Muestra el contador diario de gestión: WA + Mail + Total."""
    # Inicializar o resetear si cambió el día
    hoy = date.today().isoformat()
    if st.session_state.get("wa_fecha_hoy") != hoy:
        st.session_state.wa_fecha_hoy = hoy
        st.session_state.wa_enviados_hoy = 0

    wa_enviados = st.session_state.get("wa_enviados_hoy", 0)

    # Contar mails de hoy desde historial
    historial = cargar_historial()
    mails_hoy = 0
    for doc_data in historial.values():
        for c in doc_data.get("contactos", []):
            if c.get("fecha") == hoy and c.get("canal") == "mail":
                mails_hoy += 1

    total_hoy = wa_enviados + mails_hoy

    # Color WA según límite
    wa_color = "#dc3545" if wa_enviados >= WA_LIMITE_DIARIO else "#00A651"
    wa_extra = " LÍMITE" if wa_enviados >= WA_LIMITE_DIARIO else ""

    st.markdown(f"""
    <div style="display:inline-flex; align-items:center; gap:1rem;
                background:#f7f9fc; border:1px solid #e0e5ec; border-radius:20px;
                padding:0.4rem 1.2rem; font-size:0.85rem; margin-bottom:1rem;">
        <span style="font-weight:600; color:{wa_color};">📱 WA: {wa_enviados}/{WA_LIMITE_DIARIO}{wa_extra}</span>
        <span style="color:#999;">|</span>
        <span style="font-weight:600; color:#00A651;">📧 Mail: {mails_hoy}</span>
        <span style="color:#999;">|</span>
        <span style="font-weight:600; color:#1a1a2e;">👥 Total: {total_hoy}</span>
    </div>
    """, unsafe_allow_html=True)


def _incrementar_contador_wa():
    """Incrementa el contador de WA enviados hoy."""
    hoy = date.today().isoformat()
    if st.session_state.get("wa_fecha_hoy") != hoy:
        st.session_state.wa_fecha_hoy = hoy
        st.session_state.wa_enviados_hoy = 0
    st.session_state.wa_enviados_hoy = st.session_state.get("wa_enviados_hoy", 0) + 1


# ==================== CARD DE CONTACTO ====================

def _apply_filters(df, estado, canal, urgencia):
    """Aplica filtros al DataFrame para la sesión de contacto."""
    mask = pd.Series(True, index=df.index)

    if estado != "todos":
        estados = st.session_state.get("estados", {})
        mask &= df.index.map(lambda i: estados.get(i, "pendiente") == estado)

    if canal != "todos":
        mask &= df["_contactabilidad"] == canal

    if urgencia != "todas":
        mask &= df["_urgencia_code"] == urgencia

    # Excluir sin contacto
    mask &= df["_contactabilidad"] != "sin_contacto"

    return df[mask]


def _render_contact_card(row, real_idx, operador, sucursal, historial):
    """Renderiza la card de un caso de contacto con score y acción sugerida."""
    estado_actual = st.session_state.get("estados", {}).get(real_idx, "pendiente")

    # Badge de urgencia
    urgencia_label = row.get("_urgencia_label", "")
    urgencia_code = row.get("_urgencia_code", "")
    badge_type = "default"
    if urgencia_code == "urgente":
        badge_type = "urgente"
    elif urgencia_code == "prioridad_alta":
        badge_type = "prioridad"

    # Acción sugerida hoy — badge grande y visible
    accion = determinar_accion_hoy(row, historial)
    if accion:
        canal = accion["canal"]
        if canal == "mail":
            accion_html = '<span style="background:#00A651; color:white; font-size:1rem; font-weight:700; padding:0.4rem 1rem; border-radius:20px; display:inline-block;">📧 MAIL HOY</span>'
        elif canal == "wa":
            accion_html = '<span style="background:#00A651; color:white; font-size:1rem; font-weight:700; padding:0.4rem 1rem; border-radius:20px; display:inline-block;">📱 WA HOY</span>'
        else:
            accion_html = '<span style="background:#00A651; color:white; font-size:1rem; font-weight:700; padding:0.4rem 1rem; border-radius:20px; display:inline-block;">📨 CONTACTAR HOY</span>'
    else:
        from services.contact_history import esta_agotado
        doc_check = str(row.get("_documento", ""))
        if esta_agotado(doc_check, historial):
            accion_html = '<span style="background:#dc3545; color:white; font-size:1rem; font-weight:700; padding:0.4rem 1rem; border-radius:20px; display:inline-block;">✅ AGOTADO</span>'
        else:
            accion_html = '<span style="background:#e0e5ec; color:#666; font-size:1rem; font-weight:700; padding:0.4rem 1rem; border-radius:20px; display:inline-block;">⏸ ESPERAR</span>'

    # Historial del cliente
    doc = str(row.get("_documento", ""))
    conteo = contar_contactos(doc, historial)
    historial_html = ""
    if conteo["total"] > 0:
        historial_html = f'<span style="font-size:0.75rem; color:#999;">Contactos previos: {conteo["mails"]}📧 {conteo["was"]}📱</span>'

    st.markdown(f"""
    <div class="contacto-card activo">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
            <div>
                <span style="font-size:1.1rem; font-weight:700; color:#1a1a2e;">{row.get("_nombre", "Sin nombre")}</span>
                <br><span style="font-size:0.8rem; color:#666;">DNI: {row.get("_documento", "—")} · {row.get("_tipo_tarjeta", "—")}</span>
                <br>{historial_html}
            </div>
            <div style="display:flex; gap:0.5rem; align-items:center; flex-wrap:wrap;">
                {accion_html}
                {render_badge(urgencia_label, badge_type)}
                {render_badge(estado_actual)}
            </div>
        </div>
        <div style="display:flex; gap:2rem; font-size:0.85rem; color:#555;">
            <span>📱 {format_phone_display(row.get("_telefono_norm"))}</span>
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
        _render_wa_section(row, real_idx, operador, sucursal, historial)

    if has_mail:
        _render_mail_section(row, real_idx, operador, sucursal, historial)

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

                # Persistir en stock en disco
                nro_tarjeta = str(row.get("_numero_tarjeta", ""))
                if nro_tarjeta:
                    actualizar_estado_tarjeta(nro_tarjeta, state_value)

                # Registrar en historial
                doc = str(row.get("_documento", ""))
                banda = row.get("_urgencia_code", "informativo")
                if state_value == "enviado WhatsApp":
                    registrar_contacto(doc, "wa", banda)
                    _incrementar_contador_wa()
                elif state_value == "enviado Mail":
                    registrar_contacto(doc, "mail", banda)
                elif state_value == "enviado ambos":
                    registrar_contacto(doc, "wa", banda)
                    registrar_contacto(doc, "mail", banda)
                    _incrementar_contador_wa()

                st.rerun()


def _render_wa_section(row, real_idx, operador, sucursal, historial):
    """Renderiza sección de WhatsApp con mensaje y acciones."""
    render_section_label("Mensaje WhatsApp")

    # Verificar límite diario
    enviados_hoy = st.session_state.get("wa_enviados_hoy", 0)
    if enviados_hoy >= WA_LIMITE_DIARIO:
        st.warning("⚠️ Llegaste al límite diario de WhatsApp (15). Continuá mañana para evitar baneo.")

    wa_key = f"_wa_msg_{real_idx}"
    if wa_key not in st.session_state:
        st.session_state[wa_key] = get_message_wa(row, operador, sucursal)
    wa_msg = st.session_state[wa_key]

    wa_msg_edited = st.text_area(
        "Mensaje (podés editar antes de copiar)",
        value=wa_msg,
        height=150,
        key=f"wa_text_{real_idx}",
        label_visibility="collapsed",
    )

    col_wa1, col_wa2, col_wa3, col_wa4 = st.columns(4)
    with col_wa1:
        render_copy_button(wa_msg_edited, "📋 Copiar mensaje WA", key=f"copy_wa_{real_idx}")
    with col_wa2:
        wa_app_url = get_wa_app_url(row.get("_telefono_norm"), wa_msg_edited)
        if wa_app_url:
            st.link_button("💬 Abrir WhatsApp", wa_app_url, use_container_width=True)
    with col_wa3:
        wa_url = get_wa_url(row.get("_telefono_norm"), wa_msg_edited)
        if wa_url:
            st.link_button("🌐 WhatsApp Web", wa_url, use_container_width=True)
    with col_wa4:
        if st.button("🔄 Regenerar mensaje", key=f"regen_wa_{real_idx}", use_container_width=True):
            new_msg = get_message_wa(row, operador, sucursal)
            st.session_state[wa_key] = new_msg
            st.rerun()


def _render_mail_section(row, real_idx, operador, sucursal, historial):
    """Renderiza sección de Mail con mensaje y acciones."""
    render_section_label("Mensaje Mail")

    mail_key = f"_mail_msg_{real_idx}"
    if mail_key not in st.session_state:
        st.session_state[mail_key] = get_message_mail(row, operador, sucursal)
    mail_subject, mail_body = st.session_state[mail_key]

    subject_edited = st.text_input(
        "Asunto",
        value=mail_subject,
        key=f"mail_subject_{real_idx}",
    )

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
    index_col = "index" if "index" in df_work.columns else None

    for i in range(current_idx + 1, len(df_work)):
        real_i = df_work.iloc[i][index_col] if index_col else df_work.index[i]
        if estados.get(real_i, "pendiente") == "pendiente":
            return i
    for i in range(0, current_idx):
        real_i = df_work.iloc[i][index_col] if index_col else df_work.index[i]
        if estados.get(real_i, "pendiente") == "pendiente":
            return i
    return None
