from pathlib import Path

import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from sklearn.metrics import (
    accuracy_score,
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

# Clasificación binaria:
# BAJO = UVI < 6
# ALTO = UVI >= 6
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

# Separación temporal
train = df[df["YEAR"] <= 2021].copy()
test = df[df["YEAR"] >= 2022].copy()

X_train = train[features]
y_train = train["CLASE_UV"]

X_test = test[features]
y_test = test["CLASE_UV"]

print("=" * 65)
print("SEPARACIÓN TEMPORAL")
print("=" * 65)

print(
    "Entrenamiento:",
    train["FECHA"].min().date(),
    "a",
    train["FECHA"].max().date(),
)

print(
    "Prueba:",
    test["FECHA"].min().date(),
    "a",
    test["FECHA"].max().date(),
)

print("\nDistribución entrenamiento:")
print(y_train.value_counts())
print(y_train.value_counts(normalize=True) * 100)

print("\nDistribución prueba:")
print(y_test.value_counts())
print(y_test.value_counts(normalize=True) * 100)

modelo = Pipeline([
    (
        "imputacion",
        SimpleImputer(strategy="median"),
    ),
    (
        "escalado",
        StandardScaler(),
    ),
    (
        "clasificador",
        LogisticRegression(
            class_weight="balanced",
            max_iter=2000,
            random_state=42,
        ),
    ),
])

modelo.fit(X_train, y_train)

predicciones = modelo.predict(X_test)
probabilidades = modelo.predict_proba(X_test)[:, 1]

print("\n" + "=" * 65)
print("RESULTADOS SOBRE AÑOS FUTUROS")
print("=" * 65)

print(
    f"Accuracy : "
    f"{accuracy_score(y_test, predicciones):.4f}"
)

print(
    f"Precision ALTO: "
    f"{precision_score(y_test, predicciones):.4f}"
)

print(
    f"Recall ALTO   : "
    f"{recall_score(y_test, predicciones):.4f}"
)

print(
    f"F1 ALTO       : "
    f"{f1_score(y_test, predicciones):.4f}"
)

print(
    f"ROC-AUC       : "
    f"{roc_auc_score(y_test, probabilidades):.4f}"
)

print("\nMatriz de confusión:")
print(
    confusion_matrix(
        y_test,
        predicciones,
    )
)

print("\nReporte completo:")
print(
    classification_report(
        y_test,
        predicciones,
        target_names=[
            "BAJO",
            "ALTO",
        ],
    )
)