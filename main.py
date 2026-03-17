from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import os

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'inventoryapp-ut-4d27.g.aivencloud.com',
    'port': 18827,
    'user': 'avnadmin',
    'password': os.environ.get('DB_PASSWORD'),
    'database': 'inventario_db',
    'cursorclass': pymysql.cursors.DictCursor,
    'connect_timeout': 10  # Tiempo de espera para evitar bloqueos
}

def get_db_connection():
    # Establece la conexión con autocommit para asegurar que los cambios se guarden
    return pymysql.connect(**DB_CONFIG, autocommit=True)

@app.route('/productos', methods=['GET'])
def get_productos():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM productos ORDER BY fecha_actualizacion DESC")
            productos = cursor.fetchall()
        return jsonify(productos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/actualizar', methods=['POST'])
def actualizar():
    data = request.json
    barcode = data.get('barcode')
    operacion = data.get('operacion') # 'sumar', 'restar', 'crear', 'consultar'
    nombre = data.get('nombre', 'Nuevo Producto')
    precio = data.get('precio', 0.0)

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. Buscar si el producto existe
            cursor.execute("SELECT * FROM productos WHERE codigo_barras = %s", (barcode,))
            producto = cursor.fetchone()

            # Lógica para DAR DE ALTA
            if operacion == 'crear':
                if producto:
                    return jsonify({"mensaje": "El producto ya existe", "success": False})
                cursor.execute(
                    "INSERT INTO productos (codigo_barras, nombre, cantidad, precio) VALUES (%s, %s, %s, %s)",
                    (barcode, nombre, 1, precio)
                )
                mensaje = f"Producto '{nombre}' registrado con éxito."
                return jsonify({"mensaje": mensaje, "success": True})

            # Lógica para SUMAR / RESTAR
            if producto:
                if operacion == 'sumar':
                    nueva_qty = producto['cantidad'] + 1
                elif operacion == 'restar':
                    nueva_qty = max(0, producto['cantidad'] - 1)
                else:
                    # Si solo es consultar, devolvemos el nombre para el menú de Flutter
                    return jsonify({"mensaje": producto['nombre'], "success": True, "not_found": False})

                cursor.execute("UPDATE productos SET cantidad = %s WHERE id = %s", (nueva_qty, producto['id']))
                mensaje = f"{producto['nombre']} actualizado a {nueva_qty} unidades."
                return jsonify({"mensaje": mensaje, "success": True})
            
            else:
                # Si no existe y no es una orden de creación
                return jsonify({"mensaje": "Producto no encontrado", "success": False, "not_found": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# Ruta de diagnóstico para Vercel
@app.route('/')
def health_check():
    return jsonify({"status": "online", "database": "connected" if DB_CONFIG['password'] else "missing_password"})

if __name__ == '__main__':
    app.run(debug=True)