"""Pruebas que respaldan las afirmaciones de la tesis (Capítulos III y IV).

Los identificadores CP-xx, ID-xx, FO-xx, SE-xx y CU-xx se citan en la matriz de trazabilidad.
Todos los datos son ficticios.
"""
import pytest
from sqlalchemy import String, Text

from tests.conftest import iniciar
from api import auth, models
from api.auditoria import FICHAS

INTERNOS = {"id", "paciente_id", "evaluacion_id", "codigo_paciente", "creado_en", "registrado_por", "responsable_id", "responsable"}


def campo_de_prueba(modelo):
    for c in modelo.__table__.columns:
        if c.name not in INTERNOS and isinstance(c.type, (String, Text)):
            return c.name


def nuevo(client, ci, nombre="PRUEBA", apellido="TESIS"):
    p = client.post("/pacientes/", json={"nombre": nombre, "apellido": apellido, "ci": ci}).json()
    e = client.post("/evaluaciones/", json={"paciente_id": p["id"], "tipo": "PERIODICO", "empresa": "EMPRESA FICTICIA"}).json()
    return p, e


def test_CP01_estado_api(anonimo):
    r = anonimo.get("/")
    assert r.status_code == 200


def test_CP02_listar_pacientes(client):
    r = client.get("/pacientes/")
    assert r.status_code == 200 and isinstance(r.json(), list)


def test_CP03_crear_paciente_ficticio(client):
    r = client.post("/pacientes/", json={"nombre": "ana", "apellido": "prueba", "ci": "7700001"})
    assert r.status_code == 200
    d = r.json()
    assert d["id"] > 0 and d["ci"] == "7700001" and d["codigo_paciente"] == "7700001" and d["existente"] is False


def test_CP04_identidad_duplicada_no_crea_ni_sobrescribe(client):
    a = client.post("/pacientes/", json={"nombre": "ana", "apellido": "prueba", "ci": "7700002"}).json()
    r = client.post("/pacientes/", json={"nombre": "otro", "apellido": "nombre", "ci": " 7700002 "})
    assert r.status_code == 200
    b = r.json()
    assert b["existente"] is True and b["id"] == a["id"]
    assert b["nombre"] == "ANA" and b["apellido"] == "PRUEBA"
    assert sum(1 for p in client.get("/pacientes/").json() if p["ci"] == "7700002") == 1


def test_CP05_consultar_paciente_creado(client):
    a = client.post("/pacientes/", json={"nombre": "ana", "apellido": "prueba", "ci": "7700003"}).json()
    r = client.get("/pacientes/buscar/7700003")
    assert r.status_code == 200 and r.json()["id"] == a["id"]
    r = client.get(f"/api/paciente-completo/{a['id']}")
    assert r.status_code == 200 and r.json()["paciente"]["ci"] == "7700003"


def test_CP06_actualizar_paciente(client):
    a = client.post("/pacientes/", json={"nombre": "ana", "apellido": "prueba", "ci": "7700004"}).json()
    client.post("/pacientes/", json={"nombre": "beto", "apellido": "prueba", "ci": "7700005"})
    r = client.put(f"/api/pacientes/{a['id']}", json={"nombre": "ana maria", "ci": "7700014"})
    assert r.status_code == 200 and r.json()["nombre"] == "ANA MARIA" and r.json()["codigo_paciente"] == "7700014"
    assert client.get("/pacientes/buscar/7700014").json()["id"] == a["id"]
    assert client.put(f"/api/pacientes/{a['id']}", json={"ci": "7700005"}).status_code == 409
    assert client.put(f"/api/pacientes/{a['id']}", json={"nombre": "  "}).status_code == 400
    cambios = client.get("/auditoria", params={"paciente_id": a["id"]}).json()
    assert any(c.get("campo") == "nombre" and c.get("valor_nuevo") == "ANA MARIA" for c in cambios)


