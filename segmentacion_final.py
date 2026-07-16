# =============================================================================
# segmentacion_final.py
#
# FASE 5
# INTERPRETACIÓN DE NEGOCIO
#
# PCA + WCSS + KMEANS + SILUETA + REGLAS DE NEGOCIO
# =============================================================================

import json
import os
from datetime import datetime

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
    "segmentacion_final.json"
)

# =============================================================================
# CARGAR DATOS
# =============================================================================

def cargar_datos():

    if not os.path.exists(ARCHIVO_PCA):
        raise FileNotFoundError(
            "No existe segmentacion_pca.json"
        )

    with open(
        ARCHIVO_PCA,
        "r",
        encoding="utf-8"
    ) as archivo:

        datos = json.load(
            archivo
        )

    return datos


# =============================================================================
# CLASIFICACIÓN DE CLIENTES
# =============================================================================

def clasificar_cliente(cliente):

    frecuencia = cliente["frecuencia"]
    gasto_total = cliente["gasto_total"]
    ticket = cliente["ticket_promedio"]
    recencia = cliente["recencia_dias"]
    hora = cliente["hora_preferida"]
    fin_semana = cliente["pct_fines_semana"]
    diversidad = cliente["diversidad_productos"]

    # VIP
    if frecuencia >= 20 and gasto_total >= 10000:

        return {
            "segmento": "🏆 Cliente VIP",
            "prioridad": "ALTA",
            "descripcion":
                "Cliente con alta frecuencia y elevado gasto.",
            "recomendacion":
                "Programa VIP, recompensas y promociones exclusivas."
        }

    # Café mañanero
    elif (
        frecuencia >= 10
        and ticket < 300
        and hora < 11
    ):

        return {
            "segmento": "☕ Amante del café mañanero",
            "prioridad": "MEDIA",
            "descripcion":
                "Compra frecuentemente durante las mañanas.",
            "recomendacion":
                "Promociones para desayunos y combos matutinos."
        }

    # Fin de semana
    elif fin_semana >= 0.70:

        return {
            "segmento": "📅 Comprador de fin de semana",
            "prioridad": "MEDIA",
            "descripcion":
                "Realiza la mayoría de sus compras los fines de semana.",
            "recomendacion":
                "Ofrecer promociones exclusivas sábado y domingo."
        }

    # Dormido
    elif recencia > 30:

        return {
            "segmento": "💤 Cliente dormido",
            "prioridad": "ALTA",
            "descripcion":
                "Hace tiempo que no realiza compras.",
            "recomendacion":
                "Campaña de recuperación con descuentos."
        }

    # Nuevo con potencial
    elif frecuencia <= 5 and ticket >= 500:

        return {
            "segmento": "🆕 Nuevo con potencial",
            "prioridad": "MEDIA",
            "descripcion":
                "Tiene pocas compras pero genera tickets altos.",
            "recomendacion":
                "Incentivar compras recurrentes."
        }

    # Explorador
    elif diversidad >= 10:

        return {
            "segmento": "🛒 Explorador del menú",
            "prioridad": "MEDIA",
            "descripcion":
                "Consume gran variedad de productos.",
            "recomendacion":
                "Recomendar nuevos productos y lanzamientos."
        }

    # Premium ocasional
    elif gasto_total >= 8000 and frecuencia < 10:

        return {
            "segmento": "💎 Comprador premium ocasional",
            "prioridad": "ALTA",
            "descripcion":
                "Gasta mucho dinero pero compra pocas veces.",
            "recomendacion":
                "Ofrecer experiencias premium y membresías."
        }

    # Regular
    else:

        return {
            "segmento": "⭐ Cliente regular",
            "prioridad": "BAJA",
            "descripcion":
                "Mantiene un comportamiento estable de compra.",
            "recomendacion":
                "Mantener promociones generales."
        }


# =============================================================================
# GENERAR REPORTE
# =============================================================================

def generar_segmentacion():

    datos = cargar_datos()

    clientes = datos["clientes"]

    clientes_final = []

    estadisticas = {}

    for cliente in clientes:

        clasificacion = clasificar_cliente(
            cliente
        )

        cliente_final = {

            "usuario_id":
                cliente["usuario_id"],

            "nombre":
                cliente["nombre"],

            "segmento":
                clasificacion["segmento"],

            "prioridad":
                clasificacion["prioridad"],

            "descripcion":
                clasificacion["descripcion"],

            "recomendacion":
                clasificacion["recomendacion"],

            "frecuencia":
                cliente["frecuencia"],

            "gasto_total":
                cliente["gasto_total"],

            "ticket_promedio":
                cliente["ticket_promedio"],

            "recencia_dias":
                cliente["recencia_dias"],

            "hora_preferida":
                cliente["hora_preferida"],

            "pct_fines_semana":
                cliente["pct_fines_semana"],

            "diversidad_productos":
                cliente["diversidad_productos"],

            "pc1":
                cliente["pc1"],

            "pc2":
                cliente["pc2"]
        }

        clientes_final.append(
            cliente_final
        )

        segmento = clasificacion["segmento"]

        estadisticas[segmento] = (
            estadisticas.get(
                segmento,
                0
            ) + 1
        )

    salida = {

        "algoritmo":
            "PCA + K-Means + Índice de Silueta + Reglas de Negocio",

        "fecha_generacion":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "total_clientes":
            len(clientes_final),

        "estadisticas":
            estadisticas,

        "clientes":
            clientes_final
    }

    with open(
        ARCHIVO_SALIDA,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            salida,
            archivo,
            indent=4,
            ensure_ascii=False
        )

    print()
    print("====================================")
    print("SEGMENTACIÓN FINAL GENERADA")
    print("====================================")
    print(ARCHIVO_SALIDA)
    print()

    for segmento, cantidad in estadisticas.items():

        print(
            f"{segmento}: {cantidad}"
        )


# =============================================================================
# MAIN
# =============================================================================

def main():

    generar_segmentacion()


if __name__ == "__main__":
    main()