"""Cálculo de tasa de entrega mensual y proyecciones."""


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
