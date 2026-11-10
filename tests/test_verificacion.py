"""Casos de verificación de la revisión 2 (integridad, autoría, informes, semáforo y seguridad).

Cada prueba lleva un identificador Vxx que se corresponde con la matriz de pruebas y correcciones.
Todos los datos son ficticios.
"""
import json
import time

from tests.conftest import iniciar
from api import auth


def nuevo(client, ci, nombre="PRUEBA", apellido="VERIFICACION", **ev):
    p = client.post("/pacientes/", json={"nombre": nombre, "apellido": apellido, "ci": ci}).json()
    e = client.post("/evaluaciones/", json={"paciente_id": p["id"], **ev}).json()
    return p, e


def color(client, ev_id):
    return client.get(f"/semaforo/evaluacion/{ev_id}").json()


def test_V01_precedencia_entre_conclusiones(client):
    casos = [
        ("V01A", {"aptitud": "APTO", "osteo": "NO APTO"}, "ROJO"),
        ("V01B", {"aptitud": "NO APTO", "osteo": "APTO"}, "ROJO"),
        ("V01C", {"aptitud": "APTO", "osteo": "APTO CON RESTRICCIONES"}, "AMARILLO"),
        ("V01D", {"aptitud": "APTO CON RESTRICCIONES", "osteo": "NO_APTO_TEMPORAL"}, "ROJO"),
        ("V01E", {"aptitud": "APTO", "osteo": "APTO"}, "VERDE"),
        ("V01F", {"aptitud": "PENDIENTE DE ESTUDIOS"}, "AMARILLO"),
        ("V01G", {}, "GRIS"),
    ]
    for ci, c, esperado in casos:
        _, e = nuevo(client, ci)
        if "aptitud" in c:
            client.post("/guardar-aptitud", json={"codigo_paciente": ci, "resultado": c["aptitud"]})
        if "osteo" in c:
            client.post("/guardar-osteomuscular", json={"codigo_paciente": ci, "concepto_aptitud": c["osteo"]})
        assert color(client, e["id"])["color"] == esperado, ci


def test_V02_incompleta_no_es_favorable_e_indicadores_independientes(client):
    _, e1 = nuevo(client, "V02A")
    for ruta, d in [("/filiacion/", {"edad": "30"}), ("/p2/", {"vista": "NORMAL"}), ("/p3/", {"fuma": "NO"})]:
        client.post(ruta, json={"paciente_id": e1["paciente_id"], **d})
    client.post("/guardar-historial-clinico", json={"codigo_paciente": "V02A", "tipo_control": "PERIODICO"})
    s = color(client, e1["id"])
    assert s["color"] == "GRIS" and s["completitud"]["estado"] == "INCOMPLETA" and s["completitud"]["faltantes"] == ["Aptitud médico ocupacional"]

    client.post("/guardar-aptitud", json={"codigo_paciente": "V02A", "resultado": "NO APTO"})
    s = color(client, e1["id"])
    assert (s["color"], s["completitud"]["estado"]) == ("ROJO", "COMPLETA")

    _, e2 = nuevo(client, "V02B")
    client.post("/guardar-aptitud", json={"codigo_paciente": "V02B", "resultado": "APTO"})
    s = color(client, e2["id"])
    assert (s["color"], s["completitud"]["estado"]) == ("VERDE", "INCOMPLETA")


def test_V03_modificar_una_ficha_actualiza_semaforo_detalle_e_informe(client):
    p, e = nuevo(client, "V03")
    client.post("/guardar-aptitud", json={"codigo_paciente": "V03", "resultado": "APTO"})
    antes = color(client, e["id"])
    creada = next(f for f in antes["fichas"] if f["clave"] == "aptitud")
    time.sleep(1.1)
    client.post("/guardar-aptitud", json={"codigo_paciente": "V03", "resultado": "NO APTO"})
    despues = color(client, e["id"])
    ficha = next(f for f in despues["fichas"] if f["clave"] == "aptitud")
    assert antes["color"] == "VERDE" and despues["color"] == "ROJO"
    assert ficha["conclusiones"][0]["valor"] == "NO APTO"
    assert ficha["fecha"] == creada["fecha"]
    assert ficha["ultima_modificacion"] and ficha["ultima_modificacion"]["fecha"] > creada["fecha"]
    assert client.get(f"/api/expediente/{p['id']}", params={"evaluacion_id": e["id"]}).json()["fichas"]["aptitud"]["resultado"] == "NO APTO"
    assert client.get("/semaforo", params={"solo_ultima": True}).json()["resumen"]["ROJO"] == 1


