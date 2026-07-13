# api/ml_trainer.py
# Ejecutar: source .venv/bin/activate && python ml_trainer.py

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, count, sum as spark_sum, round as spark_round
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import DecisionTreeClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
from collections import defaultdict
from itertools import combinations
import certifi
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = "CoffeSoft2"


def conectar_mongo():
    client = MongoClient(
        MONGO_URI,
        server_api=ServerApi('1'),
        tlsCAFile=certifi.where(),
        tls=True
    )
    return client, client[DATABASE_NAME]


# ============================================================
# UTILIDADES COMPARTIDAS
# ============================================================

def limpiar_numero(valor):
    if valor is None:
        return 0.0
    if isinstance(valor, str):
        valor = valor.replace("$", "").replace(",", "").strip()
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def limpiar_nombre(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def normalizar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def es_object_id(valor):
    try:
        ObjectId(str(valor))
        return True
    except Exception:
        return False


def obtener_items_productos(productos):
    if isinstance(productos, dict):
        return productos.values()
    if isinstance(productos, list):
        return productos
    return []


# ============================================================
# SPARK — VENTAS / CLIENTES / PREDICCIONES
# ============================================================

def leer_ventas_pymongo(db):
    """Lee todas las ventas y aplana el dict de productos."""
    ventas = list(db["ventas"].find())
    filas = []
    for venta in ventas:
        total = float(venta.get("total", 0) or 0)
        productos = venta.get("productos", {})
        if isinstance(productos, dict):
            for _, producto in productos.items():
                nombre   = producto.get("nombre", "")
                cantidad = producto.get("cantidad")
                precio   = producto.get("precio")
                if isinstance(precio, str):
                    precio = precio.replace("$", "").replace(",", "").strip()
                try:
                    cantidad = float(cantidad)
                    precio   = float(precio)
                    if cantidad > 0 and precio > 0:
                        filas.append((nombre, cantidad, precio, total))
                except (TypeError, ValueError):
                    continue
    return filas


def leer_clientes_pymongo(db):
    """Lee ventas del mes actual con usuario_id."""
    inicio_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ventas = list(db["ventas"].find(
        {"created_at": {"$gte": inicio_mes}, "usuario_id": {"$exists": True, "$ne": None}},
        {"usuario_id": 1, "total": 1, "created_at": 1}
    ))

    usuarios_map = {}
    for venta in ventas:
        uid = str(venta.get("usuario_id", ""))
        if uid and uid not in usuarios_map:
            try:
                usuario = db["usuarios"].find_one({"_id": ObjectId(uid)}, {"nombre": 1})
                usuarios_map[uid] = usuario["nombre"] if usuario else f"Usuario {uid[:6]}"
            except Exception:
                usuarios_map[uid] = f"Usuario {uid[:6]}"

    filas = []
    for v in ventas:
        uid    = str(v.get("usuario_id", ""))
        total  = float(v.get("total", 0) or 0)
        nombre = usuarios_map.get(uid, "Desconocido")
        filas.append((uid, nombre, total))

    return filas


def entrenar(spark, db):
    """Entrena el modelo de árbol de decisión y guarda modelo_meta.json."""
    filas = leer_ventas_pymongo(db)

    if len(filas) < 5:
        print("✗ No hay suficientes datos para entrenar (mínimo 5 registros)")
        return None

    df = spark.createDataFrame(filas, ["nombre", "cantidad", "precio", "total"])
    df = df.withColumn("ingreso", col("cantidad") * col("precio"))

    umbral = df.approxQuantile("ingreso", [0.5], 0.01)[0]

    df = df.withColumn("label",
        when(col("ingreso") >= umbral, 1.0).otherwise(0.0)
    )

    assembler = VectorAssembler(
        inputCols=["cantidad", "precio", "ingreso"],
        outputCol="features",
        handleInvalid="skip"
    )
    df_ml = assembler.transform(df).select("features", "label")
    train, test = df_ml.randomSplit([0.8, 0.2], seed=42)

    dt = DecisionTreeClassifier(featuresCol="features", labelCol="label", maxDepth=5)
    model = dt.fit(train)

    predictions = model.transform(test)
    evaluator = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName="accuracy"
    )
    accuracy        = evaluator.evaluate(predictions)
    total_registros = df.count()

    model_path = os.path.join(os.path.dirname(__file__), "modelo_ventas")
    model.write().overwrite().save(model_path)

    meta = {
        "accuracy":              round(accuracy, 4),
        "total_registros":       int(total_registros),
        "umbral":                round(umbral, 2),
        "modelo_path":           model_path,
        "ultima_actualizacion":  datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(os.path.join(os.path.dirname(__file__), "modelo_meta.json"), "w") as f:
        json.dump(meta, f)

    print(f"✓ Modelo entrenado | Accuracy: {accuracy:.2%} | Umbral: ${umbral:.2f} | Registros: {total_registros}")
    return meta


def analizar_clientes(spark, db):
    """Analiza clientes frecuentes del mes actual con Spark y guarda clientes_frecuentes.json."""
    filas = leer_clientes_pymongo(db)

    if not filas:
        print("⚠ Sin ventas de clientes este mes")
        with open(os.path.join(os.path.dirname(__file__), "clientes_frecuentes.json"), "w") as f:
            json.dump([], f)
        return []

    df = spark.createDataFrame(filas, ["usuario_id", "nombre", "total"])

    resumen = df.groupBy("usuario_id", "nombre").agg(
        count("*").alias("num_compras"),
        spark_round(spark_sum("total"), 2).alias("total_gastado")
    ).orderBy(col("num_compras").desc())

    resultado = resumen.collect()

    data = [
        {
            "posicion":      i + 1,
            "nombre":        row["nombre"],
            "num_compras":   row["num_compras"],
            "total_gastado": float(row["total_gastado"])
        }
        for i, row in enumerate(resultado)
    ]

    with open(os.path.join(os.path.dirname(__file__), "clientes_frecuentes.json"), "w") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"✓ Clientes del mes analizados | Total: {len(data)} | Top: {data[0]['nombre'] if data else '—'}")
    return data


