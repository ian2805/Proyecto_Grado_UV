from pathlib import Path

import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score


BASE_DIR = Path(__file__).resolve().parent.parent
RUTA = BASE_DIR / "data" / "dataset_ml.csv"

df = pd.read_csv(RUTA)

df["FECHA"] = pd.to_datetime(df["FECHA"])

# Clasificación binaria:
# 0 = BAJO  -> UVI < 6
# 1 = ALTO  -> UVI >= 6
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


# ---------------------------------------------------------
# Separación temporal
# ---------------------------------------------------------

train = df[df["YEAR"] <= 2019].copy()

validacion = df[
    (df["YEAR"] >= 2020) &
    (df["YEAR"] <= 2021)
].copy()


X_train = train[features]
y_train = train["CLASE_UV"]

X_val = validacion[features]
y_val = validacion["CLASE_UV"]


print("=" * 70)
print("ANÁLISIS DE IMPORTANCIA DE VARIABLES")
print("=" * 70)

print(
    f"\nEntrenamiento: "
    f"{train['FECHA'].min().date()} a "
    f"{train['FECHA'].max().date()}"
)

print(
    f"Validación: "
    f"{validacion['FECHA'].min().date()} a "
    f"{validacion['FECHA'].max().date()}"
)

print("\nDistribución de clases en validación:")
print(y_val.value_counts())


# ---------------------------------------------------------
# Modelo
# ---------------------------------------------------------

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
# Rendimiento base
# ---------------------------------------------------------

probabilidades = modelo.predict_proba(X_val)[:, 1]

auc = roc_auc_score(
    y_val,
    probabilidades
)

print(f"\nROC-AUC validación: {auc:.4f}")


# ---------------------------------------------------------
# Permutation Importance
# ---------------------------------------------------------

resultado = permutation_importance(
    modelo,
    X_val,
    y_val,
    scoring="roc_auc",
    n_repeats=30,
    random_state=42,
    n_jobs=-1
)


importancias = pd.DataFrame({
    "VARIABLE": features,
    "IMPORTANCIA": resultado.importances_mean,
    "DESVIACION": resultado.importances_std
})


importancias = importancias.sort_values(
    "IMPORTANCIA",
    ascending=False
)


print("\n" + "=" * 70)
print("IMPORTANCIA POR PERMUTACIÓN")
print("=" * 70)

for _, fila in importancias.iterrows():

    print(
        f"{fila['VARIABLE']:<25} "
        f"{fila['IMPORTANCIA']:.5f} "
        f"(± {fila['DESVIACION']:.5f})"
    )


# ---------------------------------------------------------
# Coeficientes de regresión logística
# ---------------------------------------------------------

clasificador = modelo.named_steps["clasificador"]

coeficientes = pd.DataFrame({
    "VARIABLE": features,
    "COEFICIENTE": clasificador.coef_[0]
})

coeficientes["MAGNITUD"] = (
    coeficientes["COEFICIENTE"].abs()
)

coeficientes = coeficientes.sort_values(
    "MAGNITUD",
    ascending=False
)


print("\n" + "=" * 70)
print("COEFICIENTES ESTANDARIZADOS")
print("=" * 70)

for _, fila in coeficientes.iterrows():

    direccion = (
        "↑ ALTO"
        if fila["COEFICIENTE"] > 0
        else "↓ ALTO"
    )

    print(
        f"{fila['VARIABLE']:<25} "
        f"{fila['COEFICIENTE']:>9.4f} "
        f"{direccion}"
    )


print("\n" + "=" * 70)
print("NOTA")
print("=" * 70)

print(
    "La importancia por permutación será la referencia principal "
    "para evaluar qué variables aportan información al modelo."
)

print(
    "Los coeficientes ayudan a interpretar la dirección de la "
    "relación, pero pueden verse afectados por variables correlacionadas."
)

from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score
)
import numpy as np

print("\n" + "=" * 70)
print("ANÁLISIS DETALLADO DE VALIDACIÓN")
print("=" * 70)

