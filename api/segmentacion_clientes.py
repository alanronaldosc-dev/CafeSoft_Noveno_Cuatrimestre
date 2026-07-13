# =============================================================================
# segmentacion_clientes.py  ·  FASE 1: PCA
# =============================================================================
# Objetivo: reducir las 7 dimensiones del perfil de cada cliente a 2
# componentes principales (PC1, PC2) usando sklearn y numpy.
#
# Librerías:
#   - numpy:               operaciones matriciales y manejo de arrays
#   - sklearn.preprocessing.StandardScaler:  normalización Z-score
#   - sklearn.decomposition.PCA:             análisis de componentes principales
# =============================================================================

import os
import json
from collections import defaultdict
from datetime import datetime
from bson import ObjectId
from config import ventas_collection, usuarios_collection

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


# Orden fijo de las 7 features.
# Este orden se respeta en normalización, PCA y fases posteriores (WCSS, Silueta).
FEATURES = [
    "frecuencia",           # cuántas veces compró
    "gasto_total",          # suma de todos sus totales
    "ticket_promedio",      # gasto_total / frecuencia
    "recencia_dias",        # días desde la última compra
    "hora_preferida",       # promedio de la hora del día (0-23)
    "pct_fines_semana",     # % de compras en sábado o domingo (0.0 - 1.0)
    "diversidad_productos"  # cantidad de productos distintos comprados
]


# =============================================================================
# SECCIÓN 1 — EXTRACCIÓN DE FEATURES
# =============================================================================
# Cada cliente queda representado por un vector de 7 números.
# Todos se calculan recorriendo la colección "ventas" de MongoDB.
#
# Vector por cliente:
#   [frecuencia, gasto_total, ticket_promedio, recencia_dias,
#    hora_preferida, pct_fines_semana, diversidad_productos]
# =============================================================================

