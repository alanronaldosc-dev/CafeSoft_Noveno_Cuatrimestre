# =============================================================================
# entrenamiento_clientes.py
#
# FASE 4
# ENTRENAMIENTO, PRUEBA Y VALIDACIÓN DEL MODELO K-MEANS
#
# Objetivo:
#
# Evaluar la estabilidad del modelo K-Means utilizando una división
# de los datos en entrenamiento y prueba.
#
# Flujo:
#
# segmentacion_pca.json
#           │
#           ▼
#   División 80% - 20%
#           │
#           ▼
# Entrenar K-Means
#           │
#           ▼
# Predecir conjunto de prueba
#           │
#           ▼
# Calcular métricas
#           │
#           ▼
# entrenamiento_prueba.json
# =============================================================================

import json
import os

import numpy as np

from sklearn.cluster import KMeans

from sklearn.metrics import (

    silhouette_score

)

from sklearn.model_selection import (

    train_test_split

)

# =============================================================================
# RUTAS
# =============================================================================

RUTA_ACTUAL = os.path.dirname(

    os.path.abspath(__file__)

)

ARCHIVO_PCA = os.path.join(

    RUTA_ACTUAL,

    "segmentacion_pca.json"

)

ARCHIVO_WCSS = os.path.join(

    RUTA_ACTUAL,

    "segmentacion_wcss.json"

)

ARCHIVO_SALIDA = os.path.join(

    RUTA_ACTUAL,

    "entrenamiento_prueba.json"

)

# =============================================================================
# CARGAR DATOS
# =============================================================================

def cargar_datos():

    if not os.path.exists(ARCHIVO_PCA):

        raise FileNotFoundError(

            "No existe segmentacion_pca.json"

        )

    if not os.path.exists(ARCHIVO_WCSS):

        raise FileNotFoundError(

            "No existe segmentacion_wcss.json"

        )

    with open(

        ARCHIVO_PCA,

        "r",

        encoding="utf-8"

    ) as archivo:

        datos_pca = json.load(

            archivo

        )

    with open(

        ARCHIVO_WCSS,

        "r",

        encoding="utf-8"

    ) as archivo:

        datos_wcss = json.load(

            archivo

        )

    clientes = datos_pca["clientes"]

    k = datos_wcss["k_optimo"]

    return clientes, k


# =============================================================================
# PREPARAR MATRIZ PCA
# =============================================================================

def obtener_coordenadas(

    clientes

):

    coordenadas = []

    for cliente in clientes:

        coordenadas.append([

            float(cliente["pc1"]),

            float(cliente["pc2"])

        ])

    return np.array(

        coordenadas

    )


# =============================================================================
# DIVISIÓN ENTRENAMIENTO / PRUEBA
# =============================================================================

def dividir_datos(

    coordenadas,

    porcentaje_prueba=0.20

):

    entrenamiento, prueba = train_test_split(

        coordenadas,

        test_size=porcentaje_prueba,

        random_state=42,

        shuffle=True

    )

    return entrenamiento, prueba


# =============================================================================
# ENTRENAMIENTO DEL MODELO
# =============================================================================

def entrenar_modelo(

    entrenamiento,

    k

):

    modelo = KMeans(

        n_clusters=k,

        init="k-means++",

        random_state=42,

        n_init=10,

        max_iter=300

    )

    modelo.fit(

        entrenamiento

    )

    return modelo


# =============================================================================
# PREDICCIÓN DEL CONJUNTO DE PRUEBA
# =============================================================================

def predecir(

    modelo,

    prueba

):

    etiquetas = modelo.predict(

        prueba

    )

    return etiquetas
# =============================================================================
# CÁLCULO DEL WCSS
# =============================================================================

def calcular_wcss(

    modelo,

    datos

):

    etiquetas = modelo.predict(

        datos

    )

    centroides = modelo.cluster_centers_

    suma = 0.0

    for punto, cluster in zip(

        datos,

        etiquetas

    ):

        distancia = np.sum(

            (punto - centroides[cluster]) ** 2

        )

        suma += distancia

    return round(

        float(suma),

        4

    )


# =============================================================================
# CÁLCULO DEL ÍNDICE DE SILUETA
# =============================================================================

def calcular_silueta(

    datos,

    etiquetas

):

    clusters = np.unique(

        etiquetas

    )

    if len(clusters) < 2:

        return None

    if len(datos) <= len(clusters):

        return None

    try:

        score = silhouette_score(

            datos,

            etiquetas

        )

        return round(

            float(score),

            4

        )

    except Exception:

        return None


# =============================================================================
# DIFERENCIA PORCENTUAL
# =============================================================================

def diferencia_porcentual(

    entrenamiento,

    prueba

):

    if entrenamiento == 0:

        return 0.0

    diferencia = abs(

        entrenamiento - prueba

    )

    porcentaje = (

        diferencia /

        entrenamiento

    ) * 100

    return round(

        float(porcentaje),

        2

    )


# =============================================================================
# INTERPRETACIÓN AUTOMÁTICA
# =============================================================================