def analizar_productos_mes(spark, db):
    """Analiza top 10 productos del mes actual con Spark y guarda productos_mes.json."""
    inicio_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    ventas = list(db["ventas"].find(
        {"created_at": {"$gte": inicio_mes}},
        {"productos": 1}
    ))

    filas = []
    for venta in ventas:
        productos = venta.get("productos", {})
        if isinstance(productos, dict):
            for _, producto in productos.items():
                nombre   = producto.get("nombre", "")
                cantidad = producto.get("cantidad")
                try:
                    cantidad = int(cantidad)
                    if nombre and cantidad > 0:
                        filas.append((nombre, cantidad))
                except (TypeError, ValueError):
                    continue

    if not filas:
        print("⚠ Sin ventas este mes")
        with open(os.path.join(os.path.dirname(__file__), "productos_mes.json"), "w") as f:
            json.dump([], f)
        return []

    df = spark.createDataFrame(filas, ["nombre", "cantidad"])

    resumen = df.groupBy("nombre").agg(
        spark_sum("cantidad").alias("total_vendido")
    ).orderBy(col("total_vendido").desc()).limit(10)

    resultado = resumen.collect()

    data = [{"nombre": row["nombre"], "cantidad": int(row["total_vendido"])} for row in resultado]

    with open(os.path.join(os.path.dirname(__file__), "productos_mes.json"), "w") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"✓ Productos del mes analizados | Top: {data[0]['nombre'] if data else '—'}")
    return data


def predecir_productos_semana(spark, db):
    """
    Analiza ventas del último mes por producto y predice
    los 5 más y 5 menos vendidos de la próxima semana.
    """
    from pyspark.sql.functions import avg, stddev

    fecha_limite = datetime.utcnow() - timedelta(days=30)
    ventas = list(db["ventas"].find(
        {"created_at": {"$gte": fecha_limite}},
        {"productos": 1, "created_at": 1}
    ))

    filas = []
    for venta in ventas:
        productos = venta.get("productos", {})
        fecha = venta.get("created_at")
        semana = int(fecha.isocalendar()[1]) if fecha else 0
        if isinstance(productos, dict):
            for _, producto in productos.items():
                nombre   = producto.get("nombre", "")
                cantidad = producto.get("cantidad")
                try:
                    cantidad = int(cantidad)
                    if nombre and cantidad > 0:
                        filas.append((nombre, cantidad, semana))
                except (TypeError, ValueError):
                    continue

    if not filas:
        print("⚠ Sin datos para predicción de productos")
        with open(os.path.join(os.path.dirname(__file__), "prediccion_productos.json"), "w") as f:
            json.dump({"mas_vendidos": [], "menos_vendidos": []}, f)
        return

    df = spark.createDataFrame(filas, ["nombre", "cantidad", "semana"])

    resumen = df.groupBy("nombre").agg(
        avg("cantidad").alias("promedio_semanal"),
        stddev("cantidad").alias("desviacion"),
        spark_sum("cantidad").alias("total_mes")
    )

    resumen = resumen.withColumn(
        "prediccion_semana",
        spark_round(col("promedio_semanal") * 1.05, 1)
    ).orderBy(col("prediccion_semana").desc())

    todos = resumen.collect()

    mas_vendidos = [
        {
            "nombre":           r["nombre"],
            "prediccion":       float(r["prediccion_semana"]),
            "promedio_semanal": round(float(r["promedio_semanal"]), 1),
            "total_mes":        int(r["total_mes"])
        }
        for r in todos[:5]
    ]
    menos_vendidos = [
        {
            "nombre":           r["nombre"],
            "prediccion":       float(r["prediccion_semana"]),
            "promedio_semanal": round(float(r["promedio_semanal"]), 1),
            "total_mes":        int(r["total_mes"])
        }
        for r in todos[-5:]
    ]
    menos_vendidos.reverse()

    data = {"mas_vendidos": mas_vendidos, "menos_vendidos": menos_vendidos}

    with open(os.path.join(os.path.dirname(__file__), "prediccion_productos.json"), "w") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"✓ Predicción productos | Top: {mas_vendidos[0]['nombre'] if mas_vendidos else '—'}")
    return data


