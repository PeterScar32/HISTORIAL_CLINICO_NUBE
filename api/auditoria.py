import datetime
import decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column, Integer, String, Text, DateTime, func, event, inspect, desc
from sqlalchemy.orm import Session

from . import models
from .database import Base, SessionLocal
from .crud import PROFESIONAL_ACTUAL, EVALUACION_ACTUAL, nombre_profesional, evaluacion_vigente

router = APIRouter()

IGNORAR = {"id", "creado_en", "registrado_por", "paciente_id", "evaluacion_id"}

FICHAS = {
    "declaracion": models.DeclaracionJurada,
    "antecedentes": models.AntecedentesP2,
    "habitos": models.HabitosRiesgosP3,
    "oftalmologia": models.FichaOftalmologica,
    "psicologia": models.FichaPsicologia,
    "espirometria": models.FichaEspirometria,
    "cardiologia": models.FichaCardiologia,
    "altura": models.FichaAltura,
    "electroencefalograma": models.FichaElectroencefalograma,
    "aptitud": models.FichaAptitud,
    "aptitud_fisica": models.FichaAptitudFisica,
    "historial_clinico": models.HistorialClinico,
    "osteomuscular": models.FichaOsteomuscular,
}
CLAVE_POR_MODELO = {m: k for k, m in FICHAS.items()}
AUDITADOS = tuple(FICHAS.values()) + (models.Paciente, models.Evaluacion)


class Auditoria(Base):
    __tablename__ = "auditoria"
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, server_default=func.now(), index=True)
    usuario = Column(String)
    accion = Column(String, nullable=False)
    tabla = Column(String, nullable=False, index=True)
    ficha = Column(String)
    registro_id = Column(Integer)
    paciente_id = Column(Integer, index=True)
    evaluacion_id = Column(Integer, index=True)
    campo = Column(String)
    valor_anterior = Column(Text)
    valor_nuevo = Column(Text)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def texto(v):
    if v is None:
        return None
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    if isinstance(v, decimal.Decimal):
        return str(v)
    return str(v)


def vacio(v):
    return v is None or (isinstance(v, str) and v.strip() == "")


def usuario_actual(connection):
    clave = PROFESIONAL_ACTUAL.get()
    return (nombre_profesional(connection, clave) if clave else None) or "SIN SESIÓN"


def paciente_de(obj):
    if isinstance(obj, models.Paciente):
        return obj.id
    return getattr(obj, "paciente_id", None)


def evaluacion_de(obj):
    if isinstance(obj, models.Evaluacion):
        return obj.id
    return getattr(obj, "evaluacion_id", None)


@event.listens_for(SessionLocal, "before_flush")
def registrar_cambios(session, flush_context, instances):
    for obj in list(session.dirty):
        if not isinstance(obj, AUDITADOS) or not session.is_modified(obj, include_collections=False):
            continue
        estado = inspect(obj)
        usuario = usuario_actual(session.connection())
        for attr in estado.mapper.column_attrs:
            if attr.key in IGNORAR:
                continue
            hist = estado.attrs[attr.key].history
            if not hist.has_changes():
                continue
            antes = hist.deleted[0] if hist.deleted else None
            despues = hist.added[0] if hist.added else None
            if texto(antes) == texto(despues) or (vacio(antes) and vacio(despues)):
                continue
            session.add(Auditoria(
                usuario=usuario, accion="MODIFICACION", tabla=obj.__tablename__,
                ficha=CLAVE_POR_MODELO.get(type(obj)), registro_id=obj.id,
                paciente_id=paciente_de(obj), evaluacion_id=evaluacion_de(obj),
                campo=attr.key, valor_anterior=texto(antes), valor_nuevo=texto(despues),
            ))


def _registrar_creacion(mapper, connection, target):
    connection.execute(Auditoria.__table__.insert().values(
        usuario=usuario_actual(connection), accion="CREACION", tabla=target.__tablename__,
        ficha=CLAVE_POR_MODELO.get(type(target)), registro_id=target.id,
        paciente_id=paciente_de(target), evaluacion_id=evaluacion_de(target),
    ))


for _m in AUDITADOS:
    event.listen(_m, "after_insert", _registrar_creacion)


def registrar_eliminacion(db: Session, tabla: str, registro_id: int, paciente_id: int, detalle: str):
    db.add(Auditoria(usuario=usuario_actual(db.connection()), accion="ELIMINACION", tabla=tabla,
                     registro_id=registro_id, paciente_id=paciente_id, valor_anterior=detalle))