def test_V04_ci_identifica_trabajador_y_cada_evaluacion_tiene_id_propio(client):
    a = client.post("/pacientes/", json={"nombre": "ANA", "apellido": "QUISPE", "ci": "4455667 LP"}).json()
    b = client.post("/pacientes/", json={"nombre": "ana", "apellido": "quispe", "ci": " 4455667 lp "}).json()
    assert a["id"] == b["id"] and b["existente"] is True and len(client.get("/pacientes/").json()) == 1
    ids = {client.post("/evaluaciones/", json={"paciente_id": a["id"]}).json()["id"] for _ in range(3)}
    assert len(ids) == 3
    assert [x["ci"] for x in client.get("/pacientes/busqueda", params={"q": "4455"}).json()] == ["4455667 LP"]
    assert [x["ci"] for x in client.get("/pacientes/busqueda", params={"q": "quispe ana"}).json()] == ["4455667 LP"]


def test_V05_editar_una_evaluacion_no_altera_las_anteriores(client):
    p, e1 = nuevo(client, "V05", fecha="2026-05-10")
    client.post("/filiacion/", json={"paciente_id": p["id"], "evaluacion_id": e1["id"], "edad": "40"})
    client.post("/guardar-cardiologia", json={"codigo_paciente": "V05", "hta": "NO"}, headers={"X-Evaluacion": str(e1["id"])})
    e2 = client.post("/evaluaciones/", json={"paciente_id": p["id"], "fecha": "2026-11-10"}).json()
    heredada = client.get(f"/api/paciente-completo/{p['id']}", params={"evaluacion_id": e2["id"]}).json()
    assert heredada["filiacion_heredada"] is True and heredada["filiacion"]["edad"] == "40"
    client.post("/filiacion/", json={"paciente_id": p["id"], "evaluacion_id": e2["id"], "edad": "41"})
    client.post("/guardar-cardiologia", json={"codigo_paciente": "V05", "hta": "SI"}, headers={"X-Evaluacion": str(e2["id"])})
    client.post("/guardar-cardiologia", json={"codigo_paciente": "V05", "hta": "NO"}, headers={"X-Evaluacion": str(e2["id"])})
    x1 = client.get(f"/api/expediente/{p['id']}", params={"evaluacion_id": e1["id"]}).json()
    x2 = client.get(f"/api/expediente/{p['id']}", params={"evaluacion_id": e2["id"]}).json()
    assert (x1["fichas"]["declaracion"]["edad"], x1["fichas"]["cardiologia"]["hta"]) == ("40", "NO")
    assert (x2["fichas"]["declaracion"]["edad"], x2["fichas"]["cardiologia"]["hta"]) == ("41", "NO")
    assert x1["fichas"]["cardiologia"]["id"] != x2["fichas"]["cardiologia"]["id"]
    mods = [a for a in client.get("/auditoria", params={"evaluacion_id": e1["id"]}).json() if a["accion"] == "MODIFICACION"]
    assert mods == []


def test_V06_eliminacion_confirmada_papelera_y_restauracion(client):
    p, e = nuevo(client, "V06")
    client.post("/filiacion/", json={"paciente_id": p["id"], "edad": "33"})
    client.post("/guardar-aptitud", json={"codigo_paciente": "V06", "resultado": "APTO"})
    e2 = client.post("/evaluaciones/", json={"paciente_id": p["id"]}).json()
    client.post("/guardar-aptitud", json={"codigo_paciente": "V06", "resultado": "NO APTO"})
    antes = client.get(f"/api/expediente/{p['id']}", params={"evaluacion_id": e["id"]}).json()

    assert client.delete(f"/api/pacientes/{p['id']}").status_code == 400
    assert client.delete(f"/api/pacientes/{p['id']}", params={"confirmar_ci": "OTRO"}).status_code == 400
    assert client.get(f"/api/expediente/{p['id']}").status_code == 200
    assert client.delete(f"/api/pacientes/{p['id']}", params={"confirmar_ci": "v06"}).status_code == 200
    assert client.get(f"/api/expediente/{p['id']}").status_code == 404
    pap = client.get("/papelera").json()
    assert pap[0]["ci"] == "V06" and pap[0]["evaluaciones"] == 2

    assert client.post(f"/papelera/{pap[0]['id']}/restaurar").json()["restaurado"] is True
    despues = client.get(f"/api/expediente/{p['id']}", params={"evaluacion_id": e["id"]}).json()
    assert despues["fichas"]["aptitud"] == antes["fichas"]["aptitud"]
    assert despues["fichas"]["declaracion"]["edad"] == "33"
    assert client.get(f"/api/expediente/{p['id']}", params={"evaluacion_id": e2["id"]}).json()["fichas"]["aptitud"]["resultado"] == "NO APTO"
    assert client.post(f"/papelera/{pap[0]['id']}/restaurar").status_code == 404
    acciones = [a["accion"] for a in client.get("/auditoria", params={"paciente_id": p["id"]}).json()]
    assert "ELIMINACION" in acciones and "RESTAURACION" in acciones
    n = client.post("/pacientes/", json={"nombre": "X", "apellido": "Y", "ci": "V06B"}).json()
    assert n["id"] != p["id"]


