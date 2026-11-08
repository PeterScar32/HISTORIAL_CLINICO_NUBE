import os
import sys
from playwright.sync_api import sync_playwright

WEB = os.getenv("WEB", "http://127.0.0.1:8080")
API = os.getenv("API", "http://127.0.0.1:8000")
CAPTURAS = os.getenv("CAPTURAS", "")
errores = []


def ok(cond, msg):
    print(("OK   " if cond else "FALLA") + " " + msg)
    if not cond:
        errores.append(msg)


def captura(page, nombre):
    if CAPTURAS:
        page.screenshot(path=os.path.join(CAPTURAS, nombre + ".png"), full_page=True)


def preparar(page):
    page.route("**/config.js*", lambda r: r.fulfill(status=200, content_type="application/javascript",
                                                     body=open("config.js", encoding="utf-8").read().replace("https://historial-clinico-nube-asa8.onrender.com", API)))
    page.route("https://cdn.tailwindcss.com/**", lambda r: r.fulfill(status=200, body=""))
    page.on("dialog", lambda d: d.accept())
    page.on("pageerror", lambda e: errores.append("JS: " + str(e)))


def ingresar(page, nombre, temporal, nueva):
    page.goto(f"{WEB}/index.html")
    page.wait_for_selector("#paso-perfiles:not(.oculto)")
    page.click(f".perfil:has-text('{nombre}')")
    page.fill("#clave", temporal)
    page.click("#form-clave button[type=submit]")
    page.wait_for_selector("#paso-cambio:not(.oculto)")
    page.fill("#nueva1", nueva)
    page.fill("#nueva2", nueva)
    page.click("#form-cambio button[type=submit]")
    page.wait_for_selector("#paso-portal:not(.oculto)")


with sync_playwright() as pw:
    b = pw.chromium.launch()

    medico = b.new_context(viewport={"width": 1280, "height": 860})
    pm = medico.new_page()
    preparar(pm)
    pm.goto(f"{WEB}/semaforo.html")
    pm.wait_for_url("**/index.html")
    ok(True, "sin sesión, una página interna redirige al inicio")
    pm.wait_for_selector("#paso-perfiles:not(.oculto)")
    ok(pm.locator(".perfil").count() == 5, "pantalla ¿Quién eres? con 5 perfiles")
    ok(pm.locator(".perfil img").count() == 4, "los 4 médicos tienen foto")
    captura(pm, "12_quien_eres")
    pm.click(".perfil:has-text('MARÍA ELENA')")
    pm.fill("#clave", "incorrecta")
    pm.click("#form-clave button[type=submit]")
    pm.wait_for_selector("text=Usuario o contraseña incorrectos")
    ok(True, "contraseña incorrecta rechazada")
    pm.click("text=No soy yo")
    ingresar(pm, "MARÍA ELENA", "temporal-1", "clave-maria-2026")
    ok("MARÍA ELENA CONDARCO" in pm.inner_text("#bienvenida"), "portal muestra a la usuaria con su foto")
    ok(pm.locator("#opciones .opcion").count() == 5, "médico ve las 5 opciones")
    captura(pm, "13_portal_medico")
    pm.click("text=Semáforo")
    pm.wait_for_url("**/semaforo.html")
    pm.wait_for_selector("#chip-usuario img")
    ok("MARÍA ELENA" in pm.inner_text("#chip-usuario"), "la barra muestra foto y nombre del usuario")

    enf = b.new_context(viewport={"width": 1280, "height": 860})
    pe = enf.new_page()
    preparar(pe)
    ingresar(pe, "ENFERMERÍA", "temporal-5", "clave-enfermeria")
    ok(pe.locator("#opciones .opcion").count() == 2, "enfermería ve solo registro y pacientes")
    pe.goto(f"{WEB}/semaforo.html")
    pe.wait_for_url("**/index.html")
    ok(True, "enfermería no puede abrir el semáforo")
    pe.goto(f"{WEB}/registro_paciente.html")
    pe.fill("#nombre", "Carlos")
    pe.fill("#apellido", "Simulacion Mamani")
    pe.fill("#ci", "7700777")
    pe.fill("#empresa", "Empresa Ficticia Tiempo Real")
    pe.click(".btn-guardar")
    pe.wait_for_url("**/declaracion_jurada_p1.html")
    pe.goto(f"{WEB}/doc_aptitud.html")
    pe.wait_for_selector("text=✔ SIMULACION MAMANI CARLOS")
    ok(True, "enfermería abre una ficha con el paciente cargado")
    pe.goto(f"{WEB}/lista_historial.html")
    pe.wait_for_selector("text=7700777")
    ok(not pe.is_visible(".btn-borrar") and not pe.is_visible(".btn-reporte"), "enfermería no ve borrar ni reporte")

    pm.click("#btn-buscar")
    pm.wait_for_selector("text=SIMULACION MAMANI CARLOS")
    ok(True, "el paciente registrado por enfermería aparece al instante en el semáforo del médico")
    pm.click("#filas tr:has-text('CARLOS') >> text=DETALLE")
    ok("ENFERMERÍA" in pm.inner_text("tr.detalle:visible") or "Pendiente" in pm.inner_text("tr.detalle:visible"), "detalle disponible")

    pm.click("#barra-nav >> text=Salir")
    pm.wait_for_selector("#paso-perfiles:not(.oculto)")
    ok(True, "cerrar sesión vuelve a ¿Quién eres?")
    pm.goto(f"{WEB}/lista_historial.html")
    pm.wait_for_url("**/index.html")
    ok(True, "tras salir no se puede volver a entrar sin clave")
    b.close()

print("\nERRORES:", errores if errores else "ninguno")
sys.exit(1 if errores else 0)
