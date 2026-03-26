"""Lógica de secuencia de contacto — determina qué acción corresponde hoy para cada tarjeta."""

import pandas as pd
from datetime import date, timedelta
from services.contact_history import (
    contar_contactos, ultimo_contacto, esta_agotado
)

# Secuencia de contacto por días de guarda
# (min_dias, max_dias, canal_si_tiene_tel, canal_si_solo_mail, banda)
SECUENCIA = [
    (1, 2, "mail", "mail", "informativo"),
    (5, 6, "mail", "mail", "recordatorio"),
    (10, 15, "mail", "mail", "recordatorio"),
    (16, 29, "wa", "mail", "recordatorio"),
    (30, 45, "wa", "mail", "urgente"),
    (46, 9999, "wa", "mail", "prioridad_alta"),
]

# Mínimo días entre contactos por el mismo canal
MIN_DIAS_ENTRE_CONTACTOS = 2


def determinar_accion_hoy(row, historial=None):
    """Determina qué acción de contacto corresponde hoy para una tarjeta.

    Returns:
        dict con keys: canal ("mail"|"wa"|"ambos"|None), banda, motivo
        o None si no corresponde contactar hoy.
    """
    dias = row.get("_dias_guarda")
    contactabilidad = row.get("_contactabilidad", "sin_contacto")
    documento = str(row.get("_documento", ""))

    # Sin contacto posible
    if contactabilidad == "sin_contacto":
        return None

    # Agotado
    if esta_agotado(documento, historial):
        return None

    # Sin fecha → tratar como informativo si nunca se contactó
    if pd.isna(dias) or dias is None:
        conteo = contar_contactos(documento, historial)
        if conteo["total"] == 0:
            canal = _canal_para_contactabilidad(contactabilidad, "mail")
            return {"canal": canal, "banda": "sin_fecha", "motivo": "Sin fecha, primer contacto"}
        return None

    dias = int(dias)

    # Buscar en qué tramo de la secuencia cae
    for min_d, max_d, canal_tel, canal_mail, banda in SECUENCIA:
        if min_d <= dias <= max_d:
            # Determinar canal según contactabilidad
            if contactabilidad in ("solo_telefono", "ambos"):
                canal_base = canal_tel
            else:
                canal_base = canal_mail

            # Verificar topes
            conteo = contar_contactos(documento, historial)

            # Tope global: 3 mails + 2 WA = agotado
            if conteo["mails"] >= 3 and conteo["was"] >= 2:
                return None

            if canal_base == "wa" and conteo["was"] >= 2:
                # Ya agotó WA, intentar mail si tiene
                if contactabilidad in ("solo_mail", "ambos") and conteo["mails"] < 3:
                    canal_base = "mail"
                else:
                    return None

            if canal_base == "mail" and conteo["mails"] >= 3:
                # Ya agotó mail, intentar WA si tiene y corresponde
                if contactabilidad in ("solo_telefono", "ambos") and conteo["was"] < 2 and dias >= 16:
                    canal_base = "wa"
                else:
                    return None

            # Verificar que no se contactó hace menos de MIN_DIAS
            ult = ultimo_contacto(documento, canal_base, historial)
            if ult:
                dias_desde = (date.today() - date.fromisoformat(ult)).days
                if dias_desde < MIN_DIAS_ENTRE_CONTACTOS:
                    return None

            return {
                "canal": canal_base,
                "banda": banda,
                "motivo": f"Día {dias} de guarda — {banda}",
            }

    return None


def _canal_para_contactabilidad(contactabilidad, canal_preferido):
    """Ajusta el canal según lo que tiene disponible el cliente."""
    if canal_preferido == "wa":
        if contactabilidad in ("solo_telefono", "ambos"):
            return "wa"
        elif contactabilidad == "solo_mail":
            return "mail"
    elif canal_preferido == "mail":
        if contactabilidad in ("solo_mail", "ambos"):
            return "mail"
        elif contactabilidad == "solo_telefono":
            return "wa"
    return None


def get_pendientes_mail_hoy(df, historial=None):
    """Filtra registros que necesitan mail hoy."""
    pendientes = []
    for idx, row in df.iterrows():
        accion = determinar_accion_hoy(row, historial)
        if accion and accion["canal"] == "mail":
            pendientes.append({
                "index": idx,
                "nombre": row.get("_nombre", "Sin nombre"),
                "documento": row.get("_documento", ""),
                "tipo": row.get("_tipo_tarjeta", ""),
                "dias": row.get("_dias_guarda", ""),
                "mail": row.get("_mail_norm", ""),
                "banda": accion["banda"],
                "motivo": accion["motivo"],
            })
    return pd.DataFrame(pendientes) if pendientes else pd.DataFrame()


def get_pendientes_wa_hoy(df, historial=None):
    """Filtra registros que necesitan WhatsApp hoy."""
    pendientes = []
    for idx, row in df.iterrows():
        accion = determinar_accion_hoy(row, historial)
        if accion and accion["canal"] == "wa":
            pendientes.append({
                "index": idx,
                "nombre": row.get("_nombre", "Sin nombre"),
                "documento": row.get("_documento", ""),
                "tipo": row.get("_tipo_tarjeta", ""),
                "dias": row.get("_dias_guarda", ""),
                "telefono": row.get("_telefono_norm", ""),
                "banda": accion["banda"],
                "motivo": accion["motivo"],
            })
    return pd.DataFrame(pendientes) if pendientes else pd.DataFrame()


def resumen_pendientes_hoy(df, historial=None):
    """Genera un resumen de cuántos contactos corresponden hoy por canal y banda."""
    mail_hoy = get_pendientes_mail_hoy(df, historial)
    wa_hoy = get_pendientes_wa_hoy(df, historial)

    resumen = {
        "total_mail": len(mail_hoy),
        "total_wa": len(wa_hoy),
        "mail_por_banda": mail_hoy["banda"].value_counts().to_dict() if len(mail_hoy) > 0 else {},
        "wa_por_banda": wa_hoy["banda"].value_counts().to_dict() if len(wa_hoy) > 0 else {},
    }
    return resumen
