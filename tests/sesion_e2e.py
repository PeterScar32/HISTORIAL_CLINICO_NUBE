import json
import os
import urllib.error
import urllib.request

API = os.getenv("API", "http://127.0.0.1:8000")


def _post(ruta, datos, token=None):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API + ruta, data=json.dumps(datos).encode(), headers=h)
    return json.loads(urllib.request.urlopen(req).read())


def obtener_sesion(usuario, temporal, nueva):
    try:
        d = _post("/auth/login", {"usuario": usuario, "clave": nueva})
    except urllib.error.HTTPError:
        d = _post("/auth/login", {"usuario": usuario, "clave": temporal})
        d = _post("/auth/cambiar-clave", {"actual": temporal, "nueva": nueva}, d["token"])
    return d


def abrir_sesion(page, web, d):
    page.goto(f"{web}/index.html")
    page.evaluate("([t, u]) => { localStorage.setItem('ohs_token', t); localStorage.setItem('ohs_usuario', JSON.stringify(u)); }",
                  [d["token"], d["usuario"]])