# ============================================================
# REGRESIÓN LINEAL — INSUMOS
# ============================================================

def predecir_insumos_semana(spark, db):
    """
    Regresión lineal para predecir cuánto insumo se necesitará
    la próxima semana. Guarda prediccion_insumos.json
    """
    from pyspark.ml.regression import LinearRegression

    fecha_limite = datetime.utcnow() - timedelta(days=30)

    ventas = list(db["ventas"].find(
        {"created_at": {"$gte": fecha_limite}},
        {"productos": 1, "created_at": 1}
    ))

    if not ventas:
        print("⚠ Sin ventas para predecir insumos")
        with open(os.path.join(os.path.dirname(__file__), "prediccion_insumos.json"), "w") as f:
            json.dump([], f)
        return []

    ventas_por_producto = {}
    for venta in ventas:
        productos = venta.get("productos", {})
        if isinstance(productos, dict):
            items = productos.values()
        elif isinstance(productos, list):
            items = productos
        else:
            continue

        for producto in items:
            pid      = str(producto.get("producto_id", ""))
            cantidad = producto.get("cantidad", 0)
            try:
                cantidad = float(cantidad)
                if pid and cantidad > 0:
                    ventas_por_producto[pid] = ventas_por_producto.get(pid, 0) + cantidad
            except (TypeError, ValueError):
                continue

    if not ventas_por_producto:
        print("⚠ No se pudo acumular ventas por producto")
        with open(os.path.join(os.path.dirname(__file__), "prediccion_insumos.json"), "w") as f:
            json.dump([], f)
        return []

    # ── Consumo REAL de la semana pasada (lunes-domingo anterior) ──────────
    hoy             = datetime.utcnow()
    inicio_sem_pas  = hoy - timedelta(days=hoy.weekday() + 7)   # lunes semana pasada
    fin_sem_pas     = inicio_sem_pas + timedelta(days=7)         # lunes semana actual

    ventas_sem_pas  = list(db["ventas"].find(
        {"created_at": {"$gte": inicio_sem_pas, "$lt": fin_sem_pas}},
        {"productos": 1}
    ))

    ventas_sem_por_producto = {}
    for venta in ventas_sem_pas:
        productos = venta.get("productos", {})
        if isinstance(productos, dict):
            items = productos.values()
        elif isinstance(productos, list):
            items = productos
        else:
            continue
        for producto in items:
            pid      = str(producto.get("producto_id", ""))
            cantidad = producto.get("cantidad", 0)
            try:
                cantidad = float(cantidad)
                if pid and cantidad > 0:
                    ventas_sem_por_producto[pid] = ventas_sem_por_producto.get(pid, 0) + cantidad
            except (TypeError, ValueError):
                continue

    # Acumular consumo real de insumos para la semana pasada
    consumo_real_sem = {}   # { nombre_insumo: consumo_real }
    for pid, total_vendido in ventas_sem_por_producto.items():
        try:
            producto = db["tb_productos"].find_one({"_id": ObjectId(pid)})
        except Exception:
            producto = db["tb_productos"].find_one({"_id": pid})
        if not producto:
            continue
        insumos          = producto.get("insumos", [])
        insumos_cantidad = producto.get("insumos_cantidad", {})
        for insumo_id in insumos:
            cantidad_por_unidad = float(insumos_cantidad.get(str(insumo_id), 0) or 0)
            if cantidad_por_unidad <= 0:
                continue
            try:
                insumo_doc = db["Insumos"].find_one({"_id": ObjectId(insumo_id)})
            except Exception:
                insumo_doc = db["Insumos"].find_one({"_id": insumo_id})
            nombre_insumo = insumo_doc["nombre"] if insumo_doc else str(insumo_id)
            consumo_real_sem[nombre_insumo] = round(
                consumo_real_sem.get(nombre_insumo, 0.0) + cantidad_por_unidad * total_vendido, 3
            )
    # ──────────────────────────────────────────────────────────────────────

    filas_insumos = {}


    for pid, total_vendido in ventas_por_producto.items():
        try:
            producto = db["tb_productos"].find_one({"_id": ObjectId(pid)})
        except Exception:
            producto = db["tb_productos"].find_one({"_id": pid})

        if not producto:
            continue

        insumos          = producto.get("insumos", [])
        insumos_cantidad = producto.get("insumos_cantidad", {})

        for insumo_id in insumos:
            cantidad_por_unidad = float(insumos_cantidad.get(str(insumo_id), 0) or 0)
            if cantidad_por_unidad <= 0:
                continue

            consumo_total = cantidad_por_unidad * total_vendido

            if insumo_id not in filas_insumos:
                try:
                    insumo_doc = db["Insumos"].find_one({"_id": ObjectId(insumo_id)})
                except Exception:
                    insumo_doc = db["Insumos"].find_one({"_id": insumo_id})

                nombre_insumo = insumo_doc["nombre"] if insumo_doc else str(insumo_id)
                tipo_insumo   = insumo_doc.get("tipo", "unidad") if insumo_doc else "unidad"
                stock_actual  = float(insumo_doc.get("cantidad", 0) or 0) if insumo_doc else 0

                filas_insumos[insumo_id] = {
                    "nombre":       nombre_insumo,
                    "tipo":         tipo_insumo,
                    "consumo_mes":  0.0,
                    "stock_actual": stock_actual,
                }

            filas_insumos[insumo_id]["consumo_mes"] += consumo_total

    if not filas_insumos:
        print("⚠ No se encontraron insumos asociados a las ventas")
        with open(os.path.join(os.path.dirname(__file__), "prediccion_insumos.json"), "w") as f:
            json.dump([], f)
        return []

    filas_spark = []
    for iid, data in filas_insumos.items():
        consumo_mes   = data["consumo_mes"]
        necesidad_sem = consumo_mes / 4.0
        filas_spark.append((
            str(iid),
            data["nombre"],
            data["tipo"],
            float(consumo_mes),
            float(necesidad_sem),
            float(data["stock_actual"]),
        ))

    df = spark.createDataFrame(
        filas_spark,
        ["insumo_id", "nombre", "tipo", "consumo_mes", "necesidad_semana", "stock_actual"]
    )

    resultado = []

    if df.count() >= 3:
        assembler = VectorAssembler(
            inputCols=["consumo_mes"],
            outputCol="features",
            handleInvalid="skip"
        )
        df_ml = assembler.transform(df)
        train, test = df_ml.randomSplit([0.8, 0.2], seed=42)

        lr = LinearRegression(featuresCol="features", labelCol="necesidad_semana", regParam=0.1)

        if train.count() > 0:
            model        = lr.fit(train)
            predicciones = model.transform(df_ml)

            rows = predicciones.select(
                "insumo_id", "nombre", "tipo",
                "consumo_mes", "necesidad_semana",
                "prediction", "stock_actual"
            ).collect()

            for row in rows:
                pred_semana    = max(0.0, float(row["prediction"]))
                nombre_insumo  = row["nombre"]
                # Consumo real de la semana pasada; si no hubo ventas ese insumo → None
                necesidad_real = consumo_real_sem.get(nombre_insumo, None)
                stock          = float(row["stock_actual"])
                dias_restantes = round((stock / pred_semana * 7), 1) if pred_semana > 0 else None
                error_absoluto = round(abs(pred_semana - necesidad_real), 3) if necesidad_real is not None else None
                resultado.append({
                    "nombre":           nombre_insumo,
                    "tipo":             row["tipo"],
                    "consumo_mes":      round(float(row["consumo_mes"]), 3),
                    "necesidad_real":   necesidad_real,
                    "necesidad_semana": round(pred_semana, 3),
                    "error_absoluto":   error_absoluto,
                    "stock_actual":     round(stock, 3),
                    "dias_restantes":   dias_restantes,
                    "alerta":           stock < pred_semana
                })


        else:
            resultado = _fallback_insumos(filas_insumos)
    else:
        resultado = _fallback_insumos(filas_insumos)

    resultado.sort(key=lambda x: x["necesidad_semana"], reverse=True)

    with open(os.path.join(os.path.dirname(__file__), "prediccion_insumos.json"), "w") as f:
        json.dump(resultado, f, ensure_ascii=False)

    alertas = sum(1 for r in resultado if r["alerta"])
    print(f"✓ Predicción insumos | Total: {len(resultado)} | Alertas stock bajo: {alertas}")
    return resultado


