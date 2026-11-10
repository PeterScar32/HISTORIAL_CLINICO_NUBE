import base64

from tests.conftest import iniciar

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


def b64(datos):
    return base64.b64encode(datos).decode()


def nuevo(client, ci="7800001", nombre="ana maria", apellido="prueba ficticia"):
    p = client.post("/pacientes/", json={"nombre": nombre, "apellido": apellido, "ci": ci}).json()
    e = client.post("/evaluaciones/", json={"paciente_id": p["id"], "tipo": "PERIODICO"}).json()
    return p, e


def test_AD01_sube_lista_y_descarga_pdf_y_fotos(client):
    p, e = nuevo(client)
    for nombre, datos, tipo in (("examen.pdf", PDF, "application/pdf"), ("foto.png", PNG, "image/png"), ("radiografía", JPG, "image/jpeg")):
        r = client.post(f"/pacientes/{p['id']}/adjuntos", json={"nombre": nombre, "contenido": b64(datos), "descripcion": "Prueba"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["tipo"] == tipo and d["tamano"] == len(datos) and d["evaluacion_id"] == e["id"] and "contenido" not in d
        f = client.get(f"/adjuntos/{d['id']}")
        assert f.status_code == 200 and f.content == datos and f.headers["content-type"] == tipo
    lista = client.get(f"/pacientes/{p['id']}/adjuntos").json()
    assert len(lista) == 3 and lista[0]["nombre"] == "radiografía.jpg"


def test_AD02_acepta_data_url(client):
    p, _ = nuevo(client)
    r = client.post(f"/pacientes/{p['id']}/adjuntos", json={"nombre": "a.pdf", "contenido": "data:application/pdf;base64," + b64(PDF)})
    assert r.status_code == 200


def test_AD03_rechaza_tipo_falso_vacio_grande_y_paciente_inexistente(client):
    p, _ = nuevo(client)
    url = f"/pacientes/{p['id']}/adjuntos"
    assert client.post(url, json={"nombre": "virus.pdf", "contenido": b64(b"MZ\x90\x00 ejecutable")}).status_code == 415
    assert client.post(url, json={"nombre": "x.pdf", "contenido": ""}).status_code == 400
    assert client.post(url, json={"nombre": "x.pdf", "contenido": "no es base64!!"}).status_code == 400
    assert client.post(url, json={"nombre": "x.pdf", "contenido": b64(PDF + b"0" * (5 * 1024 * 1024))}).status_code == 413
    assert client.post("/pacientes/999999/adjuntos", json={"nombre": "x.pdf", "contenido": b64(PDF)}).status_code == 404
    assert client.get("/pacientes/999999/adjuntos").status_code == 404
    assert client.get("/adjuntos/999999").status_code == 404


def test_AD04_evaluacion_de_otro_paciente(client):
    p1, _ = nuevo(client, "7800002")
    _, e2 = nuevo(client, "7800003")
    r = client.post(f"/pacientes/{p1['id']}/adjuntos", json={"nombre": "x.pdf", "contenido": b64(PDF), "evaluacion_id": e2["id"]})
    assert r.status_code == 404


def test_AD05_eliminar_audita(client):
    p, _ = nuevo(client)
    a = client.post(f"/pacientes/{p['id']}/adjuntos", json={"nombre": "x.pdf", "contenido": b64(PDF)}).json()
    assert client.delete(f"/adjuntos/{a['id']}").status_code == 200
    assert client.get(f"/adjuntos/{a['id']}").status_code == 404
    acciones = [x["accion"] for x in client.get("/auditoria", params={"paciente_id": p["id"]}).json() if x["tabla"] == "adjuntos"]
    assert "ADJUNTO" in acciones and "ELIMINACION" in acciones


def test_AD06_papelera_conserva_y_restaura_adjuntos(client):
    p, _ = nuevo(client, "7800004")
    client.post(f"/pacientes/{p['id']}/adjuntos", json={"nombre": "x.pdf", "contenido": b64(PDF)})
    assert client.delete(f"/api/pacientes/{p['id']}", params={"confirmar_ci": "7800004"}).status_code == 200
    item = [x for x in client.get("/papelera").json() if x["ci"] == "7800004"][0]
    assert item["adjuntos"] == 1
    assert client.post(f"/papelera/{item['id']}/restaurar").status_code == 200
    lista = client.get(f"/pacientes/{p['id']}/adjuntos").json()
    assert len(lista) == 1 and client.get(f"/adjuntos/{lista[0]['id']}").content == PDF


def test_AD07_respaldo_incluye_adjuntos(client):
    p, _ = nuevo(client)
    client.post(f"/pacientes/{p['id']}/adjuntos", json={"nombre": "x.pdf", "contenido": b64(PDF)})
    r = client.get("/admin/respaldo").json()
    assert base64.b64decode(r["tablas"]["adjuntos"][0]["contenido"]) == PDF


def test_AD08_permisos_por_perfil(client, anonimo):
    p, _ = nuevo(client)
    a = client.post(f"/pacientes/{p['id']}/adjuntos", json={"nombre": "x.pdf", "contenido": b64(PDF)}).json()
    lec = client.post("/auth/usuarios", json={"nombre": "Lectura Ficticia", "rol": "LECTURA"}).json()
    esp = client.post("/auth/usuarios", json={"nombre": "Especialista Ficticio", "rol": "ESPECIALISTA", "fichas_permitidas": ["oftalmologia"]}).json()
    t_lec = iniciar(anonimo, lec["usuario"], lec["temporal"], "clave-nueva-123")
    t_esp = iniciar(anonimo, esp["usuario"], esp["temporal"], "clave-nueva-123")
    t_enf = iniciar(anonimo, "enfermeria", "temporal-5", "clave-enf-123")
    cuerpo = {"nombre": "y.pdf", "contenido": b64(PDF)}
    h = lambda t: {"Authorization": f"Bearer {t}"}
    anonimo.headers.pop("Authorization", None)
    assert anonimo.get(f"/pacientes/{p['id']}/adjuntos").status_code == 401
    assert anonimo.get(f"/adjuntos/{a['id']}").status_code == 401
    assert anonimo.get(f"/pacientes/{p['id']}/adjuntos", headers=h(t_lec)).status_code == 200
    assert anonimo.get(f"/adjuntos/{a['id']}", headers=h(t_lec)).status_code == 200
    assert anonimo.post(f"/pacientes/{p['id']}/adjuntos", json=cuerpo, headers=h(t_lec)).status_code == 403
    assert anonimo.post(f"/pacientes/{p['id']}/adjuntos", json=cuerpo, headers=h(t_esp)).status_code == 200
    assert anonimo.post(f"/pacientes/{p['id']}/adjuntos", json=cuerpo, headers=h(t_enf)).status_code == 200
    for t in (t_lec, t_esp, t_enf):
        assert anonimo.delete(f"/adjuntos/{a['id']}", headers=h(t)).status_code == 403


def test_CS01_busqueda_en_consulta_por_ci_y_nombre_completo(client):
    p, e = nuevo(client, "7800005", "jorge luis", "quispe huanca")
    nuevo(client, "7800006", "maria", "flores")
    client.post("/guardar-cardiologia", json={"codigo_paciente": "7800005", "hta": "SI"})
    por_ci = client.get("/consultas/cardiologia/buscar", params={"q": "7800005"}).json()
    assert len(por_ci) == 1 and por_ci[0]["registrada"] and por_ci[0]["evaluacion_id"] == e["id"]
    for q in ("jorge luis quispe huanca", "QUISPE HUANCA JORGE LUIS", "quispe jorge"):
        assert [x["ci"] for x in client.get("/consultas/cardiologia/buscar", params={"q": q}).json()] == ["7800005"], q
    sin = client.get("/consultas/cardiologia/buscar", params={"q": "flores"}).json()
    assert len(sin) == 1 and sin[0]["registrada"] is False
    assert client.get("/consultas/cardiologia/buscar", params={"q": "nadie inexistente"}).json() == []
    assert client.get("/consultas/cardiologia/buscar", params={"q": " "}).status_code == 400
    assert client.get("/consultas/xyz/buscar", params={"q": "a"}).status_code == 404


def test_CS02_busqueda_en_consulta_solo_perfiles_de_consulta(client, anonimo):
    t_enf = iniciar(anonimo, "enfermeria", "temporal-5", "clave-enf-123")
    r = anonimo.get("/consultas/cardiologia/buscar", params={"q": "a"}, headers={"Authorization": f"Bearer {t_enf}"})
    assert r.status_code == 403
