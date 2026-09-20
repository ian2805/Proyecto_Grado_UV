from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RUTA = BASE_DIR / "data" / "dataset_ml.csv"

df = pd.read_csv(RUTA)

uv = df["UV_INDEX"]

print("=" * 55)
print("ANÁLISIS DE LA VARIABLE OBJETIVO: UV_INDEX")
print("=" * 55)

print(f"\nTotal de registros: {len(df)}")
print(f"UV mínimo: {uv.min():.2f}")
print(f"UV máximo: {uv.max():.2f}")
print(f"UV promedio: {uv.mean():.2f}")
print(f"Mediana UV: {uv.median():.2f}")

print("\nDISTRIBUCIÓN POR CATEGORÍAS")
print("-" * 55)

categorias = pd.cut(
    uv,
    bins=[-float("inf"), 2, 5, 7, 10, float("inf")],
    labels=[
        "Bajo (0-2)",
        "Moderado (3-5)",
        "Alto (6-7)",
        "Muy alto (8-10)",
        "Extremo (11+)"
    ]
)

conteo = categorias.value_counts().sort_index()

for categoria, cantidad in conteo.items():
    porcentaje = cantidad / len(df) * 100
    print(f"{categoria}: {cantidad} ({porcentaje:.2f}%)")


print("\nCLASIFICACIÓN BINARIA PROPUESTA")
print("-" * 55)

# Por ahora solo analizamos este umbral.
# NO se guarda todavía en el dataset.
clase = uv.apply(
    lambda valor: "ALTO" if valor >= 6 else "BAJO"
)

conteo_binario = clase.value_counts()

for categoria, cantidad in conteo_binario.items():
    porcentaje = cantidad / len(df) * 100
    print(f"{categoria}: {cantidad} ({porcentaje:.2f}%)")