def extraer_features_clientes():
    """
    Lee todas las ventas de MongoDB y construye el perfil numérico
    de cada cliente identificado por usuario_id.

    No recibe parámetros: usa ventas_collection y usuarios_collection
    importados desde config.py.

    Retorna una lista de dicts, uno por cliente:
    {
        "usuario_id":           str,
        "nombre":               str,
        "frecuencia":           int,
        "gasto_total":          float,
        "ticket_promedio":      float,
        "recencia_dias":        float,
        "hora_preferida":       float,
        "pct_fines_semana":     float,
        "diversidad_productos": int
    }
    """

    # Acumuladores indexados por usuario_id.
    # defaultdict evita verificar si la clave existe antes de escribir.
    acum = defaultdict(lambda: {
        "totales":     [],   # lista de totales (float) de cada venta
        "fechas":      [],   # lista de datetimes de cada venta
        "dias_semana": [],   # 0=lunes … 6=domingo por cada venta
        "productos":   set() # set de nombres de productos distintos
    })

    ventas = list(ventas_collection.find())

    # ── Paso 1: acumular datos brutos por cliente ─────────────────────────────
    for venta in ventas:
        uid = str(venta.get("usuario_id", "")).strip()

        # Ignorar ventas anónimas o sin usuario asignado
        if not uid or uid == "None":
            continue

        total      = _limpiar_numero(venta.get("total", 0))
        created_at = venta.get("created_at")

        acum[uid]["totales"].append(total)

        if isinstance(created_at, datetime):
            acum[uid]["fechas"].append(created_at)
            # weekday(): 0=lunes, 5=sábado, 6=domingo
            acum[uid]["dias_semana"].append(created_at.weekday())

        # Recolectar nombres de productos de esta venta
        productos = venta.get("productos", {})
        items = (
            productos.values() if isinstance(productos, dict)
            else productos if isinstance(productos, list)
            else []
        )
        for item in items:
            if isinstance(item, dict):
                nombre = (
                    item.get("nombre") or item.get("name") or
                    item.get("producto") or ""
                ).strip()
                if nombre:
                    acum[uid]["productos"].add(nombre)

    # ── Paso 2: resolver nombres desde usuarios_collection ───────────────────
    # Se hace fuera del loop de ventas para evitar N consultas a MongoDB.
    usuarios_map = {}
    for uid in acum:
        try:
            doc = usuarios_collection.find_one({"_id": ObjectId(uid)}, {"nombre": 1})
            usuarios_map[uid] = doc["nombre"] if doc and "nombre" in doc \
                                else f"Usuario {uid[:6]}"
        except Exception:
            usuarios_map[uid] = f"Usuario {uid[:6]}"

    # ── Paso 3: calcular las 7 features por cliente ───────────────────────────
    hoy       = datetime.utcnow()
    resultado = []

    for uid, datos in acum.items():
        totales     = datos["totales"]
        fechas      = datos["fechas"]
        dias_semana = datos["dias_semana"]

        frecuencia  = len(totales)
        gasto_total = sum(totales)

        # Gasto promedio por visita
        ticket_promedio = gasto_total / frecuencia if frecuencia > 0 else 0.0

        # Días desde la última compra.
        # Si no hay fechas registradas se asigna 999 como valor neutro alto,
        # lo que hará que el cliente aparezca lejos del grupo activo en el PCA.
        recencia_dias = (hoy - max(fechas)).days if fechas else 999.0

        # Hora promedio de compra (0-23).
        # Distingue clientes mañaneros de vespertinos / nocturnos.
        hora_preferida = float(np.mean([f.hour for f in fechas])) if fechas else 12.0

        # Proporción de compras en fin de semana (sábado=5, domingo=6)
        pct_fines_semana = (
            sum(1 for d in dias_semana if d >= 5) / len(dias_semana)
            if dias_semana else 0.0
        )

        # Número de productos distintos pedidos en todas sus visitas
        diversidad_productos = len(datos["productos"])

        resultado.append({
            "usuario_id":           uid,
            "nombre":               usuarios_map.get(uid, f"Usuario {uid[:6]}"),
            "frecuencia":           frecuencia,
            "gasto_total":          round(gasto_total, 2),
            "ticket_promedio":      round(ticket_promedio, 2),
            "recencia_dias":        float(recencia_dias),
            "hora_preferida":       round(hora_preferida, 2),
            "pct_fines_semana":     round(pct_fines_semana, 4),
            "diversidad_productos": diversidad_productos
        })

    return resultado
    """
    Lee todas las ventas de MongoDB y construye el perfil numérico
    de cada cliente identificado por usuario_id.

    Retorna una lista de dicts, uno por cliente:
    {
        "usuario_id":           str,
        "nombre":               str,
        "frecuencia":           int,
        "gasto_total":          float,
        "ticket_promedio":      float,
        "recencia_dias":        float,
        "hora_preferida":       float,
        "pct_fines_semana":     float,
        "diversidad_productos": int
    }
    """

    # Acumuladores indexados por usuario_id.
    # defaultdict evita verificar si la clave existe antes de escribir.
    acum = defaultdict(lambda: {
        "totales":     [],   # lista de totales (float) de cada venta
        "fechas":      [],   # lista de datetimes de cada venta
        "dias_semana": [],   # 0=lunes … 6=domingo por cada venta
        "productos":   set() # set de nombres de productos distintos
    })

    ventas = list(db["ventas"].find())

    # ── Paso 1: acumular datos brutos por cliente ─────────────────────────────
    for venta in ventas:
        uid = str(venta.get("usuario_id", "")).strip()

        # Ignorar ventas anónimas o sin usuario asignado
        if not uid or uid == "None":
            continue

        total      = _limpiar_numero(venta.get("total", 0))
        created_at = venta.get("created_at")

        acum[uid]["totales"].append(total)

        if isinstance(created_at, datetime):
            acum[uid]["fechas"].append(created_at)
            # weekday(): 0=lunes, 5=sábado, 6=domingo
            acum[uid]["dias_semana"].append(created_at.weekday())

        # Recolectar nombres de productos de esta venta
        productos = venta.get("productos", {})
        items = (
            productos.values() if isinstance(productos, dict)
            else productos if isinstance(productos, list)
            else []
        )
        for item in items:
            if isinstance(item, dict):
                nombre = (
                    item.get("nombre") or item.get("name") or
                    item.get("producto") or ""
                ).strip()
                if nombre:
                    acum[uid]["productos"].add(nombre)

    # ── Paso 2: resolver nombres desde la colección "usuarios" ────────────────
    # Se hace fuera del loop de ventas para evitar N consultas a MongoDB.
    usuarios_map = {}
    for uid in acum:
        try:
            doc = db["usuarios"].find_one({"_id": ObjectId(uid)}, {"nombre": 1})
            usuarios_map[uid] = doc["nombre"] if doc and "nombre" in doc \
                                else f"Usuario {uid[:6]}"
        except Exception:
            usuarios_map[uid] = f"Usuario {uid[:6]}"

    # ── Paso 3: calcular las 7 features por cliente ───────────────────────────
    hoy       = datetime.utcnow()
    resultado = []

    for uid, datos in acum.items():
        totales     = datos["totales"]
        fechas      = datos["fechas"]
        dias_semana = datos["dias_semana"]

        frecuencia  = len(totales)
        gasto_total = sum(totales)

        # Gasto promedio por visita
        ticket_promedio = gasto_total / frecuencia if frecuencia > 0 else 0.0

        # Días desde la última compra.
        # Si no hay fechas registradas se asigna 999 como valor neutro alto,
        # lo que hará que el cliente aparezca lejos del grupo activo después del PCA.
        recencia_dias = (hoy - max(fechas)).days if fechas else 999.0

        # Hora promedio de compra (0-23).
        # Distingue clientes mañaneros de vespertinos / nocturnos.
        hora_preferida = float(np.mean([f.hour for f in fechas])) if fechas else 12.0

        # Proporción de compras en fin de semana (sábado=5, domingo=6)
        pct_fines_semana = (
            sum(1 for d in dias_semana if d >= 5) / len(dias_semana)
            if dias_semana else 0.0
        )

        # Número de productos distintos pedidos en todas sus visitas
        diversidad_productos = len(datos["productos"])

        resultado.append({
            "usuario_id":           uid,
            "nombre":               usuarios_map.get(uid, f"Usuario {uid[:6]}"),
            "frecuencia":           frecuencia,
            "gasto_total":          round(gasto_total, 2),
            "ticket_promedio":      round(ticket_promedio, 2),
            "recencia_dias":        float(recencia_dias),
            "hora_preferida":       round(hora_preferida, 2),
            "pct_fines_semana":     round(pct_fines_semana, 4),
            "diversidad_productos": diversidad_productos
        })

    return resultado


