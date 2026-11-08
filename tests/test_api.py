def test_estado(client):
    assert client.get("/").json() == {"status": "ok"}


def test_registro_usa_ci_como_codigo(client, paciente):
    assert paciente["ci"] == "9999001"
    assert paciente["codigo_paciente"] == "9999001"
    assert paciente["nombre"] == "JUAN"


def test_ci_repetido_no_duplica(client, paciente):
    r = client.post("/pacientes/", json={"nombre": "Juan", "apellido": "Perez Mamani", "ci": " 9999001 "})
    assert r.status_code == 200
    assert r.json()["id"] == paciente["id"]
    assert len(client.get("/pacientes/").json()) == 1


def test_ci_obligatorio(client):
    assert client.post("/pacientes/", json={"nombre": "Ana", "apellido": "Huanca"}).status_code == 400


def test_buscar_por_ci(client, paciente):
    assert client.get("/pacientes/buscar/9999001").json()["id"] == paciente["id"]
    assert client.get("/buscar-id-por-codigo/9999001").json()["id"] == paciente["id"]
    assert client.get("/pacientes/buscar/0000").status_code == 404


def test_declaracion_jurada_actualiza_sin_duplicar(client, paciente):
    pid = paciente["id"]
    assert client.post("/filiacion/", json={"paciente_id": pid, "edad": "30", "ciudad": "LA PAZ"}).status_code == 200
    assert client.post("/filiacion/", json={"paciente_id": pid, "edad": "31", "ciudad": "EL ALTO"}).status_code == 200
    assert client.post("/p2/", json={"paciente_id": pid, "vista": "NORMAL", "cardio": "NORMAL"}).status_code == 200
    assert client.post("/p2/", json={"paciente_id": pid, "vista": "USA LENTES", "cardio": "NORMAL"}).status_code == 200
    assert client.post("/p3/", json={"paciente_id": pid, "fuma": "NO", "campo_inexistente": "x"}).status_code == 200
    d = client.get(f"/api/paciente-completo/{pid}").json()
    assert d["paciente"]["ci"] == "9999001" and d["paciente"]["apellido"] == "PEREZ QUISPE"
    assert d["filiacion"]["edad"] == "31"
    assert d["filiacion"]["ciudad"] == "EL ALTO"
    assert d["antecedentes"]["vista"] == "USA LENTES"
    assert d["habitos"]["fuma"] == "NO"
    assert client.get(f"/api/reporte-unificado/{pid}").json()["filiacion"]["edad"] == "31"


def test_declaracion_requiere_paciente(client):
    assert client.post("/p2/", json={"vista": "NORMAL"}).status_code == 400


