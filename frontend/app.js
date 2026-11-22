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
          <div class="edit-grid">
            <select aria-label="Tipo de prenda" id="tipo_${p.id}">
              ${["superior", "inferior", "calzado", "exterior", "cuerpo_completo", "otro"]
                .map((opt) => `<option value="${opt}" ${p.tipo_articulo === opt ? "selected" : ""}>${opt}</option>`)
                .join("")}
            </select>
            <input type="text" aria-label="Color principal" id="color_${p.id}" value="${p.color_principal || ""}" placeholder="Color principal" />
            <select aria-label="Tono" id="tono_${p.id}">
              ${["claro", "medio", "oscuro", "suave", "saturado"]
                .map((opt) => `<option value="${opt}" ${p.tono === opt ? "selected" : ""}>${opt}</option>`)
                .join("")}
            </select>
            <select aria-label="Estampado" id="est_${p.id}">
              ${["liso", "rayas", "cuadros", "flores", "grafico", "otro"]
                .map((opt) => `<option value="${opt}" ${p.estampado === opt ? "selected" : ""}>${opt}</option>`)
                .join("")}
            </select>
            <select aria-label="Formalidad" id="form_${p.id}">
              ${["casual", "semiformal", "formal"]
                .map((opt) => `<option value="${opt}" ${p.formalidad === opt ? "selected" : ""}>${opt}</option>`)
                .join("")}
            </select>
            <select aria-label="Clima" id="clima_${p.id}">
              ${["templado", "frio", "calido", "lluvioso"]
                .map((opt) => `<option value="${opt}" ${(p.clima || [])[0] === opt ? "selected" : ""}>${opt}</option>`)
                .join("")}
            </select>
            <button class="btn btn-ghost span-2" type="button" onclick="guardarEdicion('${p.id}')">Guardar cambios</button>
            <button class="btn btn-danger span-2" type="button" onclick="borrarPrenda('${p.id}')">Quitar prenda</button>
          </div>
        </div>
      </article>
    `
    )
    .join("");
}

window.guardarEdicion = async function (prendaId) {
  if (!state.usuario) return;
  const tipo_articulo = document.getElementById(`tipo_${prendaId}`).value;
  const color_principal = document.getElementById(`color_${prendaId}`).value.trim() || "sin_definir";
  const tono = document.getElementById(`tono_${prendaId}`).value;
  const estampado = document.getElementById(`est_${prendaId}`).value;
  const formalidad = document.getElementById(`form_${prendaId}`).value;
  const climaPrincipal = document.getElementById(`clima_${prendaId}`).value;

  const res = await fetch(
    `/api/closet/${encodeURIComponent(state.usuario.user_id)}/prendas/${encodeURIComponent(prendaId)}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tipo_articulo,
        color_principal,
        tono,
        estampado,
        formalidad,
        clima: [climaPrincipal],
        etiquetas_confirmadas: true,
      }),
    }
  );
  if (res.ok) {
    await cargarCloset();
  }
};

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

  if (!prendaImagen.files.length) return;

  const fd = new FormData();
  fd.append("imagen", prendaImagen.files[0]);
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
    previewBox.classList.add("hidden");
    await cargarCloset();
  } else {
    mostrarMensaje(uploadMsg, data.detail || "Error al guardar la prenda.");
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
    recsContainer.innerHTML = `<div class="card"><p class="muted">Necesitas al menos una prenda superior y una inferior en tu clóset para generar opciones.</p></div>`;
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

(async function init() {
  const guardado = localStorage.getItem("outfit_user_id");
  if (guardado) {
    document.getElementById("loginId").value = guardado;
    loginForm.dispatchEvent(new Event("submit"));
  }
})();
