// Estado local de la aplicación
const AppState = {
  sessionId: localStorage.getItem("dulce_session_id") || "sess_" + Math.random().toString(36).substring(2, 9),
  products: [],
  cart: { items: [], total: 0 },
  chatHistory: [],
  activeCategory: "todos"
};

localStorage.setItem("dulce_session_id", AppState.sessionId);

// Elementos del DOM
const productsGrid = document.getElementById("productsGrid");
const searchInput = document.getElementById("searchInput");
const categoryChips = document.querySelectorAll(".chip-filter");
const catalogTitle = document.getElementById("catalogTitle");

// Carrito
const btnOpenCart = document.getElementById("btnOpenCart");
const btnCloseCart = document.getElementById("btnCloseCart");
const cartDrawer = document.getElementById("cartDrawer");
const drawerOverlay = document.getElementById("drawerOverlay");
const cartItemsList = document.getElementById("cartItemsList");
const cartDrawerTotal = document.getElementById("cartDrawerTotal");
const cartCountBadge = document.getElementById("cartCountBadge");
const btnAssistCart = document.getElementById("btnAssistCart");

// Chat
const btnChatToggle = document.getElementById("btnChatToggle");
const chatWindow = document.getElementById("chatWindow");
const btnCloseChat = document.getElementById("btnCloseChat");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatMessages = document.getElementById("chatMessages");
const chatCartPill = document.getElementById("chatCartPill");
const chatCartCount = document.getElementById("chatCartCount");
const chatCartTotal = document.getElementById("chatCartTotal");
const quickSuggestions = document.querySelectorAll(".suggestion-chip");

// Panel Admin
const btnOpenOrdersAdmin = document.getElementById("btnOpenOrdersAdmin");
const btnCloseAdmin = document.getElementById("btnCloseAdmin");
const adminModal = document.getElementById("adminModal");
const adminOrdersList = document.getElementById("adminOrdersList");

// Formateador de moneda argentina
const formatCurrency = (val) => "$" + Number(val).toLocaleString("es-AR");

// 1. CARGA INICIAL
async function initApp() {
  await fetchProducts();
  await refreshCart();
  setupEventListeners();
}

// 2. PETICIONES AL BACKEND
async function fetchProducts() {
  try {
    const res = await fetch("/api/productos");
    const data = await res.json();
    AppState.products = data.productos || [];
    renderProducts();
  } catch (err) {
    console.error("Error al cargar productos:", err);
    productsGrid.innerHTML = `<div class="error-state">No se pudieron cargar los productos.</div>`;
  }
}

async function refreshCart() {
  try {
    const res = await fetch(`/api/carrito?session_id=${AppState.sessionId}`);
    const data = await res.json();
    AppState.cart = data;
    renderCart();
  } catch (err) {
    console.error("Error al refrescar carrito:", err);
  }
}

async function addToCart(productId, quantity = 1) {
  try {
    const res = await fetch("/api/carrito/agregar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: jsonStringifySafe({
        session_id: AppState.sessionId,
        producto_id: productId,
        cantidad: quantity
      })
    });
    await refreshCart();
  } catch (err) {
    console.error("Error al agregar al carrito:", err);
  }
}

async function removeFromCart(productId) {
  try {
    await fetch("/api/carrito/quitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: jsonStringifySafe({
        session_id: AppState.sessionId,
        producto_id: productId
      })
    });
    await refreshCart();
  } catch (err) {
    console.error("Error al quitar del carrito:", err);
  }
}

// 3. RENDERIZADO DEL CATÁLOGO
function renderProducts() {
  const searchTerm = searchInput.value.toLowerCase().trim();
  const filtered = AppState.products.filter(p => {
    const matchCat = AppState.activeCategory === "todos" || p.categoria.toLowerCase() === AppState.activeCategory.toLowerCase();
    const matchSearch = p.nombre.toLowerCase().includes(searchTerm) || p.descripcion.toLowerCase().includes(searchTerm);
    return matchCat && matchSearch;
  });

  if (filtered.length === 0) {
    productsGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #888;">No encontramos delicias con ese criterio. ¡Consultá a DulceBot en el chat!</div>`;
    return;
  }

  productsGrid.innerHTML = filtered.map(p => `
    <article class="product-card">
      <div class="card-image-wrap">
        <img src="${p.imagen}" alt="${p.nombre}" loading="lazy">
        <span class="card-badge">${p.categoria}</span>
      </div>
      <div class="card-body">
        <h4 class="card-title">${p.nombre}</h4>
        <p class="card-desc">${p.descripcion}</p>
        <div class="card-footer">
          <div>
            <span class="card-price">${formatCurrency(p.precio)}</span>
            <span class="card-unit">/ ${p.unidad}</span>
          </div>
          <button class="btn-add" data-id="${p.id}">+ Agregar</button>
        </div>
      </div>
    </article>
  `).join("");

  // Conectar botones "+ Agregar"
  document.querySelectorAll(".btn-add").forEach(btn => {
    btn.addEventListener("click", () => {
      const pid = btn.dataset.id;
      addToCart(pid, 1);
      btn.innerText = "¡Agregado! ✓";
      btn.style.background = "#2a9d8f";
      btn.style.color = "white";
      setTimeout(() => {
        btn.innerText = "+ Agregar";
        btn.style.background = "";
        btn.style.color = "";
      }, 1000);
    });
  });
}

