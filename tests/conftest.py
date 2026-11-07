import os
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://ohs@/ohs_test?host=/tmp&port=5433")

from fastapi.testclient import TestClient
from api.database import Base, engine
from api.main import app
from api.database import SessionLocal
from api import semaforo


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        semaforo.sembrar_reglas(db)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def paciente(client):
    r = client.post("/pacientes/", json={"nombre": "Juan", "apellido": "Perez Quispe", "ci": "9999001"})
    assert r.status_code == 200
    return r.json()