def guardar_en_evaluacion(db: Session, nueva):
    modelo = type(nueva)
    if not nueva.paciente_id:
        db.add(nueva)
        return nueva
    ev = evaluacion_vigente(db, nueva.paciente_id, getattr(nueva, "evaluacion_id", None) or EVALUACION_ACTUAL.get())
    nueva.evaluacion_id = ev.id
    existente = db.query(modelo).filter(modelo.paciente_id == nueva.paciente_id, modelo.evaluacion_id == ev.id).order_by(desc(modelo.id)).first()
    if not existente:
        db.add(nueva)
        return nueva
    for col in modelo.__table__.columns:
        if col.name in IGNORAR or col.name == "codigo_paciente":
            continue
        setattr(existente, col.name, getattr(nueva, col.name))
    return existente


def fila_a_dict(fila):
    return {c.name: getattr(fila, c.name) for c in fila.__table__.columns} if fila else None


@router.get("/fichas/{clave}/{paciente_id}")
def ficha_actual(clave: str, paciente_id: int, evaluacion_id: Optional[int] = None, db: Session = Depends(get_db)):
    modelo = FICHAS.get(clave)
    if not modelo:
        raise HTTPException(status_code=404, detail="Ficha desconocida")
    q = db.query(models.Evaluacion).filter(models.Evaluacion.paciente_id == paciente_id)
    ev = (q.filter(models.Evaluacion.id == evaluacion_id).first() if evaluacion_id else None) or q.order_by(desc(models.Evaluacion.id)).first()
    if not ev:
        return {"evaluacion_id": None, "evaluacion": None, "ficha": None}
    fila = db.query(modelo).filter(modelo.paciente_id == paciente_id, modelo.evaluacion_id == ev.id).order_by(desc(modelo.id)).first()
    return {"evaluacion_id": ev.id, "evaluacion": fila_a_dict(ev), "ficha": fila_a_dict(fila)}


@router.get("/api/expediente/{paciente_id}")
def expediente(paciente_id: int, evaluacion_id: Optional[int] = None, db: Session = Depends(get_db)):
    p = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    q = db.query(models.Evaluacion).filter(models.Evaluacion.paciente_id == paciente_id)
    ev = (q.filter(models.Evaluacion.id == evaluacion_id).first() if evaluacion_id else None) or q.order_by(desc(models.Evaluacion.id)).first()
    fichas = {}
    if ev:
        for clave, modelo in FICHAS.items():
            fila = db.query(modelo).filter(modelo.paciente_id == paciente_id, modelo.evaluacion_id == ev.id).order_by(desc(modelo.id)).first()
            if not fila and clave == "declaracion":
                fila = db.query(modelo).filter(modelo.paciente_id == paciente_id).order_by(desc(modelo.id)).first()
            fichas[clave] = fila_a_dict(fila)
    return {"paciente": fila_a_dict(p), "evaluacion": fila_a_dict(ev), "fichas": fichas}


@router.get("/auditoria")
def consultar_auditoria(paciente_id: Optional[int] = None, evaluacion_id: Optional[int] = None,
                        ficha: Optional[str] = None, limite: int = 300, db: Session = Depends(get_db)):
    q = db.query(Auditoria)
    if paciente_id:
        q = q.filter(Auditoria.paciente_id == paciente_id)
    if evaluacion_id:
        q = q.filter(Auditoria.evaluacion_id == evaluacion_id)
    if ficha:
        q = q.filter(Auditoria.ficha == ficha)
    return [fila_a_dict(a) for a in q.order_by(desc(Auditoria.id)).limit(min(limite, 2000)).all()]


@router.get("/admin/respaldo")
def respaldo(db: Session = Depends(get_db)):
    tablas = {}
    for tabla in Base.metadata.sorted_tables:
        filas = db.execute(tabla.select()).mappings().all()
        tablas[tabla.name] = [{k: texto(v) if isinstance(v, (datetime.date, datetime.datetime, decimal.Decimal)) else v for k, v in f.items()} for f in filas]
    return {"sistema": "HC NUBE OHS", "version_respaldo": 1, "fecha": datetime.datetime.now().isoformat(),
            "orden_tablas": [t.name for t in Base.metadata.sorted_tables], "tablas": tablas}
