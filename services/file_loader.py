"""Carga y parseo de archivos Excel/CSV exportados desde TAR."""

import pandas as pd
import streamlit as st
from pathlib import Path

# Mapeo de nombres internos a patrones comunes en columnas del Excel
COLUMN_PATTERNS = {
    "nombre": ["nombre_completo", "nombre", "cliente", "titular", "denominacion", "razon_social"],
    "documento": ["nro_documento", "documento", "dni", "cuil", "cuit", "nro_doc", "nrodoc"],
    "telefono": ["telefono", "tel", "celular", "movil", "phone", "whatsapp"],
    "mail": ["email", "mail", "correo", "e-mail", "e_mail"],
    "tipo_tarjeta": ["tipo_tarjeta", "tipo tarjeta", "producto"],
    "fecha_recepcion": ["fecha_recepcion", "fecha recepcion", "fec_recep", "recepcion",
                        "ingreso", "fecha_ingreso", "fecha ingreso"],
    "numero_tarjeta": ["nro_tarjeta", "nrotarjeta", "numero_tarjeta", "numero tarjeta",
                       "nro tarjeta", "pan"],
    "estado": ["estado_plastico", "estado", "situacion", "status"],
}

# Columnas requeridas vs opcionales
REQUIRED_COLUMNS = ["nombre"]
OPTIONAL_COLUMNS = ["documento", "telefono", "mail", "tipo_tarjeta",
                    "fecha_recepcion", "numero_tarjeta", "estado"]


def load_file(uploaded_file):
    """Carga un archivo Excel o CSV y devuelve un DataFrame."""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".xlsx") or name.endswith(".xls"):
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        elif name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, encoding="utf-8", sep=None, engine="python")
        else:
            raise ValueError(f"Formato no soportado: {name}")

        # Limpiar nombres de columna
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        raise ValueError(f"Error al leer el archivo: {e}")


def detect_columns(df):
    """Intenta detectar automáticamente qué columna del Excel corresponde a cada campo interno."""
    column_map = {}
    used_cols = set()
    df_cols_lower = {col: col.lower().strip().replace(" ", "_") for col in df.columns}

    # Dos pasadas: primero matches exactos, después parciales
    for exact_only in [True, False]:
        for internal_name, patterns in COLUMN_PATTERNS.items():
            if internal_name in column_map:
                continue
            best_match = None
            for col, col_lower in df_cols_lower.items():
                if col in used_cols:
                    continue
                for pattern in patterns:
                    pattern_norm = pattern.lower().replace(" ", "_")
                    if exact_only and pattern_norm == col_lower:
                        best_match = col
                        break
                    elif not exact_only and pattern_norm in col_lower:
                        best_match = col
                        break
                if best_match:
                    break
            if best_match:
                column_map[internal_name] = best_match
                used_cols.add(best_match)

    return column_map


def validate_data(df, column_map):
    """Valida los datos cargados y devuelve lista de advertencias."""
    warnings = []

    if df.empty:
        warnings.append("El archivo está vacío.")
        return warnings

    if len(df) < 1:
        warnings.append("El archivo no tiene registros.")

    # Verificar columnas requeridas
    for req in REQUIRED_COLUMNS:
        if req not in column_map:
            warnings.append(f"No se detectó la columna '{req}'. Revisá el mapeo.")

    # Info sobre columnas opcionales faltantes
    for opt in OPTIONAL_COLUMNS:
        if opt not in column_map:
            warnings.append(f"Columna opcional '{opt}' no detectada — funcionalidad limitada.")

    # Verificar nulos en columnas clave
    for internal, actual in column_map.items():
        if internal in REQUIRED_COLUMNS:
            nulls = df[actual].isna().sum()
            if nulls > 0:
                warnings.append(f"'{actual}' tiene {nulls} valores vacíos.")

    return warnings


def get_available_columns(df):
    """Devuelve lista de columnas disponibles en el DataFrame."""
    return list(df.columns)
