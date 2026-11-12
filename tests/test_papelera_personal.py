from api import auth
from api.database import SessionLocal
from tests.conftest import iniciar


def nuevo(client, nombre, rol="ESPECIALISTA"):
    r = client.post("/auth/usuarios", json={"nombre": nombre, "rol": rol, "especialidad": "Cardiología", "fichas_permitidas": ["cardiologia"]})
    assert r.status_code == 200
    return r.json()


def test_PP01_eliminar_personal_lo_envia_a_la_papelera(client):
    u = nuevo(client, "Ana Ficticia Prueba")
    assert client.delete(f"/auth/usuarios/{u['id']}").json() == {"eliminado": True}
    assert u["id"] not in [x["id"] for x in client.get("/auth/usuarios").json()]
    pap = client.get("/papelera/personal").json()
    assert len(pap) == 1 and pap[0]["usuario"] == u["usuario"] and pap[0]["rol"] == "ESPECIALISTA" and pap[0]["restaurado_en"] is None
    assert client.get("/papelera").json() == []
    assert u["id"] not in [x["id"] for x in client.get("/auth/profesionales").json()]
    assert client.post("/auth/login", json={"usuario": u["usuario"], "clave": u["temporal"]}).status_code == 401
    aud = [a for a in client.get("/auditoria").json() if a["tabla"] == "usuarios"]
    assert any(a["accion"] == "ELIMINACION" for a in aud)


def test_PP02_restaurar_devuelve_usuario_rol_y_clave(client, anonimo):
    u = nuevo(client, "Luis Ficticio Prueba")
    client.delete(f"/auth/usuarios/{u['id']}")
    item = client.get("/papelera/personal").json()[0]
    assert client.post(f"/papelera/{item['id']}/restaurar").json()["restaurado"] is True
    lista = {x["id"]: x for x in client.get("/auth/usuarios").json()}
    assert lista[u["id"]]["activo"] is True and lista[u["id"]]["rol"] == "ESPECIALISTA"
    assert client.post("/auth/login", json={"usuario": u["usuario"], "clave": u["temporal"]}).status_code == 200
    assert client.post(f"/papelera/{item['id']}/restaurar").status_code == 404
    assert client.get("/papelera/personal").json()[0]["restaurado_en"] is not None


def test_PP03_conserva_estado_desactivado_y_bloquea_edicion(client):
    u = nuevo(client, "Rosa Ficticia Prueba")
    client.put(f"/auth/usuarios/{u['id']}", json={"activo": False})
    client.delete(f"/auth/usuarios/{u['id']}")
    assert client.put(f"/auth/usuarios/{u['id']}", json={"activo": True}).status_code == 404
    assert client.post(f"/auth/usuarios/{u['id']}/restablecer", json={}).status_code == 404
    assert client.delete(f"/auth/usuarios/{u['id']}").status_code == 404
    item = client.get("/papelera/personal").json()[0]
    client.post(f"/papelera/{item['id']}/restaurar")
    assert {x["id"]: x for x in client.get("/auth/usuarios").json()}[u["id"]]["activo"] is False


def test_PP04_no_se_elimina_a_si_mismo_ni_al_ultimo_medico(client):
    yo = client.get("/auth/yo").json()
    assert client.delete(f"/auth/usuarios/{yo['id']}").status_code == 400
    with SessionLocal() as db:
        for x in db.query(auth.Usuario).filter(auth.Usuario.rol == auth.ROL_MEDICO, auth.Usuario.id != yo["id"]).all():
            x.activo = False
        db.commit()
    otro = nuevo(client, "Medico Ficticio Dos", "MEDICO")
    assert client.delete(f"/auth/usuarios/{otro['id']}").status_code == 200
    assert client.get("/papelera/personal").json()[0]["nombre"] == "MEDICO FICTICIO DOS"


def test_PP05_el_personal_eliminado_no_reaparece_al_reiniciar(client):
    with SessionLocal() as db:
        kn = db.query(auth.Usuario).filter(auth.Usuario.usuario == "knoya").first().id
    assert client.delete(f"/auth/usuarios/{kn}").status_code == 200
    with SessionLocal() as db:
        auth.sembrar_usuarios(db)
        assert db.query(auth.Usuario).filter(auth.Usuario.usuario == "knoya").count() == 1
    assert kn not in [x["id"] for x in client.get("/auth/usuarios").json()]
    assert "knoya" not in [x["usuario"] for x in client.get("/auth/perfiles").json()]


def test_PP06_solo_medico(client, anonimo):
    tok = iniciar(anonimo, "enfermeria", "temporal-5", "clave-enfermeria-1")
    h = {"Authorization": f"Bearer {tok}"}
    u = nuevo(client, "Eva Ficticia Prueba")
    assert anonimo.get("/papelera/personal", headers=h).status_code == 403
    assert anonimo.delete(f"/auth/usuarios/{u['id']}", headers=h).status_code == 403
