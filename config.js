const CONFIG = {
    API_BASE: "https://historial-clinico-nube-asa8.onrender.com"
};

function esc(valor) {
    return String(valor ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function pacienteActual() {
    try {
        return {
            id: localStorage.getItem("p_id"),
            ci: localStorage.getItem("p_ci"),
            codigo: localStorage.getItem("p_cod"),
            nombre: localStorage.getItem("p_nom")
        };
    } catch (e) {
        return {};
    }
}

function evaluacionActual() {
    try {
        const v = localStorage.getItem("p_eval");
        return v ? parseInt(v) : null;
    } catch (e) {
        return null;
    }
}

function urlPacienteCompleto(id) {
    const ev = evaluacionActual();
    return `${CONFIG.API_BASE}/api/paciente-completo/${id}` + (ev ? `?evaluacion_id=${ev}` : "");
}

function fijarPacienteActual(p) {
    try {
        localStorage.removeItem("p_id_edicion");
        if (String(localStorage.getItem("p_id")) !== String(p.id)) localStorage.removeItem("p_eval");
        localStorage.setItem("p_id", p.id);
        localStorage.setItem("p_ci", p.ci || "");
        localStorage.setItem("p_cod", p.codigo_paciente || p.ci || "");
        localStorage.setItem("p_nom", `${p.apellido || ""} ${p.nombre || ""}`.trim());
    } catch (e) {}
}

async function despertarServidor() {
    const aviso = document.createElement("div");
    aviso.id = "aviso-servidor";
    aviso.textContent = "Conectando con el servidor... (puede tardar hasta un minuto la primera vez)";
    aviso.style.cssText = "position:fixed;bottom:12px;left:50%;transform:translateX(-50%);background:#1e293b;color:#fff;padding:8px 16px;border-radius:8px;font:600 12px sans-serif;z-index:9999;display:none";
    document.body.appendChild(aviso);
    const t = setTimeout(() => { aviso.style.display = "block"; }, 1500);
    for (let i = 0; i < 6; i++) {
        try {
            const r = await fetch(`${CONFIG.API_BASE}/`, { cache: "no-store" });
            if (r.ok) break;
        } catch (e) {}
        await new Promise(res => setTimeout(res, 5000));
    }
    clearTimeout(t);
    aviso.remove();
}

function barraNavegacion() {
    if (document.getElementById("barra-nav")) return;
    const esInicio = /(^|\/)(index\.html)?$/.test(location.pathname);
    const estilo = document.createElement("style");
    estilo.textContent = `
        #barra-nav { position: fixed; top: 10px; right: 12px; z-index: 9998; display: flex; gap: 6px; }
        #barra-nav button { background: rgba(15,23,42,.92); color: #e2e8f0; border: 1px solid #334155; border-radius: 999px;
            padding: 8px 14px; font: 700 12px system-ui, sans-serif; cursor: pointer; letter-spacing: .03em; }
        #barra-nav button:hover { border-color: #60a5fa; color: #93c5fd; }
        @media print { #barra-nav, #aviso-servidor { display: none !important; } }
    `;
    document.head.appendChild(estilo);
    const barra = document.createElement("nav");
    barra.id = "barra-nav";
    barra.setAttribute("aria-label", "Navegación");
    barra.innerHTML = `
        <button type="button" title="Atrás" onclick="history.back()">← Atrás</button>
        <button type="button" title="Adelante" onclick="history.forward()">Adelante →</button>
        ${esInicio ? "" : '<button type="button" title="Inicio" onclick="location.href=\'index.html\'">🏠 Inicio</button>'}`;
    document.body.appendChild(barra);
}

function vincularCampoPaciente() {
    const campo = document.querySelector("#codigo_paciente, form#oftalmoForm #paciente_id");
    if (!campo || !location.pathname.includes("doc_")) return;
    const etiqueta = document.createElement("span");
    etiqueta.style.cssText = "margin-left:10px;font:700 12px sans-serif;";
    campo.insertAdjacentElement("afterend", etiqueta);
    campo.placeholder = "CI DEL PACIENTE";

    const verificar = async () => {
        const ci = campo.value.trim().toUpperCase();
        if (!ci) { etiqueta.textContent = ""; return; }
        etiqueta.style.color = "#64748b";
        etiqueta.textContent = "Buscando...";
        try {
            const r = await fetch(`${CONFIG.API_BASE}/pacientes/buscar/${encodeURIComponent(ci)}`);
            if (!r.ok) throw new Error();
            const p = await r.json();
            fijarPacienteActual(p);
            etiqueta.style.color = "#047857";
            etiqueta.textContent = `✔ ${p.apellido} ${p.nombre}`;
        } catch (e) {
            etiqueta.style.color = "#b91c1c";
            etiqueta.textContent = "✘ CI no registrado";
        }
    };

    campo.addEventListener("change", verificar);
    const actual = pacienteActual();
    if (!campo.value && (actual.ci || actual.codigo)) {
        campo.value = actual.ci || actual.codigo;
        verificar();
    }
}

const PAGINAS_ENFERMERIA = ["", "index.html", "enfermera.html", "registro_paciente.html", "declaracion_jurada_p1.html",
    "declaracion_jurada_p2.html", "declaracion_jurada_p3.html", "d_menu.html", "lista_historial.html"];

function paginaActual() {
    return location.pathname.split("/").pop();
}

function sesion() {
    try {
        const token = localStorage.getItem("ohs_token");
        const usuario = JSON.parse(localStorage.getItem("ohs_usuario") || "null");
        if (!token || !usuario) return null;
        const carga = JSON.parse(atob(token.split(".")[0].replace(/-/g, "+").replace(/_/g, "/")));
        if (carga.exp * 1000 < Date.now()) return null;
        return { token, usuario };
    } catch (e) {
        return null;
    }
}

function guardarSesion(token, usuario) {
    try {
        localStorage.setItem("ohs_token", token);
        localStorage.setItem("ohs_usuario", JSON.stringify(usuario));
    } catch (e) {}
}

function cerrarSesion() {
    try {
        localStorage.removeItem("ohs_token");
        localStorage.removeItem("ohs_usuario");
    } catch (e) {}
    location.href = "index.html";
}

function esMedico() {
    const s = sesion();
    return !!s && s.usuario.rol === "MEDICO";
}

function pedirAcceso() {
    const pagina = paginaActual();
    if (pagina === "" || pagina === "index.html") return;
    const s = sesion();
    if (!s || s.usuario.debe_cambiar) {
        location.replace("index.html");
        return;
    }
    if (s.usuario.rol !== "MEDICO" && !PAGINAS_ENFERMERIA.includes(pagina) && !pagina.startsWith("doc_")) {
        alert("Su perfil no tiene acceso a esta pantalla.");
        location.replace("index.html");
    }
}

pedirAcceso();

const _fetchOriginal = window.fetch.bind(window);
window.fetch = async (url, opciones = {}) => {
    const s = sesion();
    if (s && String(url).startsWith(CONFIG.API_BASE)) {
        const h = new Headers(opciones.headers || {});
        h.set("Authorization", `Bearer ${s.token}`);
        opciones = { ...opciones, headers: h };
    }
    const r = await _fetchOriginal(url, opciones);
    if (r.status === 401 && String(url).startsWith(CONFIG.API_BASE) && !String(url).includes("/auth/login")) {
        cerrarSesion();
    }
    return r;
};

function insigniaUsuario() {
    const s = sesion();
    const barra = document.getElementById("barra-nav");
    if (!s || !barra) return;
    document.body.classList.add("rol-" + s.usuario.rol);
    const chip = document.createElement("div");
    chip.id = "chip-usuario";
    const foto = s.usuario.foto
        ? `<img src="${esc(s.usuario.foto)}" alt="" style="width:26px;height:26px;border-radius:50%;object-fit:cover;border:2px solid #22c55e">`
        : `<span style="width:26px;height:26px;border-radius:50%;background:#0f766e;display:inline-flex;align-items:center;justify-content:center;font-size:13px">⚕️</span>`;
    chip.innerHTML = `${foto}<span>${esc(s.usuario.nombre.split(" ").slice(0, 2).join(" "))}</span>`;
    chip.style.cssText = "display:flex;align-items:center;gap:8px;background:rgba(15,23,42,.92);color:#e2e8f0;border:1px solid #334155;border-radius:999px;padding:4px 12px 4px 4px;font:700 12px system-ui,sans-serif";
    const salir = document.createElement("button");
    salir.type = "button";
    salir.textContent = "Salir";
    salir.onclick = cerrarSesion;
    barra.prepend(chip);
    barra.appendChild(salir);
    const estilo = document.createElement("style");
    estilo.textContent = `.rol-ENFERMERIA .btn-reporte, .rol-ENFERMERIA .btn-borrar, .rol-ENFERMERIA .solo-medico { display: none !important; }`;
    document.head.appendChild(estilo);
}

document.addEventListener("DOMContentLoaded", () => {
    barraNavegacion();
    insigniaUsuario();
    vincularCampoPaciente();
    despertarServidor();
});
