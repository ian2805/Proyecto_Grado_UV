from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from flask import Flask, render_template, request
from sklearn.linear_model import LinearRegression


# ============================================================
# CONFIGURACIÓN
# ============================================================

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

RUTA_DATOS = BASE_DIR / "data" / "datos_solares_barranquilla.csv"
RUTA_DATASET_ANUAL = BASE_DIR / "data" / "dataset_anual.csv"
RUTA_MODELO = BASE_DIR / "models" / "modelo_uv.joblib"
RUTA_MODELO_RADIACION = BASE_DIR / "models" / "modelo_radiacion.joblib"


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


def cargar_modelo_radiacion():

    if not RUTA_MODELO_RADIACION.exists():

        raise FileNotFoundError(
            f"No se encontró el modelo en: {RUTA_MODELO_RADIACION}"
        )

    paquete = joblib.load(RUTA_MODELO_RADIACION)

    return paquete["modelo"], paquete["features"]


MODELO_RADIACION, FEATURES_RADIACION = cargar_modelo_radiacion()


# ============================================================
# CARGAR DATOS NASA POWER
# ============================================================

def cargar_datos_ambientales():

    if not RUTA_DATOS.exists():

        raise FileNotFoundError(
            f"No se encontró: {RUTA_DATOS}"
        )

    df = pd.read_csv(RUTA_DATOS, parse_dates=["FECHA"])

    df["YEAR"] = df["FECHA"].dt.year

    df = df.replace(
        -999,
        np.nan
    )

    return df


def obtener_zonas(df):

    return sorted(
        df["ZONA"].dropna().unique().tolist()
    )


def preparar_puntos_mapa(df):

    puntos = (
        df[
            ["ZONA", "LATITUD", "LONGITUD", "ALLSKY_SFC_SW_DWN"]
        ]
        .groupby("ZONA", as_index=False)
        .agg(
            LATITUD=("LATITUD", "first"),
            LONGITUD=("LONGITUD", "first"),
            RADIACION_PROMEDIO=("ALLSKY_SFC_SW_DWN", "mean")
        )
    )

    return [
        {
            "zona": fila["ZONA"],
            "latitud": float(fila["LATITUD"]),
            "longitud": float(fila["LONGITUD"]),
            "radiacion": float(fila["RADIACION_PROMEDIO"])
        }
        for _, fila in puntos.iterrows()
    ]



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


def pronosticar_radiacion_anual(df, anio_objetivo):

    anual = (
        df.groupby("YEAR", sort=True)["ALLSKY_SFC_SW_DWN"]
        .mean()
        .dropna()
    )

    anio_ultimo = int(anual.index.max())

    if anio_objetivo <= anio_ultimo:
        raise ValueError(
            f"Elige un año posterior a {anio_ultimo}."
        )

    if len(anual) < 8:
        raise ValueError(
            "No hay suficientes años históricos para pronosticar."
        )

    anios = anual.index.to_numpy(dtype=float)
    valores = anual.to_numpy(dtype=float)
    cantidad_lags = 3

    def ajustar(serie):
        X = np.array([
            serie[indice - cantidad_lags:indice]
            for indice in range(cantidad_lags, len(serie))
        ])
        y = serie[cantidad_lags:]
        regresor = LinearRegression().fit(X, y)
        return regresor

    entrenamiento = valores[:-4]
    validacion = valores[-4:]
    modelo_validacion = ajustar(entrenamiento)
    historial = list(entrenamiento)
    predicciones_validacion = []

    for _ in validacion:
        prediccion = max(0.0, float(modelo_validacion.predict([historial[-cantidad_lags:]])[0]))
        predicciones_validacion.append(prediccion)
        historial.append(prediccion)

    error_validacion = float(
        np.mean(np.abs(validacion - np.array(predicciones_validacion)))
    )

    modelo = ajustar(valores)
    historial = list(valores)

    for _ in range(anio_ultimo + 1, anio_objetivo + 1):
        prediccion = max(0.0, float(modelo.predict([historial[-cantidad_lags:]])[0]))
        historial.append(prediccion)

    valor = historial[-1]
    margen = max(error_validacion * 1.96, 0.15)

    return {
        "YEAR": int(anio_objetivo),
        "RADIACION": valor,
        "MINIMO": max(0.0, valor - margen),
        "MAXIMO": valor + margen,
        "ERROR_VALIDACION": error_validacion,
        "ANIO_ULTIMO": anio_ultimo,
        "METODO": "Regresión autorregresiva anual con 3 rezagos"
    }


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