# --------------------------------------------------
# PROBABILIDADES
# --------------------------------------------------
# Cambia solamente el nombre "modelo" si tu variable del modelo
# tiene otro nombre.
probabilidades = modelo.predict_proba(X_val)[:, 1]

# Umbral normal de clasificación.
# Después podemos repetirlo con el umbral seleccionado
# en ajustar_umbral.py.
umbral = 0.50

predicciones = (probabilidades >= umbral).astype(int)

# --------------------------------------------------
# MATRIZ DE CONFUSIÓN
# --------------------------------------------------
cm = confusion_matrix(y_val, predicciones)

tn, fp, fn, tp = cm.ravel()

print(f"\nUmbral utilizado: {umbral:.2f}")

print("\nMatriz de confusión:")
print(cm)

print("\nDesglose:")
print(f"TN - Clase 0 detectada correctamente : {tn}")
print(f"FP - Clase 0 confundida como clase 1 : {fp}")
print(f"FN - Clase 1 confundida como clase 0 : {fn}")
print(f"TP - Clase 1 detectada correctamente : {tp}")

# --------------------------------------------------
# MÉTRICAS
# --------------------------------------------------
precision = precision_score(y_val, predicciones, zero_division=0)
recall = recall_score(y_val, predicciones, zero_division=0)
f1 = f1_score(y_val, predicciones, zero_division=0)

specificity = tn / (tn + fp) if (tn + fp) > 0 else 0

pr_auc = average_precision_score(y_val, probabilidades)

print("\n" + "=" * 70)
print("MÉTRICAS")
print("=" * 70)

print(f"Precision clase 1 : {precision:.4f}")
print(f"Recall clase 1    : {recall:.4f}")
print(f"F1-score          : {f1:.4f}")
print(f"Specificity       : {specificity:.4f}")
print(f"PR-AUC            : {pr_auc:.4f}")

print("\nReporte de clasificación:")
print(
    classification_report(
        y_val,
        predicciones,
        digits=4,
        zero_division=0
    )
)

# --------------------------------------------------
# ANALIZAR ÚNICAMENTE LOS CASOS REALES DE CLASE 0
# --------------------------------------------------
print("\n" + "=" * 70)
print("ANÁLISIS DE LOS CASOS REALES DE CLASE 0")
print("=" * 70)

# Nos aseguramos de conservar índices
if isinstance(y_val, pd.Series):
    indices_cero = y_val[y_val == 0].index
else:
    indices_cero = np.where(np.asarray(y_val) == 0)[0]

# Crear DataFrame con las variables
if isinstance(X_val, pd.DataFrame):
    casos_cero = X_val.loc[indices_cero].copy()
else:
    casos_cero = pd.DataFrame(
        np.asarray(X_val)[np.asarray(y_val) == 0]
    )

# Sacar probabilidades correspondientes
if isinstance(y_val, pd.Series):
    posiciones_cero = np.where(y_val.to_numpy() == 0)[0]
else:
    posiciones_cero = np.where(np.asarray(y_val) == 0)[0]

casos_cero["PROB_CLASE_1"] = probabilidades[posiciones_cero]
casos_cero["PREDICCION"] = predicciones[posiciones_cero]
casos_cero["REAL"] = 0

casos_cero["RESULTADO"] = np.where(
    casos_cero["PREDICCION"] == 0,
    "CORRECTO",
    "ERROR"
)

print(f"\nTotal casos reales clase 0: {len(casos_cero)}")
print(
    f"Detectados correctamente: "
    f"{(casos_cero['RESULTADO'] == 'CORRECTO').sum()}"
)

print(
    f"Confundidos como clase 1: "
    f"{(casos_cero['RESULTADO'] == 'ERROR').sum()}"
)

print("\nDetalle de los casos clase 0:")
print(casos_cero.to_string())

# --------------------------------------------------
# GUARDAR RESULTADO
# --------------------------------------------------
ruta_salida = BASE_DIR / "data" / "casos_clase_0_validacion.csv"

casos_cero.to_csv(
    ruta_salida,
    index=True,
    encoding="utf-8-sig"
)

print("\nArchivo generado:")
print(ruta_salida)