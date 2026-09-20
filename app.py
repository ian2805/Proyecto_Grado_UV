from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from flask import Flask, render_template, request


# ============================================================
# CONFIGURACIÓN
# ============================================================

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

RUTA_DATOS = BASE_DIR / "data" / "datos_nasa.csv"
RUTA_DATASET_ANUAL = BASE_DIR / "data" / "dataset_anual.csv"
RUTA_MODELO = BASE_DIR / "models" / "modelo_uv.joblib"


# ============================================================
# CARGAR MODELO
# ============================================================

def cargar_modelo():

    if not RUTA_MODELO.exists():

        raise FileNotFoundError(
            f"No se encontró el modelo en: {RUTA_MODELO}"
        )

    paquete = joblib.load(
        RUTA_MODELO
    )

    modelo = paquete["modelo"]
    features = paquete["features"]
    umbral = float(
        paquete["umbral"]
    )

    if features != ["ALLSKY_KT"]:

        raise ValueError(
            "El modelo cargado no corresponde "
            "al modelo basado en ALLSKY_KT."
        )

    return (
        modelo,
        features,
        umbral
    )


MODELO_UV, FEATURES_MODELO, UMBRAL_MODELO = (
    cargar_modelo()
)


# ============================================================
# CARGAR DATOS NASA POWER
# ============================================================

def cargar_datos_ambientales():

    if not RUTA_DATOS.exists():

        raise FileNotFoundError(
            f"No se encontró: {RUTA_DATOS}"
        )

    df = pd.read_csv(
        RUTA_DATOS,
        sep=";",
        skiprows=18
    )

    df = df.replace(
        -999,
        np.nan
    )

    return df



# CARGAR DATASET ANUAL UV


def cargar_datos_uv_anuales():

    if not RUTA_DATASET_ANUAL.exists():

        raise FileNotFoundError(
            "No se encontró dataset_anual.csv. "
            "Ejecuta primero "
            "src/preparar_dataset_anual.py"
        )

    df = pd.read_csv(
        RUTA_DATASET_ANUAL
    )

    columnas = {
        "YEAR",
        "UV_INDEX"
    }

    faltantes = columnas.difference(
        df.columns
    )

    if faltantes:

        raise ValueError(
            "dataset_anual.csv no contiene "
            "las columnas necesarias."
        )

    return df


# ============================================================
# DATOS PARA LA GRÁFICA
# ============================================================

def calcular_historicos(
    df_ambiental,
    df_uv_anual
):

    variables = [
        "T2M",
        "RH2M",
        "ALLSKY_SFC_SW_DWN"
    ]

    ambiental = (
        df_ambiental
        .groupby(
            "YEAR",
            sort=True
        )[variables]
        .mean()
        .reset_index()
    )


    # Agregar UV anual.
    historico = ambiental.merge(
        df_uv_anual[
            [
                "YEAR",
                "UV_INDEX"
            ]
        ],
        on="YEAR",
        how="left"
    )


    resultado = []

    for _, fila in historico.iterrows():

        registro = {
            "YEAR": int(
                fila["YEAR"]
            )
        }

        for variable in [
            "T2M",
            "RH2M",
            "ALLSKY_SFC_SW_DWN",
            "UV_INDEX"
        ]:

            valor = fila.get(
                variable
            )

            registro[variable] = (
                float(valor)
                if pd.notna(valor)
                else None
            )

        resultado.append(
            registro
        )

    return resultado


# ============================================================
# PREDICCIÓN
# ============================================================

