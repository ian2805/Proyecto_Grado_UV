from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_DATOS = BASE_DIR / "data" / "datos_solares_barranquilla.csv"
RUTA_MODELO = BASE_DIR / "models" / "modelo_radiacion.joblib"


FEATURES_NUMERICAS = [
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "ALLSKY_KT",
    "WS10M",
    "WD10M",
    "PRECTOTCORR",
]
FEATURES_CATEGORICAS = ["ZONA"]
TARGET = "ALLSKY_SFC_SW_DWN"


def main():

    df = pd.read_csv(RUTA_DATOS, parse_dates=["FECHA"])
    df = df.replace(-999, np.nan).dropna(
        subset=FEATURES_NUMERICAS + FEATURES_CATEGORICAS + [TARGET]
    )
    df = df.sort_values("FECHA")

    corte = df["FECHA"].quantile(0.8)
    entrenamiento = df[df["FECHA"] <= corte]
    prueba = df[df["FECHA"] > corte]

    features = FEATURES_NUMERICAS + FEATURES_CATEGORICAS
    preprocesamiento = ColumnTransformer([
        (
            "numericas",
            SimpleImputer(strategy="median"),
            FEATURES_NUMERICAS,
        ),
        (
            "zonas",
            OneHotEncoder(handle_unknown="ignore"),
            FEATURES_CATEGORICAS,
        ),
    ])

    modelo = Pipeline([
        ("preprocesamiento", preprocesamiento),
        (
            "regresor",
            RandomForestRegressor(
                n_estimators=180,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            ),
        ),
    ])

    modelo.fit(entrenamiento[features], entrenamiento[TARGET])
    predicciones = modelo.predict(prueba[features])

    print("=" * 65)
    print("MODELO DE PREDICCION DE RADIACION SOLAR")
    print("=" * 65)
    print(f"Registros de entrenamiento: {len(entrenamiento):,}")
    print(f"Registros de prueba: {len(prueba):,}")
    print(f"MAE: {mean_absolute_error(prueba[TARGET], predicciones):.4f}")
    print(f"RMSE: {mean_squared_error(prueba[TARGET], predicciones) ** 0.5:.4f}")
    print(f"R2: {r2_score(prueba[TARGET], predicciones):.4f}")

    modelo.fit(df[features], df[TARGET])
    RUTA_MODELO.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "modelo": modelo,
            "features": features,
            "target": TARGET,
            "unidad": "kWh/m2/dia",
            "metadata": {
                "tipo": "RandomForestRegressor",
                "fuente": "NASA POWER",
                "zonas": sorted(df["ZONA"].unique().tolist()),
            },
        },
        RUTA_MODELO,
    )
    print(f"Modelo guardado en: {RUTA_MODELO}")


if __name__ == "__main__":
    main()