def _fallback_insumos(filas_insumos):
    resultado = []
    for iid, data in filas_insumos.items():
        pred_semana    = data["consumo_mes"] / 4.0
        stock          = data["stock_actual"]
        dias_restantes = round((stock / pred_semana * 7), 1) if pred_semana > 0 else None
        resultado.append({
            "nombre":           data["nombre"],
            "tipo":             data["tipo"],
            "consumo_mes":      round(data["consumo_mes"], 3),
            "necesidad_semana": round(pred_semana, 3),
            "stock_actual":     round(stock, 3),
            "dias_restantes":   dias_restantes,
            "alerta":           stock < pred_semana
        })
    return resultado


# ============================================================
# ÁRBOL DE DECISIONES — CLASIFICACIÓN DE INSUMOS
# ============================================================

def clasificar_insumos_arbol(spark, db):
    """
    Árbol de decisión enfocado en insumos próximos a caducar (≤14 días).
    Guarda clasificacion_insumos.json
    """
    insumos = list(db["Insumos"].find())
    if not insumos:
        print("⚠ Sin insumos para clasificar")
        with open(os.path.join(os.path.dirname(__file__), "clasificacion_insumos.json"), "w") as f:
            json.dump([], f)
        return []

    pred_path     = os.path.join(os.path.dirname(__file__), "prediccion_insumos.json")
    necesidad_map = {}
    if os.path.exists(pred_path):
        with open(pred_path, "r", encoding="utf-8") as f:
            preds = json.load(f)
        for p in preds:
            necesidad_map[p["nombre"]] = p.get("necesidad_semana", 0)

    productos_por_insumo = {}
    productos = list(db["tb_productos"].find({}, {"nombre": 1, "precio": 1, "insumos": 1}))
    for prod in productos:
        for iid in prod.get("insumos", []):
            key = str(iid)
            if key not in productos_por_insumo:
                productos_por_insumo[key] = []
            productos_por_insumo[key].append({
                "nombre": prod.get("nombre", ""),
                "precio": float(prod.get("precio", 0)),
            })

    hoy   = datetime.utcnow().date()
    filas = []

    for ins in insumos:
        nombre    = ins.get("nombre", "")
        cantidad  = float(ins.get("cantidad", 0) or 0)
        caducidad = ins.get("caducidad", "NA")
        iid       = str(ins.get("_id", ""))

        if caducidad and caducidad != "NA":
            try:
                fecha_cad = datetime.strptime(caducidad[:10], "%Y-%m-%d").date()
                dias_cad  = (fecha_cad - hoy).days
            except Exception:
                dias_cad = 999
        else:
            dias_cad = 999

        necesidad_sem = float(necesidad_map.get(nombre, 0))
        ratio_consumo = (cantidad / necesidad_sem) if necesidad_sem > 0 else 999.0

        if dias_cad > 14:
            label = 0.0
        elif dias_cad <= 3:
            label = 3.0
        elif dias_cad <= 7:
            label = 2.0
        else:
            label = 1.0

        filas.append((
            nombre,
            float(dias_cad) if dias_cad < 999 else 999.0,
            cantidad,
            necesidad_sem,
            ratio_consumo,
            label,
            iid,
            caducidad,
        ))

    if len(filas) < 3:
        print("⚠ Pocos insumos para entrenar árbol")
        with open(os.path.join(os.path.dirname(__file__), "clasificacion_insumos.json"), "w") as f:
            json.dump([], f)
        return []

    df = spark.createDataFrame(
        [(f[0], f[1], f[2], f[3], f[4], f[5]) for f in filas],
        ["nombre", "dias_cad", "cantidad", "necesidad_sem", "ratio_consumo", "label"]
    )

    assembler = VectorAssembler(
        inputCols=["dias_cad", "cantidad", "necesidad_sem", "ratio_consumo"],
        outputCol="features",
        handleInvalid="skip"
    )
    df_ml        = assembler.transform(df)
    train, test  = df_ml.randomSplit([0.8, 0.2], seed=42)
    if train.count() == 0:
        train = df_ml

    dt           = DecisionTreeClassifier(featuresCol="features", labelCol="label", maxDepth=4)
    model        = dt.fit(train)
    predicciones = model.transform(df_ml)

    etiquetas = {0.0: "Sin urgencia", 1.0: "Descuento individual", 2.0: "Descuento por paquete", 3.0: "Liquidar urgente"}
    descuentos = {0.0: 0, 1.0: 10, 2.0: 20, 3.0: 35}
    niveles    = {0.0: "success", 1.0: "info", 2.0: "warning", 3.0: "danger"}

    rows     = predicciones.select(
        "nombre", "dias_cad", "cantidad", "necesidad_sem", "ratio_consumo", "prediction"
    ).collect()

    fila_map  = {f[0]: f for f in filas}
    resultado = []

    for row in rows:
        pred          = float(row["prediction"])
        nombre        = row["nombre"]
        dias_cad      = float(row["dias_cad"])
        iid           = fila_map[nombre][6] if nombre in fila_map else ""
        caducidad_raw = fila_map[nombre][7] if nombre in fila_map else "NA"

        prods_asociados = productos_por_insumo.get(iid, [])
        descuento_pct   = descuentos[pred]

        propuestas = []
        for prod in prods_asociados:
            precio_orig = prod["precio"]
            precio_desc = round(precio_orig * (1 - descuento_pct / 100), 2)
            if pred == 2.0:
                propuestas.append({
                    "producto":      prod["nombre"],
                    "precio_normal": precio_orig,
                    "propuesta":     f"Paquete 2x1 — ${precio_orig} los dos",
                    "ahorro":        round(precio_orig, 2),
                })
            elif pred >= 1.0:
                propuestas.append({
                    "producto":      prod["nombre"],
                    "precio_normal": precio_orig,
                    "propuesta":     f"{descuento_pct}% descuento — ${precio_desc}",
                    "ahorro":        round(precio_orig - precio_desc, 2),
                })

        resultado.append({
            "nombre":          nombre,
            "caducidad":       caducidad_raw,
            "dias_restantes":  int(dias_cad) if dias_cad < 999 else None,
            "cantidad":        round(float(row["cantidad"]), 3),
            "necesidad_sem":   round(float(row["necesidad_sem"]), 3),
            "clasificacion":   etiquetas[pred],
            "nivel":           niveles[pred],
            "descuento_pct":   descuento_pct,
            "propuestas":      propuestas,
            "prediccion":      pred,
        })

    resultado_filtrado = [r for r in resultado if r["dias_restantes"] is not None and r["dias_restantes"] <= 14]
    resultado_filtrado.sort(key=lambda x: x["dias_restantes"])

    with open(os.path.join(os.path.dirname(__file__), "clasificacion_insumos.json"), "w") as f:
        json.dump(resultado_filtrado, f, ensure_ascii=False)

    print(f"✓ Árbol caducidad | Próx. a caducar (≤14d): {len(resultado_filtrado)} insumos")
    return resultado_filtrado


