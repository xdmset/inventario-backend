from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import os

app = Flask(__name__)
CORS(app)

# Configuración de conexión (Reemplaza con tus credenciales de la nube)
# Sugerencia: Usa variables de entorno en Vercel para esto
DB_CONFIG = {
    'host': 'tu_host_en_la_nube.com',
    'user': 'tu_usuario',
    'password': 'tu_password',
    'database': 'inventario_db',
    'port': 3306,
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

@app.route('/')
def home():
    return jsonify({"status": "API de Inventario Online", "message": "Conexión exitosa"})

@app.route('/productos', methods=['GET'])
def get_productos():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM productos")
            productos = cursor.fetchall()
        conn.close()
        return jsonify(productos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/escanear', methods=['POST'])
def escanear():
    data = request.json
    barcode = data.get('barcode')
    
    if not barcode:
        return jsonify({"mensaje": "Código de barras no proporcionado", "success": False}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. Buscar producto
            cursor.execute("SELECT * FROM productos WHERE codigo_barras = %s", (barcode,))
            producto = cursor.fetchone()
            
            if producto:
                if producto['cantidad'] > 0:
                    nueva_qty = producto['cantidad'] - 1
                    cursor.execute("UPDATE productos SET cantidad = %s WHERE id = %s", (nueva_qty, producto['id']))
                    conn.commit()
                    mensaje = f"Éxito: Se descontó 1 unidad de {producto['nombre']}. Quedan: {nueva_qty}"
                    success = True
                else:
                    mensaje = f"Agotado: {producto['nombre']} no tiene stock disponible."
                    success = False
            else:
                mensaje = f"No encontrado: El código {barcode} no existe en la base de datos."
                success = False
                
        conn.close()
        return jsonify({"mensaje": mensaje, "success": success})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Necesario para que Vercel reconozca la app
app.debug = True