def test_fichas_por_ci_y_consultas(client, paciente):
    ci = paciente["ci"]
    assert client.post("/guardar-cardiologia", json={"codigo_paciente": ci, "hta": "SI", "diagnostico_recomendaciones": "SOPLO CARDIACO LEVE"}).status_code == 200
    assert client.post("/guardar-altura", json={"codigo_paciente": ci, "soplo_cardiaco": "SI"}).status_code == 200
    assert client.post("/guardar-psicologia", json={"codigo_paciente": ci, "resultado_psicologico": "APTO"}).status_code == 200
    assert client.post("/guardar-espirometria", json={"codigo_paciente": ci, "hemoptisis": "SI"}).status_code == 200
    assert client.post("/guardar-electro", json={"codigo_paciente": ci, "cefaleas": "SI"}).status_code == 200
    assert client.post("/guardar-aptitud", json={"codigo_paciente": ci, "resultado": "no apto"}).json()["status"] == "success"
    assert client.post("/guardar-aptitud-fisica", json={"codigo_paciente": ci, "resultado_fisico": "APTO", "resultado_psicologico": "APTO"}).status_code == 200
    assert client.post("/guardar-osteomuscular", json={"codigo_paciente": ci, "concepto_aptitud": "APTO", "edad": 30}).status_code == 200
    assert client.post("/ficha-oftalmo/", json={"paciente_id": paciente["id"], "lentes": "SI"}).status_code == 200

    assert client.get("/buscar-cardiologia", params={"antecedente": "HTA"}).json()[0]["codigo"] == ci
    assert client.get("/filtrar-cardiologia", params={"query": "soplo"}).json()[0]["codigo_paciente"] == ci
    assert client.get("/filtrar-altura/soplo_cardiaco").json()[0]["codigo"] == ci
    assert client.get("/ficha-psicologia-filtrada/APTO").json()[0]["codigo"] == ci
    assert client.get("/espirometria-filtrada/hemoptisis").json()[0]["codigo"] == ci
    assert client.get("/listar-espirometria").json()[0]["codigo"] == ci
    assert client.get("/consultar-electro-por-campo/cefaleas").json()[0]["codigo_paciente"] == ci
    assert client.get("/filtrar-aptitud/NO APTO").json()[0]["codigo"] == ci
    assert client.get("/filtrar-aptitud/APTO/APTO").json()[0]["codigo"] == ci
    assert client.get("/filtrar-osteomuscular/APTO").json()[0]["codigo"] == ci
    assert client.get("/filtrar-oftalmo/lentes").json()[0]["codigo"] == ci
    assert client.get(f"/buscar-aptitud-fisica/{ci}").json()["paciente_id"] == paciente["id"]

    estado = client.get(f"/verificar_estado_paciente/{paciente['id']}").json()
    assert estado["cardiologia"] and estado["osteomuscular"] and not estado["historial_clinico"]

    inf = client.get(f"/api/informe-consolidado/{ci}").json()["resultados_medicos"]
    assert inf["01_aptitud_ocupacional"] == "NO APTO"
    assert inf["03_osteomuscular"] == "APTO"


def test_ficha_con_ci_inexistente(client):
    assert client.post("/guardar-cardiologia", json={"codigo_paciente": "000"}).status_code == 404
    assert client.post("/guardar-espirometria", json={"codigo_paciente": "000"}).status_code == 404
    assert client.post("/guardar-altura", json={"codigo_paciente": "000"}).status_code == 404


def test_historial_clinico_guarda_todos_los_campos(client, paciente):
    datos = {"codigo_paciente": paciente["ci"], "psicologicos": "SI", "biologicos": "NO", "boca_a": "X",
             "faringe_n": "X", "hem_na": "X", "eca_n": "X", "tipo_control": "PERIODICO",
             "aptitud_restriccion": "APTO CON RESTRICCIÓN", "nombre": "JUAN PEREZ"}
    assert client.post("/guardar-historial-clinico", json=datos).status_code == 200
    from api.database import SessionLocal
    from api import models
    db = SessionLocal()
    h = db.query(models.HistorialClinico).first()
    assert (h.psico, h.bio, h.boca_a, h.faringe_n, h.hem_na, h.eca_n, h.tipo_control) == ("SI", "NO", "X", "X", "X", "X", "PERIODICO")
    assert h.paciente_id == paciente["id"]
    db.close()
    r = client.get("/historial-filtrado/aptitud_restriccion").json()
    assert r[0]["codigo_paciente"] == paciente["ci"]


def test_borrar_paciente_borra_sus_fichas(client, paciente):
    pid, ci = paciente["id"], paciente["ci"]
    client.post("/filiacion/", json={"paciente_id": pid, "edad": "30"})
    client.post("/guardar-osteomuscular", json={"codigo_paciente": ci, "concepto_aptitud": "APTO"})
    client.post("/guardar-aptitud-fisica", json={"codigo_paciente": ci})
    client.post("/guardar-psicologia", json={"codigo_paciente": ci})
    assert client.delete(f"/api/pacientes/{pid}").status_code == 200
    assert client.get(f"/api/paciente-completo/{pid}").status_code == 404
    assert client.get("/filtrar-osteomuscular/APTO").json() == []
    assert client.delete(f"/api/pacientes/{pid}").status_code == 404