def predecir_riesgo_uv(
    valor_kt
):

    entrada = pd.DataFrame(
        [
            {
                "ALLSKY_KT":
                    valor_kt
            }
        ],
        columns=FEATURES_MODELO
    )

    score_alto = float(
        MODELO_UV
        .predict_proba(
            entrada
        )[0, 1]
    )

    clase = (
        "ALTO"
        if score_alto >= UMBRAL_MODELO
        else "BAJO"
    )

    return {
        "clase":
            clase,

        "score":
            score_alto,

        "valor_kt":
            valor_kt,

        "umbral":
            UMBRAL_MODELO
    }


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route(
    "/",
    methods=[
        "GET",
        "POST"
    ]
)
def inicio():

    # --------------------------------------------------------
    # DATOS
    # --------------------------------------------------------

    df = (
        cargar_datos_ambientales()
    )

    df_uv = (
        cargar_datos_uv_anuales()
    )


    # --------------------------------------------------------
    # RESUMEN AMBIENTAL
    # --------------------------------------------------------

    registros = len(
        df
    )

    anio_inicio = int(
        df["YEAR"].min()
    )

    anio_fin = int(
        df["YEAR"].max()
    )

    temperatura_promedio = round(
        float(
            df["T2M"].mean()
        ),
        2
    )

    humedad_promedio = round(
        float(
            df["RH2M"].mean()
        ),
        2
    )

    radiacion_promedio = round(
        float(
            df[
                "ALLSKY_SFC_SW_DWN"
            ].mean()
        ),
        2
    )


    # --------------------------------------------------------
    # RESUMEN UV
    # --------------------------------------------------------

    uv_promedio = round(
        float(
            df_uv[
                "UV_INDEX"
            ].mean()
        ),
        2
    )

    uv_minimo = round(
        float(
            df_uv[
                "UV_INDEX"
            ].min()
        ),
        2
    )

    uv_maximo = round(
        float(
            df_uv[
                "UV_INDEX"
            ].max()
        ),
        2
    )

    uv_anio_inicio = int(
        df_uv["YEAR"].min()
    )

    uv_anio_fin = int(
        df_uv["YEAR"].max()
    )


    # --------------------------------------------------------
    # HISTÓRICOS
    # --------------------------------------------------------

    datos_historicos = (
        calcular_historicos(
            df,
            df_uv
        )
    )


    # --------------------------------------------------------
    # RANGO ALLSKY_KT
    # --------------------------------------------------------

    valores_kt = (
        df[
            "ALLSKY_KT"
        ]
        .dropna()
    )

    kt_minimo = float(
        valores_kt.min()
    )

    kt_maximo = float(
        valores_kt.max()
    )


    # --------------------------------------------------------
    # PREDICCIÓN
    # --------------------------------------------------------

    resultado_prediccion = None
    error_prediccion = None
    valor_ingresado = None


    if request.method == "POST":

        texto_valor = (
            request.form
            .get(
                "allsky_kt",
                ""
            )
            .strip()
            .replace(
                ",",
                "."
            )
        )

        try:

            valor_ingresado = float(
                texto_valor
            )

            if not np.isfinite(
                valor_ingresado
            ):

                raise ValueError


            if not (
                kt_minimo
                <= valor_ingresado
                <= kt_maximo
            ):

                error_prediccion = (
                    "El valor está fuera del "
                    "rango histórico observado "
                    f"({kt_minimo:.2f} – "
                    f"{kt_maximo:.2f})."
                )

            else:

                resultado_prediccion = (
                    predecir_riesgo_uv(
                        valor_ingresado
                    )
                )


        except ValueError:

            error_prediccion = (
                "Ingresa un valor numérico "
                "válido."
            )


    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    return render_template(
        "index.html",

        registros=
            registros,

        anio_inicio=
            anio_inicio,

        anio_fin=
            anio_fin,

        temperatura_promedio=
            temperatura_promedio,

        humedad_promedio=
            humedad_promedio,

        radiacion_promedio=
            radiacion_promedio,

        uv_promedio=
            uv_promedio,

        uv_minimo=
            uv_minimo,

        uv_maximo=
            uv_maximo,

        uv_anio_inicio=
            uv_anio_inicio,

        uv_anio_fin=
            uv_anio_fin,

        datos_historicos=
            datos_historicos,

        kt_minimo=
            kt_minimo,

        kt_maximo=
            kt_maximo,

        umbral_modelo=
            UMBRAL_MODELO,

        resultado_prediccion=
            resultado_prediccion,

        error_prediccion=
            error_prediccion,

        valor_ingresado=
            valor_ingresado
    )


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )