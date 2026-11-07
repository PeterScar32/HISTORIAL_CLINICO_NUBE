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