def test_personal(client):
    r = client.post("/doctores/", json={"ci_doc": "DOC1", "nombre_doc": "ANA", "appaterno_doc": "LOPEZ", "especialidad": "CARDIOLOGIA", "turno_doc": "MAÑANA", "campo_raro": 1})
    assert r.status_code == 200
    client.post("/enfermeras/", json={"ci_enfe": "ENF1", "nombre_enfe": "ROSA", "appaterno_enfe": "MAMANI", "especialidad": "GENERAL", "turno_enfe": "TARDE"})
    p = client.get("/personal/").json()
    assert len(p["doctores"]) == 1 and len(p["enfermeras"]) == 1
    did = p["doctores"][0]["id_doc"]
    assert client.put(f"/doctores/{did}", json={"turno_doc": "NOCHE", "id_doc": 999}).json()["id_doc"] == did


def test_registro_avisa_si_existe(client, paciente):
    assert paciente["existente"] is False
    r = client.post("/pacientes/", json={"nombre": "Juan", "apellido": "Perez Quispe", "ci": "9999001"}).json()
    assert r["existente"] is True and r["id"] == paciente["id"]


def test_segunda_evaluacion_conserva_la_primera(client, paciente):
    pid, ci = paciente["id"], paciente["ci"]
    ev1 = client.post("/evaluaciones/", json={"paciente_id": pid, "empresa": "cementos andinos", "puesto": "operario", "tipo": "PREOCUPACIONAL", "fecha": "2026-11-05"}).json()
    client.post("/filiacion/", json={"paciente_id": pid, "evaluacion_id": ev1["id"], "edad": "34"})
    client.post("/p2/", json={"paciente_id": pid, "evaluacion_id": ev1["id"], "vista": "NORMAL"})
    client.post("/guardar-cardiologia", json={"codigo_paciente": ci, "hta": "NO"})

    ev2 = client.post("/evaluaciones/", json={"paciente_id": pid, "empresa": "cementos andinos", "tipo": "PERIODICO"}).json()
    assert ev2["id"] != ev1["id"] and ev2["empresa"] == "CEMENTOS ANDINOS"
    d = client.get(f"/api/paciente-completo/{pid}").json()
    assert d["evaluacion"]["id"] == ev2["id"]
    assert d["filiacion_heredada"] is True and d["filiacion"]["edad"] == "34"
    assert d["antecedentes"] is None

    client.post("/filiacion/", json={"paciente_id": pid, "evaluacion_id": ev2["id"], "edad": "35"})
    client.post("/p2/", json={"paciente_id": pid, "evaluacion_id": ev2["id"], "vista": "USA LENTES"})
    client.post("/guardar-cardiologia", json={"codigo_paciente": ci, "hta": "SI"})

    d1 = client.get(f"/api/paciente-completo/{pid}", params={"evaluacion_id": ev1["id"]}).json()
    d2 = client.get(f"/api/paciente-completo/{pid}", params={"evaluacion_id": ev2["id"]}).json()
    assert (d1["filiacion"]["edad"], d1["antecedentes"]["vista"]) == ("34", "NORMAL")
    assert (d2["filiacion"]["edad"], d2["antecedentes"]["vista"]) == ("35", "USA LENTES")
    assert d2["filiacion_heredada"] is False

    evs = client.get(f"/pacientes/{pid}/evaluaciones").json()
    assert [e["id"] for e in evs] == [ev2["id"], ev1["id"]]
    assert evs[0]["fichas"]["cardiologia"] and evs[1]["fichas"]["cardiologia"]
    assert evs[1]["fecha"] == "2026-11-05"


def test_ficha_sin_evaluacion_crea_una(client, paciente):
    client.post("/guardar-psicologia", json={"codigo_paciente": paciente["ci"]})
    evs = client.get(f"/pacientes/{paciente['id']}/evaluaciones").json()
    assert len(evs) == 1 and evs[0]["fichas"]["psicologia"]


