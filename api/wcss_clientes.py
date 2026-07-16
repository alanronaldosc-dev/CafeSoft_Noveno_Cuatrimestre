import json
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_RESULTADO = os.path.join(
    RUTA_ACTUAL,
    "segmentacion_wcss.json"
)

ARCHIVO_PCA = os.path.join(
    RUTA_ACTUAL,
    "segmentacion_pca.json"
)

GRAFICA_WCSS = os.path.join(
    RUTA_ACTUAL,
    "grafica_wcss.png"
)


def cargar_datos_pca():
    if not os.path.exists(ARCHIVO_PCA):
        raise FileNotFoundError(
            "No se encontró segmentacion_pca.json. "
            "Ejecuta primero segmentacion_clientes.py"
        )

    with open(ARCHIVO_PCA, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    clientes = datos.get("clientes", [])

    if len(clientes) < 3:
        raise ValueError(
            "Se necesitan al menos 3 clientes para calcular WCSS."
        )

    return clientes


def preparar_datos(clientes):
    coordenadas = []

    for cliente in clientes:
        pc1 = cliente.get("pc1")
        pc2 = cliente.get("pc2")

        if pc1 is None or pc2 is None:
            raise ValueError(
                "Uno de los clientes no contiene PC1 o PC2."
            )

        coordenadas.append([pc1, pc2])

    return coordenadas


def calcular_wcss(coordenadas):
    total_clientes = len(coordenadas)

    # Como hay 9 clientes, se probará de k=2 hasta k=8.
    k_maximo = min(8, total_clientes - 1)

    valores_k = list(range(2, k_maximo + 1))
    valores_wcss = []

    print("\nCalculando WCSS:")

    for k in valores_k:
        modelo = KMeans(
            n_clusters=k,
            init="k-means++",
            n_init=10,
            max_iter=300,
            random_state=42
        )

        modelo.fit(coordenadas)

        wcss = modelo.inertia_
        valores_wcss.append(wcss)

        print(f"k = {k} | WCSS = {wcss:.4f}")

    return valores_k, valores_wcss

def calcular_silueta(coordenadas, valores_k):
    resultados_silueta = []

    print("\nCalculando índice de silueta:")

    for k in valores_k:
        modelo = KMeans(
            n_clusters=k,
            init="k-means++",
            n_init=10,
            max_iter=300,
            random_state=42
        )

        etiquetas = modelo.fit_predict(coordenadas)

        puntuacion = silhouette_score(
            coordenadas,
            etiquetas
        )

        resultados_silueta.append(puntuacion)

        print(
            f"k = {k} | "
            f"Silhouette = {puntuacion:.4f}"
        )

    mejor_indice = resultados_silueta.index(
        max(resultados_silueta)
    )

    mejor_k = valores_k[mejor_indice]

    return resultados_silueta, mejor_k

def generar_grafica(valores_k, valores_wcss):
    plt.figure(figsize=(8, 5))

    plt.plot(
        valores_k,
        valores_wcss,
        marker="o"
    )

    plt.title("Método del Codo - Segmentación de Clientes")
    plt.xlabel("Número de clusters (k)")
    plt.ylabel("WCSS")
    plt.xticks(valores_k)
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(
        GRAFICA_WCSS,
        dpi=200
    )

    plt.show()

    print(f"\nGráfica guardada en: {GRAFICA_WCSS}")


def ejecutar_kmeans_final(coordenadas, k_optimo):
    modelo = KMeans(
        n_clusters=k_optimo,
        init="k-means++",
        n_init=10,
        max_iter=300,
        random_state=42
    )

    etiquetas = modelo.fit_predict(coordenadas)

    return modelo, etiquetas


def asignar_clusters(clientes, etiquetas):
    clientes_segmentados = []

    for cliente, etiqueta in zip(clientes, etiquetas):
        cliente_segmentado = cliente.copy()

        # Sumamos 1 para mostrar Cluster 1, 2 y 3
        cliente_segmentado["cluster"] = int(etiqueta) + 1

        clientes_segmentados.append(cliente_segmentado)

    return clientes_segmentados


def generar_resumen_clusters(clientes_segmentados):
    resumen = []

    clusters = sorted(
        set(cliente["cluster"] for cliente in clientes_segmentados)
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
            for cliente in clientes_segmentados
            if cliente["cluster"] == cluster
        ]

        promedios = {}

        for variable in variables:
            valores = [
                float(cliente.get(variable, 0))
                for cliente in miembros
            ]

            promedios[variable] = round(
                float(np.mean(valores)),
                2
            )

        resumen.append({
            "cluster": cluster,
            "cantidad_clientes": len(miembros),
            "promedios": promedios,
            "clientes": [
                cliente.get(
                    "nombre",
                    cliente.get("usuario_id", "Sin identificar")
                )
                for cliente in miembros
            ]
        })

    return resumen


def guardar_resultados(
    clientes_segmentados,
    resumen_clusters,
    modelo,
    k_optimo,
    valores_k=None,
    valores_wcss=None,
    resultados_silueta=None
):
    # Tabla WCSS por K para la gráfica del codo en el frontend
    wcss_por_k = []
    if valores_k and valores_wcss:
        for k, wcss in zip(valores_k, valores_wcss):
            wcss_por_k.append({
                "k":    k,
                "wcss": round(float(wcss), 4)
            })

    # Score de silueta por K para el frontend
    silueta_por_k = []
    mejor_silueta = None
    if valores_k and resultados_silueta:
        for k, score in zip(valores_k, resultados_silueta):
            silueta_por_k.append({
                "k":     k,
                "score": round(float(score), 4)
            })
        mejor_silueta = round(float(max(resultados_silueta)), 4)

    # Calidad de segmentación según el índice de silueta
    if mejor_silueta is not None:
        if mejor_silueta >= 0.70:
            calidad = "Excelente"
        elif mejor_silueta >= 0.50:
            calidad = "Buena"
        elif mejor_silueta >= 0.25:
            calidad = "Razonable"
        else:
            calidad = "Débil"
    else:
        calidad = None

    resultado = {
        "algoritmo":    "K-Means",
        "k_optimo":     k_optimo,
        "wcss_final":   round(float(modelo.inertia_), 4),
        # ── WCSS por K (para gráfica del codo) ──
        "wcss_por_k":   wcss_por_k,
        # ── Silueta por K y métricas globales ──
        "silueta_por_k":          silueta_por_k,
        "score_silueta_optimo":   mejor_silueta,
        "calidad_segmentacion":   calidad,
        "centroides_pca": [
            {
                "cluster": indice + 1,
                "pc1": round(float(centroide[0]), 4),
                "pc2": round(float(centroide[1]), 4)
            }
            for indice, centroide in enumerate(
                modelo.cluster_centers_
            )
        ],
        "resumen_clusters": resumen_clusters,
        "clientes":         clientes_segmentados
    }

    with open(
        ARCHIVO_RESULTADO,
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(
            resultado,
            archivo,
            ensure_ascii=False,
            indent=4
        )

    print(
        f"\nResultados guardados en: {ARCHIVO_RESULTADO}"
    )
def main():
    print("── WCSS: Método del Codo ─────────────────")

    clientes = cargar_datos_pca()

    print(f"Clientes cargados: {len(clientes)}")

    coordenadas = preparar_datos(clientes)

    valores_k, valores_wcss = calcular_wcss(
        coordenadas
    )

    generar_grafica(
        valores_k,
        valores_wcss
    )

    resultados_silueta, mejor_k = calcular_silueta(
        coordenadas,
        valores_k
    )
    
    k_optimo = mejor_k

    modelo_final, etiquetas = ejecutar_kmeans_final(
        coordenadas,
        k_optimo
    )

    clientes_segmentados = asignar_clusters(
        clientes,
        etiquetas
    )

    resumen_clusters = generar_resumen_clusters(
        clientes_segmentados
    )

    guardar_resultados(
        clientes_segmentados,
        resumen_clusters,
        modelo_final,
        k_optimo,
        valores_k=valores_k,
        valores_wcss=valores_wcss,
        resultados_silueta=resultados_silueta
    )

    print("\nSegmentación final:")

    for cliente in clientes_segmentados:
        nombre = cliente.get(
            "nombre",
            cliente.get("usuario_id", "Sin identificar")
        )

        print(
            f"{nombre} → Cluster {cliente['cluster']}"
        )
    print("\nResultado final:")
    print(
        f"El mejor número de clusters "
        f"según Silhouette es k = {mejor_k}"
    )

if __name__ == "__main__":
    main()