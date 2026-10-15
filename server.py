import http.server
import socketserver
import json
import os
import urllib.parse
from database import get_db, init_db
from assistant import call_gemini
from tools import execute_tool

PORT = 8000
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Leer API Key de .env si existe
API_KEY = ""
env_file = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_file):
    with open(env_file, "r") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                API_KEY = line.strip().split("=", 1)[1]
            elif line.startswith("PORT="):
                try:
                    PORT = int(line.strip().split("=", 1)[1])
                except:
                    pass

class PasteleriaHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # API: Listar productos del catálogo
        if path == "/api/productos":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM productos ORDER BY categoria, nombre")
            prods = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return self._send_json({"productos": prods})

        # API: Obtener estado del carrito de una sesión
        elif path == "/api/carrito":
            session_id = query.get("session_id", ["default"])[0]
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.cantidad, c.notas, p.id, p.nombre, p.precio, p.unidad, p.imagen, (c.cantidad * p.precio) as subtotal
                FROM carritos c
                JOIN productos p ON c.producto_id = p.id
                WHERE c.session_id = ?
            """, (session_id,))
            items = [dict(r) for r in cursor.fetchall()]
            total = sum(i["subtotal"] for i in items)
            conn.close()
            return self._send_json({"items": items, "total": total})

        # API: Listar pedidos guardados para el pastelero
        elif path == "/api/pedidos":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pedidos ORDER BY id DESC")
            pedidos = []
            for r in cursor.fetchall():
                d = dict(r)
                try:
                    d["items"] = json.loads(d["items_json"])
                except:
                    d["items"] = []
                pedidos.append(d)
            conn.close()
            return self._send_json({"pedidos": pedidos})

        elif path in ("/panel", "/panel/", "/panel.html"):
            panel_file = os.path.join(STATIC_DIR, "panel.html")
            if os.path.exists(panel_file):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(panel_file, "rb") as f:
                    self.wfile.write(f.read())
                return
            return self.send_error(404, "panel.html no encontrado")

        # Servir estáticos
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        data = json.loads(body.decode("utf-8")) if body else {}

        # API: Cambiar estado de un pedido (pendiente, en_preparacion, listo, entregado)
        if path == "/api/pedidos/estado":
            pedido_id = data.get("pedido_id")
            nuevo_estado = data.get("estado", "pendiente")
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (nuevo_estado, pedido_id))
            conn.commit()
            conn.close()
            return self._send_json({"status": "success", "pedido_id": pedido_id, "nuevo_estado": nuevo_estado})


        # API: Agregar manualmente desde la web al carrito
        if path == "/api/carrito/agregar":
            session_id = data.get("session_id", "default")
            producto_id = data.get("producto_id")
            cantidad = int(data.get("cantidad", 1))
            res = execute_tool("agregar_o_modificar_item", {"producto_id": producto_id, "cantidad": cantidad}, session_id)
            return self._send_json(res)

        # API: Eliminar del carrito
        elif path == "/api/carrito/quitar":
            session_id = data.get("session_id", "default")
            producto_id = data.get("producto_id")
            res = execute_tool("quitar_item", {"producto_id": producto_id}, session_id)
            return self._send_json(res)

        # API: Limpiar carrito
        elif path == "/api/carrito/limpiar":
            session_id = data.get("session_id", "default")
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM carritos WHERE session_id = ?", (session_id,))
            conn.commit()
            conn.close()
            return self._send_json({"status": "success"})

        # API: Chat con el Asistente IA (Gemini con Function Calling)
        elif path == "/api/chat":
            session_id = data.get("session_id", "default")
            history = data.get("history", []) # Lista de {role: "user"|"model", parts: [{text: ...}]}
            user_message = data.get("message", "")

            # Mantener los últimos turnos para no sobrecargar el límite de tokens por minuto (TPM / 429)
            trimmed_history = history[-10:] if len(history) > 10 else list(history)
            current_contents = list(trimmed_history)
            if user_message:
                current_contents.append({
                    "role": "user",
                    "parts": [{"text": user_message}]
                })

            try:
                executed_tools = []
                final_text = ""
                loop_limit = 5

                while loop_limit > 0:
                    loop_limit -= 1
                    resp = call_gemini(API_KEY, current_contents)
                    candidate = resp.get("candidates", [{}])[0]
                    content = candidate.get("content", {})
                    parts = content.get("parts", [])

                    function_calls = [p["functionCall"] for p in parts if "functionCall" in p]
                    text_parts = [p.get("text", "") for p in parts if "text" in p]
                    
                    if text_parts:
                        final_text += "".join(text_parts)

                    if not function_calls:
                        break

                    # Guardar respuesta del modelo con la invocación de función
                    current_contents.append({
                        "role": "model",
                        "parts": parts
                    })

                    function_response_parts = []
                    for fc in function_calls:
                        name = fc["name"]
                        args = fc.get("args", {})
                        tool_result = execute_tool(name, args, session_id)
                        executed_tools.append({"name": name, "args": args, "result": tool_result})

                        function_response_parts.append({
                            "functionResponse": {
                                "name": name,
                                "response": {"name": name, "content": tool_result}
                            }
                        })

                    # Devolver los resultados a Gemini
                    current_contents.append({
                        "role": "user",
                        "parts": function_response_parts
                    })


                # Obtener el estado actualizado del carrito para el frontend
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.cantidad, c.notas, p.id, p.nombre, p.precio, p.unidad, (c.cantidad * p.precio) as subtotal
                    FROM carritos c
                    JOIN productos p ON c.producto_id = p.id
                    WHERE c.session_id = ?
                """, (session_id,))
                cart_items = [dict(r) for r in cursor.fetchall()]
                cart_total = sum(i["subtotal"] for i in cart_items)
                conn.close()

                return self._send_json({
                    "response": final_text,
                    "executed_tools": executed_tools,
                    "cart": {
                        "items": cart_items,
                        "total": cart_total
                    }
                })

            except Exception as e:
                import traceback
                traceback.print_exc()
                return self._send_json({
                    "error": str(e),
                    "response": "Disculpame, hubo un error de conexión al procesar tu solicitud. Por favor volvé a intentar."
                }, status=500)

        self.send_error(404, "Ruta no encontrada")

def run():
    init_db()
    with socketserver.TCPServer(("", PORT), PasteleriaHandler) as httpd:
        print(f"=====================================================")
        print(f" Pastelería 'Dulce Aroma' Servidor Activo")
        print(f" Dirección: http://localhost:{PORT}")
        print(f" Base de Datos: SQLite (pasteleria.db)")
        print(f" Asistente IA: Gemini 2.5 Flash conectado con Tools")
        print(f"=====================================================")
        httpd.serve_forever()

if __name__ == "__main__":
    run()
