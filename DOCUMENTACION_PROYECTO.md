# Documentación detallada del proyecto

## 1. ¿Qué es esta página?

Esta página es una aplicación web desarrollada con Flask que permite analizar la radiación solar y el riesgo de exposición ultravioleta (UV) en Barrioqulla, Colombia. Su propósito es convertir datos meteorológicos y satelitales en información visual y cuantitativa que pueda entenderse fácilmente por estudiantes, investigadores y personas interesadas en clima, energía solar y salud ambiental.

La aplicación reúne cuatro grandes elementos:

- Un resumen de variables ambientales históricas.
- Una gráfica temporal de evolución anual.
- Un mapa geográfico con las zonas del municipio.
- Predicciones del riesgo UV y de la radiación solar.

La interfaz principal se construye en la plantilla [templates/index.html](templates/index.html) y la lógica de visualización y renderizado se encuentra en [static/js/main.js](static/js/main.js). El backend que procesa los datos y calcula las predicciones está en [app.py](app.py).

---

## 2. ¿Qué datos usa la página?

La aplicación usa dos fuentes principales de información:

1. El archivo solar diario: [data/datos_solares_barranquilla.csv](data/datos_solares_barranquilla.csv)
2. El archivo anual de UV: [data/dataset_anual.csv](data/dataset_anual.csv)

El primer archivo contiene observaciones diarias de diversas variables meteorológicas y de irradiación para diferentes zonas de Barranquilla. El segundo consolidado una versión anual del índice UV para analizar tendencias históricas y proyecciones.

### 2.1. Dataset solar diario

El conjunto de datos principal tiene la siguiente estructura de columnas:

- FECHA: fecha de observación.
- ZONA: nombre de la zona geográfica de Barranquilla.
- LATITUD: latitud geográfica del punto de referencia.
- LONGITUD: longitud geográfica del punto de referencia.
- T2M: temperatura media del aire en °C a 2 metros de altura.
- T2M_MAX: temperatura máxima diaria del aire en °C.
- T2M_MIN: temperatura mínima diaria del aire en °C.
- RH2M: humedad relativa media en %.
- ALLSKY_SFC_SW_DWN: radiación solar diaria media en kWh/m²/día.
- ALLSKY_KT: índice de claridad de cielo o clearness index. Es una medida relativa de cuánta radiación solar llegó a superficie comparada con la máxima posible.
- WS10M: velocidad del viento a 10 metros en m/s.
- WD10M: dirección del viento a 10 metros en grados.
- PRECTOTCORR: precipitación corregida en mm.

### 2.2. ¿Qué significa cada variable?

#### FECHA
Es la fecha del registro. La aplicación agrupa los datos por año para construir series históricas.

#### ZONA
La zona geográfica de Barranquilla. La aplicación considera nueve sectores:

- Centro
- Noroccidente
- Nororiente
- Norte
- Occidente
- Oriente
- Sur
- Suroccidente
- Suroriente

Estas zonas se usan tanto para el mapa como para comparar comportamiento ambiental.

#### LATITUD y LONGITUD
Son las coordenadas geográficas del punto representativo de cada zona. Sirven para ubicar cada zona en el mapa y calcular puntos de referencia visuales.

#### T2M, T2M_MAX y T2M_MIN
Estas variables describen la temperatura del aire:

- T2M: temperatura promedio diaria.
- T2M_MAX: temperatura máxima alcanzada durante el día.
- T2M_MIN: temperatura mínima alcanzada durante la noche o el día.

Estas tres variables ayudan a entender el calor que acompaña la radiación solar.

#### RH2M
Es la humedad relativa media del aire en porcentaje (%). Cuando la humedad es alta, la sensación térmica y el comportamiento de la radiación pueden cambiar, además de afectar el confort humano y el funcionamiento de sistemas solares.

#### ALLSKY_SFC_SW_DWN
Es la radiación solar global diaria que llega a la superficie en condiciones reales de cielo con nubes, polvo u otros elementos atmosféricos. Se expresa en kWh/m²/día.

Es probablemente la variable más importante del proyecto porque mide cuánto sol llega realmente al territorio.

#### ALLSKY_KT
Es el índice de claridad. Se puede interpretar como qué tan clara o nublada está la atmósfera. Cuanto más alto es el valor, más solar disponible llega a superficie en relación con la cantidad máxima teóricamente posible.

Un valor alto indica cielo más despejado y mayor disponibilidad de radiación. Un valor bajo indica mayor nubosidad o bloqueo atmosférico.

#### WS10M
Es la velocidad del viento a 10 metros de altura. Ayuda a describir el movimiento del aire y puede influir en la sensación térmica y en la dispersión de calor, así como en el comportamiento meteorológico.