// 4. RENDERIZADO DEL CARRITO
function renderCart() {
  const items = AppState.cart.items || [];
  const total = AppState.cart.total || 0;
  const count = items.reduce((acc, curr) => acc + curr.cantidad, 0);

  // Actualizar badges e importes
  cartCountBadge.innerText = count;
  cartDrawerTotal.innerText = formatCurrency(total);

  // Actualizar píldora dentro del chat
  if (count > 0) {
    chatCartPill.classList.remove("hidden");
    chatCartCount.innerText = count;
    chatCartTotal.innerText = formatCurrency(total);
  } else {
    chatCartPill.classList.add("hidden");
  }

  if (items.length === 0) {
    cartItemsList.innerHTML = `
      <div style="text-align: center; padding: 40px 10px; color: #888;">
        <span style="font-size: 2.5rem; display: block; margin-bottom: 10px;">🧺</span>
        Tu pedido está vacío.<br>Elegí una torta o pedile a DulceBot que te arme una opción rica.
      </div>
    `;
    return;
  }

  cartItemsList.innerHTML = items.map(item => `
    <div class="cart-item-card">
      <img src="${item.imagen || 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=100'}" class="cart-item-img" alt="${item.nombre}">
      <div class="cart-item-info">
        <h5 class="cart-item-name">${item.nombre}</h5>
        <div style="font-size: 0.8rem; color: #666;">Cantidad: <strong>${item.cantidad}</strong></div>
        ${item.notas ? `<div style="font-size: 0.78rem; color: #b45309; background: #fef3c7; padding: 2px 6px; border-radius: 4px; margin: 3px 0;">🎨 <em>${item.notas}</em></div>` : ''}
        <div class="cart-item-price">${formatCurrency(item.subtotal)}</div>
      </div>
      <button class="btn-remove-item" data-id="${item.id}" title="Quitar item">Eliminar</button>
    </div>
  `).join("");

  document.querySelectorAll(".btn-remove-item").forEach(btn => {
    btn.addEventListener("click", () => {
      removeFromCart(btn.dataset.id);
    });
  });
}

// 5. CHAT CON GEMINI Y FUNCTION CALLING
async function sendChatMessage(userText) {
  if (!userText.trim()) return;

  // Renderizar mensaje del usuario
  appendMessage(userText, "user-message");
  chatInput.value = "";
  chatInput.disabled = true;

  // Placeholder 'Pensando...'
  const loadingId = appendMessage("Pensando y consultando las delicias...", "bot-message", true);

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: jsonStringifySafe({
        session_id: AppState.sessionId,
        message: userText,
        history: AppState.chatHistory
      })
    });

    const data = await res.json();
    removeMessage(loadingId);

    if (data.response) {
      // Guardar en historial conversacional
      AppState.chatHistory.push(
        { role: "user", parts: [{ text: userText }] },
        { role: "model", parts: [{ text: data.response }] }
      );

      // Mostrar indicadores visuales si la IA ejecutó tools
      let extraHtml = "";
      if (data.executed_tools && data.executed_tools.length > 0) {
        data.executed_tools.forEach(t => {
          if (t.name === "agregar_o_modificar_item") {
            extraHtml += `<div class="tool-indicator">✨ <strong>Carrito actualizado:</strong> ${t.result.mensaje || 'Producto agregado'}</div>`;
          } else if (t.name === "confirmar_pedido") {
            extraHtml += `<div class="tool-indicator" style="border-left-color: #2a9d8f;">🎉 <strong>¡Pedido #${t.result.pedido_id} Confirmado!</strong> Total: ${formatCurrency(t.result.total)}</div>`;
          }
        });
      }

      appendMessage(data.response + extraHtml, "bot-message");

      // Actualizar estado del carrito en la interfaz
      if (data.cart) {
        AppState.cart = data.cart;
        renderCart();
      }
    } else {
      appendMessage("Hubo una demora al responder. Probá nuevamente.", "bot-message");
    }
  } catch (err) {
    console.error("Error en chat:", err);
    removeMessage(loadingId);
    appendMessage("Error de conexión con el asistente. Revisá el servidor.", "bot-message");
  } finally {
    chatInput.disabled = false;
    chatInput.focus();
  }
}

function renderMarkdownSafe(content) {
  if (typeof marked !== "undefined" && typeof DOMPurify !== "undefined") {
    // Configurar marked para saltos de línea suaves
    marked.setOptions({ breaks: true, gfm: true });
    const rawHtml = marked.parse(content);
    return DOMPurify.sanitize(rawHtml);
  }
  // Fallback simple si no cargó el CDN
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
}