def test_evaluacion_paciente_invalido(client):
    assert client.post("/evaluaciones/", json={"paciente_id": 999}).status_code == 400


def _evaluar(client, ci, nombre, empresa, aptitud=None, osteo=None, hiscli=None):
    p = client.post("/pacientes/", json={"nombre": nombre, "apellido": "PRUEBA", "ci": ci}).json()
    ev = client.post("/evaluaciones/", json={"paciente_id": p["id"], "empresa": empresa, "fecha": "2026-11-05"}).json()
    if aptitud:
        client.post("/guardar-aptitud", json={"codigo_paciente": ci, "resultado": aptitud})
    if osteo:
        client.post("/guardar-osteomuscular", json={"codigo_paciente": ci, "concepto_aptitud": osteo})
    if hiscli:
        client.post("/guardar-historial-clinico", json={"codigo_paciente": ci, **hiscli})
    return ev


def test_semaforo_colores(client):
    v = _evaluar(client, "S1", "VERDE", "Cementos  Andinos", aptitud="APTO", osteo="APTO")
    a = _evaluar(client, "S2", "AMARILLO", "cementos andinos", aptitud="APTO CON RESTRICCIONES")
    r = _evaluar(client, "S3", "ROJO", "CEMENTOS ANDINOS", aptitud="APTO", osteo="NO_APTO_TEMPORAL")
    g = _evaluar(client, "S4", "GRIS", "OTRA EMPRESA")
    h = _evaluar(client, "S5", "HISCLI", "OTRA EMPRESA", hiscli={"aptitud_restriccion": "APTO CON RESTRICCIÓN"})
    col = lambda ev: client.get(f"/semaforo/evaluacion/{ev['id']}").json()
    assert col(v)["color"] == "VERDE"
    assert col(a)["color"] == "AMARILLO"
    rr = col(r)
    assert rr["color"] == "ROJO" and "Osteomuscular" in rr["motivo"]
    assert any(d["regla_id"] for d in rr["conclusiones"] if d["color"] == "ROJO")
    gg = col(g)
    assert gg["color"] == "GRIS" and gg["completitud"]["registradas"] == 0 and gg["completitud"]["requeridas"] == 5
    assert gg["completitud"]["estado"] == "INCOMPLETA" and len(gg["completitud"]["faltantes"]) == 5
    assert col(h)["color"] == "AMARILLO"
    vv = col(v)
    assert vv["completitud"]["registradas"] == 1 and vv["completitud"]["estado"] == "INCOMPLETA"
    assert vv["completitud"]["adicionales"] == ["Osteomuscular"]
    assert vv["conclusion_sin_profesional"] == []

    panel = client.get("/semaforo", params={"empresa": "cementos andinos"}).json()
    assert panel["total"] == 3
    assert panel["resumen"] == {"ROJO": 1, "AMARILLO": 1, "VERDE": 1, "GRIS": 0}
    assert panel["cumplimiento"] == {"COMPLETA": 0, "INCOMPLETA": 3}
    osteo = next(e for e in panel["por_especialidad"] if e["clave"] == "osteomuscular")
    assert (osteo["ROJO"], osteo["VERDE"]) == (1, 1)
    apt = next(e for e in panel["por_especialidad"] if e["clave"] == "aptitud")
    assert (apt["VERDE"], apt["AMARILLO"], apt["PENDIENTE"]) == (2, 1, 0)
    assert set(client.get("/empresas").json()) == {"CEMENTOS ANDINOS", "OTRA EMPRESA"}


