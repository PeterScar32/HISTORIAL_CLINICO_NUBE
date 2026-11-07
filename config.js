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
        @media print { #barra-nav, #caja-profesional, #aviso-servidor { display: none !important; } }
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

function profesionalActual() {
    try { return localStorage.getItem("prof_actual") || ""; } catch (e) { return ""; }
}

const _fetchOriginal = window.fetch.bind(window);
window.fetch = (url, opciones = {}) => {
    const metodo = String(opciones.method || "GET").toUpperCase();
    const prof = profesionalActual();
    if (prof && ["POST", "PUT"].includes(metodo) && String(url).startsWith(CONFIG.API_BASE)) {
        const h = new Headers(opciones.headers || {});
        h.set("X-Profesional", prof);
        opciones = { ...opciones, headers: h };
    }
    return _fetchOriginal(url, opciones);
};

async function selectorProfesional() {
    if (!/(doc_|declaracion_jurada_)/.test(location.pathname)) return;
    const caja = document.createElement("div");
    caja.id = "caja-profesional";
    caja.style.cssText = "position:fixed;left:12px;bottom:12px;z-index:9997;background:rgba(15,23,42,.94);border:1px solid #334155;border-radius:12px;padding:8px 12px;font:700 11px system-ui,sans-serif;color:#cbd5e1;display:flex;gap:8px;align-items:center;max-width:calc(100vw - 24px)";
    caja.innerHTML = `<label for="sel-profesional">PROFESIONAL RESPONSABLE:</label><select id="sel-profesional" style="background:#1e293b;color:#fff;border:1px solid #475569;border-radius:8px;padding:6px;font:600 12px system-ui;max-width:260px"><option value="">— SIN IDENTIFICAR —</option></select>`;
    document.body.appendChild(caja);
    const sel = caja.querySelector("select");
    sel.addEventListener("change", () => {
        try { localStorage.setItem("prof_actual", sel.value); } catch (e) {}
        caja.style.borderColor = sel.value ? "#334155" : "#f59e0b";
    });
    try {
        const p = await (await _fetchOriginal(`${CONFIG.API_BASE}/personal/`)).json();
        const opciones = [
            ...(p.doctores || []).map(d => [`doc:${d.id_doc}`, `DR(A). ${d.nombre_doc || ""} ${d.appaterno_doc || ""} · ${d.especialidad || ""}`]),
            ...(p.enfermeras || []).map(e => [`enf:${e.id_enfe}`, `LIC. ${e.nombre_enfe || ""} ${e.appaterno_enfe || ""} · ENFERMERÍA`])
        ];
        sel.innerHTML += opciones.map(([v, t]) => `<option value="${esc(v)}">${esc(t)}</option>`).join("");
        sel.value = opciones.some(([v]) => v === profesionalActual()) ? profesionalActual() : "";
    } catch (e) {}
    caja.style.borderColor = sel.value ? "#334155" : "#f59e0b";
}

document.addEventListener("DOMContentLoaded", () => {
    barraNavegacion();
    selectorProfesional();
    vincularCampoPaciente();
    despertarServidor();
});
