import json
import urllib.request
import urllib.error

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"

TOOLS_DECLARATION = [
    {
        "name": "consultar_catalogo",
        "description": "Consulta los productos disponibles en la pastelería, opcionalmente filtrados por categoría o término de búsqueda.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "categoria": {
                    "type": "STRING",
                    "description": "Categoría opcional: 'Tortas', 'Tartas', 'Facturas', 'Budines', 'Postres', 'Salados'"
                },
                "termino": {
                    "type": "STRING",
                    "description": "Palabra clave para buscar un producto (ej. 'limon', 'medialunas', 'chocolate', 'miga')"
                }
            }
        }
    },
    {
        "name": "agregar_o_modificar_item",
        "description": "Agrega un producto al carrito del cliente o actualiza su cantidad.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "producto_id": {
                    "type": "STRING",
                    "description": "El ID exacto del producto según el catálogo (ej: 'rogel', 'medialunas-manteca', 'lemon-pie', 'sandwiches-jyq')"
                },
                "cantidad": {
                    "type": "INTEGER",
                    "description": "Cantidad de unidades, packs o docenas deseadas (debe ser mayor a 0)."
                },
                "notas": {
                    "type": "STRING",
                    "description": "Aclaraciones opcionales del cliente (ej: 'con cartel de feliz cumple', 'bien tostadas')"
                }
            },
            "required": ["producto_id", "cantidad"]
        }
    },
    {
        "name": "quitar_item",
        "description": "Elimina un producto del carrito actual.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "producto_id": {
                    "type": "STRING",
                    "description": "El ID exacto del producto a quitar."
                }
            },
            "required": ["producto_id"]
        }
    },
    {
        "name": "ver_carrito",
        "description": "Obtiene los productos que el cliente tiene cargados actualmente en su pedido y el importe total acumulado.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "confirmar_pedido",
        "description": "Cierra el pedido del cliente y lo guarda formalmente en la base de datos de la pastelería. Usar ÚNICAMENTE cuando el cliente haya indicado su nombre, tipo de entrega (retiro o envío), dirección (si es envío), teléfono y método de pago.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "cliente_nombre": {
                    "type": "STRING",
                    "description": "Nombre y apellido del cliente"
                },
                "telefono": {
                    "type": "STRING",
                    "description": "Número de teléfono o WhatsApp"
                },
                "tipo_entrega": {
                    "type": "STRING",
                    "description": "Puede ser 'Retiro en local' o 'Envío a domicilio'"
                },
                "direccion": {
                    "type": "STRING",
                    "description": "Dirección completa si es envío a domicilio (o indicar 'Retiro por sucursal')"
                },
                "metodo_pago": {
                    "type": "STRING",
                    "description": "Efectivo, Transferencia o Mercado Pago"
                }
            },
            "required": ["cliente_nombre", "tipo_entrega", "metodo_pago"]
        }
    }
]

SYSTEM_INSTRUCTION = """Sos DulceBot, el pastelero asesor estrella y anfitrión cordial de la pastelería artesanal 'Dulce Aroma'.
Tu misión NO es solo despachar productos, sino brindar una atención personalizada, asesorar en eventos y encargos especiales, y registrar el pedido en el carrito con todos los detalles de personalización.

PAUTAS ESENCIALES DE INTERACCIÓN Y ASESORAMIENTO:

1. PERSONALIZACIÓN Y MOTIVOS EN TORTAS Y ENCARGOS:
   - Cuando el cliente pida o consulte por una torta (o festejo/cumpleaños), indaga proactivamente con calidez:
     a) **Motivo u ocasión**: ¿Es para un cumpleaños infantil, adulto, aniversario, reunión o antojo del día?
     b) **Si es para niños/homenajeado**: Preguntá sutilmente quién es el agasajado (ej. edad, si es nene, nena, o si tienen alguna temática/personaje favorito como superhéroes, princesas, dinosaurios, fútbol, colores pasteles, etc.).
     c) **Dedicatoria / Cartel**: Ofrecé agregar cartel comestible o velita ("¿Querés que le pongamos un cartelito con el nombre o feliz cumple?").
     d) **Rendimiento / Comensales**: Si no están seguros del tamaño, preguntá cuántas personas van a ser para recomendar si conviene una torta grande, sumar una tarta dulce o una docena de sándwiches de miga.
   - Guarda TODAS estas aclaraciones en el campo `notas` de la función `agregar_o_modificar_item` (ej: "Para cumple de 5 años varón, temática Hombre Araña, cartel 'Feliz Cumple Lucas'").

2. RESTRICCIONES ALIMENTARIAS Y PREFERENCIAS:
   - Si el cliente duda qué llevar, preguntá si prefieren algo bien dulce (dulce de leche, chocolate belga) o algo fresco/cítrico (frutos rojos, limón, manzana).
   - Tené en cuenta consultas sobre nueces o chocolate si lo mencionan.

3. USO DE HERRAMIENTAS (TOOLS):
   - NUNCA inventes productos ni precios fuera del catálogo. Si tenés dudas, ejecutá `consultar_catalogo`.
   - Cuando el cliente defina una torta o producto y sus detalles, invocá `agregar_o_modificar_item` incluyendo las `notas` con la personalización acordada.

4. CONFIRMACIÓN Y CIERRE DEL PEDIDO:
   - Antes de cerrar, hacé un breve repaso cariñoso del pedido (productos, personalización y total).
   - Solicitá amablemente los datos necesarios: Nombre del cliente, si es Retiro en local o Envío a domicilio, dirección completa (si es envío), teléfono de contacto y forma de pago (Efectivo / Transferencia / Mercado Pago).
   - Solo cuando el cliente confirme estos datos, ejecutá `confirmar_pedido`.

5. TONO:
   - Cálido, argentino/rioplatense educado y empático ("¡Qué linda celebración!", "¡Con gusto!", "Te podemos preparar...").
   - Respuestas concisas, bien estructuradas con viñetas cuando listes opciones, fáciles de leer en pantalla.
"""

def call_gemini(api_key, contents):
    """
    Realiza la llamada HTTP a la API de Gemini enviando el historial y las tools.
    Maneja reintentos automáticos y fallback ante saturación temporal (HTTP 503).
    """
    candidate_models = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3-flash-preview"]
    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        },
        "contents": contents,
        "tools": [{"function_declarations": TOOLS_DECLARATION}]
    }

    data = json.dumps(payload).encode("utf-8")
    last_err = None

    import time
    for model_name in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                last_err = e
                # Si es 503 (saturado) o 429 (rate limit temporal), esperamos un momento o probamos el siguiente modelo
                if e.code in (429, 503):
                    time.sleep(1.8 * (attempt + 1))
                    continue
                raise e
            except Exception as e:
                last_err = e
                time.sleep(1)
                continue


    if last_err:
        raise last_err
    raise RuntimeError("No se pudo obtener respuesta de la API de Gemini")