def test_semaforo_valor_sin_regla_y_reglas_configurables(client):
    ev = _evaluar(client, "S6", "RARO", "X", aptitud="PENDIENTE DE ESTUDIOS")
    d = client.get(f"/semaforo/evaluacion/{ev['id']}").json()
    assert d["color"] == "AMARILLO" and d["conclusiones"][0]["regla_id"] is None
    r = client.post("/reglas-semaforo", json={"patron": "PENDIENTE", "color": "rojo", "prioridad": 5, "descripcion": "Pendiente"}).json()
    assert client.get(f"/semaforo/evaluacion/{ev['id']}").json()["color"] == "ROJO"
    client.post("/reglas-semaforo", json={"id": r["id"], "patron": "PENDIENTE", "color": "ROJO", "activo": False})
    assert client.get(f"/semaforo/evaluacion/{ev['id']}").json()["color"] == "AMARILLO"
    assert client.post("/reglas-semaforo", json={"patron": "X", "color": "AZUL"}).status_code == 400


def test_fichas_requeridas_y_completitud(client):
    p = client.post("/pacientes/", json={"nombre": "LUZ", "apellido": "PRUEBA", "ci": "R1"}).json()
    ev = client.post("/evaluaciones/", json={"paciente_id": p["id"], "fichas_requeridas": ["aptitud", "oftalmologia"]}).json()
    d = client.get(f"/semaforo/evaluacion/{ev['id']}").json()
    assert d["completitud"]["requeridas"] == 2 and d["completitud"]["requeridas_por_defecto"] is False
    client.post("/guardar-aptitud", json={"codigo_paciente": "R1", "resultado": "APTO"})
    client.post("/ficha-oftalmo/", json={"paciente_id": p["id"], "lentes": "NO"})
    d = client.get(f"/semaforo/evaluacion/{ev['id']}").json()
    assert d["completitud"]["estado"] == "COMPLETA" and d["completitud"]["porcentaje"] == 100
    assert d["color"] == "VERDE"
    r = client.put(f"/evaluaciones/{ev['id']}/fichas-requeridas", json={"fichas_requeridas": ["aptitud", "oftalmologia", "cardiologia"]})
    assert r.status_code == 200
    d = client.get(f"/semaforo/evaluacion/{ev['id']}").json()
    assert d["completitud"]["estado"] == "INCOMPLETA" and d["completitud"]["faltantes"] == ["Cardiología"]
    assert client.put(f"/evaluaciones/{ev['id']}/fichas-requeridas", json={"fichas_requeridas": ["nada"]}).status_code == 400
    cat = client.get("/catalogo-fichas").json()
    assert len(cat) == 13 and sum(c["por_defecto"] for c in cat) == 5


def test_profesional_responsable_y_fecha(client):
    p = client.post("/pacientes/", json={"nombre": "TITO", "apellido": "PRUEBA", "ci": "R2"}).json()
    ev = client.post("/evaluaciones/", json={"paciente_id": p["id"]}).json()
    client.post("/guardar-aptitud", json={"codigo_paciente": "R2", "resultado": "NO APTO"}, headers={"X-Profesional": "doc:999"})
    d = client.get(f"/semaforo/evaluacion/{ev['id']}").json()
    c = d["conclusiones"][0]
    assert c["profesional"].startswith("MARÍA ELENA CONDARCO CASTELLÓN")
    assert c["fecha"] is not None
    assert d["conclusion_sin_profesional"] == []


def test_sin_sesion_no_hay_acceso(anonimo):
    assert anonimo.get("/").status_code == 200
    assert anonimo.get("/pacientes/").status_code == 401
    assert anonimo.post("/pacientes/", json={"ci": "1"}).status_code == 401
    assert anonimo.get("/semaforo").status_code == 401
    assert anonimo.get("/pacientes/", headers={"Authorization": "Bearer falso.token"}).status_code == 401
    perfiles = anonimo.get("/auth/perfiles").json()
    assert [p["usuario"] for p in perfiles] == ["mecondarco", "knoya", "rcervantes", "lquinteros", "enfermeria"]
    assert all("pass_hash" not in p for p in perfiles)