# =============================================================================
# SECCIÓN 2 — NORMALIZACIÓN Z-SCORE con StandardScaler de sklearn
# =============================================================================
# PCA es sensible a la escala. Sin normalizar, gasto_total (miles de pesos)
# dominaría sobre pct_fines_semana (0.0 - 1.0) y distorsionaría los
# componentes principales.
#
# StandardScaler aplica columna por columna:
#   z = (x - media) / std
#
# Retorna un array numpy de shape (n_clientes, 7).
# =============================================================================

def normalizar_zscore(perfiles):
    """
    Convierte la lista de perfiles en una matriz numpy normalizada.

    Parámetros:
        perfiles: lista de dicts con las 7 features por cliente

    Retorna:
        X_norm:  np.ndarray shape (n_clientes, 7), valores normalizados
        scaler:  el StandardScaler ajustado (guarda media y std por columna)
                 — útil para diagnóstico y para invertir la transformación
                 en fases posteriores si fuera necesario
    """

    # Construir la matriz en el orden exacto de FEATURES
    # Shape resultante: (n_clientes, 7)
    X = np.array([[p[feat] for feat in FEATURES] for p in perfiles], dtype=float)

    # StandardScaler calcula media y std por columna y transforma
    scaler = StandardScaler()
    X_norm = scaler.fit_transform(X)

    # Diagnóstico: imprimir media y std originales detectados por el scaler
    for i, feat in enumerate(FEATURES):
        print(f"  {feat:25s}  media={scaler.mean_[i]:8.2f}  std={scaler.scale_[i]:8.2f}")

    return X_norm, scaler


