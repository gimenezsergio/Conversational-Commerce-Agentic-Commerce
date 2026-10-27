import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "pasteleria.db")

INITIAL_PRODUCTS = [
    # Tortas Grandes
    ("rogel", "Torta Rogel Tradicional", "Tortas", 18500, "Unidad", "Capas crocantes de masa fina con abundante dulce de leche repostero y merengue italiano tostado.", "https://images.unsplash.com/photo-1571115177098-24ec42ed204d?w=500&auto=format&fit=crop&q=60"),
    ("chocotorta", "Chocotorta Clásica", "Tortas", 16000, "Unidad", "Clásica receta argentina con galletitas de chocolate humedecidas en café y crema de dulce de leche con queso crema.", "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500&auto=format&fit=crop&q=60"),
    ("balcarce", "Postre Balcarce Artesanal", "Tortas", 17500, "Unidad", "Bizcochuelo suave con capas de merengue seco, dulce de leche, crema chantilly y castañas.", "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=500&auto=format&fit=crop&q=60"),
    ("selva-negra", "Torta Selva Negra", "Tortas", 19500, "Unidad", "Bizcochuelo de cacao amargo con cerezas al kirsch, crema chantilly y rulos de chocolate belga.", "https://images.unsplash.com/photo-1606890737304-57a1ca8a5b62?w=500&auto=format&fit=crop&q=60"),
    ("marquise", "Marquise de Chocolate y DDL", "Tortas", 20000, "Unidad", "Base húmeda de chocolate puro sin harina, colchón de dulce de leche, crema chantilly y frutos rojos frescos.", "https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?w=500&auto=format&fit=crop&q=60"),

    # Tartas Dulces
    ("lemon-pie", "Lemon Pie con Merengue Suizo", "Tartas", 15000, "Unidad", "Masa sableé crocante, crema de limón cítrica equilibrada y copas de merengue suizo dorado.", "https://images.unsplash.com/photo-1519869325930-281384150729?w=500&auto=format&fit=crop&q=60"),
    ("cheesecake", "Cheesecake de Frutos Rojos", "Tartas", 19000, "Unidad", "Estilo New York horneado con base crocante de galletitas y coulis casero de frambuesas y moras.", "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=500&auto=format&fit=crop&q=60"),
    ("tarta-ricota", "Tarta de Ricota Tradicional", "Tartas", 14000, "Unidad", "Relleno cremoso de ricota fresca aromatizada con ralladura de naranja y vainilla, espolvoreada con azúcar impalpable.", "https://images.unsplash.com/photo-1587314168485-3236d6710814?w=500&auto=format&fit=crop&q=60"),
    ("tarta-cabsha", "Tarta Cabsha (Toffee & Chocolate)", "Tartas", 16500, "Unidad", "Masa crujiente, base generosa de dulce de leche y baño superior de ganache de chocolate semiamargo.", "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?w=500&auto=format&fit=crop&q=60"),
    ("tarta-manzana", "Tarta de Manzana y Canela", "Tartas", 14500, "Unidad", "Finas láminas de manzanas verdes caramelizadas al horno con canela sobre crema pastelera suave.", "https://images.unsplash.com/photo-1568571780765-9276ac8b75a2?w=500&auto=format&fit=crop&q=60"),
    ("tarta-frutilla", "Tarta de Frutillas con Pastelera", "Tartas", 16000, "Unidad", "Base de masa dulce, abundante crema pastelera a la vainilla y frutillas frescas fileteadas con brillo.", "https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?w=500&auto=format&fit=crop&q=60"),

    # Facturas y Masas
    ("medialunas-manteca", "Medialunas de Manteca (Docena)", "Facturas", 7200, "Docena", "Clásicas medialunas hojaldradas de manteca con almíbar artesanal.", "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=500&auto=format&fit=crop&q=60"),
    ("medialunas-grasa", "Medialunas de Grasa (Docena)", "Facturas", 6500, "Docena", "Bien crocantes y saladas, ideales para el mate.", "https://images.unsplash.com/photo-1530610476181-d83430b64dcd?w=500&auto=format&fit=crop&q=60"),
    ("canon-dulce-leche", "Cañoncitos de DDL (Docena)", "Facturas", 7800, "Docena", "Hojaldre crocante relleno con dulce de leche repostero y azúcar impalpable.", "https://images.unsplash.com/photo-1587241321921-91a834d6d191?w=500&auto=format&fit=crop&q=60"),
    ("facturas-surtidas", "Facturas Surtidas (Docena)", "Facturas", 7200, "Docena", "Variedad de vigilantes, medialunas, con crema pastelera, dulce de membrillo y dulce de leche.", "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&auto=format&fit=crop&q=60"),
    ("medialunas-jyq", "Medialunas JYQ Calientes (Media docena)", "Facturas", 5800, "Media docena", "Medialunas de manteca rellenas con jamón cocido seleccionado y queso dambo gratinado.", "https://images.unsplash.com/photo-1549931319-a545dcf3bc73?w=500&auto=format&fit=crop&q=60"),

    # Budines y Porciones
    ("budin-limon", "Budín de Limón y Amapolas", "Budines", 6500, "Unidad", "Húmedo, cítrico, con semillas de amapola y glaseado crujiente de limón natural.", "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=500&auto=format&fit=crop&q=60"),
    ("budin-marmolado", "Budín Marmolado Vainilla y Cacao", "Budines", 6200, "Unidad", "Combinación perfecta de vainilla bourbon y chocolate amargo con baño de chocolate con leche.", "https://images.unsplash.com/photo-1562440499-64c9a111f713?w=500&auto=format&fit=crop&q=60"),
    ("budin-carrot", "Budín Carrot Cake con Nueces", "Budines", 7000, "Unidad", "Budín especiado con zanahorias ralladas, canela, nueces picadas y frosting de queso crema.", "https://images.unsplash.com/photo-1621303837174-89787a7d4729?w=500&auto=format&fit=crop&q=60"),
    ("brownie-nuez", "Brownie Húmedo con Nueces (x2 porciones)", "Budines", 4800, "Pack", "Cuadrados densos de chocolate semiamargo con crocantes trozos de nueces.", "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=500&auto=format&fit=crop&q=60"),

    # Postres y Alfajores
    ("tiramisu", "Tiramisú en Vaso Individual", "Postres", 4500, "Unidad", "Vainillas embebidas en café espresso y licor café, crema de mascarpone y cacao holandés.", "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500&auto=format&fit=crop&q=60"),
    ("alfajores-maicena", "Alfajores de Maicena (Caja x6)", "Postres", 5500, "Caja", "Tapas suaves que se deshacen en la boca, mucho dulce de leche y coco rallado.", "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=500&auto=format&fit=crop&q=60"),
    ("alfajores-chocolate", "Alfajores de Chocolate y DDL (Caja x6)", "Postres", 6200, "Caja", "Masa de cacao rellena de dulce de leche con cobertura crocante de chocolate semiamargo 70%.", "https://images.unsplash.com/photo-1548848221-0c2e497ed557?w=500&auto=format&fit=crop&q=60"),
    ("macarons", "Macarons Franceses Surtidos (Caja x6)", "Postres", 7500, "Caja", "Sabores surtidos: pistacho, frutos rojos, chocolate, maracuyá, vainilla y caramelo salado.", "https://images.unsplash.com/photo-1569864358642-9d1684040f43?w=500&auto=format&fit=crop&q=60"),

    # Especiales y Salados
    ("sandwiches-jyq", "Sándwiches de Miga J&Q (Docena)", "Salados", 9200, "Docena", "Pan de miga extra tierno, jamón cocido seleccionado y queso tybo con manteca.", "https://images.unsplash.com/photo-1509722747041-616f39b57569?w=500&auto=format&fit=crop&q=60"),
    ("sandwiches-especiales", "Sándwiches de Miga Especiales (Docena)", "Salados", 10800, "Docena", "Surtido especial: jamón y choclo, roquefort con nuez, jamón crudo y queso, y atún.", "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=500&auto=format&fit=crop&q=60")
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabla de productos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        categoria TEXT NOT NULL,
        precio REAL NOT NULL,
        unidad TEXT NOT NULL,
        descripcion TEXT,
        imagen TEXT
    )
    """)
    
    # Tabla de carritos de sesión (para persistir lo que la IA agrega)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS carritos (
        session_id TEXT NOT NULL,
        producto_id TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        notas TEXT,
        PRIMARY KEY (session_id, producto_id),
        FOREIGN KEY (producto_id) REFERENCES productos (id)
    )
    """)

    # Tabla de pedidos confirmados
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cliente_nombre TEXT NOT NULL,
        telefono TEXT,
        direccion TEXT,
        metodo_pago TEXT,
        tipo_entrega TEXT,
        total REAL NOT NULL,
        items_json TEXT NOT NULL,
        estado TEXT DEFAULT 'pendiente'
    )
    """)

    # Sincronizar catálogo asegurando que los productos tengan sus fotos y nombres exactos
    for prod in INITIAL_PRODUCTS:
        cursor.execute("""
        INSERT INTO productos (id, nombre, categoria, precio, unidad, descripcion, imagen)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            nombre = excluded.nombre,
            categoria = excluded.categoria,
            precio = excluded.precio,
            unidad = excluded.unidad,
            descripcion = excluded.descripcion,
            imagen = excluded.imagen
        """, prod)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de datos SQLite inicializada exitosamente en:", DB_PATH)