def test_login_y_cambio_de_clave(anonimo):
    assert anonimo.post("/auth/login", json={"usuario": "mecondarco", "clave": "mala"}).status_code == 401
    assert anonimo.post("/auth/login", json={"usuario": "knoya", "clave": ""}).status_code == 401
    r = anonimo.post("/auth/login", json={"usuario": "mecondarco", "clave": "temporal-1"}).json()
    assert r["usuario"]["debe_cambiar"] is True
    h = {"Authorization": f"Bearer {r['token']}"}
    assert anonimo.get("/pacientes/", headers=h).status_code == 403
    assert anonimo.post("/auth/cambiar-clave", json={"actual": "temporal-1", "nueva": "corta"}, headers=h).status_code == 400
    r2 = anonimo.post("/auth/cambiar-clave", json={"actual": "temporal-1", "nueva": "nueva-clave-1"}, headers=h).json()
    assert r2["usuario"]["debe_cambiar"] is False
    assert anonimo.get("/pacientes/", headers={"Authorization": f"Bearer {r2['token']}"}).status_code == 200
    assert anonimo.post("/auth/login", json={"usuario": "mecondarco", "clave": "temporal-1"}).status_code == 401
    assert anonimo.post("/auth/login", json={"usuario": "mecondarco", "clave": "nueva-clave-1"}).status_code == 200


def test_permisos_enfermeria(anonimo):
    from tests.conftest import iniciar
    med = {"Authorization": f"Bearer {iniciar(anonimo, 'mecondarco', 'temporal-1', 'clave-medico-1')}"}
    enf = {"Authorization": f"Bearer {iniciar(anonimo, 'enfermeria', 'temporal-5', 'clave-enfermera')}"}
    p = anonimo.post("/pacientes/", json={"nombre": "ANA", "apellido": "PRUEBA", "ci": "E1"}, headers=enf)
    assert p.status_code == 200
    pid = p.json()["id"]
    assert anonimo.post("/evaluaciones/", json={"paciente_id": pid}, headers=enf).status_code == 200
    assert anonimo.post("/filiacion/", json={"paciente_id": pid, "edad": "30"}, headers=enf).status_code == 200
    assert anonimo.post("/guardar-cardiologia", json={"codigo_paciente": "E1", "hta": "NO"}, headers=enf).status_code == 200
    assert anonimo.get(f"/api/paciente-completo/{pid}", headers=enf).status_code == 200
    assert anonimo.get("/pacientes/buscar/E1", headers=enf).status_code == 200
    assert anonimo.get("/semaforo", headers=enf).status_code == 403
    assert anonimo.get("/api/informe-consolidado/E1", headers=enf).status_code == 403
    assert anonimo.get("/filtrar-oftalmo/lentes", headers=enf).status_code == 403
    assert anonimo.delete(f"/api/pacientes/{pid}", headers=enf).status_code == 403
    assert anonimo.post("/doctores/", json={"ci_doc": "X"}, headers=enf).status_code == 403
    assert anonimo.get("/auth/usuarios", headers=enf).status_code == 403
    assert anonimo.get("/semaforo", headers=med).status_code == 200
    f = next(x for x in anonimo.get(f"/semaforo/evaluacion/{pid and anonimo.get(f'/pacientes/{pid}/evaluaciones', headers=med).json()[0]['id']}", headers=med).json()["fichas"] if x["clave"] == "declaracion")
    assert f["profesional"].startswith("ENFERMERÍA")
    assert anonimo.delete(f"/api/pacientes/{pid}", headers=med).status_code == 200


def test_restablecer_clave(client):
    us = client.get("/auth/usuarios").json()
    knoya = next(u for u in us if u["usuario"] == "knoya")
    r = client.post(f"/auth/usuarios/{knoya['id']}/restablecer", json={}).json()
    assert len(r["temporal"]) >= 6
    assert client.post("/auth/login", json={"usuario": "knoya", "clave": r["temporal"]}).status_code == 200
