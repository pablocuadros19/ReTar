"""Motor de mensajes personalizados con variantes para evitar baneos en WhatsApp."""

import re
import random
import urllib.parse
import pandas as pd


# --- Templates WhatsApp por banda de urgencia ---

TEMPLATES_WA = {
    "informativo": [
        "Hola {nombre}, te escribe {operador} de la sucursal {sucursal} de Banco Provincia.\n"
        "Te informamos que tu tarjeta {tipo} ya se encuentra disponible para retiro desde el {fecha}. {beneficio}\n"
        "Cuando te resulte conveniente, podés acercarte a la sucursal para retirarla.",

        "Hola {nombre}, ¿cómo estás? Soy {operador}, de la sucursal {sucursal} de Banco Provincia.\n"
        "Queríamos avisarte que tu tarjeta {tipo} está disponible para retiro desde el {fecha}. {beneficio}\n"
        "Quedamos a disposición por cualquier consulta.",

        "Hola {nombre}, te escribo desde Banco Provincia, sucursal {sucursal}.\n"
        "Tu tarjeta {tipo} llegó el {fecha} y ya se encuentra disponible para retiro. {beneficio}\n"
        "Podés acercarte a retirarla cuando te resulte conveniente.",

        "Hola {nombre}, soy {operador} de la sucursal {sucursal} de Banco Provincia.\n"
        "Queríamos informarte que tu tarjeta {tipo} ya se encuentra en la sucursal desde el {fecha}, "
        "lista para ser retirada. {beneficio}\n"
        "Quedamos a disposición ante cualquier consulta.",
    ],
    "recordatorio": [
        "Hola {nombre}, te escribe {operador} de la sucursal {sucursal} de Banco Provincia.\n"
        "Te recordamos que tu tarjeta {tipo} está disponible para retiro desde el {fecha} "
        "y permanece en la sucursal desde hace {dias} días. {beneficio}\n"
        "Si aún no pudiste retirarla, la seguimos teniendo a disposición.",

        "Hola {nombre}, ¿cómo estás? Soy {operador}, de la sucursal {sucursal} de Banco Provincia.\n"
        "Te escribimos para recordarte que tu tarjeta {tipo}, disponible desde el {fecha}, "
        "continúa aguardando retiro en la sucursal. {beneficio}\n"
        "Cuando te resulte conveniente, podés acercarte a retirarla.",

        "Hola {nombre}, te escribo desde Banco Provincia, sucursal {sucursal}.\n"
        "Tu tarjeta {tipo} está disponible para retiro desde el {fecha} "
        "y ya lleva {dias} días en la sucursal. {beneficio}\n"
        "Por eso queríamos acercarte este recordatorio.",

        "Hola {nombre}, soy {operador} de Banco Provincia, sucursal {sucursal}.\n"
        "Te recordamos que tu tarjeta {tipo} se encuentra disponible para retiro desde el {fecha}. {beneficio}\n"
        "La sucursal la mantiene a disposición para cuando puedas pasar a retirarla.",
    ],
    "urgente": [
        "Hola {nombre}, te escribe {operador} de la sucursal {sucursal} de Banco Provincia.\n"
        "Tu tarjeta {tipo} se encuentra disponible para retiro desde el {fecha} "
        "y permanece en la sucursal desde hace {dias} días. {beneficio}\n"
        "Te sugerimos acercarte en los próximos días para retirarla.",

        "Hola {nombre}, ¿cómo estás? Soy {operador}, de la sucursal {sucursal} de Banco Provincia.\n"
        "Te contactamos nuevamente porque tu tarjeta {tipo}, disponible desde el {fecha}, "
        "sigue aguardando retiro en la sucursal. {beneficio}\n"
        "Para regularizar esta situación, te sugerimos acercarte a la brevedad.",

        "Hola {nombre}, te escribo desde Banco Provincia, sucursal {sucursal}.\n"
        "Tu tarjeta {tipo} se encuentra disponible para retiro desde el {fecha} "
        "y ya transcurrieron {dias} días desde su llegada. {beneficio}\n"
        "Por ese motivo, te recomendamos retirarla en los próximos días.",

        "Hola {nombre}, soy {operador} de la sucursal {sucursal} de Banco Provincia.\n"
        "Te recordamos que tu tarjeta {tipo} está disponible para retiro desde el {fecha}. {beneficio}\n"
        "Como ya pasaron {dias} días, te sugerimos acercarte a la brevedad para retirarla.",
    ],
    "prioridad_alta": [
        "Hola {nombre}, te escribe {operador} de la sucursal {sucursal} de Banco Provincia.\n"
        "Tu tarjeta {tipo} está disponible para retiro desde el {fecha} "
        "y continúa pendiente desde hace {dias} días. {beneficio}\n"
        "Te recomendamos acercarte a la brevedad para retirarla.",

        "Hola {nombre}, ¿cómo estás? Soy {operador}, de la sucursal {sucursal} de Banco Provincia.\n"
        "Te escribimos nuevamente porque tu tarjeta {tipo}, disponible desde el {fecha}, "
        "sigue aguardando retiro en la sucursal. {beneficio}\n"
        "Por el tiempo transcurrido, te sugerimos retirarla en los próximos días.",

        "Hola {nombre}, te escribo desde Banco Provincia, sucursal {sucursal}.\n"
        "Tu tarjeta {tipo} se encuentra disponible para retiro desde el {fecha} "
        "y ya pasaron {dias} días desde su recepción. {beneficio}\n"
        "Por ese motivo, te recomendamos acercarte a la sucursal a la brevedad.",

        "Hola {nombre}, soy {operador} de la sucursal {sucursal} de Banco Provincia.\n"
        "Te recordamos que tu tarjeta {tipo} permanece disponible para retiro desde el {fecha}. {beneficio}\n"
        "Dado el tiempo transcurrido, te sugerimos retirarla en los próximos días.",
    ],
    "sin_fecha": [
        "Hola {nombre}, te escribe {operador} de la sucursal {sucursal} de Banco Provincia.\n"
        "Te informamos que tu tarjeta {tipo} se encuentra disponible para retiro en la sucursal. {beneficio}\n"
        "Cuando te resulte conveniente, podés acercarte a retirarla.",

        "Hola {nombre}, ¿cómo estás? Soy {operador}, de la sucursal {sucursal} de Banco Provincia.\n"
        "Te contactamos para informarte que tu tarjeta {tipo} ya está disponible para retiro en la sucursal. {beneficio}\n"
        "Quedamos a disposición por cualquier consulta.",
    ],
}


