from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

RUTA_AMBIENTAL = BASE_DIR / "data" / "datos_nasa.csv"
RUTA_UV = BASE_DIR / "data" / "datos_uv_nasa.csv"

RUTA_SALIDA = BASE_DIR / "data" / "dataset_ml.csv"


def cargar_datos_ambientales():
    df = pd.read_csv(
        RUTA_AMBIENTAL,
        sep=";",
        skiprows=18
    )

    df = df.replace(-999, np.nan)

    df["FECHA"] = pd.to_datetime(
        {
            "year": df["YEAR"],
            "month": df["MO"],
            "day": df["DY"]
        }
    )

    return df


def cargar_datos_uv():
    df = pd.read_csv(RUTA_UV)

    df["FECHA"] = pd.to_datetime(
        df["x"],
        utc=True
    ).dt.date

    df["FECHA"] = pd.to_datetime(df["FECHA"])

    df = df.rename(
        columns={
            "y": "UV_INDEX"
        }
    )

    return df[["FECHA", "UV_INDEX"]]


def crear_dataset():
    ambientales = cargar_datos_ambientales()
    uv = cargar_datos_uv()

    combinado = ambientales.merge(
        uv,
        on="FECHA",
        how="inner"
    )

    print("Filas coincidentes:", len(combinado))
    print(
        "UV disponibles:",
        combinado["UV_INDEX"].notna().sum()
    )
    print(
        "UV faltantes:",
        combinado["UV_INDEX"].isna().sum()
    )

    # Para entrenar no podemos utilizar filas sin variable objetivo.
    dataset_ml = combinado.dropna(
        subset=["UV_INDEX"]
    ).copy()

    columnas = [
        "FECHA",
        "YEAR",
        "MO",
        "DY",
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

    dataset_ml = dataset_ml[columnas]

    dataset_ml.to_csv(
        RUTA_SALIDA,
        index=False
    )

    print()
    print("Dataset creado correctamente.")
    print("Filas finales:", len(dataset_ml))
    print(
        "Periodo:",
        dataset_ml["FECHA"].min(),
        "a",
        dataset_ml["FECHA"].max()
    )
    print("Archivo:", RUTA_SALIDA)


if __name__ == "__main__":
    crear_dataset()