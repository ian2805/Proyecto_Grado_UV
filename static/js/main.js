(() => {
    "use strict";


    const fuente =
        document.getElementById(
            "datos-historicos"
        );

    const selector =
        document.getElementById(
            "variable-historica"
        );

    const contenedor =
        document.getElementById(
            "contenedor-grafica"
        );

    const grafica =
        document.getElementById(
            "grafica-historica"
        );

    const titulo =
        document.getElementById(
            "titulo-serie"
        );

    const detalle =
        document.getElementById(
            "detalle-punto"
        );

    const nota =
        document.getElementById(
            "nota-serie"
        );

    const estado =
        document.getElementById(
            "estado-grafica"
        );


    if (
        !fuente ||
        !selector ||
        !contenedor ||
        !grafica
    ) {
        return;
    }


    // =========================================================
    // VARIABLES
    // =========================================================

    const variables = {

        UV_INDEX: {

            titulo:
                "Índice UV promedio anual",

            eje:
                "Índice UV",

            unidad:
                "",

            nota:
                "Promedio anual calculado a partir de los registros de índice UV disponibles mediante NASA Giovanni."
        },


        T2M: {

            titulo:
                "Temperatura promedio anual",

            eje:
                "Temperatura (°C)",

            unidad:
                " °C",

            nota:
                "Promedio anual de la temperatura del aire a 2 metros."
        },


        RH2M: {

            titulo:
                "Humedad promedio anual",

            eje:
                "Humedad relativa (%)",

            unidad:
                " %",

            nota:
                "Promedio anual de la humedad relativa a 2 metros."
        },


        ALLSKY_SFC_SW_DWN: {

            titulo:
                "Radiación solar promedio anual",

            eje:
                "Valor del archivo",

            unidad:
                "",

            nota:
                "Promedio anual directo de los registros disponibles en NASA POWER."
        }

    };


    const formatoValor =
        new Intl.NumberFormat(
            "es-CO",
            {
                minimumFractionDigits:
                    2,

                maximumFractionDigits:
                    2
            }
        );


    // =========================================================
    // LEER JSON
    // =========================================================

    let datos;


    try {

        datos = JSON.parse(
            fuente.textContent
        );

        if (
            !Array.isArray(
                datos
            ) ||
            datos.length === 0
        ) {

            throw new Error(
                "Sin datos"
            );
        }

    } catch {

        estado.textContent =
            "No hay datos históricos disponibles.";

        return;
    }


    let indiceActivo =
        datos.length - 1;

    let coordenadas =
        [];

    let guia;
    let marcador;


    // =========================================================
    // SVG
    // =========================================================

    function crearElemento(
        nombre,
        atributos,
        texto
    ) {

        const elemento =
            document.createElementNS(
                "http://www.w3.org/2000/svg",
                nombre
            );


        Object.entries(
            atributos
        ).forEach(
            ([clave, valor]) => {

                elemento.setAttribute(
                    clave,
                    valor
                );

            }
        );


        if (
            texto !== undefined
        ) {

            elemento.textContent =
                texto;
        }


        grafica.appendChild(
            elemento
        );


        return elemento;
    }


    // =========================================================
    // ESCALA
    // =========================================================

    function calcularEscala(
        valores
    ) {

        const minimo =
            Math.min(
                ...valores
            );

        const maximo =
            Math.max(
                ...valores
            );


        const amplitud =
            maximo -
            minimo ||
            Math.abs(
                minimo
            ) * 0.1 ||
            1;


        const margen =
            amplitud * 0.12;


        const pasoAproximado =
            (
                maximo -
                minimo +
                2 * margen
            ) / 5;


        const potencia =
            10 **
            Math.floor(
                Math.log10(
                    pasoAproximado
                )
            );


        const factor =
            [
                1,
                2,
                5,
                10
            ].find(
                valor =>
                    valor *
                    potencia >=
                    pasoAproximado
            ) || 10;


        const paso =
            factor *
            potencia;


        return {

            minimo:
                Math.floor(
                    (
                        minimo -
                        margen
                    ) /
                    paso
                ) *
                paso,

            maximo:
                Math.ceil(
                    (
                        maximo +
                        margen
                    ) /
                    paso
                ) *
                paso,

            paso:
                paso
        };
    }


    // =========================================================
    // SELECCIONAR AÑO
    // =========================================================

    function seleccionarAnio(
        indice
    ) {

        indiceActivo =
            Math.max(
                0,
                Math.min(
                    datos.length - 1,
                    indice
                )
            );


        const punto =
            coordenadas[
                indiceActivo
            ];


        const variable =
            variables[
                selector.value
            ];


        guia.setAttribute(
            "x1",
            punto.x
        );

        guia.setAttribute(
            "x2",
            punto.x
        );


        if (
            punto.y === null
        ) {

            marcador.setAttribute(
                "visibility",
                "hidden"
            );

        } else {

            marcador.setAttribute(
                "visibility",
                "visible"
            );

            marcador.setAttribute(
                "cx",
                punto.x
            );

            marcador.setAttribute(
                "cy",
                punto.y
            );
        }


        const valor =
            punto.y === null
                ? "Sin datos disponibles"
                : (
                    formatoValor.format(
                        punto.valor
                    ) +
                    variable.unidad
                );


        detalle.textContent =
            `${datos[indiceActivo].YEAR} · ` +
            `${variable.titulo}: ` +
            `${valor}`;
    }


    // =========================================================
    // DIBUJAR
    // =========================================================

    function dibujar() {

        const variable =
            variables[
                selector.value
            ];


        const valores =
            datos.map(
                fila =>
                    fila[
                        selector.value
                    ]
            );


        const validos =
            valores.filter(
                Number.isFinite
            );


        titulo.textContent =
            variable.titulo;

        nota.textContent =
            variable.nota;


        if (
            validos.length === 0
        ) {

            estado.textContent =
                "No hay observaciones válidas para esta variable.";

            estado.hidden =
                false;

            contenedor.hidden =
                true;

            detalle.textContent =
                "";

            return;
        }


        estado.hidden =
            true;

        contenedor.hidden =
            false;


        const ancho =
            contenedor.clientWidth;

        const alto =
            contenedor.clientHeight;


        if (
            !ancho ||
            !alto
        ) {

            return;
        }


        const margen = {

            izquierda:
                54,

            derecha:
                18,

            arriba:
                38,

            abajo:
                54
        };


        const anchoUtil =
            ancho -
            margen.izquierda -
            margen.derecha;


        const altoUtil =
            alto -
            margen.arriba -
            margen.abajo;


        const primerAnio =
            datos[0].YEAR;


        const ultimoAnio =
            datos[
                datos.length - 1
            ].YEAR;


        const escala =
            calcularEscala(
                validos
            );


        const posicionX =
            anio =>

                margen.izquierda +

                (
                    ultimoAnio ===
                    primerAnio

                        ? 0.5

                        : (
                            anio -
                            primerAnio
                        ) /
                        (
                            ultimoAnio -
                            primerAnio
                        )
                )

                * anchoUtil;


        const posicionY =
            valor =>

                margen.arriba +

                (
                    (
                        escala.maximo -
                        valor
                    ) /
                    (
                        escala.maximo -
                        escala.minimo
                    )
                )

                * altoUtil;


        const formatoEje =
            new Intl.NumberFormat(
                "es-CO",
                {
                    maximumFractionDigits:
                        Math.max(
                            0,
                            -
                            Math.floor(
                                Math.log10(
                                    escala.paso
                                )
                            )
                        )
                }
            );


        grafica.replaceChildren();


        grafica.setAttribute(
            "viewBox",
            `0 0 ${ancho} ${alto}`
        );


        crearElemento(
            "title",
            {},
            `${variable.titulo}. Barranquilla, Colombia.`
        );


        crearElemento(
            "text",
            {
                x:
                    margen.izquierda,

                y:
                    16
            },
            variable.eje
        );


        // =====================================================
        // REJILLA
        // =====================================================

        const intervalos =
            Math.round(
                (
                    escala.maximo -
                    escala.minimo
                ) /
                escala.paso
            );


        for (
            let i = 0;
            i <= intervalos;
            i += 1
        ) {

            const valor =
                escala.minimo +
                i *
                escala.paso;


            const y =
                posicionY(
                    valor
                );


            crearElemento(
                "line",
                {
                    class:
                        "grafica-rejilla",

                    x1:
                        margen.izquierda,

                    y1:
                        y,

                    x2:
                        ancho -
                        margen.derecha,

                    y2:
                        y
                }
            );


            crearElemento(
                "text",
                {
                    x:
                        margen.izquierda -
                        10,

                    y:
                        y + 4,

                    "text-anchor":
                        "end"
                },

                formatoEje.format(
                    valor
                )
            );
        }


        // =====================================================
        // AÑOS
        // =====================================================

        const intervaloEtiquetas =
            ancho < 550
                ? 5
                : ancho < 950
                    ? 2
                    : 1;


        datos.forEach(
            (
                fila,
                indice
            ) => {

                if (
                    indice %
                    intervaloEtiquetas
                    !== 0
                    &&
                    indice !==
                    datos.length - 1
                ) {

                    return;
                }


                crearElemento(
                    "text",
                    {
                        x:
                            posicionX(
                                fila.YEAR
                            ),

                        y:
                            alto -
                            margen.abajo +
                            22,

                        "text-anchor":
                            "middle"
                    },

                    fila.YEAR
                );

            }
        );


        crearElemento(
            "text",
            {
                x:
                    margen.izquierda +
                    anchoUtil / 2,

                y:
                    alto - 6,

                "text-anchor":
                    "middle"
            },

            "Año"
        );


        // =====================================================
        // COORDENADAS
        // =====================================================

        coordenadas =
            datos.map(
                (
                    fila,
                    indice
                ) => {

                    const valor =
                        valores[
                            indice
                        ];


                    return {

                        x:
                            posicionX(
                                fila.YEAR
                            ),

                        y:
                            Number.isFinite(
                                valor
                            )
                                ? posicionY(
                                    valor
                                )
                                : null,

                        valor:
                            valor
                    };

                }
            );


        // =====================================================
        // LÍNEA
        // =====================================================

        let trazo =
            "";

        let nuevoTramo =
            true;


        coordenadas.forEach(
            punto => {

                if (
                    punto.y === null
                ) {

                    nuevoTramo =
                        true;

                    return;
                }


                trazo +=
                    `${
                        nuevoTramo
                            ? "M"
                            : "L"
                    }${punto.x},${punto.y} `;


                nuevoTramo =
                    false;

            }
        );


        crearElemento(
            "path",
            {
                class:
                    "grafica-linea",

                d:
                    trazo
            }
        );


        // =====================================================
        // PUNTOS
        // =====================================================

        coordenadas.forEach(
            (
                punto,
                indice
            ) => {

                if (
                    punto.y === null
                ) {

                    return;
                }


                const circulo =
                    crearElemento(
                        "circle",
                        {
                            class:
                                "grafica-punto",

                            cx:
                                punto.x,

                            cy:
                                punto.y,

                            r:
                                3
                        }
                    );


                const ayuda =
                    document.createElementNS(
                        "http://www.w3.org/2000/svg",
                        "title"
                    );


                ayuda.textContent =
                    `${datos[indice].YEAR}: ` +
                    `${formatoValor.format(punto.valor)}` +
                    `${variable.unidad}`;


                circulo.appendChild(
                    ayuda
                );

            }
        );


        // =====================================================
        // GUÍA
        // =====================================================

        guia =
            crearElemento(
                "line",
                {
                    class:
                        "grafica-guia",

                    y1:
                        margen.arriba,

                    y2:
                        alto -
                        margen.abajo
                }
            );


        marcador =
            crearElemento(
                "circle",
                {
                    class:
                        "grafica-seleccion",

                    r:
                        5
                }
            );


        seleccionarAnio(
            indiceActivo
        );
    }


    // =========================================================
    // CURSOR
    // =========================================================

    function consultarPosicion(
        evento
    ) {

        if (
            coordenadas.length === 0
        ) {

            return;
        }


        const rectangulo =
            grafica.getBoundingClientRect();


        const x =
            (
                evento.clientX -
                rectangulo.left
            )

            *

            grafica.viewBox
                .baseVal
                .width

            /

            rectangulo.width;


        const indice =
            coordenadas.reduce(
                (
                    mejor,
                    punto,
                    actual
                ) =>

                    Math.abs(
                        punto.x -
                        x
                    )

                    <

                    Math.abs(
                        coordenadas[
                            mejor
                        ].x -
                        x
                    )

                        ? actual
                        : mejor,

                0
            );


        seleccionarAnio(
            indice
        );
    }


    // =========================================================
    // EVENTOS
    // =========================================================

    selector.disabled =
        false;


    selector.addEventListener(
        "change",
        dibujar
    );


    grafica.addEventListener(
        "pointermove",
        consultarPosicion
    );


    grafica.addEventListener(
        "pointerdown",
        evento => {

            grafica.focus({
                preventScroll:
                    true
            });

            consultarPosicion(
                evento
            );
        }
    );


    grafica.addEventListener(
        "keydown",
        evento => {

            const indices = {

                ArrowLeft:
                    indiceActivo - 1,

                ArrowRight:
                    indiceActivo + 1,

                Home:
                    0,

                End:
                    datos.length - 1
            };


            if (
                Object.hasOwn(
                    indices,
                    evento.key
                )
            ) {

                evento.preventDefault();

                seleccionarAnio(
                    indices[
                        evento.key
                    ]
                );
            }
        }
    );


    // =========================================================
    // INICIAR
    // =========================================================

    dibujar();


    if (
        "ResizeObserver"
        in window
    ) {

        new ResizeObserver(
            dibujar
        ).observe(
            contenedor
        );
    }

})();