def test_V07_quitar_ficticios_no_toca_otros_pacientes(client):
    real = client.post("/pacientes/", json={"nombre": "NO", "apellido": "DEMO", "ci": "V07"}).json()
    client.post("/admin/datos-demo")
    client.delete("/admin/datos-demo")
    assert [x["ci"] for x in client.get("/pacientes/").json()] == ["V07"]
    assert client.get(f"/api/expediente/{real['id']}").status_code == 200


def test_V08_consultas_e_informes_recuperan_la_evaluacion_elegida(client):
    p, e1 = nuevo(client, "V08", fecha="2026-05-01")
    client.post("/guardar-aptitud", json={"codigo_paciente": "V08", "resultado": "APTO"})
    client.post("/guardar-osteomuscular", json={"codigo_paciente": "V08", "concepto_aptitud": "APTO"})
    e2 = client.post("/evaluaciones/", json={"paciente_id": p["id"], "fecha": "2026-11-01"}).json()
    client.post("/guardar-aptitud", json={"codigo_paciente": "V08", "resultado": "NO APTO"})
    c1 = client.get("/api/informe-consolidado/V08", params={"evaluacion_id": e1["id"]}).json()
    c2 = client.get("/api/informe-consolidado/V08").json()
    assert c1["evaluacion"]["id"] == e1["id"] and c1["resultados_medicos"]["01_aptitud_ocupacional"] == "APTO"
    assert c1["resultados_medicos"]["03_osteomuscular"] == "APTO"
    assert c2["evaluacion"]["id"] == e2["id"] and c2["resultados_medicos"]["01_aptitud_ocupacional"] == "NO APTO"
    assert c2["resultados_medicos"]["03_osteomuscular"] == "SIN EXAMEN"
    assert len(c2["evaluaciones"]) == 2
    x = client.get(f"/api/expediente/{p['id']}", params={"evaluacion_id": e2["id"]}).json()
    assert x["fichas"]["osteomuscular"] is None
    assert client.get(f"/fichas/osteomuscular/{p['id']}", params={"evaluacion_id": e2["id"]}).json()["ficha"] is None