# =============================================================================
# SECCIÓN 3 — PCA con sklearn.decomposition.PCA
# =============================================================================
# PCA encuentra las direcciones del espacio de 7 dimensiones que concentran
# la mayor varianza. Proyectamos sobre PC1 y PC2 (las dos de mayor varianza)
# para obtener una representación 2D de cada cliente.
#
# sklearn.PCA implementa internamente SVD (Singular Value Decomposition),
# que es numéricamente más estable que el método de eigenvalores directo.
#
# Pasos internos de sklearn.PCA:
#   1. Centrar los datos (con StandardScaler ya están centrados)
#   2. Calcular la SVD: X = U · Σ · Vᵀ
#   3. Los componentes principales son las filas de Vᵀ
#   4. La varianza explicada por cada componente = σ²ᵢ / Σσ²
#   5. Proyectar: Z = X · Vᵀ[:n_components]
# =============================================================================

def calcular_pca(X_norm, varianza_minima=0.70):
    """
    Aplica PCA sobre la matriz normalizada y retorna la proyección 2D
    junto con las métricas de varianza.

    Parámetros:
        X_norm:          np.ndarray (n_clientes, 7) ya normalizado
        varianza_minima: umbral de varianza acumulada para elegir n_components
                         (default 0.70 = 70%)

    Retorna un dict con:
        "pca_model":               el objeto PCA ajustado (para reutilizar)
        "proyecciones":            np.ndarray (n_clientes, n_components)
        "varianza_por_componente": list[float], varianza de cada PC elegido
        "varianza_acumulada":      float, suma de varianzas de los PCs elegidos
        "n_componentes":           int
        "eigenvalores":            list[float], todos los eigenvalores (varianza de cada PC)
        "loadings":                list[list[float]], contribución de cada feature a cada PC
    """

    n_clientes, n_features = X_norm.shape

    # ── Determinar n_components automáticamente ───────────────────────────────
    # Primero ajustamos PCA con todos los componentes posibles para ver
    # cuántos se necesitan para alcanzar el umbral de varianza.
    pca_full = PCA(n_components=min(n_clientes, n_features))
    pca_full.fit(X_norm)

    # explained_variance_ratio_: array con la fracción de varianza por componente
    # Ejemplo: [0.61, 0.18, 0.09, 0.05, ...] → acumulado al 2do: 0.79 ≥ 0.70 ✓
    varianza_acumulada = np.cumsum(pca_full.explained_variance_ratio_)

    # np.searchsorted encuentra el índice donde la varianza acumulada supera
    # el umbral. Sumamos 1 porque el índice es 0-based y queremos la cantidad.
    n_components = int(np.searchsorted(varianza_acumulada, varianza_minima) + 1)

    # Siempre al menos 2 componentes para poder visualizar en 2D
    n_components = max(n_components, 2)

    # Nunca más componentes que features o clientes disponibles
    n_components = min(n_components, n_features, n_clientes)

    # ── Ajustar PCA con el n_components definitivo ────────────────────────────
    pca = PCA(n_components=n_components, random_state=42)
    proyecciones = pca.fit_transform(X_norm)
    # proyecciones: np.ndarray shape (n_clientes, n_components)
    # Cada fila es un cliente; cada columna es su coordenada en un componente principal

    # ── Métricas de varianza ──────────────────────────────────────────────────
    # explained_variance_ratio_: fracción de varianza que explica cada PC elegido
    varianza_por_componente = pca.explained_variance_ratio_.tolist()
    varianza_acumulada_final = float(np.sum(pca.explained_variance_ratio_))

    # ── Eigenvalores ──────────────────────────────────────────────────────────
    # explained_variance_: varianza absoluta (no fracción) de cada componente
    # equivale a los eigenvalores de la matriz de covarianza
    eigenvalores_todos = pca_full.explained_variance_.tolist()

    # ── Loadings (contribución de features a cada PC) ─────────────────────────
    # components_: array shape (n_components, n_features)
    # components_[k][j] indica cuánto contribuye la feature j al componente k
    # Permite interpretar qué significa cada PC en términos del negocio
    loadings = pca.components_.tolist()

    return {
        "pca_model":               pca,
        "proyecciones":            proyecciones,
        "varianza_por_componente": [round(v, 4) for v in varianza_por_componente],
        "varianza_acumulada":      round(varianza_acumulada_final, 4),
        "n_componentes":           n_components,
        "eigenvalores":            [round(e, 4) for e in eigenvalores_todos],
        "loadings":                [[round(v, 4) for v in row] for row in loadings]
    }


