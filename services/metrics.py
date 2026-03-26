"""Cálculo de tasa de entrega mensual, proyecciones y objetivo diario."""

from datetime import date, timedelta


def calc_tasa_entrega(stock_inicial, ingresos, entregadas, derivadas):
    """Calcula la tasa de entrega mensual.

    tasa = (entregadas + derivadas) / (stock_inicial + ingresos)
    """
    denominador = stock_inicial + ingresos
    if denominador == 0:
        return 0.0
    return (entregadas + derivadas) / denominador


def calc_gap_40(stock_inicial, ingresos, entregadas, derivadas):
    """Calcula cuántas entregas faltan para llegar al 40%."""
    denominador = stock_inicial + ingresos
    if denominador == 0:
        return {"tasa_actual": 0, "objetivo": 0.40, "faltan": 0, "alcanzado": True}

    tasa_actual = (entregadas + derivadas) / denominador
    objetivo_unidades = int(denominador * 0.40)
    actual_unidades = entregadas + derivadas
    faltan = max(0, objetivo_unidades - actual_unidades)

    return {
        "tasa_actual": round(tasa_actual * 100, 1),
        "objetivo_pct": 40.0,
        "actual_unidades": actual_unidades,
        "objetivo_unidades": objetivo_unidades,
        "denominador": denominador,
        "faltan": faltan,
        "alcanzado": faltan == 0,
    }


def get_diagnostico(gap_info, depuradas=0):
    """Genera diagnóstico textual del estado de la sucursal."""
    tasa = gap_info["tasa_actual"]
    faltan = gap_info["faltan"]

    if gap_info["alcanzado"]:
        return (
            f"La sucursal alcanzó el objetivo con una tasa del {tasa}%. "
            "Mantener el ritmo de contacto para sostener el indicador."
        )

    mensaje = f"Tasa actual: {tasa}%. "

    if tasa < 20:
        mensaje += f"Estamos lejos del objetivo. Faltan {faltan} entregas/derivaciones para llegar al 40%. "
        mensaje += "Priorizar contacto masivo sobre contactables directos."
    elif tasa < 30:
        mensaje += f"Faltan {faltan} entregas/derivaciones. "
        mensaje += "Intensificar el contacto, especialmente en tarjetas con más antigüedad."
    elif tasa < 40:
        mensaje += f"Cerca del objetivo. Faltan solo {faltan} entregas/derivaciones. "
        mensaje += "Focalizar en casos con mayor probabilidad de retiro."

    if depuradas > 0:
        mensaje += (
            f"\n\nNota: se depuraron {depuradas} tarjetas. Las depuraciones no mejoran el ratio "
            "de la misma forma, pero evitan arrastrar stock inflado."
        )

    return mensaje


def calcular_dias_habiles_restantes(fecha_hoy=None):
    """Calcula los días hábiles (lun-vie) restantes en el mes."""
    if fecha_hoy is None:
        fecha_hoy = date.today()

    # Último día del mes
    if fecha_hoy.month == 12:
        ultimo_dia = date(fecha_hoy.year + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia = date(fecha_hoy.year, fecha_hoy.month + 1, 1) - timedelta(days=1)

    dias_habiles = 0
    dia = fecha_hoy + timedelta(days=1)  # desde mañana
    while dia <= ultimo_dia:
        if dia.weekday() < 5:  # lun=0 a vie=4
            dias_habiles += 1
        dia += timedelta(days=1)

    # Contar hoy si es hábil
    if fecha_hoy.weekday() < 5:
        dias_habiles += 1

    return max(dias_habiles, 1)  # mínimo 1 para evitar división por cero


def calcular_objetivo_diario(stock_inicial, ingresos, entregadas, derivadas, tasa_deseada=0.40):
    """Calcula cuántas entregas por día hábil se necesitan para alcanzar la tasa deseada.

    Returns:
        dict con entregas_necesarias, dias_habiles_restantes, objetivo_diario, alcanzado
    """
    universo = stock_inicial + ingresos
    if universo == 0:
        return {
            "entregas_necesarias": 0,
            "dias_habiles_restantes": 0,
            "objetivo_diario": 0,
            "alcanzado": True,
            "tasa_actual_pct": 0,
            "tasa_deseada_pct": round(tasa_deseada * 100, 1),
        }

    positivas_actuales = entregadas + derivadas
    objetivo_total = int(universo * tasa_deseada)
    entregas_necesarias = max(0, objetivo_total - positivas_actuales)
    dias_habiles = calcular_dias_habiles_restantes()
    objetivo_diario = round(entregas_necesarias / dias_habiles, 1) if dias_habiles > 0 else 0
    tasa_actual = round((positivas_actuales / universo) * 100, 1)

    return {
        "entregas_necesarias": entregas_necesarias,
        "dias_habiles_restantes": dias_habiles,
        "objetivo_diario": objetivo_diario,
        "alcanzado": entregas_necesarias == 0,
        "tasa_actual_pct": tasa_actual,
        "tasa_deseada_pct": round(tasa_deseada * 100, 1),
        "universo": universo,
    }
