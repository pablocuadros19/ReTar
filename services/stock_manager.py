"""Gestión de stock persistente y reconciliación diaria."""

import json
import pandas as pd
from pathlib import Path
from datetime import date
from services.contact_history import cargar_historial

STOCK_PATH = Path("data/stock.json")
MOVIMIENTOS_PATH = Path("data/movimientos.json")


def cargar_stock():
    """Carga el stock desde disco. Devuelve None si no existe."""
    if not STOCK_PATH.exists():
        return None
    try:
        return json.loads(STOCK_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def guardar_stock(stock):
    """Guarda el stock a disco."""
    STOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    STOCK_PATH.write_text(
        json.dumps(stock, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def crear_stock_inicial(df):
    """Crea el stock inicial a partir del primer Excel cargado.

    Args:
        df: DataFrame ya normalizado y clasificado (con columnas _*)
    Returns:
        dict con la estructura de stock completa
    """
    tarjetas = {}
    for _, row in df.iterrows():
        nro = str(row.get("_numero_tarjeta", ""))
        if not nro or nro == "nan":
            continue
        tarjetas[nro] = _row_to_tarjeta(row)

    stock = {
        "fecha_ultima_carga": date.today().isoformat(),
        "mes_actual": date.today().strftime("%Y-%m"),
        "metricas_mes": {
            "stock_inicial": len(tarjetas),
            "ingresos": 0,
            "entregadas": 0,
            "derivadas": 0,
            "depuradas": 0,
            "contactadas_entregadas": 0,
        },
        "tarjetas": tarjetas,
    }

    guardar_stock(stock)
    _registrar_movimiento(
        ingresaron=len(tarjetas),
        desaparecieron=0,
        entregadas=0,
        depuradas=0,
        derivadas=0,
        stock_al_cierre=len(tarjetas),
        es_primera_carga=True,
    )

    return stock


def reconciliar(df_nuevo, stock_anterior):
    """Compara el Excel nuevo con el stock anterior.

    Args:
        df_nuevo: DataFrame normalizado del Excel de hoy
        stock_anterior: dict del stock guardado

    Returns:
        dict con:
            nuevas: list de nro_tarjeta que no estaban
            desaparecidas: list de nro_tarjeta que ya no están
            desaparecidas_contactadas: list de nro_tarjeta que fueron contactadas y desaparecieron
            actualizadas: int de tarjetas que se actualizaron
    """
    tarjetas_ant = stock_anterior.get("tarjetas", {})

    # Nros de tarjeta en el Excel nuevo
    nros_nuevos = set()
    for _, row in df_nuevo.iterrows():
        nro = str(row.get("_numero_tarjeta", ""))
        if nro and nro != "nan":
            nros_nuevos.add(nro)

    nros_anteriores = set(tarjetas_ant.keys())

    nuevas = list(nros_nuevos - nros_anteriores)
    desaparecidas = list(nros_anteriores - nros_nuevos)
    actualizadas = len(nros_nuevos & nros_anteriores)

    # Verificar cuáles de las desaparecidas fueron contactadas
    historial = cargar_historial()
    desaparecidas_contactadas = []
    for nro in desaparecidas:
        tarjeta = tarjetas_ant.get(nro, {})
        doc = tarjeta.get("documento", "")
        contactos = historial.get(str(doc), {}).get("contactos", [])
        if contactos:
            desaparecidas_contactadas.append(nro)

    return {
        "nuevas": nuevas,
        "desaparecidas": desaparecidas,
        "desaparecidas_contactadas": desaparecidas_contactadas,
        "actualizadas": actualizadas,
    }


def aplicar_reconciliacion(stock, df_nuevo, resultado, depuradas=0, derivadas=0):
    """Aplica la reconciliación al stock.

    Args:
        stock: stock anterior
        df_nuevo: DataFrame normalizado del Excel nuevo
        resultado: dict de reconciliar()
        depuradas: cantidad indicada por el usuario
        derivadas: cantidad indicada por el usuario

    Returns:
        stock actualizado
    """
    tarjetas = stock.get("tarjetas", {})
    metricas = stock.get("metricas_mes", {})

    total_desaparecidas = len(resultado["desaparecidas"])
    entregadas = max(0, total_desaparecidas - depuradas - derivadas)
    # Conversiones: contactadas que desaparecieron, limitadas a las efectivamente entregadas
    # (no podemos saber cuáles de las contactadas fueron depuradas/derivadas sin discriminar una a una)
    contactadas_entregadas = min(len(resultado["desaparecidas_contactadas"]), entregadas)

    # Actualizar métricas del mes
    metricas["ingresos"] = metricas.get("ingresos", 0) + len(resultado["nuevas"])
    metricas["entregadas"] = metricas.get("entregadas", 0) + entregadas
    metricas["derivadas"] = metricas.get("derivadas", 0) + derivadas
    metricas["depuradas"] = metricas.get("depuradas", 0) + depuradas
    metricas["contactadas_entregadas"] = metricas.get("contactadas_entregadas", 0) + contactadas_entregadas

    # Remover desaparecidas del stock
    for nro in resultado["desaparecidas"]:
        tarjetas.pop(nro, None)

    # Actualizar tarjetas existentes (mantener estado_gestion)
    for _, row in df_nuevo.iterrows():
        nro = str(row.get("_numero_tarjeta", ""))
        if not nro or nro == "nan":
            continue

        if nro in tarjetas:
            # Mantener estado_gestion y fecha_primera_carga
            estado = tarjetas[nro].get("estado_gestion", "pendiente")
            fecha_primera = tarjetas[nro].get("fecha_primera_carga")
            tarjetas[nro] = _row_to_tarjeta(row)
            tarjetas[nro]["estado_gestion"] = estado
            if fecha_primera:
                tarjetas[nro]["fecha_primera_carga"] = fecha_primera
        else:
            # Nueva tarjeta
            tarjetas[nro] = _row_to_tarjeta(row)

    stock["tarjetas"] = tarjetas
    stock["metricas_mes"] = metricas
    stock["fecha_ultima_carga"] = date.today().isoformat()

    guardar_stock(stock)

    # Registrar movimiento
    _registrar_movimiento(
        ingresaron=len(resultado["nuevas"]),
        desaparecieron=total_desaparecidas,
        entregadas=entregadas,
        depuradas=depuradas,
        derivadas=derivadas,
        stock_al_cierre=len(tarjetas),
    )

    return stock


def detectar_nuevo_mes(stock):
    """Verifica si cambió el mes respecto al stock guardado."""
    if stock is None:
        return False
    mes_stock = stock.get("mes_actual", "")
    mes_actual = date.today().strftime("%Y-%m")
    return mes_stock != mes_actual


def resetear_mes(stock):
    """Resetea las métricas mensuales. stock_inicial = tarjetas actuales."""
    stock["mes_actual"] = date.today().strftime("%Y-%m")
    stock["metricas_mes"] = {
        "stock_inicial": len(stock.get("tarjetas", {})),
        "ingresos": 0,
        "entregadas": 0,
        "derivadas": 0,
        "depuradas": 0,
        "contactadas_entregadas": 0,
    }
    guardar_stock(stock)
    return stock


def restaurar_estados(df, stock):
    """Restaura los estados de gestión del stock en el DataFrame.

    Returns:
        dict {df_index: estado} para session_state.estados
    """
    tarjetas = stock.get("tarjetas", {})
    estados = {}
    for idx, row in df.iterrows():
        nro = str(row.get("_numero_tarjeta", ""))
        if nro in tarjetas:
            estados[idx] = tarjetas[nro].get("estado_gestion", "pendiente")
        else:
            estados[idx] = "pendiente"
    return estados


def actualizar_estado_tarjeta(nro_tarjeta, estado):
    """Actualiza el estado de gestión de una tarjeta en el stock persistido."""
    stock = cargar_stock()
    if stock and nro_tarjeta in stock.get("tarjetas", {}):
        stock["tarjetas"][nro_tarjeta]["estado_gestion"] = estado
        guardar_stock(stock)


def registrar_entregas_manuales(entregadas=0, derivadas=0, depuradas=0, ingresos=0):
    """Suma entregas/derivaciones/depuraciones/ingresos a las métricas del mes.

    Solo se ajustan los contadores — no se toca el stock de tarjetas.
    """
    stock = cargar_stock()
    if not stock:
        return
    metricas = stock.get("metricas_mes", {})
    metricas["entregadas"] = metricas.get("entregadas", 0) + entregadas
    metricas["derivadas"] = metricas.get("derivadas", 0) + derivadas
    metricas["depuradas"] = metricas.get("depuradas", 0) + depuradas
    metricas["ingresos"] = metricas.get("ingresos", 0) + ingresos
    stock["metricas_mes"] = metricas
    guardar_stock(stock)

    # Registrar como ajuste manual (sin movimiento de stock)
    _registrar_movimiento(
        ingresaron=ingresos,
        desaparecieron=0,
        entregadas=entregadas,
        depuradas=depuradas,
        derivadas=derivadas,
        stock_al_cierre=len(stock.get("tarjetas", {})),
        es_ajuste_manual=True,
    )


def cargar_movimientos():
    """Carga el log de movimientos diarios."""
    if not MOVIMIENTOS_PATH.exists():
        return []
    try:
        return json.loads(MOVIMIENTOS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _registrar_movimiento(ingresaron, desaparecieron, entregadas,
                          depuradas, derivadas, stock_al_cierre,
                          es_primera_carga=False, es_ajuste_manual=False):
    """Agrega un registro al log de movimientos."""
    movimientos = cargar_movimientos()
    registro = {
        "fecha": date.today().isoformat(),
        "ingresaron": ingresaron,
        "desaparecieron": desaparecieron,
        "entregadas": entregadas,
        "depuradas": depuradas,
        "derivadas": derivadas,
        "stock_al_cierre": stock_al_cierre,
    }
    if es_primera_carga:
        registro["primera_carga"] = True
    if es_ajuste_manual:
        registro["ajuste_manual"] = True
    movimientos.append(registro)
    MOVIMIENTOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    MOVIMIENTOS_PATH.write_text(
        json.dumps(movimientos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def reconstruir_df_desde_stock():
    """Reconstruye un DataFrame funcional desde el stock guardado en disco.

    Se usa cuando session_state.df se pierde (ej: F5, recarga de página).
    """
    import pandas as pd
    from services.classifier import classify_dataframe

    stock = cargar_stock()
    if not stock or not stock.get("tarjetas"):
        return None, None

    tarjetas = stock["tarjetas"]
    rows = []
    for nro, t in tarjetas.items():
        rows.append({
            "_numero_tarjeta": nro,
            "_nombre": t.get("nombre", ""),
            "_documento": t.get("documento", ""),
            "_tipo_tarjeta": t.get("tipo_tarjeta", ""),
            "_telefono_norm": t.get("telefono_norm") or None,
            "_mail_norm": t.get("mail_norm") or None,
            "_fecha_recepcion": t.get("fecha_recepcion", ""),
            "_dias_guarda": t.get("dias_guarda", 0),
            "_contactabilidad": t.get("contactabilidad", ""),
            "_estado_gestion": t.get("estado_gestion", "pendiente"),
            "_estado_original": t.get("estado_original", ""),
        })

    df = pd.DataFrame(rows)
    df = classify_dataframe(df)

    # Reconstruir estados
    estados = {i: row["_estado_gestion"] for i, row in df.iterrows()}

    return df, estados


def _safe_str(val, default=""):
    """Convierte a string de forma segura, devolviendo default si es None/NaN."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    s = str(val).strip()
    return default if s in ("nan", "None", "") else s


def _row_to_tarjeta(row):
    """Convierte una fila del DataFrame a dict de tarjeta para el stock."""
    return {
        "nombre": _safe_str(row.get("_nombre", "")),
        "documento": _safe_str(row.get("_documento", "")),
        "tipo_tarjeta": _safe_str(row.get("_tipo_tarjeta", "")),
        "telefono_norm": _safe_str(row.get("_telefono_norm")),
        "mail_norm": _safe_str(row.get("_mail_norm")),
        "fecha_recepcion": _safe_str(row.get("_fecha_recepcion", "")),
        "dias_guarda": int(row.get("_dias_guarda", 0)) if row.get("_dias_guarda") and not (isinstance(row.get("_dias_guarda"), float) and pd.isna(row.get("_dias_guarda"))) else 0,
        "contactabilidad": _safe_str(row.get("_contactabilidad", "")),
        "estado_gestion": _safe_str(row.get("_estado_gestion", "pendiente"), "pendiente"),
        "fecha_primera_carga": date.today().isoformat(),
    }
