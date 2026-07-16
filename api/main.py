from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from bson import ObjectId
from pyspark.ml.classification import DecisionTreeClassificationModel
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from ml_trainer import ejecutar_mapreduce_insumos, ejecutar_kmeans_productos



import json as json_lib
import config
import os

# Crear la aplicación FastAPI
app = FastAPI(
    title="CoffeSoft API",
    description="API para gestionar inventario, ventas, usuarios y productos",
    version="1.0.0"
)

# Configurar CORS para Laravel (importante para integración)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica el dominio de Laravel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Función auxiliar para convertir ObjectId a string
def serialize_doc(doc):
    """Convierte ObjectId de MongoDB a string para JSON"""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

# ============= ENDPOINTS DE INVENTARIO =============

@app.get("/")
def read_root():
    """Endpoint de bienvenida"""
    return {"message": "Bienvenido a CoffeSoft API", "status": "active"}

@app.get("/inventario")
def get_inventario(limit: Optional[int] = 100):
    """
    Obtener todos los productos del inventario con información del producto
    """
    try:
        inventario = list(config.inventario_collection.find().limit(limit))
        
        # Enriquecer con datos del producto
        for item in inventario:
            if "producto_id" in item:
                producto_id = item["producto_id"]
                
                # Intentar buscar el producto (manejar tanto string como int)
                try:
                    # Si es string, intentar convertir a ObjectId
                    if isinstance(producto_id, str):
                        producto = config.productos_collection.find_one({"_id": ObjectId(producto_id)})
                    else:
                        # Si es int u otro tipo, buscar directamente
                        producto = config.productos_collection.find_one({"_id": producto_id})
                    
                    if producto:
                        item["producto"] = serialize_doc(producto)
                except Exception as e:
                    # Si falla, intentar buscar por string directo
                    producto = config.productos_collection.find_one({"_id": str(producto_id)})
                    if producto:
                        item["producto"] = serialize_doc(producto)
        
        return {"data": [serialize_doc(item) for item in inventario]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inventario/{item_id}")
def get_inventario_item(item_id: str):
    """Obtener un item específico del inventario por ID"""
    try:
        item = config.inventario_collection.find_one({"_id": ObjectId(item_id)})
        if not item:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        
        # Agregar información del producto
        if "producto_id" in item:
            producto_id = item["producto_id"]
            
            try:
                if isinstance(producto_id, str):
                    producto = config.productos_collection.find_one({"_id": ObjectId(producto_id)})
                else:
                    producto = config.productos_collection.find_one({"_id": producto_id})
                
                if producto:
                    item["producto"] = serialize_doc(producto)
            except:
                producto = config.productos_collection.find_one({"_id": str(producto_id)})
                if producto:
                    item["producto"] = serialize_doc(producto)
        
        return {"data": serialize_doc(item)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inventario/producto/{producto_id}")
def get_inventario_by_producto(producto_id: str):
    """Obtener inventario de un producto específico"""
    try:
        item = config.inventario_collection.find_one({"producto_id": producto_id})
        if not item:
            raise HTTPException(status_code=404, detail="Inventario no encontrado para este producto")
        
        # Agregar información del producto
        try:
            producto = config.productos_collection.find_one({"_id": ObjectId(producto_id)})
        except:
            producto = config.productos_collection.find_one({"_id": producto_id})
        
        if producto:
            item["producto"] = serialize_doc(producto)
        
        return {"data": serialize_doc(item)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/inventario/{item_id}")
def update_inventario(item_id: str, data: dict):
    """Actualizar stock de un item del inventario"""
    try:
        # Verificar que el item existe
        existing = config.inventario_collection.find_one({"_id": ObjectId(item_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Item de inventario no encontrado")
        
        # Actualizar inventario
        from datetime import datetime
        data["fecha_actualizacion"] = datetime.utcnow().isoformat()
        
        result = config.inventario_collection.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No se pudo actualizar el inventario")
        
        # Obtener el inventario actualizado
        inventario_actualizado = config.inventario_collection.find_one({"_id": ObjectId(item_id)})
        return {"success": True, "data": serialize_doc(inventario_actualizado)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/inventario/producto/{producto_id}")
def update_inventario_by_producto(producto_id: str, data: dict):
    """Actualizar stock usando el ID del producto"""
    try:
        # Buscar inventario por producto_id
        existing = config.inventario_collection.find_one({"producto_id": producto_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Inventario no encontrado para este producto")
        
        # Actualizar inventario
        from datetime import datetime
        data["fecha_actualizacion"] = datetime.utcnow().isoformat()
        
        result = config.inventario_collection.update_one(
            {"producto_id": producto_id},
            {"$set": data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No se pudo actualizar el inventario")
        
        # Obtener el inventario actualizado
        inventario_actualizado = config.inventario_collection.find_one({"producto_id": producto_id})
        return {"success": True, "data": serialize_doc(inventario_actualizado)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inventario/resumen/estadisticas")
def get_inventario_estadisticas():
    """Obtener estadísticas del inventario"""
    try:
        # Total de stock
        pipeline_total = [
            {"$group": {"_id": None, "total_stock": {"$sum": "$stock_actual"}}}
        ]
        total_result = list(config.inventario_collection.aggregate(pipeline_total))
        total_stock = total_result[0]["total_stock"] if total_result else 0
        
        # Productos bajo stock
        bajo_stock = config.inventario_collection.count_documents({
            "$expr": {"$lte": ["$stock_actual", "$stock_minimo"]}
        })
        
        # Total de productos
        total_productos = config.inventario_collection.count_documents({})
        
        return {
            "data": {
                "total_stock": total_stock,
                "total_productos": total_productos,
                "productos_bajo_stock": bajo_stock
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= ENDPOINTS DE VENTAS =============

@app.get("/ventas")
def get_ventas(limit: Optional[int] = 100):
    """Obtener todas las ventas"""
    try:
        ventas = list(config.ventas_collection.find().limit(limit))
        return {"data": [serialize_doc(venta) for venta in ventas]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ventas/resumen")
def get_ventas_resumen():
    """
    Obtener resumen de ventas (como tu código actual)
    - Total de ventas
    - Cantidad de ventas
    - Promedio por venta
    """
    try:
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_ventas": {"$sum": "$total"},
                    "cantidad_ventas": {"$sum": 1},
                    "promedio_venta": {"$avg": "$total"}
                }
            }
        ]
        resultado = list(config.ventas_collection.aggregate(pipeline))
        
        if resultado:
            return {
                "data": {
                    "total_ventas": resultado[0]['total_ventas'],
                    "cantidad_ventas": resultado[0]['cantidad_ventas'],
                    "promedio_venta": resultado[0]['promedio_venta']
                }
            }
        return {"data": {"total_ventas": 0, "cantidad_ventas": 0, "promedio_venta": 0}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ventas/{venta_id}")
def get_venta(venta_id: str):
    """Obtener una venta específica por ID"""
    try:
        venta = config.ventas_collection.find_one({"_id": ObjectId(venta_id)})
        if not venta:
            raise HTTPException(status_code=404, detail="Venta no encontrada")
        return {"data": serialize_doc(venta)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= ENDPOINTS DE USUARIOS =============

@app.get("/usuarios")
def get_usuarios(limit: Optional[int] = 100):
    """Obtener todos los usuarios"""
    try:
        usuarios = list(config.usuarios_collection.find().limit(limit))
        return {"data": [serialize_doc(usuario) for usuario in usuarios]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/usuarios/{usuario_id}")
def get_usuario(usuario_id: str):
    """Obtener un usuario específico por ID"""
    try:
        usuario = config.usuarios_collection.find_one({"_id": ObjectId(usuario_id)})
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return {"data": serialize_doc(usuario)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= ENDPOINTS ADICIONALES DE USUARIOS =============

@app.get("/usuarios/email/{email}")
def get_usuario_by_email(email: str):
    """Obtener usuario por email"""
    try:
        usuario = config.usuarios_collection.find_one({"email": email})
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return {"data": serialize_doc(usuario)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/usuarios/token/{token}")
def get_usuario_by_token(token: str):
    """Obtener usuario por reset_token"""
    try:
        usuario = config.usuarios_collection.find_one({"reset_token": token})
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return {"data": serialize_doc(usuario)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/usuarios")
def create_usuario(usuario: dict):
    """Crear un nuevo usuario"""
    try:
        result = config.usuarios_collection.insert_one(usuario)
        nuevo = config.usuarios_collection.find_one({"_id": result.inserted_id})
        return {"success": True, "data": serialize_doc(nuevo)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/usuarios/{usuario_id}")
def update_usuario(usuario_id: str, data: dict):
    """Actualizar un usuario por ID"""
    try:
        existing = config.usuarios_collection.find_one({"_id": ObjectId(usuario_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        result = config.usuarios_collection.update_one(
            {"_id": ObjectId(usuario_id)},
            {"$set": data}
        )
        actualizado = config.usuarios_collection.find_one({"_id": ObjectId(usuario_id)})
        return {"success": True, "data": serialize_doc(actualizado)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= ENDPOINTS DE PRODUCTOS =============

@app.get("/productos")
def get_productos(limit: Optional[int] = 100):
    """Obtener todos los productos"""
    try:
        productos = list(config.productos_collection.find().limit(limit))
        return {"data": [serialize_doc(producto) for producto in productos]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/productos/{producto_id}")
def get_producto(producto_id: str):
    """Obtener un producto específico por ID"""
    try:
        producto = config.productos_collection.find_one({"_id": ObjectId(producto_id)})
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return {"data": serialize_doc(producto)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/productos")
def create_producto(producto: dict):
    """Crear un nuevo producto"""
    try:
        # Insertar producto en MongoDB
        result = config.productos_collection.insert_one(producto)
        
        # Crear inventario asociado si se proporcionan datos de stock
        if "stock_inicial" in producto:
            inventario_data = {
                "producto_id": str(result.inserted_id),
                "stock_actual": producto.get("stock_inicial", 0),
                "stock_minimo": producto.get("stock_minimo", 0),
                "fecha_actualizacion": producto.get("fecha_actualizacion")
            }
            config.inventario_collection.insert_one(inventario_data)
        
        # Obtener el producto creado
        nuevo_producto = config.productos_collection.find_one({"_id": result.inserted_id})
        return {"success": True, "data": serialize_doc(nuevo_producto)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/productos/{producto_id}")
def update_producto(producto_id: str, producto: dict):
    """Actualizar un producto existente"""
    try:
        # Verificar que el producto existe
        existing = config.productos_collection.find_one({"_id": ObjectId(producto_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        # Actualizar producto
        result = config.productos_collection.update_one(
            {"_id": ObjectId(producto_id)},
            {"$set": producto}
        )
# modified_count puede ser 0 si los datos son idénticos, igual es éxito

        
        # Obtener el producto actualizado
        producto_actualizado = config.productos_collection.find_one({"_id": ObjectId(producto_id)})
        return {"success": True, "data": serialize_doc(producto_actualizado)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/productos/{producto_id}")
def delete_producto(producto_id: str):
    """Eliminar un producto"""
    try:
        # Verificar que el producto existe
        producto = config.productos_collection.find_one({"_id": ObjectId(producto_id)})
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        # Eliminar inventario asociado primero
        config.inventario_collection.delete_many({"producto_id": producto_id})
        
        # Eliminar producto
        result = config.productos_collection.delete_one({"_id": ObjectId(producto_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="No se pudo eliminar el producto")
        
        return {"success": True, "message": "Producto eliminado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= ENDPOINT DE SALUD =============

@app.get("/health")
def health_check():
    """Verificar que la API y la conexión a MongoDB están funcionando"""
    try:
        # Intentar hacer ping a la base de datos
        config.client.admin.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

def _get_spark():
    return SparkSession.builder \
        .appName("CoffeSoftML-Predict") \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.3.0") \
        .getOrCreate()

@app.get("/ml/estadisticas")
def get_ml_estadisticas():
    """Retorna métricas del modelo entrenado"""
    try:
        meta_path = os.path.join(os.path.dirname(__file__), "modelo_meta.json")
        if not os.path.exists(meta_path):
            raise HTTPException(status_code=404, detail="Modelo no entrenado aún. Ejecuta ml_trainer.py")
        with open(meta_path, "r") as f:
            meta = json_lib.load(f)
        return {"success": True, "data": meta}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ml/clientes-frecuentes")
def get_clientes_frecuentes():
    """Retorna el ranking de clientes frecuentes del mes generado por el trainer"""
    try:
        path = os.path.join(os.path.dirname(__file__), "clientes_frecuentes.json")
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Datos no disponibles. Ejecuta ml_trainer.py")
        with open(path, "r", encoding="utf-8") as f:
            data = json_lib.load(f)
        return {"success": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ml/productos-mes")
def get_productos_mes():
    """Retorna el top 10 productos del mes generado por el trainer"""
    try:
        path = os.path.join(os.path.dirname(__file__), "productos_mes.json")
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Datos no disponibles. Ejecuta ml_trainer.py")
        with open(path, "r", encoding="utf-8") as f:
            data = json_lib.load(f)
        return {"success": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ml/prediccion-semana")
def get_prediccion_semana():
    """Retorna predicción de productos más y menos vendidos para la próxima semana"""
    try:
        path = os.path.join(os.path.dirname(__file__), "prediccion_productos.json")
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Datos no disponibles. Ejecuta ml_trainer.py")
        with open(path, "r", encoding="utf-8") as f:
            data = json_lib.load(f)
        return {"success": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/predecir")
def predecir_venta(data: dict):
    """
    Recibe: { "cantidad": 3, "precio": 90 }
    Retorna: { "prediccion": "alta"/"baja", "ingreso": 270, "confianza": 0.87 }
    """
    try:
        cantidad = float(data.get("cantidad", 0))
        precio = float(data.get("precio", 0))

        if cantidad <= 0 or precio <= 0:
            raise HTTPException(status_code=400, detail="Cantidad y precio deben ser mayores a 0")

        model_path = os.path.join(os.path.dirname(__file__), "modelo_ventas")
        if not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail="Modelo no entrenado aún. Ejecuta ml_trainer.py")

        ingreso = cantidad * precio

        spark = _get_spark()
        spark.sparkContext.setLogLevel("ERROR")

        model = DecisionTreeClassificationModel.load(model_path)

        df = spark.createDataFrame([(cantidad, precio, ingreso)], ["cantidad", "precio", "ingreso"])
        assembler = VectorAssembler(inputCols=["cantidad", "precio", "ingreso"], outputCol="features", handleInvalid="skip")
        df = assembler.transform(df)

        result = model.transform(df).select("prediction", "probability").collect()[0]
        prediccion = "alta" if result["prediction"] == 1.0 else "baja"
        probabilidades = result["probability"].toArray().tolist()
        confianza = round(max(probabilidades), 4)

        return {
            "success": True,
            "data": {
                "prediccion": prediccion,
                "ingreso": round(ingreso, 2),
                "confianza": confianza
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#REGRESION LINEAL INSUMOS

@app.get("/ml/prediccion-insumos")
def get_prediccion_insumos():
    """Retorna predicción de consumo de insumos para la próxima semana"""
    try:
        path = os.path.join(os.path.dirname(__file__), "prediccion_insumos.json")
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Datos no disponibles. Ejecuta ml_trainer.py")
        with open(path, "r", encoding="utf-8") as f:
            data = json_lib.load(f)
        return {"success": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#ARBOL DE DESICIONES

@app.get("/ml/clasificacion-insumos")
def get_clasificacion_insumos():
    """Retorna clasificación de insumos por árbol de decisión"""
    try:
        path = os.path.join(os.path.dirname(__file__), "clasificacion_insumos.json")
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Datos no disponibles. Ejecuta ml_trainer.py")
        with open(path, "r", encoding="utf-8") as f:
            data = json_lib.load(f)
        return {"success": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#MapReduce

@app.get("/analytics/mapreduce-insumos")
def get_mapreduce_insumos():
    try:
        path = os.path.join(os.path.dirname(__file__), "mapreduce_insumos.json")

        usar_cache = False

        if os.path.exists(path):
            import time
            tiempo_actual = time.time()
            tiempo_archivo = os.path.getmtime(path)

            # 300 segundos = 5 minutos
            if tiempo_actual - tiempo_archivo < 300:
                usar_cache = True

        if usar_cache:
            with open(path, "r", encoding="utf-8") as archivo:
                data = json_lib.load(archivo)

            return {
                "success": True,
                "source": "cache",
                "data": data
            }

        data = ejecutar_mapreduce_insumos()

        return {
            "success": True,
            "source": "mongodb",
            "data": data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error ejecutando MapReduce: {str(e)}"
        )


@app.get("/analytics/kmeans-productos")
def get_kmeans_productos():
    try:
        data = ejecutar_kmeans_productos()

        return {
            "success": True,
            "source": "mongodb",
            "algorithm": "combos_por_historial_ventas",
            "total_registros": len(data),
            "data": data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error ejecutando análisis de combos: {str(e)}"
        )
    
    # ===============================
# ENDPOINTS SEGMENTACION CLIENTES
# ===============================

BASE = os.path.dirname(os.path.abspath(__file__))


def leer_json(nombre):
    ruta = os.path.join(BASE, nombre)

    if not os.path.exists(ruta):
        raise HTTPException(
            status_code=404,
            detail=f"Archivo {nombre} no encontrado"
        )

    with open(ruta, "r", encoding="utf-8") as archivo:
        return json_lib.load(archivo)



@app.get("/ml/pca")
def obtener_pca():
    return {
        "success": True,
        "data": leer_json("segmentacion_pca.json")
    }



@app.get("/ml/wcss")
def obtener_wcss():
    return {
        "success": True,
        "data": leer_json("segmentacion_wcss.json")
    }



@app.get("/ml/silueta")
def obtener_silueta():
    return {
        "success": True,
        "data": leer_json("segmentacion_silueta.json")
    }



@app.get("/ml/entrenamiento")
def obtener_entrenamiento():
    return {
        "success": True,
        "data": leer_json("entrenamiento_prueba.json")
    }



@app.get("/ml/segmentacion")
def obtener_segmentacion():
    return {
        "success": True,
        "data": leer_json("segmentacion_final.json")
    }