# =============================================================================
# SECCIÓN 4 — INTERPRETACIÓN DE LOADINGS
# =============================================================================
# Los loadings explican qué significa cada componente principal en términos
# del negocio. El feature con el loading de mayor valor absoluto en un PC
# es el que más "define" ese componente.
#
# Ejemplo:
#   PC1 loading alto en frecuencia y gasto_total → PC1 = "intensidad de compra"
#   PC2 loading alto en hora_preferida          → PC2 = "patrón horario"
# =============================================================================

def interpretar_loadings(loadings, n_componentes):
    """
    Para cada componente principal, identifica los 3 features con mayor
    contribución (en valor absoluto) y genera una etiqueta descriptiva.

    Parámetros:
        loadings:      list[list[float]], shape (n_componentes, 7)
        n_componentes: int

    Retorna una lista de dicts, uno por componente:
    {
        "componente":       "PC1",
        "features_top":     [{"feature": "frecuencia", "peso": 0.61}, ...],
        "interpretacion":   "Intensidad de compra"
    }
    """
    interpretaciones = []

    for k in range(n_componentes):
        pesos = loadings[k]   # lista de 7 valores, uno por feature

        # Ordenar features por valor absoluto del loading, descendente
        ranking = sorted(
            zip(FEATURES, pesos),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:3]   # top 3

        features_top = [
            {"feature": feat, "peso": round(peso, 4)}
            for feat, peso in ranking
        ]

        # Heurística de etiquetado basada en el feature dominante
        feature_dominante = ranking[0][0]
        etiquetas = {
            "frecuencia":           "Intensidad de compra",
            "gasto_total":          "Volumen económico",
            "ticket_promedio":      "Valor por visita",
            "recencia_dias":        "Actividad reciente",
            "hora_preferida":       "Patrón horario",
            "pct_fines_semana":     "Preferencia de fin de semana",
            "diversidad_productos": "Variedad de consumo"
        }
        interpretacion = etiquetas.get(feature_dominante, f"Componente {k+1}")

        interpretaciones.append({
            "componente":     f"PC{k+1}",
            "features_top":   features_top,
            "interpretacion": interpretacion
        })

    return interpretaciones


# =============================================================================
# SECCIÓN 5 — FUNCIÓN PRINCIPAL: ejecutar_pca_clientes
# =============================================================================
# Orquesta las secciones anteriores y guarda segmentacion_pca.json.
# Este JSON es la entrada para la Fase 2 (WCSS) y Fase 3 (Silueta).
# =============================================================================

