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
CI = "9999543"
errores = []
SESION = obtener_sesion("mecondarco", "temporal-1", "clave-medico-1")


def ok(cond, msg):
    print(("OK   " if cond else "FALLA") + " " + msg)
    if not cond:
        errores.append(msg)


def captura(page, nombre):
    if CAPTURAS:
        page.screenshot(path=os.path.join(CAPTURAS, nombre + ".png"), full_page=True)


def api_get(ruta):
    req = urllib.request.Request(API + ruta, headers={"Authorization": "Bearer " + SESION["token"]})
    return json.loads(urllib.request.urlopen(req).read())


with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page()

    def config(route):
        body = open("config.js", encoding="utf-8").read().replace("https://historial-clinico-nube-asa8.onrender.com", API)
        route.fulfill(status=200, content_type="application/javascript", body=body)

    page.route("**/config.js*", config)
    page.route("https://cdn.tailwindcss.com/**", lambda r: r.fulfill(status=200, body=""))
    page.on("dialog", lambda d: d.accept())
    page.on("pageerror", lambda e: errores.append("JS: " + str(e)))
    abrir_sesion(page, WEB, SESION)

    page.goto(f"{WEB}/registro_paciente.html")
    page.fill("#nombre", "María Elena")
    page.fill("#apellido", "Ficticia Prueba")
    page.fill("#ci", CI)
    page.fill("#empresa", "OHS Salud Ficticia")
    page.fill("#puesto", "Gerente técnico")
    page.select_option("#tipo_eval", "PREOCUPACIONAL")
    page.fill("#fecha_eval", "2026-11-10")
    page.click(".btn-guardar")
    page.wait_for_url("**/declaracion_jurada_p1.html")
    page.wait_for_function("document.getElementById('p_ci').innerText.trim() === '%s'" % CI)
    page.fill("#edad", "45")
    page.select_option("#sexo", "FEMENINO")
    page.fill("#fecha_nac", "1981-03-02")
    page.fill("#ciudad", "LA PAZ")
    page.fill("#profesion", "MÉDICO")
    page.click("#btnNext")
    page.wait_for_url("**/declaracion_jurada_p2.html")
    page.wait_for_function("document.getElementById('b_codigo').innerText.trim() === '%s'" % CI)
    page.click("#btnS")
    page.wait_for_url("**/declaracion_jurada_p3.html")
    page.wait_for_function("document.getElementById('b_paciente').innerText.includes('FICTICIA')")
    ok(page.locator("#labFilas tr").count() == 1, "P3 empieza con una fila de historia laboral")
    filas = page.locator("#labFilas tr")
    filas.nth(0).locator(".lab-edad").fill("24")
    filas.nth(0).locator(".lab-empresa").fill("Samco")
    filas.nth(0).locator(".lab-cargo").fill("Encargado SG")
    filas.nth(0).locator(".lab-tiempo").fill("1 año")
    filas.nth(0).locator(".lab-riesgos").fill("Ruido")
    filas.nth(0).locator(".lab-epp").select_option("SI")
    page.click("#btnAgregarTrabajo")
    page.click("#btnAgregarTrabajo")
    ok(page.locator("#labFilas tr").count() == 3, "«Agregar otro trabajo» añade filas")
    filas.nth(1).locator(".lab-edad").fill("30")
    filas.nth(1).locator(".lab-empresa").fill("Minera Ficticia")
    filas.nth(1).locator(".lab-cargo").fill("Supervisora")
    filas.nth(1).locator(".lab-tiempo").fill("5 años")
    filas.nth(2).locator(".quitar").click()
    ok(page.locator("#labFilas tr").count() == 2, "✕ quita una fila")
    page.locator("#riesgosCheck input[value='RUIDO']").check()
    captura(page, "c01_p3_varios_trabajos")
    page.click("#btnG")
    page.wait_for_url("**/lista_historial.html")
    pid = api_get(f"/pacientes/buscar/{CI}")["id"]
    hl = (api_get(f"/fichas/habitos/{pid}")["ficha"] or {}).get("historia_laboral", "")
    ok(hl.count("\n") == 1 and "SAMCO" in hl and "MINERA FICTICIA" in hl, "se guardan los dos trabajos")

    page.goto(f"{WEB}/lista_historial.html")
    page.locator(f"tr:has-text('{CI}') .btn-editar:not(.btn-identidad)").click()
    page.wait_for_url("**/declaracion_jurada_p1.html")
    page.goto(f"{WEB}/declaracion_jurada_p3.html")
    page.wait_for_function("document.querySelectorAll('#labFilas tr').length === 2")
    ok(page.locator("#labFilas tr").nth(1).locator(".lab-empresa").input_value() == "MINERA FICTICIA", "al editar P3 se recuperan los trabajos")
    ok(page.locator("#riesgosCheck input[value='RUIDO']").is_checked(), "al editar P3 se recuperan los riesgos marcados")

    page.goto(f"{WEB}/lista_historial.html")
    page.locator(f"tr:has-text('{CI}')").click()

    page.goto(f"{WEB}/doc_aptitud.html")
    page.wait_for_selector("text=se completaron desde su registro")
    page.wait_for_function("document.getElementById('nombres').value !== ''")
    v = lambda i: page.input_value("#" + i)
    ok((v("ape_pat"), v("ape_mat"), v("nombres")) == ("FICTICIA", "PRUEBA", "MARÍA ELENA"), "certificado: apellidos y nombres desde el registro")
    ok(v("edad") == "45" and v("genero") == "FEMENINO" and v("doc_id") == CI, "certificado: edad, género y CI")
    ok(v("puesto") == "GERENTE TÉCNICO" and v("razon_social") == "OHS SALUD FICTICIA", "certificado: puesto y empresa")
    ok((v("dia"), v("mes"), v("anio")) == ("10", "11", "2026"), "certificado: fecha de la evaluación")
    ok(page.locator("input[name=tipo][value=PREOCUPACIONAL]").is_checked(), "certificado: tipo de evaluación marcado")
    captura(page, "c02_aptitud_autocompletada")

    page.goto(f"{WEB}/doc_hiscli.html")
    page.wait_for_function("document.getElementById('carnet_identidad').value !== ''")
    ok((v("empresa"), v("nombre"), v("carnet_identidad")) == ("OHS SALUD FICTICIA", "FICTICIA PRUEBA MARÍA ELENA", CI), "historia clínica: empresa, nombre y CI")
    ok(v("edad") == "45" and v("sexo") == "FEMENINO" and v("puesto_cargo") == "GERENTE TÉCNICO" and v("fecha_atencion") == "2026-11-10", "historia clínica: edad, sexo, puesto y fecha")
    ok(page.is_checked("#tipo_pre"), "historia clínica: tipo de control marcado")

    page.goto(f"{WEB}/doc_osteomuscular.html")
    page.wait_for_function("document.getElementById('ci').value !== ''")
    ok(v("nombre_completo") == "FICTICIA PRUEBA MARÍA ELENA" and v("edad") == "45" and page.is_checked("#sexo_f"), "osteomuscular: nombre, edad y sexo")

    page.goto(f"{WEB}/doc_aptitud.html")
    page.wait_for_function("document.getElementById('nombres').value !== ''")
    page.fill("#puesto", "Otro puesto escrito a mano")
    page.locator("input[name=resultado][value=APTO]").first.check()
    page.click("button[onclick='guardarDatos()']")
    page.wait_for_timeout(1500)
    page.goto(f"{WEB}/doc_aptitud.html")
    page.wait_for_selector("text=Esta ficha ya está registrada")
    page.wait_for_timeout(800)
    ok(v("puesto") == "OTRO PUESTO ESCRITO A MANO" or v("puesto").upper() == "OTRO PUESTO ESCRITO A MANO", "una ficha guardada conserva lo escrito y no se sobrescribe")

    page.goto(f"{WEB}/lista_historial.html")
    page.locator(f"tr:has-text('{CI}') .btn-reporte").click()
    page.wait_for_url("**/informe.html")
    page.wait_for_selector("#hoja .datos")
    texto = page.inner_text("body")
    ok("Occupational Health Services" not in texto, "el informe ya no dice «Occupational Health Services»")
    ok("SAMCO" in texto.upper() and "MINERA FICTICIA" in texto.upper(), "el informe muestra los trabajos anteriores")
    b.close()

print("\nERRORES:", errores if errores else "ninguno")
sys.exit(1 if errores else 0)
