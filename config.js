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

document.addEventListener("DOMContentLoaded", () => {
    vincularCampoPaciente();
    despertarServidor();
});