def test_V09_autoria_responsable_registro_y_modificacion(anonimo):
    med = {"Authorization": f"Bearer {iniciar(anonimo, 'mecondarco', 'temporal-1', 'clave-medico-1')}"}
    enf = {"Authorization": f"Bearer {iniciar(anonimo, 'enfermeria', 'temporal-5', 'clave-enfermera')}"}
    nuevo_u = anonimo.post("/auth/usuarios", json={"nombre": "Ana Optica Ficticia", "rol": "ESPECIALISTA", "especialidad": "Oftalmología", "fichas_permitidas": ["oftalmologia"]}, headers=med).json()
    esp = {"Authorization": f"Bearer {iniciar(anonimo, nuevo_u['usuario'], nuevo_u['temporal'], 'clave-especialista')}"}
    yo = anonimo.get("/auth/yo", headers=med).json()

    p = anonimo.post("/pacientes/", json={"nombre": "A", "apellido": "B", "ci": "V09"}, headers=enf).json()
    anonimo.post("/evaluaciones/", json={"paciente_id": p["id"]}, headers=enf)

    anonimo.post("/guardar-aptitud", json={"codigo_paciente": "V09", "resultado": "APTO"}, headers=enf)
    f = anonimo.get(f"/fichas/aptitud/{p['id']}", headers=med).json()["ficha"]
    assert f["registrado_por"].startswith("ENFERMERÍA") and f["responsable"] is None

    anonimo.post("/guardar-aptitud", json={"codigo_paciente": "V09", "resultado": "APTO CON RESTRICCIONES"}, headers={**enf, "X-Responsable": str(yo["id"])})
    f = anonimo.get(f"/fichas/aptitud/{p['id']}", headers=med).json()["ficha"]
    assert f["responsable"].startswith("MARÍA ELENA CONDARCO") and f["registrado_por"].startswith("ENFERMERÍA")

    anonimo.post("/guardar-aptitud", json={"codigo_paciente": "V09", "resultado": "NO APTO"}, headers=med)
    f = anonimo.get(f"/fichas/aptitud/{p['id']}", headers=med).json()["ficha"]
    assert f["responsable"].startswith("MARÍA ELENA CONDARCO") and f["registrado_por"].startswith("ENFERMERÍA")
    mods = [a for a in anonimo.get("/auditoria", params={"paciente_id": p["id"]}, headers=med).json() if a["campo"] == "resultado"]
    assert [m["usuario"].split(" ·")[0] for m in mods] == ["MARÍA ELENA CONDARCO CASTELLÓN", "ENFERMERÍA"]

    enf_id = next(u["id"] for u in anonimo.get("/auth/usuarios", headers=med).json() if u["usuario"] == "enfermeria")
    assert anonimo.post("/guardar-aptitud", json={"codigo_paciente": "V09"}, headers={**med, "X-Responsable": str(enf_id)}).status_code == 400
    assert anonimo.post("/guardar-aptitud", json={"codigo_paciente": "V09"}, headers={**med, "X-Responsable": "99999"}).status_code == 400

    anonimo.post("/guardar-aptitud", json={"codigo_paciente": "V09", "resultado": "NO APTO"}, headers={**med, "X-Responsable": "0"})
    f0 = anonimo.get(f"/fichas/aptitud/{p['id']}", headers=med).json()["ficha"]
    assert f0["responsable"] is None
    anonimo.post("/guardar-aptitud", json={"codigo_paciente": "V09", "resultado": "NO APTO"}, headers={**med, "X-Responsable": str(yo["id"])})
    anonimo.post("/ficha-oftalmo/", json={"paciente_id": p["id"], "lentes": "SI"}, headers=esp)
    o = anonimo.get(f"/fichas/oftalmologia/{p['id']}", headers=med).json()["ficha"]
    assert o["responsable"].startswith("ANA OPTICA FICTICIA · OFTALMOLOGÍA") and o["registrado_por"].startswith("ANA OPTICA FICTICIA")
    s = anonimo.get(f"/semaforo/evaluacion/{f['evaluacion_id']}", headers=med).json()
    apt = next(x for x in s["fichas"] if x["clave"] == "aptitud")
    assert apt["profesional"].startswith("MARÍA ELENA") and apt["registrado_por"].startswith("ENFERMERÍA") and apt["ultima_modificacion"]


def test_V10_personal_identidades_y_especialidades(anonimo):
    med = {"Authorization": f"Bearer {iniciar(anonimo, 'mecondarco', 'temporal-1', 'clave-medico-1')}"}
    yo = anonimo.get("/auth/yo", headers=med).json()
    lista = anonimo.get("/auth/usuarios", headers=med).json()
    assert len(lista) == 5 and all(u["rol"] in auth.ROLES for u in lista)
    assert anonimo.post("/auth/usuarios", json={"nombre": "Sin Rol"}, headers=med).status_code == 400
    assert anonimo.post("/auth/usuarios", json={"nombre": "Esp", "rol": "ESPECIALISTA"}, headers=med).status_code == 400
    assert anonimo.post("/auth/usuarios", json={"nombre": "X", "rol": "ADMIN"}, headers=med).status_code == 400
    u = anonimo.post("/auth/usuarios", json={"nombre": "José Pérez Ficticio", "rol": "ESPECIALISTA", "especialidad": "Psicología", "fichas_permitidas": ["psicologia"]}, headers=med).json()
    assert u["usuario"] == "jperez" and u["temporal"] and u["fichas_permitidas"] == ["psicologia"]
    u2 = anonimo.post("/auth/usuarios", json={"nombre": "José Pérez Ficticio", "rol": "LECTURA"}, headers=med).json()
    assert u2["usuario"] == "jperez2"
    r = anonimo.put(f"/auth/usuarios/{u['id']}", json={"especialidad": "Psicología laboral", "fichas_permitidas": ["psicologia", "aptitud_fisica"]}, headers=med).json()
    assert r["especialidad"] == "PSICOLOGÍA LABORAL" and r["fichas_permitidas"] == ["psicologia", "aptitud_fisica"]
    assert anonimo.put(f"/auth/usuarios/{yo['id']}", json={"activo": False}, headers=med).status_code == 400
    assert anonimo.put(f"/auth/usuarios/{yo['id']}", json={"rol": "LECTURA"}, headers=med).status_code == 400
    profesionales = anonimo.get("/auth/profesionales", headers=med).json()
    assert any(x["id"] == u["id"] for x in profesionales) and not any(x["id"] == u2["id"] for x in profesionales)
    tok = iniciar(anonimo, "jperez", u["temporal"], "clave-psicologo")
    anonimo.put(f"/auth/usuarios/{u['id']}", json={"activo": False}, headers=med)
    assert anonimo.get("/pacientes/", headers={"Authorization": f"Bearer {tok}"}).status_code == 401
    assert all(p["usuario"] != "jperez" for p in anonimo.get("/auth/perfiles").json())


