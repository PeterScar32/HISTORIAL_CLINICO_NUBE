import json
import sys

from sqlalchemy import text

from api.database import Base, engine
from api import models, semaforo, auth, auditoria


def restaurar(ruta):
    datos = json.load(open(ruta, encoding="utf-8"))
    Base.metadata.create_all(bind=engine)
    tablas = {t.name: t for t in Base.metadata.sorted_tables}
    with engine.begin() as con:
        for nombre in tablas:
            if con.execute(text(f"SELECT count(*) FROM {nombre}")).scalar():
                raise SystemExit(f"La tabla {nombre} no está vacía: restaure solo sobre una base nueva.")
        for nombre in datos["orden_tablas"]:
            filas = datos["tablas"].get(nombre, [])
            if nombre in tablas and filas:
                validas = {c.name for c in tablas[nombre].columns}
                con.execute(tablas[nombre].insert(), [{k: v for k, v in f.items() if k in validas} for f in filas])
        for nombre, tabla in tablas.items():
            pk = list(tabla.primary_key.columns)
            if len(pk) == 1 and str(pk[0].type) == "INTEGER":
                col = pk[0].name
                con.execute(text(f"SELECT setval(pg_get_serial_sequence('{nombre}', '{col}'), COALESCE((SELECT max({col}) FROM {nombre}), 0) + 1, false)"))
    print("Restauración completa:", {n: len(f) for n, f in datos["tablas"].items() if f})


if __name__ == "__main__":
    restaurar(sys.argv[1])
