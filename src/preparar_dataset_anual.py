from pathlib import Path

import pandas as pd


# ============================================================
# RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RUTA_ENTRADA = BASE_DIR / "data" / "dataset_ml.csv"
RUTA_MENSUAL = BASE_DIR / "data" / "dataset_mensual.csv"
RUTA_ANUAL = BASE_DIR / "data" / "dataset_anual.csv"


# ============================================================
# VARIABLES
# ============================================================

VARIABLES_AMBIENTALES = [
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "ALLSKY_SFC_SW_DWN",
    "CLRSKY_SFC_SW_DWN",
    "ALLSKY_KT",
    "WS10M",
    "WD10M",
    "PRECTOTCORR",
]

VARIABLE_OBJETIVO = "UV_INDEX"


# ============================================================
# VALIDACIONES DE ENTRADA
# ============================================================

if not RUTA_ENTRADA.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo requerido: {RUTA_ENTRADA}"
    )

df = pd.read_csv(RUTA_ENTRADA)

columnas_requeridas = {
    "FECHA",
    "YEAR",
    "MO",
    *VARIABLES_AMBIENTALES,
    VARIABLE_OBJETIVO,
}

faltantes = columnas_requeridas.difference(df.columns)

if faltantes:
    raise ValueError(
        "Faltan columnas requeridas en dataset_ml.csv: "
        + ", ".join(sorted(faltantes))
    )

df["FECHA"] = pd.to_datetime(
    df["FECHA"],
    errors="coerce"
)

if df["FECHA"].isna().any():
    raise ValueError(
        "Se encontraron fechas inválidas en dataset_ml.csv."
    )

if df["FECHA"].duplicated().any():
    raise ValueError(
        "Se encontraron fechas duplicadas en dataset_ml.csv."
    )


# ============================================================
# INFORMACIÓN GENERAL
# ============================================================

print("=" * 72)
print("PREPARACIÓN DE DATASETS MENSUAL Y ANUAL")
print("=" * 72)

print(f"\nRegistros diarios disponibles: {len(df)}")

print(
    "Periodo:",
    df["FECHA"].min().date(),
    "a",
    df["FECHA"].max().date()
)


# ============================================================
# DATASET MENSUAL
# ============================================================

columnas_promedio = [
    *VARIABLES_AMBIENTALES,
    VARIABLE_OBJETIVO,
]

mensual = (
    df
    .groupby(
        ["YEAR", "MO"],
        as_index=False
    )[columnas_promedio]
    .mean()
)

conteo_mensual = (
    df
    .groupby(
        ["YEAR", "MO"]
    )
    .size()
    .reset_index(
        name="N_DIAS"
    )
)

mensual = mensual.merge(
    conteo_mensual,
    on=["YEAR", "MO"],
    how="left"
)

mensual["FECHA"] = pd.to_datetime(
    dict(
        year=mensual["YEAR"],
        month=mensual["MO"],
        day=1
    )
)

mensual = mensual[
    [
        "FECHA",
        "YEAR",
        "MO",
        "N_DIAS",
        *VARIABLES_AMBIENTALES,
        "UV_INDEX",
    ]
]

mensual.to_csv(
    RUTA_MENSUAL,
    index=False
)


# ============================================================
# DATASET ANUAL
# ============================================================

# El promedio anual se calcula directamente sobre los registros
# diarios disponibles. Esto evita dar el mismo peso a meses con
# distinta cantidad de observaciones válidas.

anual = (
    df
    .groupby(
        "YEAR",
        as_index=False
    )[columnas_promedio]
    .mean()
)

conteo_anual = (
    df
    .groupby("YEAR")
    .size()
    .reset_index(
        name="N_DIAS"
    )
)

anual = anual.merge(
    conteo_anual,
    on="YEAR",
    how="left"
)


# ============================================================
# CLASIFICACIÓN BINARIA ANUAL
# ============================================================

# Criterio operacional conservado del proyecto:
# BAJO = promedio anual UVI < 6
# ALTO = promedio anual UVI >= 6
#
# Este script NO entrena todavía un modelo. Primero comprueba si
# el dataset anual realmente contiene ambas clases.

anual["CLASE_UV"] = (
    anual["UV_INDEX"] >= 6
).astype(int)