#### WD10M
Es la dirección del viento. Indica de dónde viene el viento y ayuda a interpretar fenómenos locales asociados con los vientos dominantes.

#### PRECTOTCORR
Es la precipitación corregida en milímetros (mm). Permite analizar el efecto de la lluvia y la humedad sobre la radiación y sobre los demás indicadores meteorológicos.

---

## 3. ¿Qué es el UV?

El UV hace referencia a la radiación ultravioleta. Es energía no visible cuya intensidad depende del sol, la hora del día, la estación del año, la nubosidad y la latitud. El índice UV se usa como medida de la intensidad de la radiación UV en la superficie terrestre.

En la página se usa el índice UV como indicador principal del riesgo de exposición solar. Cuando el valor es alto, la población tiene mayor riesgo de daño cutáneo, irritación ocular y otros efectos negativos por exposición prolongada.

### 3.1. ¿Qué significa un UV alto?

- UV bajo: menor riesgo relativo.
- UV moderado: riesgo moderado si se permanece largo tiempo al sol.
- UV alto: riesgo considerable para la piel y los ojos.
- UV extremo: riesgo muy alto, requiere precaución especial.

En el proyecto, la variable objetivo para la clasificación UV es la columna UV_INDEX del archivo anual y el modelo usa esa información para identificar si la condición es alta o baja.

---

## 4. ¿Qué hace la página web?

La aplicación tiene varias secciones principales:

### 4.1. Resumen general

En la parte superior muestra indicadores como:

- Registros ambientales totales.
- Rango temporal analizado.
- Temperatura promedio.
- Humedad promedio.
- Radiación solar promedio.
- Promedio anual del índice UV.
- Mínimo y máximo anual del UV.

Esto permite tener una vista rápida del comportamiento del clima y de la energía solar en la ciudad.

### 4.2. Gráfica histórica

La gráfica permite comparar variables históricas anuales. La app toma los datos del archivo respectivo y genera una serie de tiempo para:

- Temperatura promedio anual.
- Humedad promedio anual.
- Radiación solar promedio anual.
- Índice UV promedio anual.

El usuario puede seleccionar la variable que quiere ver y la gráfica cambia dinámicamente.

### 4.3. Mapa de zonas

El mapa geográfico muestra puntos sobre Barranquilla y cada punto representa una zona. Cada marcador tiene asociada:

- nombre de la zona,
- latitud,
- longitud,
- radiación promedio de esa zona.

Esto permite comparar la distribución espacial del potencial solar de la ciudad.

### 4.4. Predicción del riesgo UV

La sección de predicción calcula si un valor determinado de ALLSKY_KT corresponde a un riesgo UV alto o bajo.

Esto se hace con un modelo binario de clasificación y permite responder a la pregunta:

- Si el cielo tiene una claridad determinada, ¿es probable que la exposición UV sea alta?

El modelo usa variables como ALLSKY_KT y otros factores ambientales, y produce una probabilidad de riesgo de clase alta.

### 4.5. Predicción de radiación solar

La página también permite ingresar varios valores climatológicos y estimar la radiación solar esperada. Esta parte usa un modelo de regresión que toma entradas como:

- T2M
- T2M_MAX
- T2M_MIN
- RH2M
- ALLSKY_KT
- WS10M
- WD10M
- PRECTOTCORR
- ZONA

El modelo devuelve la radiación solar estimada en kWh/m²/día.

### 4.6. Proyección anual

La aplicación permite elegir un año futuro y obtener una proyección de radiación solar anual. Esto no es un dato observado, sino una estimación basada en una regresión autorregresiva con rezagos.

Se utiliza la serie histórica de radiación solar para proyectar valores futuros y mostrar un rango posible de estimación.

---

## 5. ¿Qué hace el backend?

El archivo [app.py](app.py) es el núcleo del sistema. Allí se realizan estas tareas:

1. Carga el dataset solar.
2. Carga el modelo de riesgo UV.
3. Carga el modelo de radiación solar.
4. Calcula resúmenes estadísticos.
5. Genera la estructura de datos para la gráfica.
6. Prepara los puntos del mapa.
7. Procesa solicitudes del usuario para predicción.

### 5.1. Carga de datos

Se leen los archivos CSV con pandas. Luego se convierten fechas en formato datetime y se reemplazan valores faltantes o anómalos como -999 por NaN.

### 5.2. Cálculos históricos

Se agrupan los datos por año para obtener medias anuales de:

- temperatura,
- humedad,
- radiación solar,
- UV.

Esto permite comparar la evolución del clima y del riesgo UV en el tiempo.

### 5.3. Predicción UV

La función 
`predecir_riesgo_uv(valor_kt)`
 toma un valor de claridad del cielo y aplica el modelo entrenado para calcular la probabilidad de que el riesgo UV sea alto o bajo.

### 5.4. Predicción de radiación solar

