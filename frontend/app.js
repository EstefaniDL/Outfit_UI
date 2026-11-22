const state = {
  usuario: null,
  prendas: [],
  authModo: "login",
};

const loginSection = document.getElementById("loginSection");
const appSection = document.getElementById("appSection");
const userBar = document.getElementById("userBar");
const userBadge = document.getElementById("userBadge");
const loginForm = document.getElementById("loginForm");
const loginMsg = document.getElementById("loginMsg");
const logoutBtn = document.getElementById("logoutBtn");

const modeLoginBtn = document.getElementById("modeLoginBtn");
const modeRegisterBtn = document.getElementById("modeRegisterBtn");
const authTitle = document.getElementById("authTitle");
const authSubtitle = document.getElementById("authSubtitle");
const nombreField = document.getElementById("nombreField");
const loginIdInput = document.getElementById("loginId");
const loginNombreInput = document.getElementById("loginNombre");
const authSubmitBtn = document.getElementById("authSubmitBtn");

const closetGrid = document.getElementById("closetGrid");
const closetCount = document.getElementById("closetCount");
const prendaImagen = document.getElementById("prendaImagen");
const previewBox = document.getElementById("previewBox");
const previewImg = document.getElementById("previewImg");
const uploadForm = document.getElementById("uploadForm");
const uploadMsg = document.getElementById("uploadMsg");
const generarBtn = document.getElementById("generarBtn");
const recsContainer = document.getElementById("recsContainer");

function mostrarMensaje(el, texto) {
  el.textContent = texto;
  el.classList.remove("hidden");
}

function cambiarModoAuth(nuevoModo) {
  state.authModo = nuevoModo;
  loginMsg.classList.add("hidden");
  const esRegistro = state.authModo === "register";
  modeLoginBtn.classList.toggle("active", !esRegistro);
  modeRegisterBtn.classList.toggle("active", esRegistro);
  nombreField.classList.toggle("hidden", !esRegistro);
  loginNombreInput.required = esRegistro;
  if (!esRegistro) {
    loginNombreInput.value = "";
  }
  authTitle.textContent = esRegistro ? "Crea tu cuenta" : "Inicia sesión en tu clóset";
  authSubtitle.textContent = esRegistro
    ? "Registra tu cuenta y entra directo a tu clóset."
    : "Entra con tu correo o usuario para ver las fotos guardadas de tu clóset.";
  authSubmitBtn.textContent = esRegistro ? "Crear cuenta y entrar" : "Entrar a mi clóset";
}

modeLoginBtn.addEventListener("click", () => cambiarModoAuth("login"));
modeRegisterBtn.addEventListener("click", () => cambiarModoAuth("register"));

function activarPestana(tabId) {
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabId);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === tabId);
  });
}

document.querySelectorAll(".tab[data-tab]").forEach((btn) => {
  btn.addEventListener("click", () => activarPestana(btn.dataset.tab));
});

prendaImagen.addEventListener("change", () => {
  const archivo = prendaImagen.files && prendaImagen.files[0];
  if (!archivo) {
    previewBox.classList.add("hidden");
    return;
  }
  const lector = new FileReader();
  lector.onload = (ev) => {
    previewImg.src = ev.target.result;
    previewBox.classList.remove("hidden");
  };
  lector.readAsDataURL(archivo);
});

async function abrirSesionUsuario(usuario) {
  state.usuario = usuario;
  loginMsg.classList.add("hidden");
  loginSection.classList.add("hidden");
  appSection.classList.remove("hidden");
  userBar.classList.remove("hidden");
  userBadge.textContent = usuario.nombre;
  await cargarCloset();
}

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  loginMsg.classList.add("hidden");

  const identificador = loginIdInput.value.trim();
  const nombre = loginNombreInput.value.trim();
  if (!identificador) {
    mostrarMensaje(loginMsg, "Escribe tu usuario o correo.");
    return;
  }
  if (state.authModo === "register" && !nombre) {
    mostrarMensaje(loginMsg, "Escribe tu nombre para crear la cuenta.");
    return;
  }

  const endpoint = state.authModo === "register" ? "/api/auth/register" : "/api/auth/login";
  authSubmitBtn.disabled = true;

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identificador,
        nombre: state.authModo === "register" ? nombre : null,
      }),
    });

    const texto = await res.text();
    let data = {};
    try {
      data = texto ? JSON.parse(texto) : {};
    } catch (_) {
      data = {};
    }

    if (!res.ok) {
      mostrarMensaje(loginMsg, data.detail || "No se pudo completar la acción.");
      return;
    }

    await abrirSesionUsuario(data.usuario);
  } catch (err) {
    mostrarMensaje(loginMsg, "Error de conexión con el servidor.");
  } finally {
    authSubmitBtn.disabled = false;
  }
});

