import json
import os
import sys
import urllib.request
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(__file__))
from sesion_e2e import obtener_sesion, abrir_sesion
SESION = obtener_sesion("mecondarco", "temporal-1", "clave-medico-1")

WEB = os.getenv("WEB", "http://127.0.0.1:8080")
API = os.getenv("API", "http://127.0.0.1:8000")
CAPTURAS = os.getenv("CAPTURAS", "")
errores = []


def post(ruta, datos):
    req = urllib.request.Request(API + ruta, data=json.dumps(datos).encode(), headers={"Content-Type": "application/json", "Authorization": f"Bearer {SESION['token']}"})
    return json.loads(urllib.request.urlopen(req).read())


def ok(cond, msg):
    print(("OK   " if cond else "FALLA") + " " + msg)
    if not cond:
        errores.append(msg)


casos = [
    ("8800001", "ANA", "APTO", "APTO"),
    ("8800002", "LUIS", "APTO CON RESTRICCIONES", None),
    ("8800003", "RAUL", "NO APTO", None),
    ("8800004", "EVA", None, None),
]
for ci, nombre, aptitud, osteo in casos:
    p = post("/pacientes/", {"nombre": nombre, "apellido": "SIMULACION", "ci": ci})
    post("/evaluaciones/", {"paciente_id": p["id"], "empresa": "Minera Ficticia", "puesto": "Operario", "tipo": "PERIODICO", "fecha": "2026-11-05"})
    if aptitud and ci != "8800003":
        post("/guardar-aptitud", {"codigo_paciente": ci, "resultado": aptitud})
    if osteo:
        post("/guardar-osteomuscular", {"codigo_paciente": ci, "concepto_aptitud": osteo})

with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 900})
    page.route("**/config.js*", lambda r: r.fulfill(status=200, content_type="application/javascript",
                                                     body=open("config.js", encoding="utf-8").read().replace("https://historial-clinico-nube-asa8.onrender.com", API)))
    page.route("https://cdn.tailwindcss.com/**", lambda r: r.fulfill(status=200, body=""))
    page.add_init_script("""
        window.__sonidos = 0;
        const O = window.AudioContext;
        window.AudioContext = function() { window.__sonidos++; return new O(); };
    """)
    abrir_sesion(page, WEB, SESION)
    page.on("pageerror", lambda e: errores.append("JS: " + str(e)))

    post("/guardar-aptitud", {"codigo_paciente": "8800003", "resultado": "NO APTO"})

    page.goto(f"{WEB}/semaforo.html")
    page.wait_for_function("[...document.querySelectorAll('#empresa option')].some(o => o.value === 'MINERA FICTICIA')")
    page.select_option("#empresa", "MINERA FICTICIA")
    page.click("#btn-buscar")
    page.wait_for_function("document.querySelectorAll('#filas > tr:not(.detalle)').length === 4")
    n = lambda i: page.locator(".tarjeta .n").nth(i).inner_text()
    ok([n(0), n(1), n(2), n(3), n(4)] == ["4", "1", "1", "1", "1"], "resumen: 4 total, 1 rojo, 1 amarillo, 1 verde, 1 gris")
    ok(page.is_visible("#alerta") and "1 TRABAJADOR" in page.inner_text("#alerta"), "alerta roja visible")
    ok(page.evaluate("window.__sonidos") >= 1, "suena la alerta al buscar")
    ok(page.locator("tr.fila-ROJO").count() == 1 and "RAUL" in page.inner_text("tr.fila-ROJO"), "fila roja corresponde al NO APTO")
    ok("Aptitud ocupacional: NO APTO" in page.inner_text("tr.fila-ROJO"), "la fila roja muestra el motivo")
    ok("EVA" in page.inner_text("tr.fila-GRIS"), "sin conclusión queda en gris")
    cu = lambda i: page.locator("#tarjetas-cumplimiento .n").nth(i).inner_text()
    ok((cu(0), cu(1)) == ("0", "4"), "cumplimiento: 0 completas, 4 incompletas (requeridas por defecto)")
    verde = page.inner_text("tr.fila-VERDE")
    ok("Sin alertas registradas" in verde and "INCOMPLETA" in verde and "1 de 5 requeridas" in verde, "verde con fichas faltantes se muestra como incompleta")
    ok("Conclusión sin profesional" not in page.inner_text("#filas"), "todas las conclusiones tienen profesional (sesión iniciada)")
    page.click("tr.fila-ROJO >> text=DETALLE")
    det = page.inner_text("tr.detalle:visible")
    ok("MARÍA ELENA CONDARCO" in det and "NO APTO" in det and "Pendiente" in det, "detalle por ficha con conclusión, profesional y pendientes")
    esp = page.inner_text("#especialidades")
    ok("Aptitud ocupacional" in esp, "tabla de estado por especialidad")
    if CAPTURAS:
        page.screenshot(path=os.path.join(CAPTURAS, "11_semaforo.png"), full_page=True)
    page.click("tr.fila-ROJO >> text=DETALLE")
    page.locator(".tarjeta").nth(1).click()
    ok(page.locator("#filas > tr:not(.detalle)").count() == 1, "filtrar por color rojo")
    page.click("tr.fila-ROJO >> text=REPORTE")
    page.wait_for_url("**/generar_reporte.html")
    page.wait_for_selector("text=ALERTA PRIORITARIA")
    ok(True, "el reporte muestra el semáforo de la evaluación")

    page.goto(f"{WEB}/lista_historial.html")
    page.wait_for_selector("text=8800003")
    ok(page.locator("#listaPacientes span[title*='NO APTO']").count() == 1, "la lista marca al paciente con alerta")
    b.close()

print("\nERRORES:", errores if errores else "ninguno")
sys.exit(1 if errores else 0)
