from pathlib import Path

import joblib
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression


BASE_DIR = Path(__file__).resolve().parent.parent

RUTA_DATOS = (
    BASE_DIR /
    "data" /
    "dataset_ml.csv"
)

RUTA_MODELO = (
    BASE_DIR /
    "models" /
    "modelo_uv.joblib"
)

# Umbral seleccionado mediante
# validación temporal progresiva.
UMBRAL = 0.07

# Modelo final simplificado.
FEATURES = [
    "ALLSKY_KT"
]


def main():

    df = pd.read_csv(
        RUTA_DATOS
    )

    # Clasificación binaria:
    # 0 = BAJO (UVI < 6)
    # 1 = ALTO (UVI >= 6)
    df["CLASE_UV"] = (
        df["UV_INDEX"] >= 6
    ).astype(int)

    X = df[FEATURES]
    y = df["CLASE_UV"]

    modelo = Pipeline([
        (
            "imputacion",
            SimpleImputer(
                strategy="median"
            )
        ),
        (
            "escalado",
            StandardScaler()
        ),
        (
            "clasificador",
            LogisticRegression(
                class_weight="balanced",
                max_iter=2000,
                random_state=42
            )
        ),
    ])

    # La arquitectura, las variables y
    # el umbral ya fueron evaluados
    # mediante validación temporal.
    #
    # Para despliegue se reentrena
    # utilizando todos los datos
    # disponibles.
    modelo.fit(
        X,
        y
    )

    RUTA_MODELO.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump(
        {
            "modelo": modelo,
            "features": FEATURES,
            "umbral": UMBRAL,

            "metadata": {
                "variable_objetivo":
                    "UV_INDEX",

                "criterio_bajo":
                    "UVI < 6",

                "criterio_alto":
                    "UVI >= 6",

                "modelo":
                    "Regresión logística",

                "fuente_uv":
                    "NASA Aura/OMI OMUVBd_003",

                "ubicacion":
                    "Barranquilla, Colombia",
            }
        },
        RUTA_MODELO
    )

    print("=" * 60)
    print("MODELO WEB GENERADO")
    print("=" * 60)

    print(
        f"Ruta: {RUTA_MODELO}"
    )

    print(
        f"Registros utilizados: "
        f"{len(df)}"
    )

    print(
        f"Variable: "
        f"{FEATURES[0]}"
    )

    print(
        f"Umbral de decisión: "
        f"{UMBRAL:.2f}"
    )

    print(
        "Clasificación: "
        "BAJO = UVI < 6 | "
        "ALTO = UVI >= 6"
    )


if __name__ == "__main__":
    main()