# --- Templates Mail por banda de urgencia ---

SUBJECTS_MAIL = {
    "informativo": [
        "Tu tarjeta {tipo} ya está disponible para retiro en sucursal {sucursal}",
        "Banco Provincia | Disponibilidad de tu tarjeta {tipo} en sucursal {sucursal}",
    ],
    "recordatorio": [
        "Recordatorio: tu tarjeta {tipo} continúa disponible en sucursal {sucursal}",
        "Banco Provincia | Tu tarjeta {tipo} sigue disponible para retiro",
    ],
    "urgente": [
        "Te sugerimos retirar tu tarjeta {tipo} disponible en sucursal {sucursal}",
        "Banco Provincia | Tu tarjeta {tipo} permanece disponible para retiro",
    ],
    "prioridad_alta": [
        "Importante: tu tarjeta {tipo} continúa pendiente de retiro en sucursal {sucursal}",
        "Banco Provincia | Te recordamos retirar tu tarjeta {tipo}",
    ],
    "sin_fecha": [
        "Banco Provincia | Tu tarjeta {tipo} está disponible para retiro en sucursal {sucursal}",
    ],
}

_MAIL_FOOTER = (
    "Para realizar el trámite, presentarse en el sector cajas con su DNI. "
    "En caso de tratarse de una tarjeta adicional, debe concurrir el titular de la cuenta. "
    "Si lo prefiere, puede autorizar a un tercero para realizar el retiro, "
    "comunicándolo previamente al WhatsApp institucional de la sucursal.\n\n"
    "Para mayor comodidad, puede solicitar un turno en "
    "www.bancoprovincia.com.ar/turneroweb/#/ y así evitar demoras al concurrir.\n\n"
    "Asimismo, le recordamos que tiene la posibilidad de contratar el seguro de "
    "Fraudes y Estafas, con amplia cobertura, en "
    "www.bancoprovincia.com.ar/web/seguro_robo_atm\n\n"
    "Este correo es de difusión, por favor no responder.\n\n"
    "Saludos cordiales."
)

