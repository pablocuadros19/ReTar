"""Genera un Excel de ejemplo simulando exportación de TAR con datos ficticios."""

import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

# Datos ficticios
NOMBRES = [
    "García López, María Elena", "Rodríguez Pérez, Juan Carlos", "Martínez Sosa, Ana Laura",
    "Fernández Díaz, Roberto Miguel", "González Ruiz, Carolina Beatriz",
    "López Herrera, Diego Martín", "Sánchez Torres, Lucía Soledad",
    "Ramírez Castro, Pablo Alejandro", "Díaz Morales, Valentina",
    "Torres Giménez, Fernando Ariel", "Romero Acosta, Camila Belén",
    "Álvarez Medina, Sergio Daniel", "Moreno Ríos, Florencia Giselle",
    "Gómez Varela, Martín Eduardo", "Benítez Luna, Sofía Macarena",
    "Acosta Pereyra, Nicolás Hernán", "Medina Correa, Paula Andrea",
    "Herrera Molina, Facundo Ezequiel", "Pereyra Domínguez, Julieta",
    "Castro Figueroa, Leandro José", "Ríos Navarro, Daniela Alejandra",
    "Domínguez Paz, Gustavo Adrián", "Molina Suárez, Rocío Mailen",
    "Figueroa Bravo, Matías Gonzalo", "Suárez Ojeda, Marta Susana",
    "Correa Silva, Agustín Ramiro", "Luna Vega, Celeste Yamila",
    "Navarro Rojas, Ignacio Tomás", "Paz Aguirre, Andrea Cecilia",
    "Bravo Ortiz, Maximiliano", "Ojeda Mansilla, Natalia Eugenia",
    "Vega Quiroga, Santiago Iván", "Aguirre Ledesma, Milagros Sol",
    "Quiroga Bustos, Oscar Rubén", "Mansilla Cabrera, Lorena Patricia",
]

ESTADOS = [
    "EN SUCURSAL", "EN SUCURSAL", "EN SUCURSAL", "EN SUCURSAL",
    "EN SUCURSAL", "PENDIENTE RETIRO", "PENDIENTE RETIRO",
    "EN SUCURSAL - RECLAMADA", "DISPONIBLE",
]

TIPOS = ["DEBITO", "DEBITO", "CREDITO", "CREDITO", "CREDITO VISA", "DEBITO MAESTRO",
         "CREDITO VISA PLATINUM", "CREDITO MASTERCARD"]

# Generar datos
rows = []
today = datetime.now().date()

for i, nombre in enumerate(NOMBRES):
    dni = f"{random.randint(20, 45)}{random.randint(100, 999)}{random.randint(100, 999)}"

    # Número de tarjeta enmascarado (solo últimos 4 visibles)
    tarjeta = f"XXXX-XXXX-XXXX-{random.randint(1000, 9999)}"

    tipo = random.choice(TIPOS)
    estado = random.choice(ESTADOS)

    # Fecha de llegada: entre hoy y 75 días atrás
    dias_atras = random.choices(
        [random.randint(0, 10), random.randint(11, 30),
         random.randint(31, 45), random.randint(46, 75)],
        weights=[25, 35, 25, 15],
    )[0]
    fecha = (today - timedelta(days=dias_atras)).strftime("%d/%m/%Y")

    # Teléfono: ~70% tienen, en distintos formatos argentinos
    telefono = ""
    if random.random() < 0.70:
        area = random.choice(["11", "11", "11", "2204", "2241", "114"])
        numero = f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        formato = random.choice([
            f"011-15-{numero}",
            f"15-{numero}",
            f"{area}{numero.replace('-', '')}",
            f"+54 9 {area} {numero}",
            f"({area}) {numero}",
        ])
        telefono = formato

    # Mail: ~50% tienen
    mail = ""
    if random.random() < 0.50:
        nombre_parts = nombre.lower().split(",")[0].replace("á", "a").replace("é", "e") \
            .replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        nombre_mail = nombre_parts.strip().replace(" ", ".")
        dominio = random.choice(["gmail.com", "hotmail.com", "yahoo.com.ar",
                                 "outlook.com", "live.com.ar"])
        mail = f"{nombre_mail}{random.randint(1, 99)}@{dominio}"

    rows.append({
        "NRO_TARJETA": tarjeta,
        "NOMBRE_COMPLETO": nombre,
        "NRO_DOCUMENTO": dni,
        "ESTADO_PLASTICO": estado,
        "TIPO_TARJETA": tipo,
        "EMAIL": mail if mail else None,
        "TELEFONO": telefono if telefono else None,
        "FECHA_RECEPCION_SUC": fecha,
    })

# Agregar algunos casos especiales
# Persona con 2 tarjetas
rows.append({
    "NRO_TARJETA": "XXXX-XXXX-XXXX-7777",
    "NOMBRE_COMPLETO": "García López, María Elena",
    "NRO_DOCUMENTO": rows[0]["NRO_DOCUMENTO"],
    "ESTADO_PLASTICO": "EN SUCURSAL",
    "TIPO_TARJETA": "CREDITO VISA",
    "EMAIL": rows[0]["EMAIL"],
    "TELEFONO": rows[0]["TELEFONO"],
    "FECHA_RECEPCION_SUC": (today - timedelta(days=5)).strftime("%d/%m/%Y"),
})

# Persona sin ningún dato de contacto
rows.append({
    "NRO_TARJETA": "XXXX-XXXX-XXXX-0001",
    "NOMBRE_COMPLETO": "Pérez Gómez, Ricardo Alberto",
    "NRO_DOCUMENTO": "28456123",
    "ESTADO_PLASTICO": "EN SUCURSAL",
    "TIPO_TARJETA": "DEBITO",
    "EMAIL": None,
    "TELEFONO": None,
    "FECHA_RECEPCION_SUC": (today - timedelta(days=52)).strftime("%d/%m/%Y"),
})

df = pd.DataFrame(rows)
output_path = "data/ejemplo_tar.xlsx"
df.to_excel(output_path, index=False, engine="openpyxl")
print(f"Generado: {output_path} con {len(df)} registros")
print(f"\nColumnas: {list(df.columns)}")
print(f"\nPreview:")
print(df.head(10).to_string(index=False))
print(f"\n--- Stats ---")
print(f"Con telefono: {df['TELEFONO'].notna().sum()}")
print(f"Con email: {df['EMAIL'].notna().sum()}")
print(f"Sin contacto: {((df['TELEFONO'].isna()) & (df['EMAIL'].isna())).sum()}")
print(f"Tipos: {df['TIPO_TARJETA'].value_counts().to_dict()}")
