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


def llamar(metodo, ruta, datos=None):
    req = urllib.request.Request(API + ruta, method=metodo, data=json.dumps(datos).encode() if datos is not None else None,
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {SESION['token']}"})
    return json.loads(urllib.request.urlopen(req).read())


def ok(cond, msg):
    print(("OK   " if cond else "FALLA") + " " + msg)
    if not cond:
        errores.append(msg)


p = llamar("POST", "/pacientes/", {"nombre": "Rosa", "apellido": "Informe Simulacion", "ci": "5500222"})
ev = llamar("POST", "/evaluaciones/", {"paciente_id": p["id"], "empresa": "Empresa Ficticia Informes", "puesto": "Soldadora", "tipo": "PERIODICO", "fecha": "2026-11-06"})
llamar("POST", "/filiacion/", {"paciente_id": p["id"], "evaluacion_id": ev["id"], "edad": "41", "ciudad": "EL ALTO"})
llamar("POST", "/guardar-cardiologia", {"codigo_paciente": "5500222", "hta": "NO", "diagnostico_recomendaciones": "SOPLO LEVE EN CONTROL"})
llamar("POST", "/guardar-cardiologia", {"codigo_paciente": "5500222", "hta": "SI", "diagnostico_recomendaciones": "SOPLO LEVE EN CONTROL"})
llamar("POST", "/guardar-aptitud", {"codigo_paciente": "5500222", "resultado": "APTO CON RESTRICCIONES", "recomendacion_1": "USO DE PROTECTOR AUDITIVO"})

with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width": 1366, "height": 900}, accept_downloads=True)
    page = ctx.new_page()
    page.route("**/config.js*", lambda r: r.fulfill(status=200, content_type="application/javascript",
                                                     body=open("config.js", encoding="utf-8").read().replace("https://historial-clinico-nube-asa8.onrender.com", API)))
    page.on("pageerror", lambda e: errores.append("JS: " + str(e)))
    abrir_sesion(page, WEB, SESION)

    page.goto(f"{WEB}/semaforo.html")
    page.wait_for_selector("text=INFORME SIMULACION ROSA")
    page.click("#filas tr:has-text('ROSA') >> text=REPORTE")
    page.wait_for_url("**/informe.html")
    page.wait_for_selector(".hoja .cabecera")
    hoja = lambda: page.inner_text("#hoja")
    ok("INFORME SIMULACION" in hoja() and "5500222" in hoja() and "EMPRESA FICTICIA INFORMES" in hoja(), "informe abre con los datos del trabajador y la evaluación")
    ok("Cardiología".upper() in hoja().upper() and "SOPLO LEVE EN CONTROL" in hoja(), "incluye la ficha de cardiología registrada")
    ok(page.locator("label.vacia").count() == 10, "las 10 fichas sin registrar aparecen marcadas como (sin registrar)")
    ok("Ficha no registrada" not in hoja(), "por defecto solo se incluyen las fichas registradas")
    ok("Registrada:" in hoja() and "MARÍA ELENA CONDARCO" in hoja(), "cada ficha muestra fecha y profesional")
    if CAPTURAS:
        page.screenshot(path=os.path.join(CAPTURAS, "16_informe_seleccion.png"), full_page=True)
        page.pdf(path=os.path.join(CAPTURAS, "evidencia_informe_clinico.pdf"), format="A4", print_background=True)

    page.uncheck(".casilla[value=cardiologia]")
    ok("SOPLO LEVE EN CONTROL" not in hoja(), "desmarcar cardiología la quita del informe")
    page.click("text=Ninguno")
    ok("Declaración jurada" not in hoja() and "Aptitud ocupacional".upper() not in hoja().upper(), "Ninguno deja solo cabecera y firma")
    page.click("text=Marcar todo")
    ok("Ficha no registrada en esta evaluación" in hoja(), "Marcar todo incluye también las fichas pendientes")
    page.check("#incluir-historial")
    ok("Historial de modificaciones".upper() in hoja().upper() and "Hta" in hoja(), "el historial muestra el cambio de HTA")
    fila = page.locator("table.cambios tr:has-text('Hta')").inner_text()
    ok("NO" in fila and "SI" in fila and "MARÍA ELENA" in fila, "el cambio muestra valor anterior, nuevo y usuario")
    page.uncheck("#omitir-vacios")
    ok(hoja().count("—") > 20, "desmarcar 'omitir vacíos' muestra todos los campos")

    page.check('input[name=plantilla][value=certificado]')
    ok("CERTIFICADO DE APTITUD" in hoja() and "APTO CON RESTRICCIONES" in hoja(), "certificado muestra la conclusión de aptitud")
    ok("SOPLO" not in hoja() and "PROTECTOR AUDITIVO" not in hoja() and "EL ALTO" not in hoja(), "certificado no muestra información clínica ni personal adicional")
    if CAPTURAS:
        page.screenshot(path=os.path.join(CAPTURAS, "17_certificado.png"), full_page=True)
        page.pdf(path=os.path.join(CAPTURAS, "evidencia_certificado.pdf"), format="A4", print_background=True)

    page.goto(f"{WEB}/index.html")
    page.wait_for_selector("text=Descargar respaldo")
    with page.expect_download() as d:
        page.click("text=Descargar respaldo")
    ruta = d.value.path()
    datos = json.load(open(ruta, encoding="utf-8"))
    ok(datos["sistema"] == "HC NUBE OHS" and any(x["ci"] == "5500222" for x in datos["tablas"]["pacientes"]), "el portal descarga un respaldo con los datos")
    b.close()

print("\nERRORES:", errores if errores else "ninguno")
sys.exit(1 if errores else 0)