anual["CATEGORIA_UV"] = anual[
    "CLASE_UV"
].map(
    {
        0: "BAJO",
        1: "ALTO",
    }
)

anual = anual[
    [
        "YEAR",
        "N_DIAS",
        *VARIABLES_AMBIENTALES,
        "UV_INDEX",
        "CLASE_UV",
        "CATEGORIA_UV",
    ]
]

anual.to_csv(
    RUTA_ANUAL,
    index=False
)


# ============================================================
# RESULTADOS MENSUALES
# ============================================================

print("\n" + "=" * 72)
print("DATASET MENSUAL")
print("=" * 72)

print(
    "Registros mensuales:",
    len(mensual)
)

print("\nMeses con menor cantidad de observaciones:")

print(
    mensual[
        [
            "YEAR",
            "MO",
            "N_DIAS",
            "UV_INDEX",
        ]
    ]
    .sort_values(
        ["N_DIAS", "YEAR", "MO"]
    )
    .head(15)
    .to_string(
        index=False,
        formatters={
            "UV_INDEX": lambda x: f"{x:.4f}"
        }
    )
)


# ============================================================
# RESULTADOS ANUALES
# ============================================================

print("\n" + "=" * 72)
print("DATASET ANUAL")
print("=" * 72)

print(
    "Años disponibles:",
    len(anual)
)

print("\nPromedio UV por año:")

print(
    anual[
        [
            "YEAR",
            "N_DIAS",
            "UV_INDEX",
            "CATEGORIA_UV",
        ]
    ]
    .to_string(
        index=False,
        formatters={
            "UV_INDEX": lambda x: f"{x:.4f}"
        }
    )
)


# ============================================================
# DISTRIBUCIÓN DE CLASES
# ============================================================

print("\n" + "=" * 72)
print("DISTRIBUCIÓN DE CLASES ANUALES")
print("=" * 72)

conteo_clases = (
    anual["CATEGORIA_UV"]
    .value_counts()
)

for categoria in ["BAJO", "ALTO"]:
    cantidad = int(
        conteo_clases.get(
            categoria,
            0
        )
    )

    porcentaje = (
        cantidad /
        len(anual) *
        100
        if len(anual)
        else 0
    )

    print(
        f"{categoria}: "
        f"{cantidad} "
        f"({porcentaje:.2f} %)"
    )


# ============================================================
# RANGO UV ANUAL
# ============================================================

print("\n" + "=" * 72)
print("RANGO DEL UV PROMEDIO ANUAL")
print("=" * 72)

print(
    f"Mínimo: "
    f"{anual['UV_INDEX'].min():.4f}"
)

print(
    f"Máximo: "
    f"{anual['UV_INDEX'].max():.4f}"
)

print(
    f"Media de promedios anuales: "
    f"{anual['UV_INDEX'].mean():.4f}"
)


# ============================================================
# COBERTURA POR AÑO
# ============================================================

print("\n" + "=" * 72)
print("COBERTURA ANUAL")
print("=" * 72)

print(
    anual[
        [
            "YEAR",
            "N_DIAS",
        ]
    ]
    .to_string(
        index=False
    )
)


# ============================================================
# ARCHIVOS
# ============================================================

print("\n" + "=" * 72)
print("ARCHIVOS GENERADOS")
print("=" * 72)

print(RUTA_MENSUAL)
print(RUTA_ANUAL)


# ============================================================
# CONCLUSIÓN AUTOMÁTICA
# ============================================================

print("\n" + "=" * 72)
print("CONCLUSIÓN")
print("=" * 72)

if anual["CLASE_UV"].nunique() < 2:

    unica_clase = anual[
        "CATEGORIA_UV"
    ].iloc[0]

    print(
        f"El dataset anual contiene una sola clase: {unica_clase}."
    )

    print(
        "Con esta cobertura geográfica NO se puede entrenar "
        "una regresión logística binaria anual válida."
    )

    print(
        "El siguiente paso será ampliar la cobertura geográfica "
        "antes de construir el modelo anual final."
    )

else:

    print(
        "El dataset anual contiene las dos clases BAJO y ALTO."
    )

    print(
        "Aun así, no se entrenará el modelo final hasta revisar "
        "la distribución de clases y la cobertura geográfica."
    )
