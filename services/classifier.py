"""Clasificación por contactabilidad, tipo de tarjeta y antigüedad."""

import pandas as pd


# Bandas de antigüedad (días de guarda)
BANDAS_ANTIGUEDAD = [
    (0, 10, "informativo", "🟢 Reciente"),
    (11, 30, "recordatorio", "🟡 Moderado"),
    (31, 45, "urgente", "🟠 Urgente"),
    (46, 9999, "prioridad_alta", "🔴 Prioridad alta"),
]


def classify_contactability(row):
    """Clasifica un registro según disponibilidad de contacto."""
    has_phone = pd.notna(row.get("_telefono_norm")) and row.get("_telefono_norm")
    has_mail = pd.notna(row.get("_mail_norm")) and row.get("_mail_norm")

    if has_phone and has_mail:
        return "ambos"
    elif has_phone:
        return "solo_telefono"
    elif has_mail:
        return "solo_mail"
    else:
        return "sin_contacto"


def classify_urgency(dias_guarda):
    """Clasifica la urgencia según días de guarda."""
    if dias_guarda is None or pd.isna(dias_guarda):
        return "sin_fecha", "⚪ Sin fecha"

    dias = int(dias_guarda)
    for min_d, max_d, code, label in BANDAS_ANTIGUEDAD:
        if min_d <= dias <= max_d:
            return code, label

    return "prioridad_alta", "🔴 Prioridad alta"


def suggest_channel(contactability):
    """Sugiere el canal de contacto según disponibilidad."""
    channels = {
        "ambos": "WhatsApp + Mail",
        "solo_telefono": "WhatsApp",
        "solo_mail": "Mail",
        "sin_contacto": "Sin canal",
    }
    return channels.get(contactability, "Sin canal")


def classify_dataframe(df):
    """Agrega columnas de clasificación al DataFrame."""
    df = df.copy()

    # Contactabilidad
    df["_contactabilidad"] = df.apply(classify_contactability, axis=1)

    # Canal sugerido
    df["_canal_sugerido"] = df["_contactabilidad"].apply(suggest_channel)

    # Urgencia
    urgency_data = df["_dias_guarda"].apply(
        lambda d: pd.Series(classify_urgency(d), index=["_urgencia_code", "_urgencia_label"])
    )
    df["_urgencia_code"] = urgency_data["_urgencia_code"]
    df["_urgencia_label"] = urgency_data["_urgencia_label"]

    return df


def get_summary(df):
    """Genera resumen estadístico del DataFrame clasificado."""
    total = len(df)
    if total == 0:
        return {}

    contact_counts = df["_contactabilidad"].value_counts()
    type_counts = df["_tipo_tarjeta"].value_counts()
    urgency_counts = df["_urgencia_label"].value_counts()

    con_telefono = contact_counts.get("solo_telefono", 0) + contact_counts.get("ambos", 0)
    con_mail = contact_counts.get("solo_mail", 0) + contact_counts.get("ambos", 0)
    con_ambos = contact_counts.get("ambos", 0)
    sin_contacto = contact_counts.get("sin_contacto", 0)
    contactables = total - sin_contacto

    dias = df["_dias_guarda"].dropna()
    promedio_dias = round(dias.mean(), 1) if len(dias) > 0 else None
    criticos = len(dias[dias > 30]) if len(dias) > 0 else 0

    return {
        "total": total,
        "contactables": contactables,
        "con_telefono": con_telefono,
        "con_mail": con_mail,
        "con_ambos": con_ambos,
        "sin_contacto": sin_contacto,
        "promedio_dias_guarda": promedio_dias,
        "criticos_30_dias": criticos,
        "por_tipo": type_counts.to_dict(),
        "por_urgencia": urgency_counts.to_dict(),
        "por_contactabilidad": contact_counts.to_dict(),
    }
