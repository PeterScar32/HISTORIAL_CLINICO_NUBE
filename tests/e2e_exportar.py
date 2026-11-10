import io
import os
import sys
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(__file__))
from sesion_e2e import obtener_sesion, abrir_sesion, _post

WEB = os.getenv("WEB", "http://127.0.0.1:8080")
API = os.getenv("API", "http://127.0.0.1:8000")
CI = "9999432"
errores = []
MEDICO = obtener_sesion("mecondarco", "temporal-1", "clave-medico-1")
ENF = obtener_sesion("enfermeria", "temporal-5", "clave-enf-123")


def ok(cond, msg):
    print(("OK   " if cond else "FALLA") + " " + msg)
    if not cond:
        errores.append(msg)


def preparar(page):
    def config(route):
        body = open("config.js", encoding="utf-8").read().replace("https://historial-clinico-nube-asa8.onrender.com", API)
        route.fulfill(status=200, content_type="application/javascript", body=body)
    page.route("**/config.js*", config)
    page.route("https://cdn.tailwindcss.com/**", lambda r: r.fulfill(status=200, body=""))
    page.on("pageerror", lambda e: errores.append("JS: " + str(e)))


try:
    p = _post("/pacientes/", {"nombre": "Rosa", "apellido": "Mamani Ficticia", "ci": CI}, MEDICO["token"])
    _post("/evaluaciones/", {"paciente_id": p["id"], "tipo": "PERIODICO", "empresa": "EMPRESA FICTICIA SA"}, MEDICO["token"])
except Exception as e:
    errores.append("preparación: " + str(e))

with sync_playwright() as pw:
    b = pw.chromium.launch()
    for sesion_, perfil in ((MEDICO, "médico"), (ENF, "Enfermería")):
        ctx = b.new_context(accept_downloads=True)
        page = ctx.new_page()
        preparar(page)
        abrir_sesion(page, WEB, sesion_)
        page.goto(f"{WEB}/index.html")
        page.wait_for_selector("#btn-excel")
        ok(page.is_visible("#btn-excel"), f"el portal ({perfil}) muestra «Exportar datos a Excel»")
        with page.expect_download() as dl:
            page.click("#btn-excel")
        ok(dl.value.suggested_filename.endswith(".xlsx"), f"{perfil}: se descarga un archivo .xlsx")
        wb = load_workbook(io.BytesIO(open(dl.value.path(), "rb").read()))
        ok("Pacientes" in wb.sheetnames and any(r[0] == CI for r in wb["Pacientes"].values), f"{perfil}: el Excel contiene al paciente")
        page.wait_for_selector("text=Excel descargado")
        ctx.close()
    b.close()

print("\nERRORES:", errores if errores else "ninguno")
sys.exit(1 if errores else 0)
