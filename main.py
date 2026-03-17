from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import os

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'host': 'inventoryapp-ut-4d27.g.aivencloud.com',
    'port': 18827,
    'user': 'avnadmin',
    'password': os.environ.get('DB_PASSWORD'),
    'database': 'inventario_db',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

@app.route('/productos', methods=['GET'])
def get_productos():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM productos ORDER BY fecha_actualizacion DESC")
        productos = cursor.fetchall()
    conn.close()
    return jsonify(productos)

@app.route('/actualizar', methods=['POST'])
def actualizar():
    data = request.json
    barcode = data.get('barcode')
    operacion = data.get('operacion') # 'sumar', 'restar', 'crear'
    nombre = data.get('nombre', 'Nuevo Producto')
    precio = data.get('precio', 0.0)

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM productos WHERE codigo_barras = %s", (barcode,))
        producto = cursor.fetchone()

        if operacion == 'crear':
            if producto:
                return jsonify({"mensaje": "El producto ya existe", "success": False})
            cursor.execute("INSERT INTO productos (codigo_barras, nombre, cantidad, precio) VALUES (%s, %s, %s, %s)",
                           (barcode, nombre, 1, precio))
            mensaje = f"Producto {nombre} registrado con éxito."
        
        elif producto:
            nueva_qty = producto['cantidad'] + 1 if operacion == 'sumar' else max(0, producto['cantidad'] - 1)
            cursor.execute("UPDATE productos SET cantidad = %s WHERE id = %s", (nueva_qty, producto['id']))
            mensaje = f"{producto['nombre']} actualizado a {nueva_qty} unidades."
        else:
            return jsonify({"mensaje": "Producto no encontrado", "success": False, "not_found": True})

        conn.commit()
    conn.close()
    return jsonify({"mensaje": mensaje, "success": True})

if __name__ == '__main__':
    app.run(debug=True)