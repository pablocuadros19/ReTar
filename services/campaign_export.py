"""Exportación de campañas filtradas a CSV/XLSX."""

import io
import pandas as pd
from services.message_engine import get_message_wa, get_message_mail


def prepare_campaign_df(df, column_map, operador="", sucursal=""):
    """Prepara un DataFrame limpio para exportar con mensajes generados."""
    rows = []
    for _, row in df.iterrows():
        wa_msg = get_message_wa(row, operador, sucursal) if row.get("_telefono_norm") else ""
        mail_subject, mail_body = ("", "")
        if row.get("_mail_norm"):
            mail_subject, mail_body = get_message_mail(row, operador, sucursal)

        rows.append({
            "Nombre": row.get("_nombre", ""),
            "Documento": row.get("_documento", ""),
            "Teléfono": row.get("_telefono_norm", ""),
            "Mail": row.get("_mail_norm", ""),
            "Tipo Tarjeta": row.get("_tipo_tarjeta", ""),
            "Fecha Recepción": row.get("_fecha_recepcion", ""),
            "Días de Guarda": row.get("_dias_guarda", ""),
            "Contactabilidad": row.get("_contactabilidad", ""),
            "Canal Sugerido": row.get("_canal_sugerido", ""),
            "Urgencia": row.get("_urgencia_label", ""),
            "Estado": row.get("_estado_gestion", "pendiente"),
            "Mensaje WhatsApp": wa_msg,
            "Asunto Mail": mail_subject,
            "Mensaje Mail": mail_body,
        })

    return pd.DataFrame(rows)


def export_to_csv(df_campaign):
    """Exporta DataFrame de campaña a CSV en memoria."""
    buffer = io.StringIO()
    df_campaign.to_csv(buffer, index=False, encoding="utf-8-sig")
    return buffer.getvalue().encode("utf-8-sig")


def export_to_xlsx(df_campaign):
    """Exporta DataFrame de campaña a XLSX en memoria."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_campaign.to_excel(writer, index=False, sheet_name="Campaña")
    return buffer.getvalue()
