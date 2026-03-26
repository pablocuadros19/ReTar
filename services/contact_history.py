"""Persistencia de historial de contactos en JSON local."""

import json
from pathlib import Path
from datetime import date

HISTORIAL_PATH = Path("data/historial_contactos.json")


def cargar_historial():
    """Carga el historial desde disco. Devuelve dict vacío si no existe."""
    if not HISTORIAL_PATH.exists():
        return {}
    try:
        return json.loads(HISTORIAL_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def guardar_historial(historial):
    """Guarda el historial a disco."""
    HISTORIAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORIAL_PATH.write_text(
        json.dumps(historial, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def registrar_contacto(documento, canal, banda, historial=None):
    """Registra un contacto realizado. Devuelve el historial actualizado."""
    if historial is None:
        historial = cargar_historial()

    doc = str(documento)
    if doc not in historial:
        historial[doc] = {"contactos": [], "estado": "activo"}

    historial[doc]["contactos"].append({
        "fecha": date.today().isoformat(),
        "canal": canal,
        "banda": banda,
    })

    # Actualizar estado según contactos acumulados
    contactos = historial[doc]["contactos"]
    mails = sum(1 for c in contactos if c["canal"] == "mail")
    was = sum(1 for c in contactos if c["canal"] == "wa")

    # Agotado tiene prioridad sobre todo
    if mails >= 3 and was >= 2:
        historial[doc]["estado"] = "agotado"
    elif canal == "mail":
        historial[doc]["estado"] = "enviado_ambos" if was > 0 else "enviado_mail"
    elif canal == "wa":
        historial[doc]["estado"] = "enviado_ambos" if mails > 0 else "enviado_wa"

    guardar_historial(historial)
    return historial


def get_contactos_cliente(documento, historial=None):
    """Devuelve la lista de contactos de un cliente."""
    if historial is None:
        historial = cargar_historial()
    return historial.get(str(documento), {}).get("contactos", [])


def esta_agotado(documento, historial=None):
    """Verifica si un cliente ya agotó los intentos de contacto."""
    if historial is None:
        historial = cargar_historial()
    return historial.get(str(documento), {}).get("estado") == "agotado"


def contar_contactos(documento, historial=None):
    """Devuelve conteo de mails y WA enviados a un cliente."""
    contactos = get_contactos_cliente(documento, historial)
    mails = sum(1 for c in contactos if c["canal"] == "mail")
    was = sum(1 for c in contactos if c["canal"] == "wa")
    return {"mails": mails, "was": was, "total": mails + was}


def ultimo_contacto(documento, canal=None, historial=None):
    """Devuelve la fecha del último contacto (o None). Opcionalmente filtrar por canal."""
    contactos = get_contactos_cliente(documento, historial)
    if canal:
        contactos = [c for c in contactos if c["canal"] == canal]
    if not contactos:
        return None
    return contactos[-1]["fecha"]
