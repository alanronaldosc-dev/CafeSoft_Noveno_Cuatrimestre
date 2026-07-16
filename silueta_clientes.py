# =============================================================================
# silueta_clientes.py
# FASE 3 - ÍNDICE DE SILUETA
# =============================================================================
# Objetivo:
# Validar la calidad de la segmentación obtenida mediante K-Means.
#
# Este módulo:
#
# 1. Lee segmentacion_pca.json
# 2. Lee segmentacion_wcss.json
# 3. Obtiene el k óptimo
# 4. Ejecuta nuevamente K-Means
# 5. Calcula el índice de silueta
# 6. Calcula el score por cluster
# 7. Interpreta el resultado
# 8. Etiqueta automáticamente los segmentos
# 9. Guarda segmentacion_silueta.json
# =============================================================================

import json
import os

import numpy as np

from sklearn.cluster import KMeans
from sklearn.metrics import (
    silhouette_score,
    silhouette_samples
)

# =============================================================================
# RUTAS
# =============================================================================

RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))

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
    "segmentacion_silueta.json"
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

        datos_pca = json.load(archivo)

    with open(
        ARCHIVO_WCSS,
        "r",
        encoding="utf-8"
    ) as archivo:

        datos_wcss = json.load(archivo)

    clientes = datos_pca["clientes"]

    k = datos_wcss["k_optimo"]

    return clientes, k


# =============================================================================
# PREPARAR MATRIZ PCA
# =============================================================================

def obtener_coordenadas(clientes):

    coordenadas = []

    for cliente in clientes:

        coordenadas.append([

            float(cliente["pc1"]),

            float(cliente["pc2"])

        ])

    return np.array(coordenadas)


# =============================================================================
# EJECUTAR KMEANS
# =============================================================================

def ejecutar_kmeans(
    coordenadas,
    k
):

    modelo = KMeans(

        n_clusters=k,

        init="k-means++",

        random_state=42,

        n_init=10,

        max_iter=300

    )

    etiquetas = modelo.fit_predict(

        coordenadas

    )

    return modelo, etiquetas


# =============================================================================
# DISTANCIA EUCLIDIANA
# =============================================================================

def distancia(
    punto1,
    punto2
):

    return np.linalg.norm(

        punto1 - punto2

    )
# =============================================================================
# CÁLCULO DEL ÍNDICE DE SILUETA
# =============================================================================

def calcular_silueta(
    coordenadas,
    etiquetas
):

    print("\nCalculando índice de silueta...")

    # Score global usando sklearn
    score_global = float(
        silhouette_score(
            coordenadas,
            etiquetas
        )
    )

    # Score individual de cada cliente
    score_individual = silhouette_samples(
        coordenadas,
        etiquetas
    )

    clientes = []

    for i, score in enumerate(score_individual):

        clientes.append({

            "indice": i,

            "cluster": int(etiquetas[i]) + 1,

            "score": round(
                float(score),
                4
            )

        })

    return (

        score_global,

        score_individual,

        clientes

    )


# =============================================================================
# SCORE PROMEDIO POR CLUSTER
# =============================================================================

def calcular_cluster_scores(
    etiquetas,
    score_individual
):

    resultado = []

    clusters = sorted(

        np.unique(etiquetas)

    )

    for cluster in clusters:

        indices = np.where(

            etiquetas == cluster

        )[0]

        promedio = np.mean(

            score_individual[indices]

        )

        minimo = np.min(

            score_individual[indices]

        )

        maximo = np.max(

            score_individual[indices]

        )

        resultado.append({

            "cluster": int(cluster) + 1,

            "cantidad_clientes": int(len(indices)),

            "score_promedio": round(

                float(promedio),

                4

            ),

            "score_minimo": round(

                float(minimo),

                4

            ),

            "score_maximo": round(

                float(maximo),

                4

            )

        })

    return resultado


# =============================================================================
# INTERPRETACIÓN DEL SCORE GLOBAL
# =============================================================================

def interpretar_silueta(

    score

):

    if score >= 0.70:

        return {

            "nivel": "Excelente",

            "descripcion":
            "Los clusters están muy bien separados."

        }

    elif score >= 0.50:

        return {

            "nivel": "Buena",

            "descripcion":
            "La segmentación es aceptable."

        }

    elif score >= 0.25:

        return {

            "nivel": "Regular",

            "descripcion":
            "Existe traslape entre clusters."

        }

    else:

        return {

            "nivel": "Mala",

            "descripcion":
            "Los clusters no representan grupos claros."

        }


# =============================================================================
# ETIQUETADO AUTOMÁTICO DE LOS SEGMENTOS
# =============================================================================