def test_CP07_identificador_inexistente(client):
    assert client.get("/pacientes/buscar/0000000").status_code == 404
    assert client.get("/api/paciente-completo/999999").status_code == 404
    assert client.put("/api/pacientes/999999", json={"nombre": "x"}).status_code == 404


def test_CP08_estado_del_paciente(client):
    p, e = nuevo(client, "7700006")
    client.post("/guardar-aptitud", json={"codigo_paciente": "7700006", "resultado": "APTO"})
    r = client.get(f"/semaforo/evaluacion/{e['id']}")
    assert r.status_code == 200 and r.json()["color"] == "VERDE"


def test_CP09_reporte_unificado(client):
    p, e = nuevo(client, "7700007")
    client.post("/guardar-cardiologia", json={"codigo_paciente": "7700007", "hta": "NO"})
    r = client.get(f"/api/informe-consolidado/7700007", params={"evaluacion_id": e["id"]})
    assert r.status_code == 200 and r.json()["evaluacion"]["id"] == e["id"]
    assert client.get("/api/informe-consolidado/0000000").status_code == 404


def test_CP10_eliminar_paciente_ficticio(client):
    p, _ = nuevo(client, "7700008")
    assert client.delete(f"/api/pacientes/{p['id']}").status_code == 400
    r = client.delete(f"/api/pacientes/{p['id']}", params={"confirmar_ci": "7700008"})
    assert r.status_code == 200
    assert any(x["ci"] == "7700008" for x in client.get("/papelera").json())


def test_CP11_consultar_registro_eliminado(client):
    p, _ = nuevo(client, "7700009")
    client.delete(f"/api/pacientes/{p['id']}", params={"confirmar_ci": "7700009"})
    assert client.get("/pacientes/buscar/7700009").status_code == 404
    assert client.get(f"/api/paciente-completo/{p['id']}").status_code == 404


def test_ID01_identificador_es_el_ci_normalizado(client):
    d = client.post("/pacientes/", json={"nombre": "x", "apellido": "y", "ci": " 4455667lp "}).json()
    assert d["ci"] == "4455667LP" and d["codigo_paciente"] == "4455667LP"
    assert client.post("/pacientes/", json={"nombre": "x", "apellido": "y", "ci": "  "}).status_code == 400


def test_ID02_unicidad_en_base_de_datos():
    assert models.Paciente.__table__.c.ci.unique is True
    assert models.Paciente.__table__.c.codigo_paciente.unique in (None, False)


def test_ID03_nueva_evaluacion_conserva_al_trabajador_y_la_anterior(client):
    p, e1 = nuevo(client, "7700010")
    client.post("/guardar-aptitud", json={"codigo_paciente": "7700010", "resultado": "APTO"})
    p2 = client.post("/pacientes/", json={"nombre": "x", "apellido": "y", "ci": "7700010"}).json()
    e2 = client.post("/evaluaciones/", json={"paciente_id": p2["id"], "tipo": "PERIODICO"}).json()
    client.post("/guardar-aptitud", json={"codigo_paciente": "7700010", "resultado": "NO APTO"}, headers={"X-Evaluacion": str(e2["id"])})
    assert p2["id"] == p["id"] and e2["id"] != e1["id"]
    a1 = client.get(f"/fichas/aptitud/{p['id']}", params={"evaluacion_id": e1["id"]}).json()["ficha"]
    a2 = client.get(f"/fichas/aptitud/{p['id']}", params={"evaluacion_id": e2["id"]}).json()["ficha"]
    assert a1["resultado"] == "APTO" and a2["resultado"] == "NO APTO"
    assert len(client.get(f"/pacientes/{p['id']}/evaluaciones").json()) == 2