def predecir_radiacion(valores):

    entrada = pd.DataFrame(
        [valores],
        columns=FEATURES_RADIACION
    )

    prediccion = float(
        MODELO_RADIACION.predict(entrada)[0]
    )

    return max(0.0, prediccion)


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

    zonas = obtener_zonas(df)

    datos_mapa = preparar_puntos_mapa(df)

    zona_solicitada = (
        request.values.get("zona", "Centro")
    )

    zona_activa = (
        zona_solicitada
        if zona_solicitada in zonas
        else zonas[0]
    )

    df = df[df["ZONA"] == zona_activa].copy()

    valores_referencia = {
        columna: round(float(df[columna].median()), 2)
        for columna in FEATURES_RADIACION
        if columna != "ZONA"
    }

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

    radiacion_minima = float(
        df["ALLSKY_SFC_SW_DWN"].min()
    )

    radiacion_maxima = float(
        df["ALLSKY_SFC_SW_DWN"].max()
    )

    radiacion_promedio_zona = float(
        df["ALLSKY_SFC_SW_DWN"].mean()
    )


    # --------------------------------------------------------
    # PREDICCIÓN
    # --------------------------------------------------------

    resultado_prediccion = None
    error_prediccion = None
    valor_ingresado = None
    resultado_radiacion = None
    error_radiacion = None
    resultado_proyeccion = None
    error_proyeccion = None


    if request.method == "POST":

        accion = request.form.get("accion")

        if accion == "proyeccion":

            try:
                anio_objetivo = int(request.form["anio_objetivo"])

                if anio_objetivo > 2100:
                    raise ValueError(
                        "El año máximo permitido es 2100."
                    )

                resultado_proyeccion = pronosticar_radiacion_anual(
                    df,
                    anio_objetivo
                )

            except (KeyError, TypeError, ValueError) as error:

                error_proyeccion = str(error)

        elif accion == "radiacion":

            resultado_prediccion = None
            error_prediccion = None

            try:

                valores = {
                    "T2M": float(request.form["T2M"]),
                    "T2M_MAX": float(request.form["T2M_MAX"]),
                    "T2M_MIN": float(request.form["T2M_MIN"]),
                    "RH2M": float(request.form["RH2M"]),
                    "ALLSKY_KT": float(request.form["ALLSKY_KT_RADIACION"]),
                    "WS10M": float(request.form["WS10M"]),
                    "WD10M": float(request.form["WD10M"]),
                    "PRECTOTCORR": float(request.form["PRECTOTCORR"]),
                    "ZONA": zona_activa,
                }

                if not all(
                    np.isfinite(valor)
                    for valor in valores.values()
                    if isinstance(valor, float)
                ):

                    raise ValueError

                if not (
                    kt_minimo
                    <= valores["ALLSKY_KT"]
                    <= kt_maximo
                ):

                    error_radiacion = (
                        "El índice de claridad está fuera del rango "
                        f"histórico de la zona ({kt_minimo:.2f} – "
                        f"{kt_maximo:.2f})."
                    )

                else:

                    prediccion = predecir_radiacion(valores)
                    resultado_radiacion = {
                        "valor": prediccion,
                        "promedio": radiacion_promedio_zona,
                        "diferencia": prediccion - radiacion_promedio_zona
                    }

            except (KeyError, ValueError):

                error_radiacion = (
                    "Completa todos los valores con números válidos."
                )

        else:

            texto_valor = (
                request.form.get("allsky_kt", "")
                .strip()
                .replace(",", ".")
            )

            try:

                valor_ingresado = float(texto_valor)

                if not np.isfinite(valor_ingresado):
                    raise ValueError

                if not (kt_minimo <= valor_ingresado <= kt_maximo):

                    error_prediccion = (
                        "El valor está fuera del rango histórico observado "
                        f"({kt_minimo:.2f} – {kt_maximo:.2f})."
                    )

                else:

                    resultado_prediccion = predecir_riesgo_uv(
                        valor_ingresado
                    )

            except ValueError:

                error_prediccion = "Ingresa un valor numérico válido."


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
            valor_ingresado,

        zonas=
            zonas,

        zona_activa=
            zona_activa,

        datos_mapa=
            datos_mapa,

        valores_referencia=
            valores_referencia,

        resultado_radiacion=
            resultado_radiacion,

        error_radiacion=
            error_radiacion,

        resultado_proyeccion=
            resultado_proyeccion,

        error_proyeccion=
            error_proyeccion,

        radiacion_minima=
            radiacion_minima,

        radiacion_maxima=
            radiacion_maxima
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