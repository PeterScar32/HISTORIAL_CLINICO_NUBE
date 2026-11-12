const CONFIG = {
    API_BASE: "https://historial-clinico-nube-asa8.onrender.com"
};

function esc(valor) {
    return String(valor ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function fechaServidor(v) {
    if (!v) return null;
    const t = String(v);
    if (/^\d{4}-\d{2}-\d{2}$/.test(t)) return new Date(t + "T12:00:00");
    return new Date(/[zZ]|[+-]\d{2}:?\d{2}$/.test(t) ? t : t + "Z");
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
        @media print { #barra-nav, #caja-responsable, #aviso-servidor { display: none !important; } }
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

const FICHA_DE_PAGINA = {
    "doc_cardiologia.html": "cardiologia", "doc_psicologia.html": "psicologia", "doc_espirometria.html": "espirometria",
    "doc_altura.html": "altura", "doc_electroencefalograma.html": "electroencefalograma", "doc_aptitud.html": "aptitud",
    "doc_aptifi.html": "aptitud_fisica", "doc_hiscli.html": "historial_clinico", "doc_osteomuscular.html": "osteomuscular",
    "doc_oftalmologia.html": "oftalmologia"
};

const MAPEO_FICHAS = {"cardiologia":{"ninez":{"tipo":"getval","id":"ninez_si"},"tabaquismo":{"tipo":"getval","id":"tabaquismo_si"},"hta":{"tipo":"getval","id":"hta_si"},"adolescente":{"tipo":"getval","id":"adolescente_si"},"hiperlipidemias":{"tipo":"getval","id":"hiperlipidemias_si"},"diabetes":{"tipo":"getval","id":"diabetes_si"},"adultez":{"tipo":"getval","id":"adultez_si"},"asma_bronquial":{"tipo":"getval","id":"asma_si"},"bronquitis":{"tipo":"getval","id":"bronquitis_si"},"padre":{"tipo":"getval","id":"padre_si"},"madre":{"tipo":"getval","id":"madre_si"},"hermanos":{"tipo":"getval","id":"hermanos_si"},"abuelos":{"tipo":"getval","id":"abuelos_si"},"hijos":{"tipo":"getval","id":"hijos_si"}},"psicologia":{"habitos_alcohol":{"tipo":"check_name","name":"alcohol","valor":"SI","si":"SI"},"habitos_tabaco":{"tipo":"check_name","name":"tabaco","valor":"SI","si":"SI"},"postura":{"tipo":"radio","name":"postura"},"discurso":{"tipo":"radio","name":"discurso"},"resultado_psicologico":{"tipo":"radio","name":"psicologicamente"},"frecuencia":{"tipo":"getval","id":"alcohol_freq"},"cantidad":{"tipo":"getval","id":"tabaco_cant"}},"espirometria":{"criterios_exclusion_1":{"tipo":"radio","name":"criterios_exclusion_1"},"criterios_exclusion_2":{"tipo":"radio","name":"criterios_exclusion_2"},"criterios_exclusion_3":{"tipo":"radio","name":"criterios_exclusion_3"},"criterios_exclusion_4":{"tipo":"radio","name":"criterios_exclusion_4"},"criterios_exclusion_5":{"tipo":"radio","name":"criterios_exclusion_5"},"hemoptisis":{"tipo":"radio","name":"hemoptisis"},"infarto_reciente":{"tipo":"radio","name":"infarto_reciente"},"neumotorax":{"tipo":"radio","name":"neumotorax"},"fiebre_nauseas":{"tipo":"radio","name":"fiebre_nauseas"},"traqueostomia":{"tipo":"radio","name":"traqueostomia"},"embarazo_avanzado":{"tipo":"radio","name":"embarazo_avanzado"},"sonda_pleural":{"tipo":"radio","name":"sonda_pleural"},"embarazo_complicado":{"tipo":"radio","name":"embarazo_complicado"},"aneurisma_cerebral":{"tipo":"radio","name":"aneurisma_cerebral"},"inestabilidad_cv":{"tipo":"radio","name":"inestabilidad_cv"},"embolia_pulmonar":{"tipo":"radio","name":"embolia_pulmonar"},"infeccion_respiratoria":{"tipo":"radio","name":"infeccion_respiratoria"},"infeccion_oido":{"tipo":"radio","name":"infeccion_oido"},"uso_aerosoles":{"tipo":"radio","name":"uso_aerosoles"},"fumo_ultimas_horas":{"tipo":"radio","name":"fumo_ultimas_horas"},"ejercicio_fisico":{"tipo":"radio","name":"ejercicio_fisico"},"comio_ultima_hora":{"tipo":"radio","name":"comio_ultima_hora"},"tos_flemas":{"tipo":"radio","name":"tos_flemas"},"equipo_proteccion":{"tipo":"radio","name":"equipo_proteccion"}},"electroencefalograma":{"cefaleas":{"tipo":"check","id":"cefaleas","si":"SI","no":"NO"},"perdida_conocimiento":{"tipo":"check","id":"perdida_conocimiento","si":"SI","no":"NO"},"derrame_cerebral":{"tipo":"check","id":"derrame_cerebral","si":"SI","no":"NO"},"epilepsia":{"tipo":"check","id":"epilepsia","si":"SI","no":"NO"},"paralisis":{"tipo":"check","id":"paralisis","si":"SI","no":"NO"},"quirurgicos":{"tipo":"check","id":"quirurgicos","si":"SI","no":"NO"},"convulsiones":{"tipo":"check","id":"convulsiones","si":"SI","no":"NO"},"accidente":{"tipo":"check","id":"accidente","si":"SI","no":"NO"},"otros_antecedentes":{"tipo":"check","id":"otros_antecedentes","si":"SI","no":"NO"},"marcha":{"tipo":"check","id":"marcha","si":"NORMAL","no":"ANORMAL"},"reflejos":{"tipo":"check","id":"reflejos","si":"NORMAL","no":"ANORMAL"},"coordinacion_dedo_nariz":{"tipo":"check","id":"coordinacion_dedo_nariz","si":"NORMAL","no":"ANORMAL"},"coordinacion_talon_rodilla":{"tipo":"check","id":"coordinacion_talon_rodilla","si":"NORMAL","no":"ANORMAL"},"romberg":{"tipo":"check","id":"romberg","si":"NORMAL","no":"ANORMAL"},"vertigo_nistagmo":{"tipo":"check","id":"vertigo_nistagmo","si":"NORMAL","no":"ANORMAL"},"vertigo_adaptacion":{"tipo":"check","id":"vertigo_adaptacion","si":"NORMAL","no":"ANORMAL"},"descripcion_estudio":{"tipo":"check","id":"descripcion_estudio","si":"NORMAL","no":"ANORMAL"},"resultado_estudio":{"tipo":"check","id":"resultado_estudio","si":"NORMAL","no":"ANORMAL"},"reposo":{"tipo":"check","id":"reposo_n","si":"NORMAL","no":"ANORMAL"},"fotoestimulacion":{"tipo":"check","id":"foto_n","si":"NORMAL","no":"ANORMAL"},"hipernea":{"tipo":"check","id":"hipernea_n","si":"NORMAL","no":"ANORMAL"}},"aptitud":{"tipo_examen":{"tipo":"radio","name":"tipo"},"resultado":{"tipo":"radio","name":"resultado"},"apellido_paterno":{"tipo":"id","id":"ape_pat"},"apellido_materno":{"tipo":"id","id":"ape_mat"},"nro_doc_identidad":{"tipo":"id","id":"doc_id"},"puesto_trabajo":{"tipo":"id","id":"puesto"},"recomendacion_1":{"tipo":"id","id":"rec1"},"recomendacion_2":{"tipo":"id","id":"rec2"},"recomendacion_3":{"tipo":"id","id":"rec3"},"recomendacion_4":{"tipo":"id","id":"rec4"}},"aptitud_fisica":{"tipo_examen":{"tipo":"radio","name":"tipo_examen"},"resultado_fisico":{"tipo":"radio","name":"res_fisico"},"resultado_psicologico":{"tipo":"radio","name":"res_psico"}},"osteomuscular":{"sexo":{"tipo":"radio","name":"sexo"},"grave_hombro_der":{"tipo":"radio","name":"grave_hombro_der"},"grave_hombro_izq":{"tipo":"radio","name":"grave_hombro_izq"},"gravedad_codo_der":{"tipo":"radio","name":"gravedad_codo_der"},"gravedad_codo_izq":{"tipo":"radio","name":"gravedad_codo_izq"},"grado_codo_der":{"tipo":"radio","name":"grado_codo_der"},"grado_codo_izq":{"tipo":"radio","name":"grado_codo_izq"},"gravedad_cuadro":{"tipo":"radio","name":"gravedad_cuadro"},"concepto_aptitud":{"tipo":"radio","name":"concepto_aptitud"},"ant1_fecha":{"tipo":"id","id":"fecha_ant_1"},"ant1_diagnostico":{"tipo":"id","id":"diagnostico_1"},"ant1_tratamiento":{"tipo":"id","id":"tratamiento_1"},"ant1_comentario":{"tipo":"id","id":"comentario_1"},"ant2_fecha":{"tipo":"id","id":"fecha_ant_2"},"ant2_diagnostico":{"tipo":"id","id":"diagnostico_2"},"ant2_tratamiento":{"tipo":"id","id":"tratamiento_2"},"ant2_comentario":{"tipo":"id","id":"comentario_2"},"ant3_fecha":{"tipo":"id","id":"fecha_ant_3"},"ant3_diagnostico":{"tipo":"id","id":"diagnostico_3"},"ant3_tratamiento":{"tipo":"id","id":"tratamiento_3"},"ant3_comentario":{"tipo":"id","id":"comentario_3"}}};

const ORDEN_ALTURA = ["agorafobia", "diabetes", "acrofobia", "insuficiencia_cardiaca", "arritmia", "hipertension", "consumo_drogas", "meniere",
    "enfermedad_psiquiatrica", "ametropia", "trauma_encefalo", "esteropsis", "convulsiones", "asma_bronquial", "vertigo", "hipoacusia", "sincope",
    "accidentes_fracturas", "mioclonias", "deformidades", "cefaleas", "soplo_cardiaco", "sustentacion_pie", "arritmias_cardiacas", "camina_libre",
    "nistagmus", "adiacocinesia", "test_romberg", "audicion", "test_barany", "marcha_ojos_cerrados", "test_babinsky", "extremidades"];

const CAMPOS_INTERNOS = new Set(["id", "paciente_id", "evaluacion_id", "codigo_paciente", "creado_en", "registrado_por"]);

function asignarCampo(clave, valor) {
    const v = String(valor);
    const el = document.getElementById(clave);
    const avisar = e => { e.dispatchEvent(new Event("input", { bubbles: true })); e.dispatchEvent(new Event("change", { bubbles: true })); };
    if (el && /^(INPUT|SELECT|TEXTAREA)$/.test(el.tagName)) {
        if (el.type === "checkbox") el.checked = ["SI", "TRUE", "1", "ON"].includes(v.toUpperCase()) || (el.value !== "on" && el.value === v);
        else if (el.type === "radio") el.checked = el.value === v;
        else el.value = v;
        avisar(el);
        return true;
    }
    const si = document.getElementById(clave + "_si");
    const no = document.getElementById(clave + "_no");
    if (si || no) {
        if (si) si.checked = v.toUpperCase() === "SI";
        if (no) no.checked = v.toUpperCase() === "NO";
        return true;
    }
    const grupo = document.querySelectorAll(`input[name="${CSS.escape(clave)}"]`);
    if (grupo.length) {
        grupo.forEach(g => { g.checked = g.value === v; });
        const marcado = [...grupo].find(g => g.checked);
        if (marcado) avisar(marcado);
        return true;
    }
    return false;
}

function rellenarFicha(clave, ficha) {
    if (clave === "altura") {
        const cajas = document.querySelectorAll('input[type="checkbox"]');
        ORDEN_ALTURA.forEach((k, i) => {
            if (cajas[2 * i]) cajas[2 * i].checked = ficha[k] === "SI";
            if (cajas[2 * i + 1]) cajas[2 * i + 1].checked = ficha[k] === "NO";
        });
        const obs = document.querySelectorAll(".observaciones");
        if (obs[0]) obs[0].value = ficha.obs_antecedentes || "";
        if (obs[1]) obs[1].value = ficha.obs_examen || "";
        return;
    }
    const mapa = MAPEO_FICHAS[clave] || {};
    Object.entries(ficha).forEach(([k, v]) => {
        if (CAMPOS_INTERNOS.has(k) || v === null || v === undefined || v === "") return;
        const m = mapa[k];
        const txt = String(v);
        if (!m) { asignarCampo(k, v); return; }
        if (m.tipo === "check") {
            const el = document.getElementById(m.id);
            if (el) { el.checked = txt === m.si; el.dispatchEvent(new Event("change", { bubbles: true })); }
        } else if (m.tipo === "check_name") {
            document.querySelectorAll(`input[name="${CSS.escape(m.name)}"]`).forEach(e => { e.checked = txt === m.si ? e.value === m.valor : e.value !== m.valor && e.value === txt; });
        } else if (m.tipo === "radio") {
            document.querySelectorAll(`input[name="${CSS.escape(m.name)}"]`).forEach(e => { e.checked = e.value === txt; });
        } else {
            asignarCampo(m.id, v);
        }
    });
}

function _poner(id, valor) {
    const el = document.getElementById(id);
    if (!el || valor === undefined || valor === null || String(valor).trim() === "") return;
    if (el.type === "checkbox" || el.type === "radio") { el.checked = true; return; }
    if (String(el.value || "").trim() !== "") return;
    el.value = valor;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
}

function _marcarNombre(nombre, valor) {
    if (!valor) return;
    document.querySelectorAll(`input[name="${nombre}"]`).forEach(i => { if (i.value === valor) i.checked = true; });
}

async function autocompletarFicha(pacienteId) {
    const pagina = paginaActual();
    try {
        const r = await fetch(urlPacienteCompleto(pacienteId));
        if (!r.ok) return;
        const d = await r.json();
        const p = d.paciente || {}, ev = d.evaluacion || {}, f = d.filiacion || {};
        const apellidos = String(p.apellido || "").trim().split(/\s+/);
        const paterno = apellidos[0] || "", materno = apellidos.slice(1).join(" ");
        const completo = `${p.apellido || ""} ${p.nombre || ""}`.trim();
        let edad = String(f.edad || "").replace(/\D/g, "");
        if (!edad && f.fecha_nacimiento && ev.fecha) {
            const n = new Date(f.fecha_nacimiento), e = new Date(ev.fecha);
            if (!isNaN(n) && !isNaN(e)) edad = String(e.getFullYear() - n.getFullYear() - ((e.getMonth() < n.getMonth() || (e.getMonth() === n.getMonth() && e.getDate() < n.getDate())) ? 1 : 0));
        }
        const sexo = String(f.sexo || "").toUpperCase();
        const fecha = String(ev.fecha || "").slice(0, 10);
        const [anio, mes, dia] = fecha ? fecha.split("-") : ["", "", ""];
        const tipo = String(ev.tipo || "").toUpperCase();
        const tipoCert = { PREOCUPACIONAL: "PREOCUPACIONAL", PERIODICO: "CONTROL PERIÓDICO", RETIRO: "POST-OCUPACIONAL" }[tipo];
        if (pagina === "doc_aptitud.html" || pagina === "doc_aptifi.html") {
            _poner("ape_pat", paterno); _poner("ape_mat", materno); _poner("nombres", p.nombre);
            _poner("edad", edad); _poner("genero", sexo); _poner("doc_id", p.ci);
            _poner("puesto", ev.puesto); _poner("puesto_trabajo", ev.puesto); _poner("razon_social", ev.empresa);
            _poner("dia", dia); _poner("mes", mes); _poner("anio", anio);
            _marcarNombre(pagina === "doc_aptitud.html" ? "tipo" : "tipo_examen", tipoCert);
            if (tipo === "OTRO") _poner("otros_tipo", "OTRO");
        } else if (pagina === "doc_hiscli.html") {
            _poner("empresa", ev.empresa); _poner("nombre", completo); _poner("fecha_atencion", fecha);
            _poner("carnet_identidad", p.ci); _poner("sexo", sexo); _poner("edad", edad); _poner("puesto_cargo", ev.puesto);
            _poner({ PREOCUPACIONAL: "tipo_pre", PERIODICO: "tipo_per", RETIRO: "tipo_post", OTRO: "tipo_otro" }[tipo], true);
        } else if (pagina === "doc_osteomuscular.html") {
            _poner("nombre_completo", completo); _poner("edad", edad); _poner("ci", p.ci); _poner("fecha", fecha); _poner("fecha_firma", fecha);
            if (sexo.startsWith("M")) _poner("sexo_m", true);
            if (sexo.startsWith("F")) _poner("sexo_f", true);
        }
    } catch (e) {}
}

async function precargarFicha(pacienteId, etiqueta) {
    const clave = FICHA_DE_PAGINA[paginaActual()];
    if (!clave) return;
    let aviso = document.getElementById("aviso-ficha");
    if (!aviso) {
        aviso = document.createElement("div");
        aviso.id = "aviso-ficha";
        aviso.style.cssText = "margin:8px 0;padding:8px 12px;border-radius:8px;font:600 12px system-ui,sans-serif;";
        (etiqueta.closest("div") || etiqueta.parentElement).insertAdjacentElement("afterend", aviso);
    }
    try {
        const ev = evaluacionActual();
        const r = await fetch(`${CONFIG.API_BASE}/fichas/${clave}/${pacienteId}` + (ev ? `?evaluacion_id=${ev}` : ""));
        if (!r.ok) return;
        const d = await r.json();
        const evTxt = d.evaluacion ? `evaluación del ${d.evaluacion.fecha || "—"}${d.evaluacion.tipo ? " (" + d.evaluacion.tipo + ")" : ""}` : "nueva evaluación";
        if (d.evaluacion_id) { try { localStorage.setItem("p_eval", d.evaluacion_id); } catch (e) {} }
        const selResp = document.getElementById("sel-responsable");
        if (selResp && d.ficha) {
            selResp.dataset.cargada = "1";
            selResp.dataset.pendiente = d.ficha.responsable_id ? String(d.ficha.responsable_id) : "";
            selResp.value = selResp.dataset.pendiente;
            selResp.dispatchEvent(new Event("change"));
        }
        if (d.ficha) {
            rellenarFicha(clave, d.ficha);
            const cuando = d.ficha.creado_en ? fechaServidor(d.ficha.creado_en).toLocaleString("es-BO", { dateStyle: "short", timeStyle: "short" }) : "fecha no registrada";
            aviso.style.background = "#fef3c7"; aviso.style.color = "#92400e";
            aviso.textContent = `📝 Esta ficha ya está registrada en la ${evTxt} (registrada el ${cuando}${d.ficha.registrado_por ? " por " + d.ficha.registrado_por : ""}${d.ficha.responsable ? " · responsable: " + d.ficha.responsable : " · sin profesional responsable"}). Se cargaron sus datos: al guardar se actualizarán y cada cambio quedará en el historial.`;
        } else {
            aviso.style.background = "#dcfce7"; aviso.style.color = "#166534";
            const conDatos = ["doc_aptitud.html", "doc_aptifi.html", "doc_hiscli.html", "doc_osteomuscular.html"].includes(paginaActual());
            aviso.textContent = `🆕 Ficha nueva para la ${evTxt}.` + (conDatos ? " Los datos del trabajador se completaron desde su registro; revíselos antes de guardar." : "");
            await autocompletarFicha(pacienteId);
        }
    } catch (e) {}
}

async function selectorResponsable() {
    if (!FICHA_DE_PAGINA[paginaActual()]) return;
    const s = sesion();
    if (!s) return;
    const caja = document.createElement("div");
    caja.id = "caja-responsable";
    caja.style.cssText = "position:fixed;left:12px;bottom:12px;z-index:9997;background:rgba(15,23,42,.95);border:1px solid #334155;border-radius:12px;padding:8px 12px;font:700 11px system-ui,sans-serif;color:#cbd5e1;display:flex;gap:8px;align-items:center;max-width:calc(100vw - 24px)";
    caja.innerHTML = `<label for="sel-responsable">PROFESIONAL RESPONSABLE:</label><select id="sel-responsable" style="background:#1e293b;color:#fff;border:1px solid #475569;border-radius:8px;padding:6px;font:600 12px system-ui;max-width:300px"><option value="">— SIN ASIGNAR —</option></select>`;
    document.body.appendChild(caja);
    const sel = caja.querySelector("select");
    const marcar = () => { caja.style.borderColor = sel.value ? "#334155" : "#f59e0b"; };
    sel.addEventListener("change", marcar);
    try {
        const lista = await (await fetch(`${CONFIG.API_BASE}/auth/profesionales`)).json();
        sel.innerHTML += lista.map(p => `<option value="${p.id}">${esc(p.nombre)}${p.especialidad || p.cargo ? " · " + esc(p.especialidad || p.cargo) : ""}</option>`).join("");
        if (sel.dataset.cargada) sel.value = sel.dataset.pendiente || "";
        else if (["MEDICO", "ESPECIALISTA"].includes(s.usuario.rol) && lista.some(p => p.id === s.usuario.id)) sel.value = String(s.usuario.id);
    } catch (e) {}
    marcar();
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
            if (window._pacienteFicha && window._pacienteFicha !== p.id) {
                fijarPacienteActual(p);
                location.reload();
                return;
            }
            window._pacienteFicha = p.id;
            fijarPacienteActual(p);
            etiqueta.style.color = "#047857";
            etiqueta.textContent = `✔ ${p.apellido} ${p.nombre}`;
            precargarFicha(p.id, etiqueta);
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

const PAGINAS_SOLO_MEDICO = ["lista_personal.html", "registro_personal.html"];
const PAGINAS_CONSULTA = ["semaforo.html", "lista_historial.html", "informe.html", "generar_reporte.html", "d_menu.html",
    "opciones_visor.html", "consultas.html", "informes.html", "informes_2.html"];

function paginaPermitida(u, pagina) {
    if (u.rol === "MEDICO") return true;
    if (PAGINAS_SOLO_MEDICO.includes(pagina)) return false;
    if (u.rol === "ENFERMERIA") return PAGINAS_ENFERMERIA.includes(pagina) || pagina.startsWith("doc_");
    if (u.rol === "LECTURA") return true;
    if (u.rol === "ESPECIALISTA") {
        if (PAGINAS_CONSULTA.includes(pagina) || pagina.startsWith("co_")) return true;
        const ficha = FICHA_DE_PAGINA[pagina];
        return !!ficha && (u.fichas_permitidas || []).includes(ficha);
    }
    return false;
}

function pedirAcceso() {
    const pagina = paginaActual();
    if (pagina === "" || pagina === "index.html") return;
    const s = sesion();
    if (!s || s.usuario.debe_cambiar) {
        location.replace("index.html");
        return;
    }
    if (!paginaPermitida(s.usuario, pagina)) {
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
        const ev = evaluacionActual();
        if (ev && !h.has("X-Evaluacion")) h.set("X-Evaluacion", String(ev));
        const sel = document.getElementById("sel-responsable");
        if (sel && !h.has("X-Responsable") && ["POST", "PUT"].includes(String(opciones.method || "GET").toUpperCase())) h.set("X-Responsable", sel.value || "0");
        opciones = { ...opciones, headers: h };
    }
    const r = await _fetchOriginal(url, opciones);
    const deApi = String(url).startsWith(CONFIG.API_BASE);
    if (r.status === 401 && deApi && !String(url).includes("/auth/login")) {
        cerrarSesion();
    }
    const metodo = String(opciones.method || "GET").toUpperCase();
    if (deApi && r.status === 403 && metodo !== "GET") {
        r.clone().json().then(d => alert("⛔ " + (d.detail || "No tiene permiso para esta acción"))).catch(() => {});
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
    estilo.textContent = `.rol-ENFERMERIA .btn-reporte, .rol-ENFERMERIA .btn-borrar, .rol-ENFERMERIA .solo-medico, .rol-ENFERMERIA .btn-papelera,
        .rol-ESPECIALISTA .btn-borrar, .rol-ESPECIALISTA .btn-editar, .rol-ESPECIALISTA .solo-medico, .rol-ESPECIALISTA .btn-papelera,
        .rol-LECTURA .btn-borrar, .rol-LECTURA .btn-editar, .rol-LECTURA .solo-medico, .rol-LECTURA .btn-papelera { display: none !important; }`;
    document.head.appendChild(estilo);
}

function destinoDe(el) {
    const txt = el.getAttribute("onclick") || el.getAttribute("href") || "";
    const m = txt.match(/([\w-]+\.html)/);
    return m ? m[1] : null;
}

function ocultarEnlacesNoPermitidos() {
    const s = sesion();
    if (!s) return;
    document.querySelectorAll("[onclick*='.html'], a[href$='.html']").forEach(el => {
        const destino = destinoDe(el);
        if (destino && destino !== "index.html" && !paginaPermitida(s.usuario, destino)) el.style.display = "none";
    });
}

const CONSULTA_DE_PAGINA = {
    "co_altura.html": "altura", "co_aptifi.html": "aptitud_fisica", "co_aptitud.html": "aptitud", "co_cardiologia.html": "cardiologia",
    "co_declaracion.html": "declaracion", "co_electroencefalograma.html": "electroencefalograma", "co_espirometria.html": "espirometria",
    "co_hiscli.html": "historial_clinico", "co_oftalmologia.html": "oftalmologia", "co_osteomuscular.html": "osteomuscular",
    "co_psicologia.html": "psicologia"
};

function buscadorConsulta() {
    const clave = CONSULTA_DE_PAGINA[paginaActual()];
    const tabla = document.querySelector(".container table");
    if (!clave || !tabla || document.getElementById("busqueda-consulta")) return;
    const caja = document.createElement("div");
    caja.id = "busqueda-consulta";
    caja.className = "no-print";
    caja.style.cssText = "background:#16213a;border:1px solid #1e293b;border-radius:12px;padding:16px;margin:0 0 22px";
    caja.innerHTML = `
        <div style="font-weight:800;font-size:13px;letter-spacing:.06em;color:#cbd5e1;margin-bottom:10px">BUSCAR PACIENTE POR CI O NOMBRE COMPLETO</div>
        <form id="bc-form" style="display:flex;gap:10px;flex-wrap:wrap">
            <input id="bc-q" type="search" class="form-control" style="flex:1;min-width:220px" placeholder="Ej.: 7012345 o Jorge Quispe Huanca" aria-label="CI o nombre completo">
            <button type="submit" class="btn btn-success fw-bold">BUSCAR</button>
            <button type="button" id="bc-limpiar" class="btn btn-outline-light">LIMPIAR</button>
        </form>
        <div id="bc-resultado" style="margin-top:12px"></div>`;
    tabla.parentNode.insertBefore(caja, tabla);
    const salida = caja.querySelector("#bc-resultado");
    caja.querySelector("#bc-limpiar").onclick = () => { caja.querySelector("#bc-q").value = ""; salida.innerHTML = ""; };
    caja.querySelector("#bc-form").onsubmit = async ev => {
        ev.preventDefault();
        const q = caja.querySelector("#bc-q").value.trim();
        if (!q) { salida.innerHTML = '<div style="color:#fbbf24">Escriba un CI o un nombre.</div>'; return; }
        salida.innerHTML = '<div style="color:#94a3b8">Buscando…</div>';
        try {
            const r = await fetch(`${CONFIG.API_BASE}/consultas/${clave}/buscar?q=${encodeURIComponent(q)}`);
            const d = await r.json().catch(() => ({}));
            if (!r.ok) { salida.innerHTML = `<div style="color:#f87171">${esc(d.detail || "Error " + r.status)}</div>`; return; }
            if (!d.length) { salida.innerHTML = '<div style="color:#fbbf24">No se encontró ningún paciente con ese CI o nombre.</div>'; return; }
            window._bcFilas = d;
            salida.innerHTML = `<div class="table-responsive"><table class="table table-bordered mb-0"><thead><tr>
                <th>CI</th><th>NOMBRE COMPLETO</th><th>EVALUACIÓN</th><th>ESTADO</th><th>RESPONSABLE</th><th></th></tr></thead><tbody>
                ${d.map((x, i) => `<tr><td>${esc(x.ci)}</td><td>${esc(x.apellido)} ${esc(x.nombre)}</td>
                    <td>${x.registrada ? `${esc(x.fecha || "")} · ${esc(x.tipo || "")}<div style="font-size:12px;opacity:.75">${esc(x.empresa || "")}</div>` : "—"}</td>
                    <td>${x.registrada ? '<span style="color:#22c55e;font-weight:800">REGISTRADA</span>' : '<span style="color:#94a3b8;font-weight:800">SIN REGISTRO</span>'}</td>
                    <td>${esc(x.responsable || x.registrado_por || "—")}</td>
                    <td><button type="button" class="btn btn-sm btn-primary" onclick="verDesdeConsulta(${i})">VER INFORME</button></td></tr>`).join("")}
                </tbody></table></div>`;
        } catch (e) {
            salida.innerHTML = '<div style="color:#f87171">El servidor no responde.</div>';
        }
    };
}

function verDesdeConsulta(i) {
    const x = (window._bcFilas || [])[i];
    if (!x) return;
    fijarPacienteActual({ id: x.paciente_id, ci: x.ci, codigo_paciente: x.codigo_paciente, nombre: x.nombre, apellido: x.apellido });
    try {
        localStorage.setItem("p_id_reporte", x.paciente_id);
        if (x.evaluacion_id) localStorage.setItem("p_eval", x.evaluacion_id); else localStorage.removeItem("p_eval");
    } catch (e) {}
    window.location.href = "informe.html";
}

function panelLateral(titulo, descripcion) {
    if (!document.getElementById("pl-estilos")) {
        const st = document.createElement("style");
        st.id = "pl-estilos";
        st.textContent = `
            .pl-fondo { position: fixed; inset: 0; background: rgba(2, 6, 23, .6); z-index: 10000; opacity: 0; transition: opacity .2s; }
            .pl-panel { position: fixed; top: 0; right: 0; height: 100%; width: min(620px, 100vw); box-sizing: border-box; background: #0f172a; color: #e2e8f0; border-left: 1px solid #334155;
                z-index: 10001; display: flex; flex-direction: column; transform: translateX(100%); transition: transform .25s ease; box-shadow: -12px 0 40px rgba(0, 0, 0, .45);
                font-family: "Segoe UI", system-ui, sans-serif; }
            .pl-abierto .pl-fondo { opacity: 1; } .pl-abierto .pl-panel { transform: none; }
            .pl-cabecera { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 18px 20px; border-bottom: 1px solid #1e293b; }
            .pl-cabecera h3 { margin: 0; font-size: 15px; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; color: #f8fafc; }
            .pl-panel .pl-cerrar { padding: 0; line-height: 1; letter-spacing: 0; font-weight: 400; background: #1e293b; color: #e2e8f0; border: 1px solid #334155; border-radius: 10px; width: 36px; height: 36px; font-size: 18px; cursor: pointer; }
            .pl-desc { margin: 0; padding: 12px 20px 0; font-size: 12px; color: #94a3b8; line-height: 1.5; }
            .pl-cuerpo { flex: 1; overflow-y: auto; padding: 14px 20px 24px; }
            .pl-item { background: #111c33; border: 1px solid #1e293b; border-radius: 12px; padding: 12px 14px; margin-bottom: 10px; }
            .pl-item.pl-restaurado { opacity: .55; }
            .pl-nombre { font-weight: 800; font-size: 14px; color: #fff; }
            .pl-dato { font-size: 12px; color: #94a3b8; margin-top: 3px; }
            .pl-pie { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-top: 10px; flex-wrap: wrap; }
            .pl-panel .pl-restaurar { letter-spacing: 0; background: #16a34a; color: #fff; border: none; border-radius: 9px; padding: 7px 14px; font-weight: 800; font-size: 12px; cursor: pointer; }
            .pl-vacio { color: #94a3b8; font-size: 13px; padding: 20px 0; text-align: center; }`;
        document.head.appendChild(st);
    }
    document.getElementById("pl-raiz")?.remove();
    const raiz = document.createElement("div");
    raiz.id = "pl-raiz";
    raiz.innerHTML = `<div class="pl-fondo"></div><aside class="pl-panel" role="dialog" aria-modal="true" aria-label="${esc(titulo)}">
        <div class="pl-cabecera"><h3>${esc(titulo)}</h3><button type="button" class="pl-cerrar" aria-label="Cerrar">✕</button></div>
        ${descripcion ? `<p class="pl-desc">${esc(descripcion)}</p>` : ""}<div class="pl-cuerpo" id="pl-cuerpo"><div class="pl-vacio">Cargando…</div></div></aside>`;
    document.body.appendChild(raiz);
    const cerrar = () => { raiz.classList.remove("pl-abierto"); document.removeEventListener("keydown", tecla); setTimeout(() => raiz.remove(), 250); };
    const tecla = e => { if (e.key === "Escape") cerrar(); };
    raiz.querySelector(".pl-fondo").onclick = cerrar;
    raiz.querySelector(".pl-cerrar").onclick = cerrar;
    document.addEventListener("keydown", tecla);
    requestAnimationFrame(() => raiz.classList.add("pl-abierto"));
    return raiz.querySelector("#pl-cuerpo");
}

document.addEventListener("DOMContentLoaded", () => {
    barraNavegacion();
    ocultarEnlacesNoPermitidos();
    insigniaUsuario();
    selectorResponsable();
    vincularCampoPaciente();
    buscadorConsulta();
    despertarServidor();
});
