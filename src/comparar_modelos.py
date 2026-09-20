from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)


BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_DATOS = BASE_DIR / "data" / "dataset_ml.csv"

df = pd.read_csv(RUTA_DATOS)

df["FECHA"] = pd.to_datetime(df["FECHA"])

# 0 = BAJO  (UVI < 6)
# 1 = ALTO  (UVI >= 6)
df["CLASE_UV"] = (df["UV_INDEX"] >= 6).astype(int)


MODELOS = {
    "1 variable": [
        "ALLSKY_KT",
    ],

    "2 variables": [
        "ALLSKY_KT",
        "T2M",
    ],

    "4 variables": [
        "ALLSKY_KT",
        "T2M",
        "T2M_MAX",
        "T2M_MIN",
    ],

    "10 variables": [
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
    ],
}


# ---------------------------------------------------------
# División temporal
# ---------------------------------------------------------

train = df[df["YEAR"] <= 2019].copy()

validacion = df[
    (df["YEAR"] >= 2020) &
    (df["YEAR"] <= 2021)
].copy()

test = df[df["YEAR"] >= 2022].copy()


def crear_modelo():
    return Pipeline([
        (
            "imputacion",
            SimpleImputer(strategy="median")
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


def seleccionar_umbral(modelo, X_val, y_val):

    probabilidades = modelo.predict_proba(X_val)[:, 1]

    resultados = []

    for umbral in np.arange(0.05, 0.91, 0.01):

        predicciones = (
            probabilidades >= umbral
        ).astype(int)

        recall_alto = recall_score(
            y_val,
            predicciones,
            pos_label=1,
            zero_division=0
        )

        balanced = balanced_accuracy_score(
            y_val,
            predicciones
        )

        f1_macro = f1_score(
            y_val,
            predicciones,
            average="macro",
            zero_division=0
        )

        resultados.append({
            "umbral": umbral,
            "recall_alto": recall_alto,
            "balanced_accuracy": balanced,
            "f1_macro": f1_macro,
        })

    resultados = pd.DataFrame(resultados)

    candidatos = resultados[
        resultados["recall_alto"] >= 0.95
    ]

    if len(candidatos) > 0:

        mejor = candidatos.sort_values(
            [
                "f1_macro",
                "balanced_accuracy"
            ],
            ascending=False
        ).iloc[0]

    else:

        mejor = resultados.sort_values(
            "balanced_accuracy",
            ascending=False
        ).iloc[0]

    return float(mejor["umbral"])


def calcular_metricas(
    y_real,
    probabilidades,
    umbral
):

    predicciones = (
        probabilidades >= umbral
    ).astype(int)

    resultado = {
        "accuracy":
            accuracy_score(
                y_real,
                predicciones
            ),

        "balanced_accuracy":
            balanced_accuracy_score(
                y_real,
                predicciones
            ),

        "precision_alto":
            precision_score(
                y_real,
                predicciones,
                zero_division=0
            ),

        "recall_alto":
            recall_score(
                y_real,
                predicciones,
                zero_division=0
            ),

        "f1_alto":
            f1_score(
                y_real,
                predicciones,
                zero_division=0
            ),

        "f1_macro":
            f1_score(
                y_real,
                predicciones,
                average="macro",
                zero_division=0
            ),
    }

    if len(np.unique(y_real)) > 1:
        resultado["roc_auc"] = roc_auc_score(
            y_real,
            probabilidades
        )
    else:
        resultado["roc_auc"] = np.nan

    return resultado, predicciones


print("=" * 75)
print("COMPARACIÓN DE MODELOS")
print("=" * 75)

print(
    f"\nEntrenamiento: "
    f"{train['FECHA'].min().date()} "
    f"a {train['FECHA'].max().date()}"
)

print(
    f"Validación: "
    f"{validacion['FECHA'].min().date()} "
    f"a {validacion['FECHA'].max().date()}"
)

print(
    f"Prueba: "
    f"{test['FECHA'].min().date()} "
    f"a {test['FECHA'].max().date()}"
)


resumen = []


for nombre, features in MODELOS.items():

    print("\n" + "=" * 75)
    print(nombre.upper())
    print("=" * 75)

    print("Variables:")
    for variable in features:
        print(f"  - {variable}")

    modelo = crear_modelo()

    X_train = train[features]
    y_train = train["CLASE_UV"]

    X_val = validacion[features]
    y_val = validacion["CLASE_UV"]

    X_test = test[features]
    y_test = test["CLASE_UV"]

    modelo.fit(
        X_train,
        y_train
    )

    umbral = seleccionar_umbral(
        modelo,
        X_val,
        y_val
    )

    probabilidades_test = (
        modelo.predict_proba(X_test)[:, 1]
    )

    metricas, predicciones = calcular_metricas(
        y_test,
        probabilidades_test,
        umbral
    )

    print(f"\nUmbral seleccionado: {umbral:.2f}")

    print(
        f"Accuracy: "
        f"{metricas['accuracy']:.4f}"
    )

    print(
        f"Balanced accuracy: "
        f"{metricas['balanced_accuracy']:.4f}"
    )

    print(
        f"Precision ALTO: "
        f"{metricas['precision_alto']:.4f}"
    )

    print(
        f"Recall ALTO: "
        f"{metricas['recall_alto']:.4f}"
    )

    print(
        f"F1 ALTO: "
        f"{metricas['f1_alto']:.4f}"
    )

    print(
        f"F1 macro: "
        f"{metricas['f1_macro']:.4f}"
    )

    print(
        f"ROC-AUC: "
        f"{metricas['roc_auc']:.4f}"
    )

    print("\nMatriz de confusión:")

    print(
        confusion_matrix(
            y_test,
            predicciones
        )
    )


    # -----------------------------------------------------
    # Evaluación por año
    # -----------------------------------------------------

    print("\nRESULTADOS POR AÑO")

    for anio in [
        2022,
        2023,
        2024,
        2025
    ]:

        datos_anio = test[
            test["YEAR"] == anio
        ]

        X_anio = datos_anio[features]

        y_anio = datos_anio[
            "CLASE_UV"
        ]

        probabilidades_anio = (
            modelo.predict_proba(
                X_anio
            )[:, 1]
        )

        metricas_anio, _ = calcular_metricas(
            y_anio,
            probabilidades_anio,
            umbral
        )

        print(
            f"{anio} | "
            f"n={len(datos_anio):4d} | "
            f"BalAcc="
            f"{metricas_anio['balanced_accuracy']:.3f} | "
            f"Recall ALTO="
            f"{metricas_anio['recall_alto']:.3f} | "
            f"F1 macro="
            f"{metricas_anio['f1_macro']:.3f}"
        )


    resumen.append({
        "modelo": nombre,
        "variables": len(features),
        "umbral": umbral,
        **metricas
    })


# ---------------------------------------------------------
# Resumen final
# ---------------------------------------------------------

resumen = pd.DataFrame(resumen)

print("\n" + "=" * 75)
print("RESUMEN FINAL")
print("=" * 75)

print(
    resumen[
        [
            "modelo",
            "variables",
            "umbral",
            "accuracy",
            "balanced_accuracy",
            "recall_alto",
            "f1_macro",
            "roc_auc",
        ]
    ].to_string(
        index=False
    )
)


RUTA_SALIDA = (
    BASE_DIR /
    "data" /
    "resultados_comparacion_modelos.csv"
)

resumen.to_csv(
    RUTA_SALIDA,
    index=False
)

print(
    "\nResultados guardados en:"
)

print(RUTA_SALIDA)