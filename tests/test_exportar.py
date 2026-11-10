import base64
import io

from openpyxl import load_workbook

from tests.conftest import iniciar


def libro(r):
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/vnd.openxmlformats")
    return load_workbook(io.BytesIO(r.content))


def test_EX01_excel_con_pacientes_evaluaciones_fichas_y_archivos(client):
    p = client.post("/pacientes/", json={"nombre": "ana", "apellido": "prueba ficticia", "ci": "7900001"}).json()
    e = client.post("/evaluaciones/", json={"paciente_id": p["id"], "tipo": "PERIODICO", "empresa": "EMPRESA FICTICIA"}).json()
    client.post("/guardar-cardiologia", json={"codigo_paciente": "7900001", "hta": "SI\x01"})
    client.post(f"/pacientes/{p['id']}/adjuntos", json={"nombre": "lab.pdf", "contenido": base64.b64encode(b"%PDF-1.4 x").decode()})
    wb = libro(client.get("/exportar/excel"))
    assert {"Pacientes", "Evaluaciones", "Cardiología", "P1 Filiación", "Osteomuscular", "Archivos"} <= set(wb.sheetnames)
    pac = list(wb["Pacientes"].values)
    assert pac[0][:3] == ("CI", "Apellidos", "Nombres") and pac[1][0] == "7900001" and pac[1][3] == 1
    ev = list(wb["Evaluaciones"].values)
    assert ev[1][0] == "7900001" and ev[1][4] == "EMPRESA FICTICIA"
    car = list(wb["Cardiología"].values)
    assert car[1][0] == "7900001" and "Hta" in car[0] and car[1][car[0].index("Hta")] == "SI"
    assert list(wb["Archivos"].values)[1][3] == "lab.pdf"
    acciones = [x["accion"] for x in client.get("/auditoria").json()]
    assert "EXPORTACION" in acciones


def test_EX02_excel_vacio(client):
    wb = libro(client.get("/exportar/excel"))
    assert list(wb["Pacientes"].values) == [("CI", "Apellidos", "Nombres", "N.º evaluaciones", "Última evaluación", "Tipo", "Empresa", "Puesto")]


def test_EX03_permisos(client, anonimo):
    lec = client.post("/auth/usuarios", json={"nombre": "Lectura Ficticia", "rol": "LECTURA"}).json()
    esp = client.post("/auth/usuarios", json={"nombre": "Especialista Ficticio", "rol": "ESPECIALISTA", "fichas_permitidas": ["oftalmologia"]}).json()
    t_lec = iniciar(anonimo, lec["usuario"], lec["temporal"], "clave-nueva-123")
    t_esp = iniciar(anonimo, esp["usuario"], esp["temporal"], "clave-nueva-123")
    t_enf = iniciar(anonimo, "enfermeria", "temporal-5", "clave-enf-123")
    anonimo.headers.pop("Authorization", None)
    h = lambda t: {"Authorization": f"Bearer {t}"}
    assert anonimo.get("/exportar/excel").status_code == 401
    assert anonimo.get("/exportar/excel", headers=h(t_lec)).status_code == 403
    assert anonimo.get("/exportar/excel", headers=h(t_esp)).status_code == 403
    libro(anonimo.get("/exportar/excel", headers=h(t_enf)))
