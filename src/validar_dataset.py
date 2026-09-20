from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

RUTA = (
    BASE_DIR /
    "data" /
    "dataset_ml.csv"
)


df = pd.read_csv(RUTA)

df["FECHA"] = pd.to_datetime(
    df["FECHA"],
    errors="coerce"
)


print("=" * 70)
print("VALIDACIÓN GENERAL DEL DATASET")
print("=" * 70)


# ---------------------------------------------------------
# INFORMACIÓN GENERAL
# ---------------------------------------------------------

print("\nRegistros:", len(df))

print(
    "Periodo:",
    df["FECHA"].min(),
    "a",
    df["FECHA"].max()
)

print(
    "Columnas:",
    len(df.columns)
)


# ---------------------------------------------------------
# FECHAS
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("VALIDACIÓN DE FECHAS")
print("=" * 70)

fechas_invalidas = (
    df["FECHA"].isna().sum()
)

duplicados_fecha = (
    df["FECHA"].duplicated().sum()
)

print(
    "Fechas inválidas:",
    fechas_invalidas
)

print(
    "Fechas duplicadas:",
    duplicados_fecha
)


if duplicados_fecha > 0:

    print("\nEjemplos de fechas duplicadas:")

    print(
        df[
            df["FECHA"].duplicated(
                keep=False
            )
        ][
            [
                "FECHA",
                "UV_INDEX",
                "ALLSKY_KT"
            ]
        ].head(20)
    )


# ---------------------------------------------------------
# DATOS FALTANTES
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("VALORES FALTANTES")
print("=" * 70)

faltantes = (
    df
    .isna()
    .sum()
    .sort_values(
        ascending=False
    )
)

print(faltantes)


# ---------------------------------------------------------
# ALLSKY_KT
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("VALIDACIÓN ALLSKY_KT")
print("=" * 70)

kt = df["ALLSKY_KT"]

print(
    "Mínimo:",
    kt.min()
)

print(
    "Máximo:",
    kt.max()
)

print(
    "Media:",
    kt.mean()
)

print(
    "Mediana:",
    kt.median()
)


fuera_kt = df[
    (df["ALLSKY_KT"] < 0)
    |
    (df["ALLSKY_KT"] > 1)
]

print(
    "Valores fuera de 0–1:",
    len(fuera_kt)
)


# ---------------------------------------------------------
# UV INDEX
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("VALIDACIÓN UV INDEX")
print("=" * 70)

uv = df["UV_INDEX"]

print(
    "Mínimo:",
    uv.min()
)

print(
    "Máximo:",
    uv.max()
)

print(
    "Media:",
    uv.mean()
)

print(
    "Mediana:",
    uv.median()
)


uv_negativo = df[
    df["UV_INDEX"] < 0
]

print(
    "Valores UV negativos:",
    len(uv_negativo)
)


# ---------------------------------------------------------
# VARIABLES AMBIENTALES
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("RANGOS DE VARIABLES")
print("=" * 70)

variables = [
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
    "UV_INDEX",
]


for variable in variables:

    if variable not in df.columns:
        continue

    print(
        f"{variable:25} "
        f"min={df[variable].min():10.4f} "
        f"max={df[variable].max():10.4f} "
        f"media={df[variable].mean():10.4f}"
    )


# ---------------------------------------------------------
# COHERENCIA DE TEMPERATURAS
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("COHERENCIA DE TEMPERATURA")
print("=" * 70)

errores_temperatura = df[
    (df["T2M_MIN"] > df["T2M"])
    |
    (df["T2M"] > df["T2M_MAX"])
]

print(
    "Filas donde no se cumple "
    "T2M_MIN <= T2M <= T2M_MAX:",
    len(errores_temperatura)
)


# ---------------------------------------------------------
# HUMEDAD
# ---------------------------------------------------------

humedad_fuera = df[
    (df["RH2M"] < 0)
    |
    (df["RH2M"] > 100)
]

print(
    "Humedad fuera de 0–100:",
    len(humedad_fuera)
)


# ---------------------------------------------------------
# DIRECCIÓN DEL VIENTO
# ---------------------------------------------------------

viento_fuera = df[
    (df["WD10M"] < 0)
    |
    (df["WD10M"] > 360)
]

print(
    "Dirección del viento fuera de 0–360:",
    len(viento_fuera)
)


# ---------------------------------------------------------
# PRECIPITACIÓN
# ---------------------------------------------------------

precipitacion_negativa = df[
    df["PRECTOTCORR"] < 0
]

print(
    "Precipitación negativa:",
    len(precipitacion_negativa)
)


# ---------------------------------------------------------
# DISTRIBUCIÓN DE CLASES
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("CLASIFICACIÓN UV")
print("=" * 70)

df["CLASE_UV"] = (
    df["UV_INDEX"] >= 6
).astype(int)

conteo = (
    df["CLASE_UV"]
    .value_counts()
    .sort_index()
)

porcentaje = (
    df["CLASE_UV"]
    .value_counts(
        normalize=True
    )
    .sort_index()
    * 100
)

print("\nClase 0 = BAJO")
print("Clase 1 = ALTO")

for clase in [
    0,
    1
]:

    print(
        f"\nClase {clase}: "
        f"{conteo.get(clase, 0)} "
        f"({porcentaje.get(clase, 0):.2f} %)"
    )


# ---------------------------------------------------------
# CONCLUSIÓN AUTOMÁTICA
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("RESULTADO DE VALIDACIÓN")
print("=" * 70)

errores_criticos = (
    fechas_invalidas
    + duplicados_fecha
    + len(fuera_kt)
    + len(uv_negativo)
    + len(humedad_fuera)
    + len(viento_fuera)
    + len(precipitacion_negativa)
)


if errores_criticos == 0:

    print(
        "No se detectaron errores críticos "
        "en las validaciones principales."
    )

else:

    print(
        "Se encontraron posibles inconsistencias."
    )

    print(
        "Cantidad total de alertas:",
        errores_criticos
    )