def ejecutar_pca_clientes():
    """
    Pipeline completo de PCA:
        1. Extrae features de ventas usando ventas_collection (config.py)
        2. Normaliza con Z-score (StandardScaler)
        3. Aplica PCA (sklearn)
        4. Interpreta los loadings
        5. Guarda segmentacion_pca.json

    No recibe parámetros: la conexión está centralizada en config.py.
    Retorna el dict con los resultados, o None si no hay suficientes clientes.
    """

    print("── PCA: extrayendo features de clientes ──────────────────────────")
    perfiles = extraer_features_clientes()

    # PCA no tiene sentido con menos de 3 clientes
    if len(perfiles) < 3:
        print(f"⚠ Solo {len(perfiles)} cliente(s) con datos. Mínimo 3 para PCA.")
        return None

    print(f"  Clientes encontrados: {len(perfiles)}")

    # ── Normalización ─────────────────────────────────────────────────────────
    print("── PCA: aplicando normalización Z-score (StandardScaler) ─────────")
    X_norm, scaler = normalizar_zscore(perfiles)

    # ── PCA ───────────────────────────────────────────────────────────────────
    print("── PCA: calculando componentes principales (sklearn PCA) ─────────")
    resultado_pca = calcular_pca(X_norm)

    print(f"  Componentes elegidos: {resultado_pca['n_componentes']}")
    print(f"  Varianza explicada:   {resultado_pca['varianza_acumulada'] * 100:.1f}%")
    for k, v in enumerate(resultado_pca["varianza_por_componente"]):
        print(f"    PC{k+1}: {v * 100:.1f}%")

    # ── Interpretación de loadings ────────────────────────────────────────────
    interpretaciones = interpretar_loadings(
        resultado_pca["loadings"],
        resultado_pca["n_componentes"]
    )
    print("── PCA: interpretación de componentes ────────────────────────────")
    for item in interpretaciones:
        top = ", ".join(f["feature"] for f in item["features_top"])
        print(f"  {item['componente']}: {item['interpretacion']}  ({top})")

    # ── Ensamblar resultado por cliente ───────────────────────────────────────
    proyecciones = resultado_pca["proyecciones"]

    clientes_pca = []
    for i, perfil in enumerate(perfiles):
        clientes_pca.append({
            # Identificación
            "usuario_id": perfil["usuario_id"],
            "nombre":     perfil["nombre"],
            # Features originales — necesarias en Fase 3 para etiquetar segmentos
            "frecuencia":           perfil["frecuencia"],
            "gasto_total":          perfil["gasto_total"],
            "ticket_promedio":      perfil["ticket_promedio"],
            "recencia_dias":        perfil["recencia_dias"],
            "hora_preferida":       perfil["hora_preferida"],
            "pct_fines_semana":     perfil["pct_fines_semana"],
            "diversidad_productos": perfil["diversidad_productos"],
            # Coordenadas en el espacio PCA
            # pc1 y pc2 son los valores que consumirá WCSS y K-Means
            "pc1": round(float(proyecciones[i][0]), 6),
            "pc2": round(float(proyecciones[i][1]), 6) if proyecciones.shape[1] > 1 else 0.0
        })

    # ── Construcción del JSON de salida ───────────────────────────────────────
    salida = {
        # Metadata del PCA
        "total_clientes":          len(clientes_pca),
        "features_usadas":         FEATURES,
        "n_componentes_pca":       resultado_pca["n_componentes"],
        "varianza_por_componente": resultado_pca["varianza_por_componente"],
        "varianza_acumulada_pca":  resultado_pca["varianza_acumulada"],
        "eigenvalores":            resultado_pca["eigenvalores"],
        # Loadings: qué feature impulsa cada componente
        "loadings": [
            {
                "componente": f"PC{k+1}",
                "pesos":      dict(zip(FEATURES, resultado_pca["loadings"][k]))
            }
            for k in range(resultado_pca["n_componentes"])
        ],
        # Interpretación en lenguaje natural
        "interpretacion_componentes": interpretaciones,
        # Datos por cliente listos para la Fase 2 (WCSS + K-Means)
        "clientes": clientes_pca
    }

    # ── Guardar JSON ──────────────────────────────────────────────────────────
    output_path = os.path.join(os.path.dirname(__file__), "segmentacion_pca.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=4)

    print(f"\n✓ segmentacion_pca.json guardado → {output_path}")
    return salida

# =============================================================================
# UTILIDAD
# =============================================================================

def _limpiar_numero(valor):
    """Convierte cualquier valor a float. Retorna 0.0 si no es posible."""
    if valor is None:
        return 0.0
    if isinstance(valor, str):
        valor = valor.replace("$", "").replace(",", "").strip()
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


# =============================================================================
# ENTRY POINT — prueba standalone
# =============================================================================

if __name__ == "__main__":
    resultado = ejecutar_pca_clientes()
    if resultado:
        print("\nResumen:")
        print(f"  Clientes procesados:  {resultado['total_clientes']}")
        print(f"  Componentes PCA:      {resultado['n_componentes_pca']}")
        print(f"  Varianza explicada:   {resultado['varianza_acumulada_pca'] * 100:.1f}%")
