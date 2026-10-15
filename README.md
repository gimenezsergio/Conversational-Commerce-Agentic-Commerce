# Conversational Commerce & Agentic Commerce (Pastelería Dulce Aroma)

MVP funcional de una aplicación de **comercio conversacional agéntico**.
Permite a los clientes navegar un catálogo de pastelería, consultar dudas y encargar pedidos completos interactuando con un asistente de Inteligencia Artificial (**Gemini**) que ejecuta acciones en tiempo real sobre la base de datos (**SQLite**) mediante **Function Calling**.

---

## 🚀 Características Principales

1. **E-commerce & Catálogo**:
   - Más de 25 productos artesanales organizados en 6 categorías (Tortas, Tartas, Facturas, Budines, Postres y Salados de miga).
   - Buscador en tiempo real y filtros con scroll táctil responsive.
   - Drawer lateral deslizable con el carrito en vivo.

2. **Asistente IA Agéntico (DulceBot)**:
   - Chatbot flotante ("Pedir con IA") conectado a la API de **Gemini** con soporte de herramientas (*Tools*).
   - **Asesoramiento y personalización**: indaga motivo del festejo, homenajeado, temáticas infantiles, carteles y cálculo de comensales.
   - **Acciones directas**: agrega o modifica productos en el carrito y registra el pedido sin que el usuario llene formularios manualmente.
   - Salida formateada con **Markdown** (listas, negritas y enlaces limpios).

3. **Panel de Pedidos & Cocina (`/panel`)**:
   - Vista para el pastelero con métricas de facturación y pedidos en tiempo real.
   - Desglose de cada comanda con notas de personalización acordadas en el chat.
   - Selector en vivo para cambiar el estado del pedido (`Pendiente`, `En preparación`, `Listo`, `Entregado`).

4. **Persistencia & Backend**:
   - Backend ligero en **Python** (sin dependencias externas complejas).
   - Base de datos local **SQLite** (`pasteleria.db`).

---

## 🛠️ Requisitos e Instalación

- **Python 3.10+**

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/gimenezsergio/Conversational-Commerce-Agentic-Commerce.git
   cd Conversational-Commerce-Agentic-Commerce
   ```

2. Configurar la clave de API de Gemini:
   Crea un archivo `.env` en la raíz del proyecto:
   ```env
   GEMINI_API_KEY=tu_gemini_api_key_aqui
   PORT=8000
   ```

3. Iniciar el servidor:
   ```bash
   python3 server.py
   ```

4. Abrir en el navegador:
   - **Tienda y Chat IA**: [http://localhost:8000](http://localhost:8000)
   - **Panel Pastelero**: [http://localhost:8000/panel](http://localhost:8000/panel)

---

## 📁 Estructura del Proyecto

```text
├── assistant.py       # Configuración de Gemini, Function Calling y System Prompt
├── database.py        # Esquemas SQLite y precarga de productos del catálogo
├── server.py          # Servidor HTTP nativo y endpoints REST (/api/chat, /api/pedidos, etc.)
├── tools.py           # Ejecución de herramientas de la IA sobre la base de datos
├── static/
│   ├── index.html     # Tienda online con widget flotante de chat
│   ├── panel.html     # Panel de comandas y estado de pedidos en vivo
│   ├── styles.css     # Estilos modernos y responsive (mobile-first)
│   └── app.js         # Lógica frontend, sincronización de carrito y chat
├── .gitignore
└── README.md
```