def test_V11_permisos_en_el_servidor(anonimo):
    med = {"Authorization": f"Bearer {iniciar(anonimo, 'mecondarco', 'temporal-1', 'clave-medico-1')}"}
    enf = {"Authorization": f"Bearer {iniciar(anonimo, 'enfermeria', 'temporal-5', 'clave-enfermera')}"}
    e = anonimo.post("/auth/usuarios", json={"nombre": "Esp Cardio", "rol": "ESPECIALISTA", "fichas_permitidas": ["cardiologia"]}, headers=med).json()
    l = anonimo.post("/auth/usuarios", json={"nombre": "Revisora Ficticia", "rol": "LECTURA"}, headers=med).json()
    esp = {"Authorization": f"Bearer {iniciar(anonimo, e['usuario'], e['temporal'], 'clave-cardio-1')}"}
    lec = {"Authorization": f"Bearer {iniciar(anonimo, l['usuario'], l['temporal'], 'clave-lectura')}"}
    p = anonimo.post("/pacientes/", json={"nombre": "A", "apellido": "B", "ci": "V11"}, headers=med).json()

    assert anonimo.post("/guardar-cardiologia", json={"codigo_paciente": "V11", "hta": "NO"}, headers=esp).status_code == 200
    assert anonimo.post("/guardar-aptitud", json={"codigo_paciente": "V11", "resultado": "APTO"}, headers=esp).status_code == 403
    assert anonimo.post("/pacientes/", json={"nombre": "C", "apellido": "D", "ci": "V11B"}, headers=esp).status_code == 403
    assert anonimo.get("/semaforo", headers=esp).status_code == 200
    assert anonimo.get("/auditoria", headers=esp).status_code == 403

    for ruta in ["/pacientes/", "/semaforo", "/api/expediente/%d" % p["id"]]:
        assert anonimo.get(ruta, headers=lec).status_code == 200
    assert anonimo.post("/guardar-cardiologia", json={"codigo_paciente": "V11"}, headers=lec).status_code == 403
    assert anonimo.post("/pacientes/", json={"ci": "Z"}, headers=lec).status_code == 403
    assert anonimo.get("/admin/respaldo", headers=lec).status_code == 403

    for metodo, ruta in [("delete", f"/api/pacientes/{p['id']}"), ("get", "/admin/respaldo"), ("post", "/admin/datos-demo"),
                         ("get", "/papelera"), ("post", "/auth/usuarios"), ("get", "/auditoria"), ("get", "/semaforo"),
                         ("get", "/api/informe-consolidado/V11"), ("post", "/reglas-semaforo")]:
        r = getattr(anonimo, metodo)(ruta, headers=enf, **({"json": {}} if metodo == "post" else {}))
        assert r.status_code == 403, (metodo, ruta, r.status_code)

    tok = enf["Authorization"][7:]
    carga, firma = tok.split(".")
    datos = json.loads(auth._unb64(carga))
    datos["rol"] = "MEDICO"
    falsa = auth._b64(json.dumps(datos).encode()) + "." + firma
    assert anonimo.get("/semaforo", headers={"Authorization": f"Bearer {falsa}"}).status_code == 401
    vencido = auth._b64(json.dumps({"uid": 1, "rol": "MEDICO", "exp": 1}).encode())
    vencido += "." + auth._b64(auth.hmac.new(auth.SECRETO.encode(), vencido.encode(), auth.hashlib.sha256).digest())
    assert anonimo.get("/pacientes/", headers={"Authorization": f"Bearer {vencido}"}).status_code == 401
    assert anonimo.get("/pacientes/").status_code == 401
