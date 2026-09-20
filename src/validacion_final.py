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
RUTA = BASE_DIR / "data" / "dataset_ml.csv"

df = pd.read_csv(RUTA)

df["FECHA"] = pd.to_datetime(df["FECHA"])

# 0 = BAJO
# 1 = ALTO
df["CLASE_UV"] = (
    df["UV_INDEX"] >= 6
).astype(int)


MODELOS = {

    "1 variable": [
        "ALLSKY_KT"
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


FOLDS = [

    {
        "train_fin": 2011,
        "val_inicio": 2012,
        "val_fin": 2014,
    },

    {
        "train_fin": 2014,
        "val_inicio": 2015,
        "val_fin": 2017,
    },

    {
        "train_fin": 2017,
        "val_inicio": 2018,
        "val_fin": 2021,
    },

]


def crear_modelo():

    return Pipeline([
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


def buscar_umbral(
    reales,
    probabilidades
):

    resultados = []

    # Ampliamos la búsqueda hasta 0.01
    for umbral in np.arange(
        0.01,
        0.51,
        0.01
    ):

        pred = (
            probabilidades >= umbral
        ).astype(int)

        recall_alto = recall_score(
            reales,
            pred,
            zero_division=0
        )

        balanced = (
            balanced_accuracy_score(
                reales,
                pred
            )
        )

        f1_macro = f1_score(
            reales,
            pred,
            average="macro",
            zero_division=0
        )

        resultados.append({
            "umbral": umbral,
            "recall_alto": recall_alto,
            "balanced": balanced,
            "f1_macro": f1_macro,
        })


    resultados = pd.DataFrame(
        resultados
    )


    # Prioridad:
    # detectar al menos 95 % de ALTO
    candidatos = resultados[
        resultados["recall_alto"]
        >= 0.95
    ]


    if len(candidatos):

        mejor = candidatos.sort_values(
            [
                "f1_macro",
                "balanced"
            ],
            ascending=False
        ).iloc[0]

    else:

        mejor = resultados.sort_values(
            "balanced",
            ascending=False
        ).iloc[0]


    return mejor


for nombre, features in MODELOS.items():

    print("\n" + "=" * 75)
    print(nombre.upper())
    print("=" * 75)

    probabilidades_val = []
    reales_val = []


    # ---------------------------------------------
    # VALIDACIÓN TEMPORAL PROGRESIVA
    # ---------------------------------------------

    for numero, fold in enumerate(
        FOLDS,
        start=1
    ):

        train = df[
            df["YEAR"]
            <= fold["train_fin"]
        ].copy()

        val = df[
            (
                df["YEAR"]
                >= fold["val_inicio"]
            )
            &
            (
                df["YEAR"]
                <= fold["val_fin"]
            )
        ].copy()


        modelo = crear_modelo()

        modelo.fit(
            train[features],
            train["CLASE_UV"]
        )


        probabilidades = (
            modelo.predict_proba(
                val[features]
            )[:, 1]
        )


        probabilidades_val.extend(
            probabilidades
        )

        reales_val.extend(
            val["CLASE_UV"].to_numpy()
        )


        bajos = (
            val["CLASE_UV"] == 0
        ).sum()

        altos = (
            val["CLASE_UV"] == 1
        ).sum()


        print(
            f"\nFold {numero}: "
            f"entrena hasta "
            f"{fold['train_fin']} | "
            f"valida "
            f"{fold['val_inicio']}-"
            f"{fold['val_fin']}"
        )

        print(
            f"Validación: "
            f"{len(val)} registros | "
            f"BAJO={bajos} | "
            f"ALTO={altos}"
        )


    probabilidades_val = np.array(
        probabilidades_val
    )

    reales_val = np.array(
        reales_val
    )


    mejor = buscar_umbral(
        reales_val,
        probabilidades_val
    )


    umbral = float(
        mejor["umbral"]
    )


    print("\n" + "-" * 75)

    print(
        f"UMBRAL SELECCIONADO: "
        f"{umbral:.2f}"
    )

    print(
        f"Recall ALTO validación: "
        f"{mejor['recall_alto']:.4f}"
    )

    print(
        f"Balanced accuracy validación: "
        f"{mejor['balanced']:.4f}"
    )

    print(
        f"F1 macro validación: "
        f"{mejor['f1_macro']:.4f}"
    )


    # ---------------------------------------------
    # PRUEBA FINAL
    # ---------------------------------------------

    train_final = df[
        df["YEAR"] <= 2021
    ].copy()

    test = df[
        df["YEAR"] >= 2022
    ].copy()


    modelo_final = crear_modelo()

    modelo_final.fit(
        train_final[features],
        train_final["CLASE_UV"]
    )


    prob_test = (
        modelo_final.predict_proba(
            test[features]
        )[:, 1]
    )


    pred_test = (
        prob_test >= umbral
    ).astype(int)


    y_test = test["CLASE_UV"]


    print("\n" + "=" * 75)
    print("PRUEBA FINAL 2022-2025")
    print("=" * 75)


    print(
        f"Accuracy: "
        f"{accuracy_score(y_test, pred_test):.4f}"
    )

    print(
        f"Balanced accuracy: "
        f"{balanced_accuracy_score(y_test, pred_test):.4f}"
    )

    print(
        f"Precision ALTO: "
        f"{precision_score(y_test, pred_test):.4f}"
    )

    print(
        f"Recall ALTO: "
        f"{recall_score(y_test, pred_test):.4f}"
    )

    print(
        f"F1 ALTO: "
        f"{f1_score(y_test, pred_test):.4f}"
    )

    print(
        f"F1 macro: "
        f"{f1_score(
            y_test,
            pred_test,
            average='macro'
        ):.4f}"
    )

    print(
        f"ROC-AUC: "
        f"{roc_auc_score(
            y_test,
            prob_test
        ):.4f}"
    )


    print("\nMatriz de confusión:")

    print(
        confusion_matrix(
            y_test,
            pred_test
        )
    )


    # ---------------------------------------------
    # RESULTADOS POR AÑO
    # ---------------------------------------------

    print("\nResultados por año:")

    for anio in range(
        2022,
        2026
    ):

        datos = test[
            test["YEAR"] == anio
        ]

        prob = (
            modelo_final.predict_proba(
                datos[features]
            )[:, 1]
        )

        pred = (
            prob >= umbral
        ).astype(int)

        real = datos["CLASE_UV"]

        matriz = confusion_matrix(
            real,
            pred,
            labels=[0, 1]
        )

        print(
            f"\n{anio} "
            f"(n={len(datos)})"
        )

        print(matriz)

        print(
            "Balanced accuracy: "
            f"{balanced_accuracy_score(
                real,
                pred
            ):.4f}"
        )