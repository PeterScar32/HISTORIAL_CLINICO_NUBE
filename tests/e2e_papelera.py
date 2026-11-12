import os
import sys
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(__file__))
from sesion_e2e import obtener_sesion, abrir_sesion, _post

WEB = os.getenv("WEB", "http://127.0.0.1:8080")
API = os.getenv("API", "http://127.0.0.1:8000")
CAPTURAS = os.getenv("CAPTURAS", "")
CI = "9999561"
NOMBRE = "JULIA PAPELERA " + "".join(chr(65 + int(c)) for c in str(__import__("time").time_ns())[-6:])
errores = []
SESION = obtener_sesion("mecondarco", "temporal-1", "clave-medico-1")


def ok(cond, msg):
    print(("OK   " if cond else "FALLA") + " " + msg)
    if not cond:
        errores.append(msg)


def captura(page, nombre):
    if CAPTURAS:
        page.screenshot(path=os.path.join(CAPTURAS, nombre + ".png"))


def panel_a_la_derecha(page):
    caja = page.locator(".pl-panel").bounding_box()
    ancho = page.viewport_size["width"]
    return caja and abs(caja["x"] + caja["width"] - ancho) < 2 and caja["y"] == 0 and caja["x"] > ancho / 3


with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 1366, "height": 768})

    def config(route):
        body = open("config.js", encoding="utf-8").read().replace("https://historial-clinico-nube-asa8.onrender.com", API)
        route.fulfill(status=200, content_type="application/javascript", body=body)

    page.route("**/config.js*", config)
    page.route("https://cdn.tailwindcss.com/**", lambda r: r.fulfill(status=200, body=""))
    dialogos = []
    page.on("dialog", lambda d: (dialogos.append(d.message), d.accept(CI) if d.type == "prompt" else d.accept()))
    page.on("pageerror", lambda e: errores.append("JS: " + str(e)))
    abrir_sesion(page, WEB, SESION)

    p = _post("/pacientes/", {"nombre": "Pedro", "apellido": "Papelera Ficticio", "ci": CI}, SESION["token"])
    _post("/evaluaciones/", {"paciente_id": p["id"], "tipo": "PERIODICO", "empresa": "Empresa Ficticia"}, SESION["token"])
    page.goto(f"{WEB}/lista_historial.html")
    page.locator(f"tr:has-text('{CI}') .btn-borrar").click()
    page.wait_for_load_state("load")
    page.wait_for_selector("#listaPacientes tr")
    page.wait_for_selector(f"#listaPacientes tr:has-text('{CI}')", state="detached")
    page.click(".btn-papelera")
    page.wait_for_selector(f"#filasPapelera >> text=PAPELERA FICTICIO PEDRO")
    page.wait_for_timeout(400)
    ok(panel_a_la_derecha(page), "la papelera de pacientes se abre como panel a la derecha, sin bajar la página")
    ok(page.evaluate("window.scrollY") == 0, "abrir la papelera no desplaza la página hacia abajo")
    ok("CI " + CI in page.inner_text(".pl-panel"), "el panel muestra el CI del paciente eliminado")
    captura(page, "p01_papelera_pacientes")
    page.keyboard.press("Escape")
    page.wait_for_selector(".pl-panel", state="detached")
    ok(True, "Escape cierra el panel")
    page.click(".btn-papelera")
    page.locator("#filasPapelera .pl-item:has-text('PAPELERA FICTICIO PEDRO') .pl-restaurar").first.click()
    page.wait_for_selector(f"#listaPacientes >> text={CI}", timeout=15000)
    ok(True, "el paciente se restaura desde el panel")

    u = _post("/auth/usuarios", {"nombre": NOMBRE, "rol": "ESPECIALISTA", "especialidad": "Cardiología", "fichas_permitidas": ["cardiologia"]}, SESION["token"])
    page.goto(f"{WEB}/lista_personal.html")
    fila = page.locator(f"#tabla tr:has-text('{NOMBRE}')")
    fila.wait_for()
    captura(page, "p02_personal_boton_eliminar")
    fila.locator(".btn-eliminar-personal").click()
    page.wait_for_selector(f"#tabla tr:has-text('{NOMBRE}')", state="detached")
    ok(any("papelera" in m for m in dialogos), "eliminar personal pide confirmación")
    ok(page.locator(".btn-eliminar-personal").count() >= 1 and page.locator("#tabla tr:has-text('MARÍA ELENA CONDARCO') .btn-eliminar-personal").count() == 0,
       "no se ofrece eliminar al propio usuario")
    page.click("#btn-papelera-personal")
    page.wait_for_selector(f"#filasPapelera >> text={NOMBRE}")
    page.wait_for_timeout(400)
    ok(panel_a_la_derecha(page), "la papelera de personal se abre como panel a la derecha")
    ok(u["usuario"] in page.inner_text(".pl-panel") and "ESPECIALISTA" in page.inner_text(".pl-panel"), "muestra usuario y rol del personal eliminado")
    captura(page, "p03_papelera_personal")
    page.locator(f"#filasPapelera .pl-item:has-text('{NOMBRE}') .pl-restaurar").click()
    page.wait_for_selector(f"#filasPapelera .pl-restaurado >> text={NOMBRE}")
    ok(page.locator(f"#tabla tr:has-text('{NOMBRE}')").count() == 1, "el personal restaurado vuelve a la lista")
    captura(page, "p04_personal_restaurado")
    page.click(".pl-cerrar")
    page.wait_for_selector(".pl-panel", state="detached")

    m = b.new_page(viewport={"width": 390, "height": 844})
    m.route("**/config.js*", config)
    m.route("https://cdn.tailwindcss.com/**", lambda r: r.fulfill(status=200, body=""))
    abrir_sesion(m, WEB, SESION)
    m.goto(f"{WEB}/lista_historial.html")
    m.click(".btn-papelera")
    m.wait_for_selector("#filasPapelera")
    m.wait_for_timeout(400)
    c = m.locator(".pl-panel").bounding_box()
    ok(c["x"] >= 0 and c["width"] <= 390, "en el celular el panel ocupa el ancho de la pantalla")
    captura(m, "p05_papelera_celular")
    b.close()

print("\nERRORES:", errores if errores else "ninguno")
sys.exit(1 if errores else 0)