function appendMessage(rawContent, className, isLoading = false, isRawHtml = false) {
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${className}`;
  if (isLoading) msgDiv.id = "loading_" + Date.now();
  
  if (isRawHtml || isLoading || className === "user-message") {
    // Si es mensaje de usuario o loading, texto seguro escapado
    if (className === "user-message") {
      msgDiv.textContent = rawContent;
    } else {
      msgDiv.innerHTML = rawContent;
    }
  } else {
    // Mensaje de la IA formateado con Markdown limpio
    msgDiv.innerHTML = renderMarkdownSafe(rawContent);
  }

  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return msgDiv.id;
}

function removeMessage(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// 6. PANEL ADMIN DE PEDIDOS
async function openAdminPanel() {
  try {
    const res = await fetch("/api/pedidos");
    const data = await res.json();
    const pedidos = data.pedidos || [];

    if (pedidos.length === 0) {
      adminOrdersList.innerHTML = `<div style="text-align: center; padding: 20px; color: #777;">No hay pedidos registrados todavía en la base de datos SQLite.</div>`;
    } else {
      adminOrdersList.innerHTML = `
        <table class="orders-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Fecha</th>
              <th>Cliente</th>
              <th>Entrega / Dirección</th>
              <th>Productos Encargados</th>
              <th>Pago</th>
              <th>Total</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            ${pedidos.map(p => `
              <tr>
                <td><strong>#${p.id}</strong></td>
                <td><small>${new Date(p.fecha).toLocaleDateString("es-AR")} ${new Date(p.fecha).toLocaleTimeString("es-AR", {hour: '2-digit', minute:'2-digit'})}</small></td>
                <td><strong>${p.cliente_nombre}</strong><br><small>Tel: ${p.telefono || '-'}</small></td>
                <td>${p.tipo_entrega}<br><small>${p.direccion || ''}</small></td>
                <td>
                  <ul style="padding-left: 16px; margin: 0; font-size: 0.82rem;">
                    ${(p.items || []).map(i => `<li>${i.cantidad}x ${i.nombre} (${formatCurrency(i.subtotal)})</li>`).join("")}
                  </ul>
                </td>
                <td><small>${p.metodo_pago}</small></td>
                <td><strong style="color: var(--primary);">${formatCurrency(p.total)}</strong></td>
                <td><span class="status-badge">${p.estado}</span></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    }

    adminModal.classList.add("active");
  } catch (err) {
    console.error("Error al cargar pedidos:", err);
  }
}

// 7. EVENT LISTENERS
function setupEventListeners() {
  // Búsqueda y Filtros
  searchInput.addEventListener("input", renderProducts);

  categoryChips.forEach(chip => {
    chip.addEventListener("click", () => {
      categoryChips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      AppState.activeCategory = chip.dataset.category;
      catalogTitle.innerText = AppState.activeCategory === "todos" ? "Todos nuestros productos" : `Categoría: ${chip.innerText}`;
      renderProducts();
    });
  });

  // Drawer Carrito
  const openCart = () => { cartDrawer.classList.add("open"); drawerOverlay.classList.add("active"); };
  const closeCart = () => { cartDrawer.classList.remove("open"); drawerOverlay.classList.remove("active"); };
  btnOpenCart.addEventListener("click", openCart);
  btnCloseCart.addEventListener("click", closeCart);
  drawerOverlay.addEventListener("click", closeCart);

  btnAssistCart.addEventListener("click", () => {
    closeCart();
    chatWindow.classList.add("open");
    sendChatMessage("Hola, quiero confirmar lo que tengo en mi carrito, ¿cómo seguimos?");
  });

  // Chat Widget Toggle
  btnChatToggle.addEventListener("click", () => {
    chatWindow.classList.toggle("open");
    if (chatWindow.classList.contains("open")) {
      chatInput.focus();
    }
  });

  btnCloseChat.addEventListener("click", () => {
    chatWindow.classList.remove("open");
  });

  // Enviar mensaje en Chat
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const txt = chatInput.value;
    sendChatMessage(txt);
  });

  // Chips de sugerencia rápida
  quickSuggestions.forEach(chip => {
    chip.addEventListener("click", () => {
      chatWindow.classList.add("open");
      sendChatMessage(chip.innerText);
    });
  });

  // Panel Pastelero
  btnOpenOrdersAdmin.addEventListener("click", openAdminPanel);
  btnCloseAdmin.addEventListener("click", () => adminModal.classList.remove("active"));
  adminModal.addEventListener("click", (e) => {
    if (e.target === adminModal) adminModal.classList.remove("active");
  });
}

function jsonStringifySafe(obj) {
  return JSON.stringify(obj);
}

// Inicializar al cargar
document.addEventListener("DOMContentLoaded", initApp);
