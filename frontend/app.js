const state = {
  usuario: null,
  prendas: [],
};

const loginSection = document.getElementById("loginSection");
const appSection = document.getElementById("appSection");
const userBar = document.getElementById("userBar");
const userBadge = document.getElementById("userBadge");
const loginForm = document.getElementById("loginForm");
const loginMsg = document.getElementById("loginMsg");
const logoutBtn = document.getElementById("logoutBtn");

const closetGrid = document.getElementById("closetGrid");
const closetCount = document.getElementById("closetCount");
const uploadForm = document.getElementById("uploadForm");
const uploadMsg = document.getElementById("uploadMsg");
const generarBtn = document.getElementById("generarBtn");
const recsContainer = document.getElementById("recsContainer");

function mostrarMensaje(el, texto) {
  el.textContent = texto;
  el.classList.remove("hidden");
}

function activarPestana(tabId) {
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabId);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === tabId);
  });
}

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => activarPestana(btn.dataset.tab));
});

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const identificador = document.getElementById("loginId").value.trim();
  const nombre = document.getElementById("loginNombre").value.trim();
  if (!identificador) return;

  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identificador, nombre: nombre || null }),
  });
  const data = await res.json();
  if (!res.ok) {
    mostrarMensaje(loginMsg, data.detail || "No se pudo iniciar sesión.");
    return;
  }

  state.usuario = data.usuario;
  localStorage.setItem("outfit_user_id", state.usuario.user_id);
  loginSection.classList.add("hidden");
  appSection.classList.remove("hidden");
  userBar.classList.remove("hidden");
  userBadge.textContent = `${state.usuario.nombre} (@${state.usuario.user_id})`;
  await cargarCloset();
});

logoutBtn.addEventListener("click", () => {
  state.usuario = null;
  state.prendas = [];
  localStorage.removeItem("outfit_user_id");
  appSection.classList.add("hidden");
  userBar.classList.add("hidden");
  loginSection.classList.remove("hidden");
});

async function cargarCloset() {
  if (!state.usuario) return;
  const res = await fetch(`/api/closet/${encodeURIComponent(state.usuario.user_id)}`);
  const data = await res.json();
  state.prendas = data.prendas || [];
  renderCloset();
}

function renderCloset() {
  closetCount.textContent = `${state.prendas.length} ${state.prendas.length === 1 ? "prenda" : "prendas"}`;
  if (!state.prendas.length) {
    closetGrid.innerHTML = `<div class="card"><p class="muted">Aún no tienes prendas guardadas. Ve a <strong>Subir prenda</strong> para agregar las primeras.</p></div>`;
    return;
  }

  closetGrid.innerHTML = state.prendas
    .map(
      (p) => `
      <article class="prenda-card">
        <img src="${p.imagen_url}" alt="${p.tipo_articulo}" loading="lazy" />
        <div class="prenda-body">
          <strong>${p.tipo_articulo} · ${p.color_principal}</strong>
          <div class="tags">
            <span class="tag">Tono: ${p.tono}</span>
            <span class="tag">${p.estampado}</span>
            <span class="tag">${p.formalidad}</span>
            <span class="tag">Clima: ${(p.clima || []).join(", ")}</span>
          </div>
          <button class="btn btn-danger" type="button" onclick="borrarPrenda('${p.id}')">Quitar</button>
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
  if (!state.usuario) return;

  const fileInput = document.getElementById("prendaImagen");
  if (!fileInput.files.length) return;

  const fd = new FormData();
  fd.append("imagen", fileInput.files[0]);
  fd.append("tipo_articulo", document.getElementById("prendaTipo").value);
  fd.append("color_principal", document.getElementById("prendaColor").value.trim() || "sin_definir");
  fd.append("tono", document.getElementById("prendaTono").value);
  fd.append("estampado", document.getElementById("prendaEstampado").value);
  fd.append("formalidad", document.getElementById("prendaFormalidad").value);
  fd.append("clima", document.getElementById("prendaClima").value);
  fd.append("corte", document.getElementById("prendaCorte").value);
  fd.append("ocasiones", document.getElementById("prendaOcasiones").value.trim() || "diario");

  const res = await fetch(`/api/closet/${encodeURIComponent(state.usuario.user_id)}/prendas`, {
    method: "POST",
    body: fd,
  });
  const data = await res.json();
  if (res.ok) {
    mostrarMensaje(uploadMsg, `Guardada "${data.prenda.tipo_articulo}" en tu clóset.`);
    uploadForm.reset();
    await cargarCloset();
  } else {
    mostrarMensaje(uploadMsg, data.detail || "Error al guardar la prenda.");
  }
});

// Selección curada inicial (se ampliará con el motor completo de 18 reglas en la siguiente fracción)
generarBtn.addEventListener("click", () => {
  const ocasion = document.getElementById("filtroOcasion").value;
  const clima = document.getElementById("filtroClima").value;
  const limite = parseInt(document.getElementById("filtroCantidad").value, 10) || 5;

  const superiores = state.prendas.filter((p) => p.tipo_articulo === "superior");
  const inferiores = state.prendas.filter((p) => p.tipo_articulo === "inferior");
  const calzados = state.prendas.filter((p) => p.tipo_articulo === "calzado");

  if (!superiores.length || !inferiores.length) {
    recsContainer.innerHTML = `<div class="card"><p class="muted">Necesitas al menos una prenda superior y una inferior en tu clóset para armar opciones.</p></div>`;
    return;
  }

  const opciones = [];
  for (const sup of superiores) {
    for (const inf of inferiores) {
      const cal = calzados.length ? calzados[opciones.length % calzados.length] : null;
      const coloresUnicos = new Set([sup.color_principal, inf.color_principal, ...(cal ? [cal.color_principal] : [])]);
      if (coloresUnicos.size > 4) continue;
      opciones.push({ sup, inf, cal });
      if (opciones.length >= limite) break;
    }
    if (opciones.length >= limite) break;
  }

  if (!opciones.length) {
    recsContainer.innerHTML = `<div class="card"><p class="muted">No se encontraron combinaciones equilibradas para los filtros actuales.</p></div>`;
    return;
  }

  recsContainer.innerHTML = opciones
    .map((op, idx) => {
      const piezas = [op.sup, op.inf, ...(op.cal ? [op.cal] : [])];
      return `
        <article class="outfit-card">
          <h3>Opción #${idx + 1}</h3>
          <div class="outfit-desc">
            <strong>Para qué funciona:</strong> Propuesta pensada para <strong>${ocasion.replace("_", " ")}</strong> en clima <strong>${clima}</strong>, manteniendo variedad en las opciones mostradas y equilibrio visual entre piezas.
          </div>
          <div class="outfit-pieces">
            ${piezas
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
        </article>
      `;
    })
    .join("");
});

// Auto-sesión si ya había iniciado sesión antes en este navegador
(async function init() {
  const guardado = localStorage.getItem("outfit_user_id");
  if (guardado) {
    document.getElementById("loginId").value = guardado;
    loginForm.dispatchEvent(new Event("submit"));
  }
})();