@pytest.mark.parametrize("clave", list(FICHAS))
def test_FO01_cada_ficha_guarda_y_recupera_en_su_evaluacion(client, clave):
    ci = "78" + str(abs(hash(clave)) % 100000).zfill(5)
    p, e = nuevo(client, ci)
    campo = campo_de_prueba(FICHAS[clave])
    r = client.post(auth.RUTAS_FICHA[clave], json={"paciente_id": p["id"], "codigo_paciente": ci, campo: "VALOR FICTICIO"})
    assert r.status_code == 200, r.text
    f = client.get(f"/fichas/{clave}/{p['id']}", params={"evaluacion_id": e["id"]}).json()["ficha"]
    assert f[campo] == "VALOR FICTICIO" and f["evaluacion_id"] == e["id"] and f["paciente_id"] == p["id"]
    r = client.post(auth.RUTAS_FICHA[clave], json={"paciente_id": p["id"], "codigo_paciente": ci, campo: "VALOR CORREGIDO"})
    assert r.status_code == 200
    f2 = client.get(f"/fichas/{clave}/{p['id']}", params={"evaluacion_id": e["id"]}).json()["ficha"]
    assert f2["id"] == f["id"] and f2[campo] == "VALOR CORREGIDO"


@pytest.mark.parametrize("clave", list(FICHAS))
def test_FO02_ficha_rechaza_paciente_inexistente(client, clave):
    campo = campo_de_prueba(FICHAS[clave])
    r = client.post(auth.RUTAS_FICHA[clave], json={"paciente_id": 999999, "codigo_paciente": "0000000", campo: "X"})
    assert r.status_code in (400, 404), r.status_code


def test_FO03_oftalmologia_registra_ojo_derecho_e_izquierdo(client):
    p, e = nuevo(client, "7700011")
    datos = {"paciente_id": p["id"], "lentes": "SI", "od_l_sc": "20/40", "od_l_cc": "20/20", "od_l_dio": "-1.25",
             "oi_l_sc": "20/50", "oi_l_cc": "20/20", "oi_l_dio": "-1.50"}
    assert client.post("/ficha-oftalmo/", json=datos).status_code == 200
    f = client.get(f"/fichas/oftalmologia/{p['id']}", params={"evaluacion_id": e["id"]}).json()["ficha"]
    assert all(f[k] == v for k, v in datos.items() if k != "paciente_id")


def test_SE01_rutas_clinicas_exigen_autenticacion(anonimo):
    for metodo, ruta in [("GET", "/pacientes/"), ("POST", "/pacientes/"), ("GET", "/semaforo"), ("GET", "/admin/respaldo"),
                         ("PUT", "/api/pacientes/1"), ("DELETE", "/api/pacientes/1"), ("GET", "/auditoria")]:
        assert anonimo.request(metodo, ruta, json={}).status_code == 401, ruta


def test_SE02_errores_internos_no_exponen_detalles(client):
    import inspect
    from api import main
    assert "detail=str(e)" not in inspect.getsource(main)


def test_SE03_roles_restringen_edicion_de_identidad(client, anonimo):
    p = client.post("/pacientes/", json={"nombre": "x", "apellido": "y", "ci": "7700012"}).json()
    lec = client.post("/auth/usuarios", json={"nombre": "Lectura Ficticia", "rol": "LECTURA"}).json()
    esp = client.post("/auth/usuarios", json={"nombre": "Especialista Ficticio", "rol": "ESPECIALISTA", "fichas_permitidas": ["oftalmologia"]}).json()
    for u in (lec, esp):
        t = iniciar(anonimo, u["usuario"], u["temporal"], "clave-nueva-123")
        r = anonimo.put(f"/api/pacientes/{p['id']}", json={"nombre": "Z"}, headers={"Authorization": f"Bearer {t}"})
        assert r.status_code == 403, u["usuario"]
    enf = iniciar(anonimo, "enfermeria", "temporal-5", "clave-enf-123")
    r = anonimo.put(f"/api/pacientes/{p['id']}", json={"nombre": "Z"}, headers={"Authorization": f"Bearer {enf}"})
    assert r.status_code == 200
    r = anonimo.delete(f"/api/pacientes/{p['id']}", params={"confirmar_ci": "7700012"}, headers={"Authorization": f"Bearer {enf}"})
    assert r.status_code == 403
