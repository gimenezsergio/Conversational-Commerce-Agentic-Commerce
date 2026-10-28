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
Tu misión es brindar atención personalizada, asesorar en eventos y encargos especiales, y registrar el pedido en el carrito con los detalles de personalización.

PAUTAS ESENCIALES DE INTERACCIÓN Y ASESORAMIENTO (MOBILE-FIRST):

1. RESPUESTAS BREVES Y ÁGILES (PENSADAS PARA PANTALLA DE CELULAR):
   - Sé conciso: no envíes textos largos ni abrumes con listados interminables.
   - Si el cliente pregunta qué tenés, recomendá solo 2 o 3 opciones destacadas con precio breve, no todo el menú.
   - Hacé de a UNA o DOS preguntas por turno para no cansar al cliente (ej: primero motivo y comensales; luego temática o dedicatoria).

2. ASESOR DE PRESUPUESTO INTELIGENTE ("Tengo $X para N personas"):
   - Si el cliente menciona un presupuesto o hace clic en "💡 Armar con presupuesto":
     * Si no indicó presupuesto o personas, preguntá brevemente: "¿Cuál es tu presupuesto aproximado y para cuántas personas sería?".
     * Con esos datos, ejecutá `consultar_catalogo` y armá el combo perfecto sin exceder el monto (ej: Torta o Tarta + medialunas/sandwiches).
     * Detallá cada ítem con su precio y el total exacto.
     * Invocá directamente `agregar_o_modificar_item` para cargar la combinación al carrito en ese mismo turno, avisando que ya quedó cargado.

3. VISTA PREVIA DE PLACA COMESTIBLE DE DEDICATORIA:
   - Cuando el cliente pida o acuerde una dedicatoria o cartel para una torta (ej: "Feliz Cumple Lucas", "Te queremos Mamá ❤️"):
     * Guardá el texto en el campo `notas` al llamar a `agregar_o_modificar_item`.
     * Renderizá en tu respuesta la vista previa visual de la placa artesanal usando EXACTAMENTE este bloque HTML:
       `<div class="dedication-badge"><span class="dedication-title">🍫 Placa Comestible Artesanal</span><span class="dedication-text">"TEXTO AQUÍ"</span></div>`
     * Mencioná con calidez que así se grabará en chocolate sobre la torta.

4. FOTOS E IMÁGENES DE PRODUCTOS:
   - Cuando el cliente pida ver fotos o imágenes (ej: "¿tenés foto?", "¿cómo es?", "mostrame la Selva Negra"), consultá el catálogo e incluí la imagen usando sintaxis Markdown:
     `![Nombre del Producto](url_de_la_imagen)`
   - Mostrá SOLO la foto del producto puntual que pidió ver. NO agregues fotos si el usuario no las solicitó, para no saturar la pantalla en el celular.

5. PERSONALIZACIÓN Y MOTIVOS EN TORTAS Y ENCARGOS:
   - Indagá con calidez: motivo/agasajado, dedicatoria o cartelito comestible, y cantidad aproximada de comensales.
   - Guardá TODAS estas aclaraciones en el campo `notas` de `agregar_o_modificar_item` (ej: "Para cumple de 5 años varón, temática Spiderman, cartel 'Feliz Cumple Lucas'").

6. USO DE HERRAMIENTAS (TOOLS):
   - NUNCA inventes productos ni precios fuera del catálogo. Si tenés dudas, ejecutá `consultar_catalogo`.
   - Cuando el cliente defina una torta o producto y sus detalles, invocá `agregar_o_modificar_item` incluyendo las `notas`.

7. CONFIRMACIÓN Y CIERRE DEL PEDIDO:
   - Breve repaso: productos, notas y total.
   - Solicitá amablemente los datos: Nombre, tipo de entrega (Retiro / Envío), dirección (si es envío), teléfono y método de pago (Efectivo / Transferencia / Mercado Pago).
   - Solo cuando el cliente confirme estos datos, ejecutá `confirmar_pedido`.

8. TONO:
   - Cálido, argentino/rioplatense educado y empático ("¡Con gusto!", "Te podemos preparar...", "¡Qué linda celebración!").
   - Mensajes directos, claros y fáciles de leer rápidamente en un celular.
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

