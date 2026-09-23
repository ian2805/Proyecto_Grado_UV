import requests
import pandas as pd
import time
from pathlib import Path


# ============================================================
# CONFIGURACIÓN
# ============================================================

FECHA_INICIO = "2004-01-01"
FECHA_FIN = "2025-12-31"

# Puntos de referencia dentro de Barranquilla.
# Después podemos reemplazarlos por coordenadas más precisas
# de las zonas que definamos para el proyecto.

ZONAS = {
    "Norte": (11.0200, -74.8000),
    "Centro": (10.9800, -74.7900),
    "Sur": (10.9300, -74.8000),
    "Noroccidente": (11.0100, -74.8500),
    "Nororiente": (11.0100, -74.7600),
    "Occidente": (10.9700, -74.8500),
    "Oriente": (10.9700, -74.7500),
    "Suroccidente": (10.9200, -74.8500),
    "Suroriente": (10.9200, -74.7500),
}


# Variables NASA POWER
PARAMETROS = ",".join([
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "ALLSKY_SFC_SW_DWN",
    "ALLSKY_KT",
    "WS10M",
    "WD10M",
    "PRECTOTCORR"
])


# Carpeta de salida
BASE_DIR = Path(__file__).resolve().parent.parent
CARPETA_DATA = BASE_DIR / "data"
CARPETA_DATA.mkdir(exist_ok=True)

ARCHIVO_SALIDA = CARPETA_DATA / "datos_solares_barranquilla.csv"


# ============================================================
# DESCARGAR UNA ZONA
# ============================================================

def descargar_zona(nombre, latitud, longitud):

    print("=" * 70)
    print(f"Descargando: {nombre}")
    print(f"Latitud: {latitud}")
    print(f"Longitud: {longitud}")
    print("=" * 70)

    url = "https://power.larc.nasa.gov/api/temporal/daily/point"

    parametros = {
        "parameters": PARAMETROS,
        "community": "RE",
        "longitude": longitud,
        "latitude": latitud,
        "start": FECHA_INICIO.replace("-", ""),
        "end": FECHA_FIN.replace("-", ""),
        "format": "JSON"
    }

    respuesta = requests.get(
        url,
        params=parametros,
        timeout=120
    )

    respuesta.raise_for_status()

    datos = respuesta.json()

    valores = datos["properties"]["parameter"]

    fechas = sorted(
        valores["T2M"].keys()
    )

    registros = []

    for fecha in fechas:

        fila = {
            "FECHA": pd.to_datetime(fecha),
            "ZONA": nombre,
            "LATITUD": latitud,
            "LONGITUD": longitud
        }

        for variable in PARAMETROS.split(","):

            fila[variable] = valores[variable].get(fecha)

        registros.append(fila)

    df = pd.DataFrame(registros)

    print(f"Registros descargados: {len(df)}")

    return df


# ============================================================
# PROCESO PRINCIPAL
# ============================================================

def main():

    print()
    print("=" * 70)
    print("DESCARGA DE DATOS SOLARES - BARRANQUILLA")
    print("=" * 70)
    print()

    todos = []

    for nombre, coordenadas in ZONAS.items():

        latitud, longitud = coordenadas

        try:

            df = descargar_zona(
                nombre,
                latitud,
                longitud
            )

            todos.append(df)

            # Pequeña pausa para evitar demasiadas solicitudes seguidas
            time.sleep(1)

        except Exception as e:

            print()
            print(f"ERROR EN {nombre}:")
            print(e)
            print()

    if not todos:

        print("No se pudieron descargar datos.")
        return

    # Unir todas las zonas
    dataset = pd.concat(
        todos,
        ignore_index=True
    )

    # Ordenar
    dataset = dataset.sort_values(
        ["FECHA", "ZONA"]
    ).reset_index(drop=True)

    # Guardar
    dataset.to_csv(
        ARCHIVO_SALIDA,
        index=False,
        encoding="utf-8"
    )

    # ========================================================
    # RESUMEN
    # ========================================================

    print()
    print("=" * 70)
    print("DESCARGA COMPLETADA")
    print("=" * 70)

    print(f"Archivo:")
    print(ARCHIVO_SALIDA)

    print()
    print(f"Registros totales: {len(dataset):,}")

    print()
    print("Zonas:")
    print(dataset["ZONA"].value_counts())

    print()
    print("Periodo:")
    print(dataset["FECHA"].min())
    print("a")
    print(dataset["FECHA"].max())

    print()
    print("Columnas:")
    print(list(dataset.columns))

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()