import os
import sys
from playwright.sync_api import sync_playwright

WEB = os.getenv("WEB", "http://127.0.0.1:8080")
API = os.getenv("API", "http://127.0.0.1:8000")
CAPTURAS = os.getenv("CAPTURAS", "")
ci = "9999123"
errores = []
dialogos = []


def captura(page, nombre):
    if CAPTURAS:
        page.screenshot(path=os.path.join(CAPTURAS, nombre + ".png"), full_page=True)


def ok(cond, msg):
    print(("OK   " if cond else "FALLA") + " " + msg)
    if not cond:
        errores.append(msg)


with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page()

    def config(route):
        body = open("config.js", encoding="utf-8").read().replace("https://historial-clinico-nube-asa8.onrender.com", API)
        route.fulfill(status=200, content_type="application/javascript", body=body)

    page.route("**/config.js*", config)
    page.route("https://cdn.tailwindcss.com/**", lambda r: r.fulfill(status=200, body=""))

    def on_dialog(d):
        dialogos.append(d.message)
        d.accept()

    page.on("dialog", on_dialog)
    page.on("pageerror", lambda e: errores.append("JS: " + str(e)))

    page.goto(f"{WEB}/registro_paciente.html")
    page.fill("#nombre", "Jorge")
    page.fill("#apellido", "Quispe Huanca")
    page.fill("#ci", ci)
    ok(page.inner_text("#display-codigo") == ci, "el código mostrado es el CI")
    page.fill("#empresa", "Empresa Ficticia SA")
    page.fill("#puesto", "Operario")
    page.fill("#fecha_eval", "2026-11-05")
    page.click(".btn-guardar")
    page.wait_for_url("**/declaracion_jurada_p1.html")
    page.wait_for_function("document.getElementById('p_ci').innerText.trim() === '%s'" % ci)
    ok(True, "P1 muestra el paciente registrado")
    page.fill("#edad", "34")
    page.fill("#fecha_nac", "1991-05-10")
    page.fill("#ciudad", "LA PAZ")
    page.fill("#profesion", "OPERARIO")
    captura(page, "01_p1")
    page.click("#btnNext")
    page.wait_for_url("**/declaracion_jurada_p2.html")
    page.wait_for_function("document.getElementById('b_codigo').innerText.trim() === '%s'" % ci)
    page.select_option("#s_vista", "SI")
    page.fill("#d_vista", "USA LENTES")
    captura(page, "02_p2")
    page.click("#btnS")
    page.wait_for_url("**/declaracion_jurada_p3.html")
    page.wait_for_function("document.getElementById('b_paciente').innerText.includes('QUISPE')")
    ok(True, "P3 muestra el paciente (ya no queda en CARGANDO)")
    page.select_option("#fuma", "SI")
    page.fill("#fuma_cantidad", "2 por semana")
    page.fill("#grupo_sanguineo", "ORH+")
    captura(page, "03_p3")
    page.click("#btnG")
    page.wait_for_url("**/lista_historial.html")
    page.wait_for_selector(f"text={ci}")
    ok(page.locator("#listaPacientes tr").count() == 1, "la lista muestra un solo paciente")
    captura(page, "04_lista")

    page.click(".btn-reporte")
    page.wait_for_url("**/generar_reporte.html")
    page.wait_for_selector("text=USA LENTES")
    texto = page.inner_text("body")
    ok("LA PAZ" in texto, "reporte muestra P1")
    ok("USA LENTES" in texto, "reporte muestra P2")
    ok("2 POR SEMANA" in texto and "ORH+" in texto, "reporte muestra P3")
    captura(page, "05_reporte")

    page.goto(f"{WEB}/doc_cardiologia.html")
    page.wait_for_function("document.getElementById('codigo_paciente').value === '%s'" % ci)
    page.wait_for_selector("text=✔ QUISPE HUANCA JORGE")
    ok(True, "la ficha de cardiología se abre con el CI y el nombre del paciente")
    page.check("#hta_si")
    page.fill("#diagnostico_recomendaciones", "SOPLO CARDIACO")
    captura(page, "06_cardiologia")
    page.click(".btn-guardar")
    page.wait_for_timeout(1500)
    ok(any("GUARDADO" in m for m in dialogos), "ficha de cardiología guardada")

    page.goto(f"{WEB}/doc_oftalmologia.html")
    page.wait_for_function("document.getElementById('paciente_id').value === '%s'" % ci)
    page.check("input[name=lentes][value=SI]")
    page.evaluate("document.getElementById('oftalmoForm').requestSubmit()")
    page.wait_for_timeout(1500)
    page.goto(f"{WEB}/co_oftalmologia.html")
    page.select_option("#patologiaSelect", "lentes")
    page.evaluate("filtrar()")
    page.wait_for_selector(f"#listaPacientes >> text={ci}")
    ok(True, "consulta oftalmología: USA LENTES devuelve al paciente")
    captura(page, "07_consulta_oftalmo")

    page.goto(f"{WEB}/registro_paciente.html")
    page.fill("#ci", ci)
    page.dispatch_event("#ci", "change")
    page.wait_for_selector("#aviso-existente:visible")
    ok("YA ESTÁ REGISTRADO" in page.inner_text("#aviso-existente"), "registro avisa que el CI ya existe")
    ok(page.input_value("#nombre") == "JORGE", "registro completa el nombre del paciente existente")
    page.select_option("#tipo_eval", "PERIODICO")
    page.fill("#fecha_eval", "2027-06-10")
    page.click(".btn-guardar")
    page.wait_for_url("**/declaracion_jurada_p1.html")
    page.wait_for_function("document.getElementById('edad').value === '34'")
    ok(True, "nueva evaluación: P1 trae los datos de la evaluación anterior")
    page.fill("#edad", "35")
    page.click("#btnNext")
    page.wait_for_url("**/declaracion_jurada_p2.html")
    page.wait_for_function("document.getElementById('b_codigo').innerText.trim() === '%s'" % ci)
    ok(page.input_value("#s_vista") != "SI", "nueva evaluación: P2 empieza vacía")
    page.click("#btnS")
    page.wait_for_url("**/declaracion_jurada_p3.html")
    page.wait_for_function("document.getElementById('b_paciente').innerText.includes('QUISPE')")
    page.click("#btnG")
    page.wait_for_url("**/lista_historial.html")
    page.wait_for_selector(f"text={ci}")
    ok(page.locator("#listaPacientes tr").count() == 1, "sigue habiendo un solo paciente")
    page.click(".btn-reporte")
    page.wait_for_url("**/generar_reporte.html")
    page.wait_for_function("document.querySelectorAll('#sel_evaluacion option').length === 2")
    ok(True, "el reporte ofrece las dos evaluaciones")
    page.wait_for_function("document.getElementById('main_info').innerText.includes('SEMÁFORO')")
    ok("2027-06-10" in page.inner_text("#main_info") and "USA LENTES" not in page.inner_text("body"), "reporte muestra la evaluación nueva")
    page.select_option("#sel_evaluacion", index=1)
    page.wait_for_selector("text=USA LENTES")
    ok("2026-11-05" in page.inner_text("#main_info") and "EMPRESA FICTICIA SA" in page.inner_text("#main_info"), "la evaluación anterior se conserva intacta")
    captura(page, "09_reporte_evaluacion_anterior")

    page.goto(f"{WEB}/registro_personal.html")
    page.click("#btn-doc")
    page.fill("#ci_val", "D-777")
    page.fill("#nombre_val", "Ana")
    page.fill("#paterno_val", "Lopez")
    page.fill("#especialidad_val", "Cardiologia")
    page.click("#form-registro button[type=submit]")
    page.wait_for_url("**/lista_personal.html")
    page.wait_for_selector("text=D-777")
    ok(True, "personal médico aparece en la lista tras registrarlo")
    captura(page, "08_personal")

    page.goto(f"{WEB}/lista_historial.html")
    page.wait_for_selector(f"text={ci}")
    page.click(".btn-borrar")
    page.wait_for_selector("text=NO HAY REGISTROS DISPONIBLES")
    ok(True, "borrar paciente funciona")

    b.close()

print("\nERRORES:", errores if errores else "ninguno")
sys.exit(1 if errores else 0)
