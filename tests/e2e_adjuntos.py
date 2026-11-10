import os
import sys
import tempfile
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(__file__))
from sesion_e2e import obtener_sesion, abrir_sesion, _post

WEB = os.getenv("WEB", "http://127.0.0.1:8080")
API = os.getenv("API", "http://127.0.0.1:8000")
CAPTURAS = os.getenv("CAPTURAS", "")
CI = "9999321"
errores = []

MEDICO = obtener_sesion("mecondarco", "temporal-1", "clave-medico-1")
ENF = obtener_sesion("enfermeria", "temporal-5", "clave-enf-123")

d = tempfile.mkdtemp()
PDF = os.path.join(d, "laboratorio.pdf")
PNG = os.path.join(d, "radiografia.png")
TXT = os.path.join(d, "notas.txt")
open(PDF, "wb").write(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF")
from PIL import Image
Image.new("RGB", (40, 30), (120, 40, 200)).save(PNG)
open(TXT, "w").write("texto")


def ok(cond, msg):
    print(("OK   " if cond else "FALLA") + " " + msg)
    if not cond:
        errores.append(msg)


def captura(page, nombre):
    if CAPTURAS:
        page.screenshot(path=os.path.join(CAPTURAS, nombre + ".png"))


def preparar(page):
    def config(route):
        body = open("config.js", encoding="utf-8").read().replace("https://historial-clinico-nube-asa8.onrender.com", API)
        route.fulfill(status=200, content_type="application/javascript", body=body)
    page.route("**/config.js*", config)
    page.route("https://cdn.tailwindcss.com/**", lambda r: r.fulfill(status=200, body=""))
    page.on("dialog", lambda dl: dl.accept())
    page.on("pageerror", lambda e: errores.append("JS: " + str(e)))


try:
    p = _post("/pacientes/", {"nombre": "Jorge Luis", "apellido": "Quispe Huanca", "ci": CI}, MEDICO["token"])
    _post("/evaluaciones/", {"paciente_id": p["id"], "tipo": "PERIODICO", "empresa": "EMPRESA FICTICIA SA"}, MEDICO["token"])
    _post("/guardar-cardiologia", {"codigo_paciente": CI, "hta": "SI"}, MEDICO["token"])
except Exception as e:
    errores.append("preparación: " + str(e))

with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(accept_downloads=True)
    page = ctx.new_page()
    preparar(page)
    abrir_sesion(page, WEB, MEDICO)

    page.goto(f"{WEB}/lista_historial.html")
    fila = page.locator(f"#listaPacientes tr:has-text('{CI}')")
    fila.wait_for()
    ok(fila.locator(".btn-adjuntos").is_visible(), "cada paciente tiene el botón 📎 de archivos")
    fila.locator(".btn-adjuntos").click()
    page.wait_for_selector("#dlgAdjuntos[open]")
    page.wait_for_selector("text=todavía no tiene archivos")
    ok(CI in page.inner_text("#adj-paciente"), "el diálogo muestra el paciente")
    page.set_input_files("#adj-archivo", [PDF, PNG])
    page.fill("#adj-descripcion", "Examen ficticio")
    page.click("#adj-subir")
    page.wait_for_selector("#adj-filas >> text=radiografia.png")
    page.wait_for_selector("#adj-filas >> text=laboratorio.pdf")
    ok("2 archivo(s) subido(s)" in page.inner_text("#adj-estado"), "sube un PDF y una foto a la vez")
    ok(page.locator("#adj-filas tr").count() == 2 and "Examen ficticio" in page.inner_text("#adj-filas"), "la lista muestra los archivos con su descripción")
    captura(page, "a01_adjuntos")

    page.set_input_files("#adj-archivo", [TXT])
    page.click("#adj-subir")
    page.wait_for_function("document.getElementById('adj-estado').innerText.includes('solo PDF')")
    ok(True, "rechaza archivos que no son PDF, JPG o PNG")

    with ctx.expect_page() as nueva:
        page.locator("#adj-filas tr:has-text('radiografia.png') button:has-text('Ver')").click()
    pop = nueva.value
    try:
        pop.wait_for_function("location.href.startsWith('blob:')", timeout=10000)
        ok(True, "Ver abre el archivo en otra pestaña")
    except Exception:
        ok(False, "Ver abre el archivo en otra pestaña: " + pop.url)
    pop.close()
    with page.expect_download() as dl:
        page.locator("#adj-filas tr:has-text('radiografia.png') button:has-text('Descargar')").click()
    ok(dl.value.suggested_filename == "radiografia.png", "Descargar guarda el archivo con su nombre")
    ruta = dl.value.path()
    ok(open(ruta, "rb").read() == open(PNG, "rb").read(), "el archivo descargado es idéntico al subido")

    page.locator("#adj-filas tr:has-text('laboratorio.pdf') button:has-text('Eliminar')").click()
    page.wait_for_function("document.querySelectorAll('#adj-filas tr').length === 1")
    ok(True, "el médico puede eliminar un archivo")
    page.click("#dlgAdjuntos button:has-text('Cerrar')")

    page.goto(f"{WEB}/co_cardiologia.html")
    page.wait_for_selector("#busqueda-consulta")
    ok(True, "la consulta de cardiología tiene buscador por CI y nombre")
    page.fill("#bc-q", CI)
    page.click("#bc-form button[type=submit]")
    page.wait_for_selector("#bc-resultado >> text=REGISTRADA")
    ok("QUISPE HUANCA" in page.inner_text("#bc-resultado"), "busca por CI")
    page.fill("#bc-q", "jorge luis quispe huanca")
    page.click("#bc-form button[type=submit]")
    page.wait_for_selector(f"#bc-resultado >> text={CI}")
    ok(True, "busca por nombre completo")
    captura(page, "a02_busqueda_consulta")
    page.fill("#bc-q", "nadie inexistente")
    page.click("#bc-form button[type=submit]")
    page.wait_for_selector("#bc-resultado >> text=No se encontró")
    ok(True, "avisa cuando no hay resultados")
    page.fill("#bc-q", CI)
    page.click("#bc-form button[type=submit]")
    page.click("#bc-resultado button:has-text('VER INFORME')")
    page.wait_for_url("**/informe.html")
    page.wait_for_selector(f"#hoja >> text={CI}")
    ok(True, "VER INFORME abre el informe del paciente buscado")

    for pagina in ["co_altura", "co_aptifi", "co_aptitud", "co_declaracion", "co_electroencefalograma", "co_espirometria",
                   "co_hiscli", "co_oftalmologia", "co_osteomuscular", "co_psicologia"]:
        page.goto(f"{WEB}/{pagina}.html")
        page.wait_for_selector("#busqueda-consulta")
        page.fill("#bc-q", CI)
        page.click("#bc-form button[type=submit]")
        page.wait_for_selector(f"#bc-resultado >> text={CI}")
    ok(True, "las 11 consultas por especialidad tienen el buscador")

    p2 = b.new_context().new_page()
    preparar(p2)
    abrir_sesion(p2, WEB, ENF)
    p2.goto(f"{WEB}/lista_historial.html")
    f2 = p2.locator(f"#listaPacientes tr:has-text('{CI}')")
    f2.wait_for()
    f2.locator(".btn-adjuntos").click()
    p2.wait_for_selector("#adj-filas >> text=radiografia.png")
    ok(p2.locator("#adj-subida").is_visible(), "Enfermería puede subir archivos")
    ok(p2.locator("#adj-filas button:has-text('Eliminar')").count() == 0, "Enfermería no ve el botón Eliminar")
    p2.set_input_files("#adj-archivo", [PDF])
    p2.click("#adj-subir")
    p2.wait_for_selector("#adj-filas >> text=laboratorio.pdf")
    ok(True, "Enfermería sube un PDF")

    b.close()

print("\nERRORES:", errores if errores else "ninguno")
sys.exit(1 if errores else 0)