La función 
`predecir_radiacion(valores)`
 toma varias variables climáticas y usa el modelo entrenado para obtener un valor estimado de radiación solar.

### 5.5. Proyección anual

La función 
`pronosticar_radiacion_anual(df, anio_objetivo)`
 crea una serie temporal y proyecta un año futuro con regresión autorregresiva. El resultado muestra:

- el año objetivo,
- el valor estimado,
- mínimo y máximo estimado,
- método usado.

---

## 6. ¿Qué archivos del proyecto son importantes?

### [app.py](app.py)
Archivo principal de la aplicación. Aquí se define el backend Flask, las rutas web, la carga de datos y la lógica de predicción.

### [templates/index.html](templates/index.html)
Es la estructura visual de la página. Define secciones como resumen, gráfica, mapa y paneles de predicción.

### [static/js/main.js](static/js/main.js)
Script que dibuja la gráfica anual, conecta la interfaz con los datos JSON y renderiza el mapa.

### [static/css/styles.css](static/css/styles.css)
Diseña los colores, paneles, tarjetas, formularios y el aspecto visual general.

### [data/datos_solares_barranquilla.csv](data/datos_solares_barranquilla.csv)
Dataset principal de radiación solar y clima.

### [data/dataset_anual.csv](data/dataset_anual.csv)
Dataset anual del índice UV.

### [models/modelo_uv.joblib](models/modelo_uv.joblib)
Modelo entrenado para clasificación del riesgo UV.

### [models/modelo_radiacion.joblib](models/modelo_radiacion.joblib)
Modelo entrenado para predecir la radiación solar.

---

## 7. ¿Qué significan los resultados que aparecen en la página?

### Temperatura promedio
Indica el calor medio observado durante el periodo. Sirve para entender el clima del lugar y su relación con la intensidad de la radiación.

### Humedad promedio
Muestra la cantidad relativa de vapor de agua en el aire. La humedad puede influir en la sensación térmica y en la claridad atmosférica.

### Radiación promedio
Mide cuánta energía solar llega al suelo. Es una métrica fundamental para evaluar el potencial solar de la zona.

### UV promedio anual
Muestra el nivel típico de radiación UV durante el año, útil para comparar diferentes periodos y detectar cambios climáticos.

### Mínimo y máximo UV
Indican la variación esperada durante el periodo analizado. Si hay valores altos, esto refleja mayor riesgo de exposición.

### Predicción UV
Da un diagnóstico del riesgo asociado a un valor específico de ALLSKY_KT. Puede indicar si el nivel está en “alto” o “bajo”.

### Predicción de radiación
Estima cuánta energía solar debería llegar con ciertas condiciones climáticas. Esto sirve para valorar el comportamiento esperado.

---

## 8. ¿Por qué este proyecto es útil?

Este proyecto es útil porque combina tres temas importantes:

- Clima y energía solar.
- Salud pública y UV.
- Ciencia de datos aplicada a un caso real.

Permite:

- entender el comportamiento del sol en Barranquilla,
- detectar patrones temporales y espaciales,
- comparar zonas urbanas,
- modelar riesgo UV,
- estimar radiación solar,
- apoyar decisiones académicas, ambientales y de salud.

---

## 9. Cómo interpretar la página de manera práctica

Si un usuario quiere entender la página de un vistazo, puede seguir este flujo:

1. Revisar el resumen general de la zona seleccionada.
2. Observar la gráfica histórica para comparar tendencias.
3. Ver el mapa para identificar diferencias entre sectores.
4. Entrar a la sección de predicción UV con un valor de claridad del cielo.
5. Usar la predicción solar para estimar irradiación con condiciones climáticas concretas.
6. Proyectar un año futuro para ver el comportamiento esperado en el tiempo.

---

## 10. Conclusión

La página no es solo una visualización bonita. Es una herramienta analítica que toma datos reales de clima y radiación solar, los transforma en indicadores, y los presenta como información útil para entender cómo se comporta la energía solar y el riesgo UV en Barranquilla.

En otras palabras, la aplicación convierte una base de datos climática en un sistema de análisis, diagnóstico y predicción que permite interpretar el entorno solar de una ciudad con un enfoque académico y práctico.

---

## 11. Palabras clave del proyecto

- Irradiación solar
- Índice UV
- Meteorología
- Climatología
- Clearness index
- Aprendizaje automático
- Regresión
- Clasificación
- Barranquilla
- Energía renovable
- Salud ambiental

---

## 12. Nota final

Este documento ha sido escrito para explicar la página, los datos y la lógica del proyecto de manera clara y técnica. Si se desea, se puede ampliar con:

- un manual de usuario,
- un diccionario de variables en formato tabular,
- una explicación técnica de cada modelo,
- o una versión en formato Word para entregar como anexo académico.