TEMPLATES_MAIL = {
    "informativo": [
        "Estimado/a {nombre}:\n\n"
        "Le informamos que su tarjeta {tipo} ya se encuentra disponible para retirar "
        "en nuestra sucursal {sucursal} desde el {fecha}. {beneficio}\n\n"
        + _MAIL_FOOTER,
    ],
    "recordatorio": [
        "Estimado/a {nombre}:\n\n"
        "Le recordamos que su tarjeta {tipo} se encuentra disponible para retirar "
        "en nuestra sucursal {sucursal} desde el {fecha}. "
        "La disponibilidad se mantiene por un período de tiempo limitado. {beneficio}\n\n"
        + _MAIL_FOOTER,
    ],
    "urgente": [
        "Estimado/a {nombre}:\n\n"
        "Le recordamos que su tarjeta {tipo} se encuentra disponible para retirar "
        "en nuestra sucursal {sucursal} desde el {fecha}. "
        "Es importante que realice el trámite lo antes posible, ya que la disponibilidad "
        "se mantiene por un período de tiempo limitado. {beneficio}\n\n"
        + _MAIL_FOOTER,
    ],
    "prioridad_alta": [
        "Estimado/a {nombre}:\n\n"
        "Le recordamos que su tarjeta {tipo} se encuentra disponible para retirar "
        "en nuestra sucursal {sucursal} desde el {fecha}. "
        "Es importante que realice el trámite lo antes posible, ya que la disponibilidad "
        "se mantiene por un período de tiempo limitado. {beneficio}\n\n"
        + _MAIL_FOOTER,
    ],
    "sin_fecha": [
        "Estimado/a {nombre}:\n\n"
        "Le informamos que su tarjeta {tipo} ya se encuentra disponible para retirar "
        "en nuestra sucursal {sucursal}. {beneficio}\n\n"
        + _MAIL_FOOTER,
    ],
}


# Beneficios por tipo de tarjeta
BENEFICIOS = {
    "Débito": [
        "Con tu tarjeta también podés operar y aprovechar beneficios vigentes del banco.",
        "Una vez retirada, vas a poder utilizarla para tus operaciones habituales y compras con beneficios vigentes.",
        "",
    ],
    "Crédito": [
        "Además, con tu tarjeta podés acceder a promociones y beneficios vigentes del banco.",
        "Una vez retirada, vas a poder comenzar a usarla en compras y aprovechar promociones vigentes.",
        "",
    ],
    "Crédito Premium": [
        "",
    ],
    "Premium": [
        "",
    ],
}


def _get_beneficio(tipo_tarjeta):
    """Devuelve un beneficio aleatorio según tipo de tarjeta."""
    options = BENEFICIOS.get(tipo_tarjeta, [""])
    return random.choice(options)


def _format_fecha(fecha):
    """Formatea fecha para incluir en mensaje — solo dd/mm/aaaa, sin hora ni timezone."""
    if fecha is None:
        return ""
    try:
        if pd.isna(fecha):
            return ""
    except Exception:
        pass
    try:
        return fecha.strftime("%d/%m/%Y")
    except AttributeError:
        # String o Timestamp — parsear y formatear limpio
        try:
            return pd.to_datetime(str(fecha)).strftime("%d/%m/%Y")
        except Exception:
            return ""


def _clean_message(msg):
    """Limpia espacios dobles, líneas vacías extra y artefactos de beneficio/fecha vacíos."""
    # Limpiar "desde el " cuando no hay fecha
    msg = re.sub(r'desde el\s*\.', '.', msg)
    msg = re.sub(r'desde el\s*y\b', 'y', msg)
    msg = re.sub(r'desde el\s*,', ',', msg)
    msg = re.sub(r'desde el\s+\n', '.\n', msg)
    # Limpiar "el {fecha}" suelto sin fecha
    msg = re.sub(r'el\s+y\b', 'y', msg)
    # Limpiar ". \n" o ".  \n" que quedan cuando beneficio está vacío
    msg = re.sub(r'\. +\n', '.\n', msg)
    # Limpiar " . " sueltos
    msg = re.sub(r' +\.', '.', msg)
    # Dobles espacios
    msg = re.sub(r'  +', ' ', msg)
    # Líneas que quedaron solo con espacios
    msg = re.sub(r'\n +\n', '\n\n', msg)
    # Más de 2 saltos de línea consecutivos
    msg = re.sub(r'\n{3,}', '\n\n', msg)
    return msg.strip()