def obtener_segmento(

    cliente

):

    frecuencia = cliente["frecuencia"]

    gasto = cliente["gasto_total"]

    ticket = cliente["ticket_promedio"]

    recencia = cliente["recencia_dias"]

    hora = cliente["hora_preferida"]

    fin = cliente["pct_fines_semana"]

    diversidad = cliente["diversidad_productos"]

    if frecuencia >= 20 and gasto >= 10000:

        return "Cliente VIP"

    if frecuencia >= 10 and ticket >= 500:

        return "Cliente Premium"

    if frecuencia >= 8 and diversidad >= 6:

        return "Cliente Frecuente"

    if recencia >= 90:

        return "Cliente Inactivo"

    if fin >= 0.80:

        return "Cliente de Fin de Semana"

    if hora <= 10:

        return "Cliente Matutino"

    if hora >= 18:

        return "Cliente Nocturno"

    return "Cliente Regular"


# =============================================================================
# AGREGAR SEGMENTO A CADA CLIENTE
# =============================================================================

def etiquetar_clientes(

    clientes,

    etiquetas,

    score_individual

):

    clientes_final = []

    for cliente, cluster, score in zip(

        clientes,

        etiquetas,

        score_individual

    ):

        nuevo = cliente.copy()

        nuevo["cluster"] = int(cluster) + 1

        nuevo["segmento"] = obtener_segmento(

            cliente

        )

        nuevo["score_silueta"] = round(

            float(score),

            4

        )

        clientes_final.append(

            nuevo

        )

    return clientes_final
# =============================================================================
# RESUMEN DE CLUSTERS
# =============================================================================

def generar_resumen_clusters(clientes):

    resumen = []

    clusters = sorted(
        set(cliente["cluster"] for cliente in clientes)
    )

    variables = [
        "frecuencia",
        "gasto_total",
        "ticket_promedio",
        "recencia_dias",
        "hora_preferida",
        "pct_fines_semana",
        "diversidad_productos"
    ]

    for cluster in clusters:

        miembros = [
            cliente
            for cliente in clientes
            if cliente["cluster"] == cluster
        ]

        promedios = {}

        for variable in variables:

            valores = [
                float(cliente[variable])
                for cliente in miembros
            ]

            promedios[variable] = round(
                float(np.mean(valores)),
                2
            )

        promedio_silueta = round(
            float(
                np.mean([
                    cliente["score_silueta"]
                    for cliente in miembros
                ])
            ),
            4
        )

        resumen.append({

            "cluster": cluster,

            "cantidad_clientes": len(miembros),

            "score_promedio_silueta": promedio_silueta,

            "segmentos": sorted(
                list(
                    set(
                        cliente["segmento"]
                        for cliente in miembros
                    )
                )
            ),

            "promedios": promedios,

            "clientes": [

                {

                    "nombre": cliente["nombre"],

                    "segmento": cliente["segmento"],

                    "score_silueta": cliente["score_silueta"]

                }

                for cliente in miembros

            ]

        })

    return resumen


# =============================================================================
# GUARDAR JSON
# =============================================================================

def guardar_resultado(

    modelo,

    k,

    score_global,

    interpretacion,

    score_clusters,

    resumen,

    clientes

):

    salida = {

        "algoritmo": "Indice de Silueta",

        "k_utilizado": k,

        "score_global": round(
            score_global,
            4
        ),

        "interpretacion": interpretacion,

        "centroides": [

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

        "score_por_cluster": score_clusters,

        "resumen_clusters": resumen,

        "clientes": clientes

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

    print(
        f"\nArchivo generado:\n{ARCHIVO_SALIDA}"
    )


# =============================================================================
# MAIN
# =============================================================================

def main():

    print(
        "\n========== ÍNDICE DE SILUETA =========="
    )

    clientes, k = cargar_datos()

    print(f"Clientes: {len(clientes)}")

    print(f"k óptimo: {k}")

    coordenadas = obtener_coordenadas(
        clientes
    )

    modelo, etiquetas = ejecutar_kmeans(
        coordenadas,
        k
    )

    (
        score_global,
        score_individual,
        _
    ) = calcular_silueta(
        coordenadas,
        etiquetas
    )

    score_clusters = calcular_cluster_scores(

        etiquetas,

        score_individual

    )

    interpretacion = interpretar_silueta(

        score_global

    )

    clientes_final = etiquetar_clientes(

        clientes,

        etiquetas,

        score_individual

    )

    resumen = generar_resumen_clusters(

        clientes_final

    )

    guardar_resultado(

        modelo,

        k,

        score_global,

        interpretacion,

        score_clusters,

        resumen,

        clientes_final

    )

    print("\n===================================")

    print(
        f"Score global: {score_global:.4f}"
    )

    print(
        f"Nivel: {interpretacion['nivel']}"
    )

    print(
        interpretacion["descripcion"]
    )

    print("\nScore por cluster")

    for cluster in score_clusters:

        print(

            f"Cluster {cluster['cluster']}"

            f" -> {cluster['score_promedio']}"

        )


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":

    main()