# ============================================================
# MAPREDUCE — CONSUMO DE INSUMOS
# ============================================================

def buscar_nombre_insumo(valor, db):
    texto = normalizar_texto(valor)
    if not texto:
        return "Insumo sin nombre"
    if not es_object_id(texto):
        return texto
    try:
        insumo = db["Insumos"].find_one({"_id": ObjectId(texto)})
        if insumo:
            return (
                insumo.get("nombre")
                or insumo.get("insumo")
                or insumo.get("descripcion")
                or f"Insumo {texto}"
            )
    except Exception:
        pass
    return f"Insumo {texto}"


def buscar_producto_en_catalogo(nombre_producto, db):
    nombre_producto = normalizar_texto(nombre_producto)
    if not nombre_producto:
        return None
    return (
        db["tb_productos"].find_one({"nombre": nombre_producto})
        or db["tb_productos"].find_one({"name": nombre_producto})
        or db["tb_productos"].find_one({"producto": nombre_producto})
        or db["tb_productos"].find_one({"descripcion": nombre_producto})
    )


def obtener_nombre_producto_vendido(producto_vendido):
    nombre = (
        producto_vendido.get("nombre")
        or producto_vendido.get("name")
        or producto_vendido.get("producto")
        or producto_vendido.get("descripcion")
        or ""
    )
    return normalizar_texto(nombre)