def _apply_name_fallback_wa(msg, nombre):
    """Si el nombre está vacío o malformado, usa fallback para WA."""
    if not nombre or nombre == "Sin nombre" or pd.isna(nombre):
        msg = re.sub(r'Hola [^,]*,', 'Hola,', msg, count=1)
    return msg


def _apply_name_fallback_mail(msg, nombre):
    """Si el nombre está vacío o malformado, usa fallback para Mail."""
    if not nombre or nombre == "Sin nombre" or pd.isna(nombre):
        msg = msg.replace(f"Estimado/a {nombre}:", "Estimado/a cliente:", 1)
        msg = msg.replace("Estimado/a Sin nombre:", "Estimado/a cliente:", 1)
        msg = msg.replace("Estimado/a :", "Estimado/a cliente:", 1)
    return msg


def get_message_wa(row, operador="", sucursal=""):
    """Genera un mensaje de WhatsApp personalizado para un registro."""
    urgencia = row.get("_urgencia_code", "sin_fecha")
    templates = TEMPLATES_WA.get(urgencia, TEMPLATES_WA["sin_fecha"])
    template = random.choice(templates)

    nombre = row.get("_nombre", "")
    tipo = row.get("_tipo_tarjeta", "tarjeta")
    fecha = _format_fecha(row.get("_fecha_recepcion"))
    dias = row.get("_dias_guarda", "")
    if pd.notna(dias) and dias != "":
        dias = str(int(dias))

    beneficio = _get_beneficio(tipo)

    msg = template.format(
        nombre=nombre,
        tipo=tipo.lower() if tipo else "tarjeta",
        fecha=fecha,
        dias=dias,
        operador=operador or "un operador",
        sucursal=sucursal or "nuestra sucursal",
        beneficio=beneficio,
    )

    msg = _apply_name_fallback_wa(msg, nombre)
    msg = _clean_message(msg)

    return msg


def get_message_mail(row, operador="", sucursal=""):
    """Genera asunto y cuerpo de mail para un registro."""
    urgencia = row.get("_urgencia_code", "sin_fecha")

    # Asunto
    subjects = SUBJECTS_MAIL.get(urgencia, SUBJECTS_MAIL["sin_fecha"])
    subject_template = random.choice(subjects)

    # Cuerpo
    templates = TEMPLATES_MAIL.get(urgencia, TEMPLATES_MAIL["sin_fecha"])
    body_template = random.choice(templates)

    nombre = row.get("_nombre", "")
    tipo = row.get("_tipo_tarjeta", "tarjeta")
    fecha = _format_fecha(row.get("_fecha_recepcion"))
    dias = row.get("_dias_guarda", "")
    if pd.notna(dias) and dias != "":
        dias = str(int(dias))

    beneficio = _get_beneficio(tipo)

    fmt_args = dict(
        nombre=nombre,
        tipo=tipo.lower() if tipo else "tarjeta",
        fecha=fecha,
        dias=dias,
        operador=operador or "un operador",
        sucursal=sucursal or "nuestra sucursal",
        beneficio=beneficio,
    )

    subject = subject_template.format(**fmt_args)
    body = body_template.format(**fmt_args)

    body = _apply_name_fallback_mail(body, nombre)
    body = _clean_message(body)

    return subject, body


def get_wa_url(phone, message):
    """Genera URL de WhatsApp Web con número y mensaje precargado."""
    if not phone:
        return None
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{phone}?text={encoded}"


def get_wa_app_url(phone, message):
    """Genera URL con protocolo whatsapp:// que abre WhatsApp común (no Business)."""
    if not phone:
        return None
    encoded = urllib.parse.quote(message)
    return f"https://api.whatsapp.com/send?phone={phone}&text={encoded}"


def get_mailto_url(email, subject, body):
    """Genera URL mailto con asunto y cuerpo precargado."""
    if not email:
        return None
    params = urllib.parse.urlencode({"subject": subject, "body": body}, quote_via=urllib.parse.quote)
    return f"mailto:{email}?{params}"
