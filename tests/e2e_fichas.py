import json
import os
import sys
import urllib.request
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(__file__))
from sesion_e2e import obtener_sesion, abrir_sesion

WEB = os.getenv("WEB", "http://127.0.0.1:8080")
API = os.getenv("API", "http://127.0.0.1:8000")
CAPTURAS = os.getenv("CAPTURAS", "")
SESION = obtener_sesion("mecondarco", "temporal-1", "clave-medico-1")
errores = []
CI = "6600111"


def llamar(metodo, ruta, datos=None):
    req = urllib.request.Request(API + ruta, method=metodo, data=json.dumps(datos).encode() if datos is not None else None,
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {SESION['token']}"})
    return json.loads(urllib.request.urlopen(req).read())


def ok(cond, msg):
    print(("OK   " if cond else "FALLA") + " " + msg)
    if not cond:
        errores.append(msg)


def norm(v):
    return "" if v is None else str(v).strip().upper()


PAGINAS = [
    ("doc_cardiologia.html", "cardiologia", "/guardar-cardiologia"),
    ("doc_psicologia.html", "psicologia", "/guardar-psicologia"),
    ("doc_espirometria.html", "espirometria", "/guardar-espirometria"),
    ("doc_altura.html", "altura", "/guardar-altura"),
    ("doc_electroencefalograma.html", "electroencefalograma", "/guardar-electro"),
    ("doc_aptitud.html", "aptitud", "/guardar-aptitud"),
    ("doc_aptifi.html", "aptitud_fisica", "/guardar-aptitud-fisica"),
    ("doc_hiscli.html", "historial_clinico", "/guardar-historial-clinico"),
    ("doc_osteomuscular.html", "osteomuscular", "/guardar-osteomuscular"),
    ("doc_oftalmologia.html", "oftalmologia", None),
]

p = llamar("POST", "/pacientes/", {"nombre": "Prueba", "apellido": "Fichas Simulacion", "ci": CI})
ev = llamar("POST", "/evaluaciones/", {"paciente_id": p["id"], "tipo": "PERIODICO", "fecha": "2026-11-05"})

with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 900})
    page.route("**/config.js*", lambda r: r.fulfill(status=200, content_type="application/javascript",
                                                     body=open("config.js", encoding="utf-8").read().replace("https://historial-clinico-nube-asa8.onrender.com", API)))
    page.route("https://cdn.tailwindcss.com/**", lambda r: r.fulfill(status=200, body=""))
    dialogos = []
    page.on("dialog", lambda d: (dialogos.append(d.message), d.accept()))
    page.on("pageerror", lambda e: errores.append("JS: " + str(e)))
    abrir_sesion(page, WEB, SESION)
    page.evaluate("([id, ci]) => { localStorage.setItem('p_id', id); localStorage.setItem('p_ci', ci); localStorage.setItem('p_cod', ci); }", [p["id"], CI])

    for archivo, clave, ruta in PAGINAS:
        page.goto(f"{WEB}/{archivo}")
        page.wait_for_selector("#aviso-ficha", timeout=15000)
        page.wait_for_function("document.getElementById('aviso-ficha').innerText.length > 0", timeout=15000)
        ok("FICHA NUEVA" in page.inner_text("#aviso-ficha").upper(), f"{clave}: sin datos previos se anuncia ficha nueva " + page.inner_text("#aviso-ficha")[:60])
        dialogos.clear()
        page.evaluate("""() => {
            document.querySelectorAll('input[type=text], textarea').forEach((e, i) => { if (!e.id || !['codigo_paciente','paciente_id'].includes(e.id)) { if (!e.readOnly && e.offsetParent !== null && !e.value) e.value = 'DATO ' + i; } });
            const grupos = {};
            document.querySelectorAll('input[type=radio]').forEach(r => { if (!grupos[r.name]) { grupos[r.name] = 1; r.checked = true; } });
            document.querySelectorAll('input[type=checkbox]').forEach((c, i) => { if (i % 3 === 0) c.click(); });
            document.querySelectorAll('select').forEach(s => { if (s.options.length > 1 && s.id !== 'sel-profesional') s.selectedIndex = 1; });
            document.querySelectorAll('input[type=number]').forEach(e => { if (!e.value) e.value = '42'; });
        }""")
        boton = page.locator("button:has-text('GUARDAR'), button:has-text('Guardar'), .save-btn, .btn-guardar").first
        boton.click()
        page.wait_for_timeout(1500)
        antes = llamar("GET", f"/fichas/{clave}/{p['id']}")["ficha"]
        ok(antes is not None and antes["evaluacion_id"] == ev["id"], f"{clave}: primer guardado en la evaluación correcta")
        if not antes:
            continue
        llenos = {k: v for k, v in antes.items() if k not in ("id", "paciente_id", "evaluacion_id", "codigo_paciente", "creado_en", "registrado_por") and norm(v) not in ("", "NO", "FALSE")}

        page.goto(f"{WEB}/{archivo}")
        page.wait_for_selector("#aviso-ficha", timeout=15000)
        page.wait_for_function("document.getElementById('aviso-ficha').textContent.includes('ya está registrada')", timeout=15000)
        ok(True, f"{clave}: al volver a abrir, se avisa que la ficha ya existe")
        if CAPTURAS and clave == "cardiologia":
            page.screenshot(path=os.path.join(CAPTURAS, "15_ficha_precargada.png"))
        page.locator("button:has-text('GUARDAR'), button:has-text('Guardar'), .save-btn, .btn-guardar").first.click()
        page.wait_for_timeout(1500)
        despues = llamar("GET", f"/fichas/{clave}/{p['id']}")["ficha"]
        perdidos = {k: (antes[k], despues.get(k)) for k in llenos if norm(antes[k]) != norm(despues.get(k))}
        ok(despues["id"] == antes["id"], f"{clave}: el segundo guardado actualiza la misma ficha (no duplica)")
        ok(not perdidos, f"{clave}: abrir y guardar sin cambios conserva {len(llenos)} campos con datos" + (f" — PERDIDOS: {perdidos}" if perdidos else ""))

    b.close()

aud = llamar("GET", f"/auditoria?paciente_id={p['id']}")
ok(sum(1 for a in aud if a["accion"] == "CREACION" and a["ficha"]) >= 10, "auditoría registra la creación de las 10 fichas")
print("\nERRORES:", errores if errores else "ninguno")
sys.exit(1 if errores else 0)
