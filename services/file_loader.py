"""Carga y parseo de archivos Excel/CSV exportados desde TAR."""

import pandas as pd

# Mapeo de nombres internos a patrones comunes en columnas del Excel
COLUMN_PATTERNS = {
    "nombre": ["cliente", "nombre_completo", "nombre", "titular", "denominacion", "razon_social"],
    "documento": ["nro. documento", "nro_documento", "nro documento", "documento", "dni", "cuil",
                   "cuit", "nro_doc", "nrodoc"],
    "telefono": ["teléfono", "telefono", "tel", "celular", "movil", "phone", "whatsapp"],
    "mail": ["email", "mail", "correo", "e-mail", "e_mail"],
    "tipo_tarjeta": ["tipo", "tipo_tarjeta", "tipo tarjeta", "producto"],
    "fecha_recepcion": ["fecha", "fecha_recepcion", "fecha recepcion", "fec_recep", "recepcion",
                        "ingreso", "fecha_ingreso", "fecha ingreso"],
    "numero_tarjeta": ["nro. tarjeta", "nro_tarjeta", "nro tarjeta", "nrotarjeta",
                       "numero_tarjeta", "numero tarjeta", "pan"],
    "estado": ["estado", "estado_plastico", "situacion", "status"],
}

# Columnas requeridas vs opcionales
REQUIRED_COLUMNS = ["nombre"]
OPTIONAL_COLUMNS = ["documento", "telefono", "mail", "tipo_tarjeta",
                    "fecha_recepcion", "numero_tarjeta", "estado"]


def load_file(uploaded_file):
    """Carga un archivo Excel o CSV y devuelve un DataFrame.

    Detecta automáticamente si las primeras filas son título/vacías
    y las omite para encontrar los headers reales.
    """
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".xlsx") or name.endswith(".xls"):
            df = _load_excel_smart(uploaded_file)
        elif name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, encoding="utf-8", sep=None, engine="python")
        else:
            raise ValueError(f"Formato no soportado: {name}")

        # Limpiar nombres de columna — asegurar que todos sean strings
        df.columns = [
            str(c).strip() if (c is not None and str(c) not in ("nan", "None", ""))
            else f"_col_{i}"
            for i, c in enumerate(df.columns)
        ]

        # Eliminar filas completamente vacías
        df = df.dropna(how="all").reset_index(drop=True)

        return df
    except Exception as e:
        raise ValueError(f"Error al leer el archivo: {e}")


def _load_excel_smart(uploaded_file):
    """Carga Excel detectando automáticamente la fila de headers.

    El Excel de TAR tiene:
    - Fila 1: "Detalle de Plásticos" (título)
    - Fila 2: vacía
    - Fila 3: headers reales
    - Fila 4+: datos

    Esta función detecta eso automáticamente.
    """
    # Intentar leer las primeras filas sin header para analizar
    df_raw = pd.read_excel(uploaded_file, engine="openpyxl", header=None, nrows=10)

    # Buscar la fila que tiene los headers reales
    header_row = _find_header_row(df_raw)

    # Volver al inicio del archivo
    uploaded_file.seek(0)

    # Leer con el header correcto
    df = pd.read_excel(uploaded_file, engine="openpyxl", header=header_row)

    return df


def _find_header_row(df_raw):
    """Detecta en qué fila están los headers reales.

    Busca la fila que tenga más coincidencias con nombres de columna conocidos.
    """
    # Palabras clave que indican que es una fila de headers
    keywords = set()
    for patterns in COLUMN_PATTERNS.values():
        for p in patterns:
            keywords.add(p.lower())

    best_row = 0
    best_score = 0

    for i in range(min(5, len(df_raw))):
        row_values = df_raw.iloc[i].astype(str).str.lower().str.strip()
        score = 0
        for val in row_values:
            if val in ("nan", "", "none"):
                continue
            for kw in keywords:
                if kw in val or val in kw:
                    score += 1
                    break
        if score > best_score:
            best_score = score
            best_row = i

    return best_row


def detect_columns(df):
    """Intenta detectar automáticamente qué columna del Excel corresponde a cada campo interno."""
    column_map = {}
    used_cols = set()

    def normalize(s):
        return str(s).lower().strip().replace(" ", "_").replace(".", "")

    # Dos pasadas: primero matches exactos, después parciales
    for exact_only in [True, False]:
        for internal_name, patterns in COLUMN_PATTERNS.items():
            if internal_name in column_map:
                continue
            best_match = None
            for col in df.columns:
                if col in used_cols:
                    continue
                col_norm = normalize(col)
                for pattern in patterns:
                    pattern_norm = normalize(pattern)
                    if exact_only and pattern_norm == col_norm:
                        best_match = col
                        break
                    elif not exact_only and (pattern_norm in col_norm or col_norm in pattern_norm):
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
