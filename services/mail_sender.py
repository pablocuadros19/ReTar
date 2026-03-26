"""Envío de mails vía Outlook COM (win32com) con fallback a exportación."""

import time
import pandas as pd
from services.message_engine import get_message_mail

# Intentar importar win32com (solo disponible en Windows con pywin32)
try:
    import win32com.client
    OUTLOOK_DISPONIBLE = True
except ImportError:
    OUTLOOK_DISPONIBLE = False


def outlook_disponible():
    """Verifica si Outlook está disponible para envío automático."""
    if not OUTLOOK_DISPONIBLE:
        return False
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        _ = outlook.GetNamespace("MAPI")
        return True
    except Exception:
        return False


def enviar_mail_outlook(destinatario, asunto, cuerpo):
    """Envía un mail individual vía Outlook COM.

    Returns:
        True si se envió correctamente, False si falló.
    """
    if not OUTLOOK_DISPONIBLE:
        return False

    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)  # 0 = MailItem
        mail.To = destinatario
        mail.Subject = asunto
        mail.Body = cuerpo
        mail.Send()
        return True
    except Exception:
        return False


def enviar_campana_mail(df_pendientes, df_original, operador, sucursal,
                        progress_callback=None, cancel_check=None, delay=2):
    """Envía mails a todos los pendientes del día vía Outlook.

    Args:
        df_pendientes: DataFrame con pendientes de mail (de get_pendientes_mail_hoy)
        df_original: DataFrame original con todos los datos
        operador: nombre del operador
        sucursal: nombre de la sucursal
        progress_callback: función(i, total, nombre) para actualizar progreso
        cancel_check: función() que devuelve True si se canceló
        delay: segundos entre envíos

    Returns:
        dict con resultados: enviados, fallidos, cancelado
    """
    resultados = {"enviados": 0, "fallidos": 0, "cancelado": False, "detalle": []}
    total = len(df_pendientes)

    for i, (_, pendiente) in enumerate(df_pendientes.iterrows()):
        # Chequear cancelación
        if cancel_check and cancel_check():
            resultados["cancelado"] = True
            break

        idx_original = pendiente["index"]
        row = df_original.loc[idx_original]
        mail_dest = pendiente["mail"]

        # Generar mensaje
        asunto, cuerpo = get_message_mail(row, operador, sucursal)

        # Notificar progreso
        if progress_callback:
            progress_callback(i + 1, total, pendiente.get("nombre", ""))

        # Enviar
        ok = enviar_mail_outlook(mail_dest, asunto, cuerpo)

        detalle = {
            "nombre": pendiente.get("nombre", ""),
            "mail": mail_dest,
            "banda": pendiente.get("banda", ""),
            "enviado": ok,
        }
        resultados["detalle"].append(detalle)

        if ok:
            resultados["enviados"] += 1
        else:
            resultados["fallidos"] += 1

        # Delay entre envíos (excepto el último)
        if i < total - 1 and delay > 0:
            time.sleep(delay)

    return resultados


def exportar_mails_csv(df_pendientes, df_original, operador, sucursal):
    """Genera un DataFrame con los mails listos para exportar como CSV.

    Fallback cuando Outlook no está disponible.
    """
    filas = []
    for _, pendiente in df_pendientes.iterrows():
        idx_original = pendiente["index"]
        row = df_original.loc[idx_original]
        asunto, cuerpo = get_message_mail(row, operador, sucursal)

        filas.append({
            "nombre": pendiente.get("nombre", ""),
            "documento": pendiente.get("documento", ""),
            "mail": pendiente.get("mail", ""),
            "tipo_tarjeta": pendiente.get("tipo", ""),
            "banda": pendiente.get("banda", ""),
            "asunto": asunto,
            "cuerpo": cuerpo,
        })

    return pd.DataFrame(filas)
