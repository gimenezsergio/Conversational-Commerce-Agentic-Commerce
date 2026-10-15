import json
from database import get_db

def execute_tool(tool_name, tool_args, session_id):
    """
    Ejecuta la función solicitada por la IA sobre la base de datos SQLite
    y retorna un resultado estructurado que se le devuelve a Gemini.
    """
    conn = get_db()
    cursor = conn.cursor()

    if tool_name == "consultar_catalogo":
        categoria = tool_args.get("categoria")
        termino = tool_args.get("termino")
        
        query = "SELECT id, nombre, categoria, precio, unidad, descripcion FROM productos WHERE 1=1"
        params = []
        if categoria:
            query += " AND categoria LIKE ?"
            params.append(f"%{categoria}%")
        if termino:
            query += " AND (nombre LIKE ? OR descripcion LIKE ?)"
            params.append(f"%{termino}%")
            params.append(f"%{termino}%")
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        productos = [dict(row) for row in rows]
        conn.close()
        return {"total_encontrados": len(productos), "productos": productos[:10]}

    elif tool_name == "agregar_o_modificar_item":
        producto_id = tool_args.get("producto_id")
        cantidad = int(tool_args.get("cantidad", 1))
        notas = tool_args.get("notas", "")

        # Verificar que el producto exista
        cursor.execute("SELECT id, nombre, precio, unidad FROM productos WHERE id = ?", (producto_id,))
        prod = cursor.fetchone()
        if not prod:
            # Buscar por coincidencia parcial si la IA no puso el ID exacto
            cursor.execute("SELECT id, nombre, precio, unidad FROM productos WHERE id LIKE ? OR nombre LIKE ? LIMIT 1", (f"%{producto_id}%", f"%{producto_id}%"))
            prod = cursor.fetchone()

        if not prod:
            conn.close()
            return {"error": f"No se encontró el producto con id o nombre '{producto_id}'"}

        real_id = prod["id"]
        cursor.execute("""
            INSERT INTO carritos (session_id, producto_id, cantidad, notas)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(session_id, producto_id) DO UPDATE SET
            cantidad = excluded.cantidad,
            notas = excluded.notas
        """, (session_id, real_id, cantidad, notas))
        conn.commit()

        # Calcular carrito actual
        cursor.execute("""
            SELECT c.cantidad, c.notas, p.id, p.nombre, p.precio, (c.cantidad * p.precio) as subtotal
            FROM carritos c
            JOIN productos p ON c.producto_id = p.id
            WHERE c.session_id = ?
        """, (session_id,))
        items = [dict(row) for row in cursor.fetchall()]
        total = sum(item["subtotal"] for item in items)
        conn.close()

        return {
            "status": "success",
            "mensaje": f"Se agregó {cantidad} x {prod['nombre']} al carrito.",
            "carrito_items": items,
            "total_acumulado": total
        }

    elif tool_name == "quitar_item":
        producto_id = tool_args.get("producto_id")
        cursor.execute("DELETE FROM carritos WHERE session_id = ? AND producto_id = ?", (session_id, producto_id))
        conn.commit()
        conn.close()
        return {"status": "success", "mensaje": f"Se removió el producto {producto_id} del pedido."}

    elif tool_name == "ver_carrito":
        cursor.execute("""
            SELECT c.cantidad, c.notas, p.id, p.nombre, p.precio, (c.cantidad * p.precio) as subtotal
            FROM carritos c
            JOIN productos p ON c.producto_id = p.id
            WHERE c.session_id = ?
        """, (session_id,))
        items = [dict(row) for row in cursor.fetchall()]
        total = sum(item["subtotal"] for item in items)
        conn.close()
        return {"items": items, "total": total}

    elif tool_name == "confirmar_pedido":
        cursor.execute("""
            SELECT c.cantidad, c.notas, p.id, p.nombre, p.precio, (c.cantidad * p.precio) as subtotal
            FROM carritos c
            JOIN productos p ON c.producto_id = p.id
            WHERE c.session_id = ?
        """, (session_id,))
        items = [dict(row) for row in cursor.fetchall()]
        
        if not items:
            conn.close()
            return {"error": "El carrito está vacío, no se puede confirmar el pedido."}

        total = sum(item["subtotal"] for item in items)
        cliente_nombre = tool_args.get("cliente_nombre")
        telefono = tool_args.get("telefono", "")
        direccion = tool_args.get("direccion", "")
        metodo_pago = tool_args.get("metodo_pago", "")
        tipo_entrega = tool_args.get("tipo_entrega", "Retiro en local")

        cursor.execute("""
            INSERT INTO pedidos (cliente_nombre, telefono, direccion, metodo_pago, tipo_entrega, total, items_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cliente_nombre, telefono, direccion, metodo_pago, tipo_entrega, total, json.dumps(items)))
        
        pedido_id = cursor.lastrowid

        # Vaciar el carrito de la sesión
        cursor.execute("DELETE FROM carritos WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()

        return {
            "status": "success",
            "pedido_id": pedido_id,
            "total": total,
            "cliente_nombre": cliente_nombre,
            "tipo_entrega": tipo_entrega,
            "mensaje": f"Pedido #{pedido_id} confirmado exitosamente en el sistema."
        }

    conn.close()
    return {"error": f"Herramienta '{tool_name}' no reconocida."}
