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
    classification_report,
)

BASE_DIR = Path(__file__).resolve().parent.parent
RUTA = BASE_DIR / "data" / "dataset_ml.csv"

df = pd.read_csv(RUTA)

df["FECHA"] = pd.to_datetime(df["FECHA"])

# 0 = BAJO
# 1 = ALTO
df["CLASE_UV"] = (df["UV_INDEX"] >= 6).astype(int)

features = [
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

# División cronológica
train = df[df["YEAR"] <= 2019].copy()

validacion = df[
    (df["YEAR"] >= 2020) &
    (df["YEAR"] <= 2021)
].copy()

test = df[df["YEAR"] >= 2022].copy()

X_train = train[features]
y_train = train["CLASE_UV"]

X_val = validacion[features]
y_val = validacion["CLASE_UV"]

X_test = test[features]
y_test = test["CLASE_UV"]

modelo = Pipeline([
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
    )
])

modelo.fit(X_train, y_train)

# ---------------------------------------------------------
# Elegir umbral utilizando ÚNICAMENTE validación
# ---------------------------------------------------------

prob_val = modelo.predict_proba(X_val)[:, 1]

resultados = []

for umbral in np.arange(0.10, 0.91, 0.01):

    pred = (prob_val >= umbral).astype(int)

    recall_alto = recall_score(
        y_val,
        pred,
        pos_label=1
    )

    balanced = balanced_accuracy_score(
        y_val,
        pred
    )

    f1_macro = f1_score(
        y_val,
        pred,
        average="macro"
    )

    resultados.append(
        {
            "umbral": umbral,
            "recall_alto": recall_alto,
            "balanced_accuracy": balanced,
            "f1_macro": f1_macro,
        }
    )

resultados = pd.DataFrame(resultados)

# Para este proyecto queremos evitar clasificar
# como BAJO demasiados días realmente ALTOS.
candidatos = resultados[
    resultados["recall_alto"] >= 0.95
]

if len(candidatos) > 0:

    mejor = candidatos.sort_values(
        ["f1_macro", "balanced_accuracy"],
        ascending=False
    ).iloc[0]

else:

    mejor = resultados.sort_values(
        "balanced_accuracy",
        ascending=False
    ).iloc[0]

umbral_optimo = float(mejor["umbral"])

print("=" * 65)
print("UMBRAL SELECCIONADO CON VALIDACIÓN")
print("=" * 65)

print(f"Umbral: {umbral_optimo:.2f}")
print(
    f"Recall ALTO validación: "
    f"{mejor['recall_alto']:.4f}"
)
print(
    f"Balanced accuracy validación: "
    f"{mejor['balanced_accuracy']:.4f}"
)
print(
    f"F1 macro validación: "
    f"{mejor['f1_macro']:.4f}"
)

# ---------------------------------------------------------
# Evaluación FINAL
# ---------------------------------------------------------

prob_test = modelo.predict_proba(X_test)[:, 1]

pred_test = (
    prob_test >= umbral_optimo
).astype(int)

print("\n" + "=" * 65)
print("PRUEBA FINAL: 2022 - 2025")
print("=" * 65)

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
    f"{f1_score(y_test, pred_test, average='macro'):.4f}"
)

print(
    f"ROC-AUC: "
    f"{roc_auc_score(y_test, prob_test):.4f}"
)

print("\nMatriz de confusión:")

print(
    confusion_matrix(
        y_test,
        pred_test
    )
)

print("\nReporte completo:")

print(
    classification_report(
        y_test,
        pred_test,
        target_names=[
            "BAJO",
            "ALTO"
        ]
    )
)