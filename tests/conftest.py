import json
import os
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://ohs@/ohs_test?host=/tmp&port=5433")
os.environ["SECRET_KEY"] = "clave-de-prueba"
os.environ["OHS_CLAVES_INICIALES"] = json.dumps({"mecondarco": "temporal-1", "enfermeria": "temporal-5"})

from fastapi.testclient import TestClient
from api.database import Base, engine, SessionLocal
from api.main import app
from api import semaforo, auth


def iniciar(c, usuario, temporal, nueva):
    r = c.post("/auth/login", json={"usuario": usuario, "clave": temporal}).json()
    r = c.post("/auth/cambiar-clave", json={"actual": temporal, "nueva": nueva},
               headers={"Authorization": f"Bearer {r['token']}"}).json()
    return r["token"]


@pytest.fixture()
def anonimo():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        semaforo.sembrar_reglas(db)
        auth.sembrar_usuarios(db)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def client(anonimo):
    token = iniciar(anonimo, "mecondarco", "temporal-1", "clave-medico-1")
    anonimo.headers.update({"Authorization": f"Bearer {token}"})
    return anonimo


@pytest.fixture()
def paciente(client):
    r = client.post("/pacientes/", json={"nombre": "Juan", "apellido": "Perez Quispe", "ci": "9999001"})
    assert r.status_code == 200
    return r.json()
