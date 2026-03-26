"""Normalización de teléfonos, mails, fechas y días de guarda."""

import re
import pandas as pd
from datetime import datetime, date


def normalize_phone(raw):
    """Normaliza un teléfono argentino al formato WhatsApp: 549XXXXXXXXXX."""
    if not raw or pd.isna(raw):
        return None

    digits = re.sub(r"\D", "", str(raw))

    if len(digits) < 8:
        return None

    # Si ya viene con formato internacional completo
    if digits.startswith("549") and len(digits) >= 12:
        return digits[:13]

    # Remover código de país
    if digits.startswith("54"):
        digits = digits[2:]

    # Remover 0 inicial (prefijo interurbano)
    if digits.startswith("0"):
        digits = digits[1:]

    # Remover 15 del número local (prefijo móvil viejo)
    # El 15 puede estar después del código de área (2, 3 o 4 dígitos)
    if len(digits) > 10:
        for pos in [2, 3, 4]:
            if pos < len(digits) - 1 and digits[pos : pos + 2] == "15":
                candidate = digits[:pos] + digits[pos + 2 :]
                if len(candidate) == 10:
                    digits = candidate
                    break

    if len(digits) == 10:
        return f"549{digits}"

    # 8 dígitos sin código de área → asumir Buenos Aires (11)
    if len(digits) == 8:
        return f"5411{digits}"

    # Fallback: tomar últimos 10 dígitos
    if len(digits) > 10:
        return f"549{digits[-10:]}"

    return None


def validate_email(raw):
    """Valida formato básico de email. Devuelve el email limpio o None."""
    if not raw or pd.isna(raw):
        return None

    email = str(raw).strip().lower()
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"

    if re.match(pattern, email):
        return email
    return None


def parse_date(raw):
    """Intenta parsear una fecha en varios formatos comunes."""
    if not raw or pd.isna(raw):
        return None

    if isinstance(raw, (datetime, date)):
        return raw if isinstance(raw, date) else raw.date()

    raw_str = str(raw).strip()
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y",
        "%d-%m-%y", "%Y/%m/%d", "%d.%m.%Y", "%d.%m.%y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(raw_str, fmt).date()
        except ValueError:
            continue

    # Intentar con pandas como último recurso
    try:
        return pd.to_datetime(raw_str, dayfirst=True).date()
    except Exception:
        return None


def calc_dias_guarda(fecha_recepcion):
    """Calcula días desde la recepción hasta hoy."""
    if not fecha_recepcion:
        return None
    try:
        if isinstance(fecha_recepcion, datetime):
            fecha_recepcion = fecha_recepcion.date()
        delta = date.today() - fecha_recepcion
        return max(0, delta.days)
    except Exception:
        return None


def normalize_dataframe(df, column_map):
    """Aplica normalización completa al DataFrame usando el mapeo de columnas."""
    df = df.copy()

    # Normalizar teléfonos
    if "telefono" in column_map:
        col = column_map["telefono"]
        df["_telefono_norm"] = df[col].apply(normalize_phone)
    else:
        df["_telefono_norm"] = None

    # Normalizar mails
    if "mail" in column_map:
        col = column_map["mail"]
        df["_mail_norm"] = df[col].apply(validate_email)
    else:
        df["_mail_norm"] = None

    # Parsear fecha de recepción
    if "fecha_recepcion" in column_map:
        col = column_map["fecha_recepcion"]
        df["_fecha_recepcion"] = df[col].apply(parse_date)
        df["_dias_guarda"] = df["_fecha_recepcion"].apply(calc_dias_guarda)
    else:
        df["_fecha_recepcion"] = None
        df["_dias_guarda"] = None

    # Normalizar tipo de tarjeta
    if "tipo_tarjeta" in column_map:
        col = column_map["tipo_tarjeta"]
        df["_tipo_tarjeta"] = df[col].apply(_normalize_card_type)
    else:
        df["_tipo_tarjeta"] = "Sin dato"

    # Nombre limpio
    if "nombre" in column_map:
        col = column_map["nombre"]
        df["_nombre"] = df[col].apply(lambda x: str(x).strip().title() if pd.notna(x) else "Sin nombre")
    else:
        df["_nombre"] = "Sin nombre"

    # Documento limpio
    if "documento" in column_map:
        col = column_map["documento"]
        df["_documento"] = df[col].apply(lambda x: str(x).strip() if pd.notna(x) else "")
    else:
        df["_documento"] = ""

    # Número de tarjeta
    if "numero_tarjeta" in column_map:
        col = column_map["numero_tarjeta"]
        df["_numero_tarjeta"] = df[col].apply(lambda x: str(x).strip() if pd.notna(x) else "")
    else:
        df["_numero_tarjeta"] = ""

    # Estado original del plástico
    if "estado" in column_map:
        col = column_map["estado"]
        df["_estado_original"] = df[col].apply(lambda x: str(x).strip() if pd.notna(x) else "")
    else:
        df["_estado_original"] = ""

    return df


def _normalize_card_type(raw):
    """Normaliza el tipo de tarjeta a categorías estándar."""
    if not raw or pd.isna(raw):
        return "Sin dato"

    val = str(raw).lower().strip()

    if any(k in val for k in ["debito", "débito", "deb"]):
        return "Débito"
    if any(k in val for k in ["credito", "crédito", "cred"]):
        if any(p in val for p in ["platinum", "black", "signature", "infinite", "premium"]):
            return "Crédito Premium"
        return "Crédito"
    if any(k in val for k in ["platinum", "black", "signature", "infinite", "premium"]):
        return "Premium"
    if any(k in val for k in ["prepaga", "prepaid"]):
        return "Prepaga"

    return val.title()