def interpretar_resultados(

    wcss_train,

    wcss_test,

    silueta_train,

    silueta_test

):

    diferencia = diferencia_porcentual(

        wcss_train,

        wcss_test

    )

    if diferencia <= 10:

        estabilidad = "Excelente"

    elif diferencia <= 20:

        estabilidad = "Buena"

    elif diferencia <= 35:

        estabilidad = "Aceptable"

    else:

        estabilidad = "Baja"

    if silueta_train is None:

        calidad = "No fue posible calcular la silueta del entrenamiento."

    elif silueta_train >= 0.70:

        calidad = "Excelente separación entre clusters."

    elif silueta_train >= 0.50:

        calidad = "Buena separación entre clusters."

    elif silueta_train >= 0.25:

        calidad = "Separación aceptable."

    else:

        calidad = "Los clusters presentan traslape."

    if silueta_test is None:

        prueba = (

            "No fue posible calcular la silueta del conjunto de prueba "

            "por el tamaño reducido de la muestra."

        )

    else:

        prueba = (

            f"Silueta del conjunto de prueba: {silueta_test}"

        )

    return {

        "estabilidad": estabilidad,

        "calidad": calidad,

        "prueba": prueba,

        "diferencia_wcss": diferencia

    }


# =============================================================================
# EVALUACIÓN DEL MODELO
# =============================================================================

def evaluar_modelo(

    modelo,

    entrenamiento,

    prueba

):

    etiquetas_train = modelo.predict(

        entrenamiento

    )

    etiquetas_test = modelo.predict(

        prueba

    )

    wcss_train = calcular_wcss(

        modelo,

        entrenamiento

    )

    wcss_test = calcular_wcss(

        modelo,

        prueba

    )

    silueta_train = calcular_silueta(

        entrenamiento,

        etiquetas_train

    )

    silueta_test = calcular_silueta(

        prueba,

        etiquetas_test

    )

    interpretacion = interpretar_resultados(

        wcss_train,

        wcss_test,

        silueta_train,

        silueta_test

    )

    return {

        "wcss_entrenamiento": wcss_train,

        "wcss_prueba": wcss_test,

        "silueta_entrenamiento": silueta_train,

        "silueta_prueba": silueta_test,

        "interpretacion": interpretacion,

        "etiquetas_train": etiquetas_train.tolist(),

        "etiquetas_test": etiquetas_test.tolist()

    }
# =============================================================================
# GUARDAR RESULTADOS
# =============================================================================

def guardar_resultados(

    modelo,

    k,

    entrenamiento,

    prueba,

    evaluacion

):

    salida = {

        "algoritmo": "K-Means",

        "tipo_validacion": "Train/Test Split",

        "porcentaje_entrenamiento": 80,

        "porcentaje_prueba": 20,

        "k_utilizado": k,

        "total_clientes": int(

            len(entrenamiento) + len(prueba)

        ),

        "clientes_entrenamiento": int(

            len(entrenamiento)

        ),

        "clientes_prueba": int(

            len(prueba)

        ),

        "centroides":[

            {

                "cluster": i + 1,

                "pc1": round(

                    float(c[0]),

                    4

                ),

                "pc2": round(

                    float(c[1]),

                    4

                )

            }

            for i, c in enumerate(

                modelo.cluster_centers_

            )

        ],

        "metricas":{

            "wcss_entrenamiento":

                evaluacion["wcss_entrenamiento"],

            "wcss_prueba":

                evaluacion["wcss_prueba"],

            "silueta_entrenamiento":

                evaluacion["silueta_entrenamiento"],

            "silueta_prueba":

                evaluacion["silueta_prueba"]

        },

        "interpretacion":

            evaluacion["interpretacion"]

    }

    with open(

        ARCHIVO_SALIDA,

        "w",

        encoding="utf-8"

    ) as archivo:

        json.dump(

            salida,

            archivo,

            ensure_ascii=False,

            indent=4

        )

    print("\nArchivo generado correctamente.")

    print(ARCHIVO_SALIDA)
# =============================================================================
# MAIN
# =============================================================================

def main():

    print("\n==============================")
    print("ENTRENAMIENTO Y VALIDACIÓN")
    print("==============================")


    # ==============================
    # CARGA DE DATOS
    # ==============================

    clientes, k = cargar_datos()


    # ==============================
    # OBTENER COORDENADAS PCA
    # ==============================

    coordenadas = obtener_coordenadas(
        clientes
    )


    # ==============================
    # DIVISIÓN ENTRENAMIENTO / PRUEBA
    # ==============================

    entrenamiento, prueba = dividir_datos(
        coordenadas
    )


    print()

    print(
        f"Clientes totales: {len(coordenadas)}"
    )

    print(
        f"Entrenamiento: {len(entrenamiento)}"
    )

    print(
        f"Prueba: {len(prueba)}"
    )

    print(
        f"k óptimo: {k}"
    )


    # ==============================
    # ENTRENAMIENTO K-MEANS
    # ==============================

    modelo = entrenar_modelo(
        entrenamiento,
        k
    )


    # ==============================
    # EVALUACIÓN
    # ==============================

    evaluacion = evaluar_modelo(
        modelo,
        entrenamiento,
        prueba
    )


    # ==============================
    # GUARDAR RESULTADOS
    # ==============================

    guardar_resultados(
        modelo,
        k,
        entrenamiento,
        prueba,
        evaluacion
    )


    print()

    print("============== RESUMEN ==============")


    print(
        "WCSS entrenamiento:",
        evaluacion["wcss_entrenamiento"]
    )


    print(
        "WCSS prueba:",
        evaluacion["wcss_prueba"]
    )


    print(
        "Silueta entrenamiento:",
        evaluacion["silueta_entrenamiento"]
    )


    print(
        "Silueta prueba:",
        evaluacion["silueta_prueba"]
    )


    print()


    print(
        "Estabilidad:",
        evaluacion["interpretacion"]["estabilidad"]
    )


    print(
        "Calidad:",
        evaluacion["interpretacion"]["calidad"]
    )


    print(
        evaluacion["interpretacion"]["prueba"]
    )


    print()

    print("==============================")

# =============================================================================
# EJECUCIÓN
# =============================================================================

if __name__ == "__main__":
    main()