def obtener_insumos_producto(producto_db, db):
    if not producto_db:
        return []
    insumos    = producto_db.get("insumos") or []
    cantidades = producto_db.get("insumos_cantidad") or {}
    if not isinstance(insumos, list):
        return []
    resultado = []
    for insumo in insumos:
        if isinstance(insumo, dict):
            raw_id = (
                insumo.get("_id") or insumo.get("id") or insumo.get("insumo_id")
                or insumo.get("inventario_id") or insumo.get("producto_id")
                or insumo.get("nombre") or insumo.get("name") or insumo.get("insumo")
            )
            nombre_insumo = buscar_nombre_insumo(raw_id, db)
            cantidad = limpiar_numero(
                insumo.get("cantidad") or insumo.get("cantidad_por_producto")
                or insumo.get("cantidad_usada") or cantidades.get(str(raw_id)) or 1
            )
        elif isinstance(insumo, str):
            nombre_insumo = buscar_nombre_insumo(insumo, db)
            cantidad      = limpiar_numero(cantidades.get(insumo, 1))
        else:
            continue
        if cantidad <= 0:
            cantidad = 1
        resultado.append({"insumo": nombre_insumo, "cantidad": cantidad})
    return resultado


def ejecutar_mapreduce_insumos(db):
    consumo_por_insumo = defaultdict(lambda: defaultdict(lambda: {
        "producto": "", "cantidad_vendida": 0.0, "consumo_estimado": 0.0
    }))

    ventas = list(db["ventas"].find())

    for venta in ventas:
        productos = venta.get("productos", {})
        for producto_vendido in obtener_items_productos(productos):
            if not isinstance(producto_vendido, dict):
                continue
            nombre_producto  = obtener_nombre_producto_vendido(producto_vendido)
            cantidad_vendida = limpiar_numero(
                producto_vendido.get("cantidad") or producto_vendido.get("qty")
                or producto_vendido.get("quantity") or 0
            )
            if not nombre_producto or cantidad_vendida <= 0:
                continue
            producto_db = buscar_producto_en_catalogo(nombre_producto, db)
            if not producto_db:
                continue
            insumos = obtener_insumos_producto(producto_db, db)
            if not insumos:
                continue
            for insumo_data in insumos:
                nombre_insumo         = insumo_data["insumo"] or "Insumo sin nombre"
                cantidad_por_producto = limpiar_numero(insumo_data["cantidad"])
                if cantidad_por_producto <= 0:
                    cantidad_por_producto = 1
                consumo_estimado = cantidad_por_producto * cantidad_vendida
                ref = consumo_por_insumo[nombre_insumo][nombre_producto]
                ref["producto"]          = nombre_producto
                ref["cantidad_vendida"] += cantidad_vendida
                ref["consumo_estimado"] += consumo_estimado

    resultado = []
    for nombre_insumo, productos_dict in consumo_por_insumo.items():
        productos         = list(productos_dict.values())
        productos_ordenados = sorted(productos, key=lambda x: x["consumo_estimado"], reverse=True)
        ranking = []
        for index, producto in enumerate(productos_ordenados[:10], start=1):
            ranking.append({
                "posicion":         index,
                "producto":         producto["producto"],
                "cantidad_vendida": round(float(producto["cantidad_vendida"]), 2),
                "consumo_estimado": round(float(producto["consumo_estimado"]), 2)
            })
        resultado.append({
            "insumo":           nombre_insumo,
            "total_consumido":  round(sum(p["consumo_estimado"] for p in productos), 2),
            "ranking_productos": ranking
        })

    resultado = sorted(resultado, key=lambda x: x["total_consumido"], reverse=True)

    output_path = os.path.join(os.path.dirname(__file__), "mapreduce_insumos.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=4)

    print(f"✓ MapReduce comparativo generado correctamente | Insumos: {len(resultado)}")
    return resultado


# ============================================================
# KMEANS — COMBOS DE PRODUCTOS
# ============================================================

def buscar_producto_por_id(producto_id, db):
    if not producto_id:
        return None
    try:
        producto = db["tb_productos"].find_one({"_id": producto_id})
        if producto:
            return producto
    except Exception:
        pass
    try:
        producto = db["tb_productos"].find_one({"_id": ObjectId(str(producto_id))})
        if producto:
            return producto
    except Exception:
        pass
    return None


def buscar_producto_por_nombre(nombre, db):
    nombre = limpiar_nombre(nombre)
    if not nombre:
        return None
    return (
        db["tb_productos"].find_one({"nombre": nombre})
        or db["tb_productos"].find_one({"name": nombre})
        or db["tb_productos"].find_one({"producto": nombre})
        or db["tb_productos"].find_one({"descripcion": nombre})
    )


def obtener_nombre_desde_documento(producto_db):
    if not producto_db:
        return ""
    return limpiar_nombre(
        producto_db.get("nombre") or producto_db.get("name")
        or producto_db.get("producto") or producto_db.get("descripcion") or ""
    )


def obtener_precio_desde_documento(producto_db):
    if not producto_db:
        return 0.0
    return limpiar_numero(
        producto_db.get("precio") or producto_db.get("price")
        or producto_db.get("precio_unitario") or 0
    )


def resolver_producto(producto_venta, db):
    if not isinstance(producto_venta, dict):
        return None

    nombre_directo = limpiar_nombre(
        producto_venta.get("nombre") or producto_venta.get("name")
        or producto_venta.get("producto") or producto_venta.get("descripcion") or ""
    )
    precio_directo = limpiar_numero(
        producto_venta.get("precio") or producto_venta.get("price")
        or producto_venta.get("precio_unitario") or producto_venta.get("subtotal") or 0
    )

    producto_db = None
    producto_id = (
        producto_venta.get("producto_id")
        or producto_venta.get("_id")
        or producto_venta.get("id")
    )

    if producto_id:
        producto_db = buscar_producto_por_id(producto_id, db)
    if not producto_db and nombre_directo:
        producto_db = buscar_producto_por_nombre(nombre_directo, db)

    nombre_final = nombre_directo or obtener_nombre_desde_documento(producto_db)
    precio_final = precio_directo or obtener_precio_desde_documento(producto_db)

    if not nombre_final:
        return None

    return {"nombre": nombre_final, "precio": precio_final}


def calcular_descuento(frecuencia):
    if frecuencia >= 10: return 0.15
    if frecuencia >= 5:  return 0.10
    if frecuencia >= 3:  return 0.05
    return 0.0


def clasificar_combo(frecuencia):
    if frecuencia >= 10: return "Combo fuerte"
    if frecuencia >= 5:  return "Combo recomendado"
    if frecuencia >= 3:  return "Combo potencial"
    return "Combo exploratorio"


def generar_accion(tipo, combo):
    if tipo == "Combo fuerte":      return f"Crear promoción principal con {combo}"
    if tipo == "Combo recomendado": return f"Ofrecer descuento moderado para {combo}"
    if tipo == "Combo potencial":   return f"Probar combo temporal con {combo}"
    return f"Monitorear comportamiento de {combo}"


def ejecutar_kmeans_productos(db):
    conteo_combos      = defaultdict(int)
    precios_detectados = defaultdict(list)
    ventas_analizadas               = 0
    ventas_con_dos_o_mas_productos  = 0

    ventas = list(db["ventas"].find())

    for venta in ventas:
        ventas_analizadas += 1
        productos      = venta.get("productos", {})
        productos_venta = {}

        for producto_raw in obtener_items_productos(productos):
            producto = resolver_producto(producto_raw, db)
            if not producto:
                continue
            nombre = producto["nombre"]
            precio = producto["precio"]
            productos_venta[nombre] = precio
            if precio > 0:
                precios_detectados[nombre].append(precio)

        nombres = sorted(list(productos_venta.keys()))
        if len(nombres) < 2:
            continue

        ventas_con_dos_o_mas_productos += 1
        for producto_a, producto_b in combinations(nombres, 2):
            conteo_combos[f"{producto_a} + {producto_b}"] += 1

    resultado = []
    for combo, frecuencia in conteo_combos.items():
        producto_1, producto_2 = combo.split(" + ")

        precio_1 = (
            sum(precios_detectados[producto_1]) / len(precios_detectados[producto_1])
            if precios_detectados[producto_1]
            else obtener_precio_desde_documento(buscar_producto_por_nombre(producto_1, db))
        )
        precio_2 = (
            sum(precios_detectados[producto_2]) / len(precios_detectados[producto_2])
            if precios_detectados[producto_2]
            else obtener_precio_desde_documento(buscar_producto_por_nombre(producto_2, db))
        )

        precio_normal    = precio_1 + precio_2
        descuento        = calcular_descuento(frecuencia)
        precio_sugerido  = precio_normal * (1 - descuento)
        ahorro           = precio_normal - precio_sugerido
        porcentaje       = (frecuencia / ventas_con_dos_o_mas_productos * 100
                           if ventas_con_dos_o_mas_productos > 0 else 0)
        tipo             = clasificar_combo(frecuencia)

        resultado.append({
            "combo":                          combo,
            "producto_1":                     producto_1,
            "producto_2":                     producto_2,
            "frecuencia":                     int(frecuencia),
            "ventas_analizadas":              int(ventas_analizadas),
            "ventas_con_dos_o_mas_productos": int(ventas_con_dos_o_mas_productos),
            "porcentaje_aparicion":           round(porcentaje, 2),
            "precio_producto_1":              round(float(precio_1), 2),
            "precio_producto_2":              round(float(precio_2), 2),
            "precio_normal":                  round(float(precio_normal), 2),
            "descuento_sugerido":             int(descuento * 100),
            "precio_combo_sugerido":          round(float(precio_sugerido), 2),
            "ahorro_cliente":                 round(float(ahorro), 2),
            "recomendacion_tipo":             tipo,
            "recomendacion":                  generar_accion(tipo, combo)
        })

    resultado = sorted(resultado, key=lambda x: x["frecuencia"], reverse=True)[:10]
    for index, item in enumerate(resultado, start=1):
        item["posicion"] = index

    output_path = os.path.join(os.path.dirname(__file__), "kmeans_productos.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=4)

    print(f"✓ Análisis de combos generado | Ventas: {ventas_analizadas} | Combos: {len(resultado)}")
    return resultado


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    client, db = conectar_mongo()

    spark = SparkSession.builder \
        .appName("CoffeSoftML") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    entrenar(spark, db)
    analizar_clientes(spark, db)
    analizar_productos_mes(spark, db)
    predecir_productos_semana(spark, db)
    predecir_insumos_semana(spark, db)
    clasificar_insumos_arbol(spark, db)
    ejecutar_mapreduce_insumos(db)
    ejecutar_kmeans_productos(db)

    spark.stop()
    client.close()