logoutBtn.addEventListener("click", () => {
  state.usuario = null;
  state.prendas = [];
  loginIdInput.value = "";
  loginNombreInput.value = "";
  loginMsg.classList.add("hidden");
  appSection.classList.add("hidden");
  userBar.classList.add("hidden");
  loginSection.classList.remove("hidden");
  cambiarModoAuth("login");
});

async function cargarCloset() {
  if (!state.usuario) return;
  const res = await fetch(`/api/closet/${encodeURIComponent(state.usuario.user_id)}`);
  if (!res.ok) return;
  const data = await res.json();
  state.prendas = data.prendas || [];
  renderCloset();
}

function renderCloset() {
  closetCount.textContent = `${state.prendas.length} ${state.prendas.length === 1 ? "prenda" : "prendas"}`;
  if (!state.prendas.length) {
    closetGrid.innerHTML = `<div class="card"><p class="muted">Aún no tienes fotos guardadas. Ve a <strong>Subir foto</strong> para agregar las primeras.</p></div>`;
    return;
  }

  closetGrid.innerHTML = state.prendas
    .map(
      (p) => `
      <article class="prenda-card">
        <img src="${p.imagen_url}" alt="Prenda guardada" loading="lazy" />
        <div class="prenda-body">
          <strong>Prenda guardada</strong>
          <div class="tags">
            <span class="tag">Tipo: ${p.etiquetas_confirmadas ? p.tipo_articulo : "pendiente de modelo"}</span>
            <span class="tag">Color: ${p.etiquetas_confirmadas ? p.color_principal : "pendiente de modelo"}</span>
          </div>
          <button class="btn btn-danger" type="button" onclick="borrarPrenda('${p.id}')">Quitar foto</button>
        </div>
      </article>
    `
    )
    .join("");
}

window.borrarPrenda = async function (prendaId) {
  if (!state.usuario) return;
  const res = await fetch(
    `/api/closet/${encodeURIComponent(state.usuario.user_id)}/prendas/${encodeURIComponent(prendaId)}`,
    { method: "DELETE" }
  );
  if (res.ok) {
    await cargarCloset();
  }
};

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!state.usuario || !prendaImagen.files.length) return;

  const fd = new FormData();
  fd.append("imagen", prendaImagen.files[0]);

  const res = await fetch(`/api/closet/${encodeURIComponent(state.usuario.user_id)}/prendas`, {
    method: "POST",
    body: fd,
  });
  const data = await res.json();
  if (res.ok) {
    mostrarMensaje(uploadMsg, "Foto guardada en tu clóset.");
    uploadForm.reset();
    previewBox.classList.add("hidden");
    await cargarCloset();
  } else {
    mostrarMensaje(uploadMsg, data.detail || "Error al guardar la foto.");
  }
});

generarBtn.addEventListener("click", async () => {
  if (!state.usuario) return;
  const ocasion = document.getElementById("filtroOcasion").value;
  const clima = document.getElementById("filtroClima").value;
  const limite = parseInt(document.getElementById("filtroCantidad").value, 10) || 5;

  const res = await fetch(`/api/recomendar/${encodeURIComponent(state.usuario.user_id)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ocasion, clima, limite }),
  });
  const data = await res.json();
  const outfits = data.outfits || [];

  if (!outfits.length) {
    recsContainer.innerHTML = `<div class="card"><p class="muted">Aún no hay suficientes prendas etiquetadas para armar outfits con las reglas actuales. Cuando lleguen las etiquetas del modelo, aquí aparecerán las opciones recomendadas.</p></div>`;
    return;
  }

  recsContainer.innerHTML = outfits
    .map(
      (op, idx) => `
      <article class="outfit-card">
        <h3>Opción #${idx + 1} · ${op.calificacion} / 10</h3>
        <div class="outfit-desc">
          <strong>Para qué funciona:</strong> ${op.descripcion}
        </div>
        <div class="outfit-pieces">
          ${op.piezas
            .map(
              (pz) => `
            <div class="outfit-piece">
              <img src="${pz.imagen_url}" alt="${pz.tipo_articulo}" />
              <div><strong>${pz.tipo_articulo}</strong><br />${pz.color_principal}</div>
            </div>
          `
            )
            .join("")}
        </div>
        <ul class="muted" style="margin:0;padding-left:18px;">
          ${(op.razones || []).map((r) => `<li>${r}</li>`).join("")}
        </ul>
      </article>
    `
    )
    .join("");
});

localStorage.removeItem("outfit_user_id");
loginIdInput.value = "";
loginNombreInput.value = "";
cambiarModoAuth("login");
