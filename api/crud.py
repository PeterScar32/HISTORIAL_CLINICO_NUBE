from sqlalchemy.orm import Session
from . import models

import contextvars
from sqlalchemy import func, or_, event

FICHAS_POR_ID = [
    models.DeclaracionJurada, models.AntecedentesP2, models.HabitosRiesgosP3,
    models.FichaOftalmologica, models.FichaPsicologia, models.FichaEspirometria,
    models.FichaCardiologia, models.FichaAltura, models.FichaElectroencefalograma,
    models.FichaAptitud, models.FichaAptitudFisica, models.HistorialClinico,
    models.FichaOsteomuscular, models.Evaluacion,
]
FICHAS_POR_CODIGO = [models.FichaAptitudFisica, models.FichaOsteomuscular, models.HistorialClinico]


def columnas(modelo):
    return {c.name for c in modelo.__table__.columns}


def filtrar(modelo, data: dict, excluir=("id",)):
    validas = columnas(modelo) - set(excluir)
    return {k: v for k, v in data.items() if k in validas}


def normalizar_ci(valor) -> str:
    return str(valor or "").strip().upper()


def evaluacion_vigente(db: Session, paciente_id: int, evaluacion_id=None):
    q = db.query(models.Evaluacion).filter(models.Evaluacion.paciente_id == paciente_id)
    if evaluacion_id:
        ev = q.filter(models.Evaluacion.id == int(evaluacion_id)).first()
        if ev:
            return ev
    ev = q.order_by(models.Evaluacion.id.desc()).first()
    if not ev:
        ev = models.Evaluacion(paciente_id=paciente_id, tipo="INICIAL")
        db.add(ev)
        db.flush()
    return ev


def crear_evaluacion(db: Session, data: dict):
    if isinstance(data.get("fichas_requeridas"), (list, tuple)):
        data["fichas_requeridas"] = ",".join(str(x) for x in data["fichas_requeridas"])
    data = filtrar(models.Evaluacion, data, ("id", "creado_en"))
    for k in ("empresa", "puesto", "tipo", "observaciones"):
        if data.get(k):
            data[k] = " ".join(str(data[k]).upper().split())
    if not data.get("fecha"):
        data.pop("fecha", None)
    ev = models.Evaluacion(**data)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def _upsert_por_evaluacion(db: Session, modelo, data: dict):
    data = filtrar(modelo, data)
    p_id = int(data["paciente_id"])
    ev = evaluacion_vigente(db, p_id, data.get("evaluacion_id"))
    data["evaluacion_id"] = ev.id
    existente = db.query(modelo).filter(modelo.paciente_id == p_id, modelo.evaluacion_id == ev.id).order_by(modelo.id.desc()).first()
    if existente:
        for key, value in data.items(): setattr(existente, key, value)
    else:
        existente = modelo(**data)
        db.add(existente)
    db.commit()
    db.refresh(existente)
    return existente


def get_paciente_by_ci(db: Session, ci: str):
    return db.query(models.Paciente).filter(func.upper(models.Paciente.ci) == normalizar_ci(ci)).first()


def buscar_paciente(db: Session, codigo: str):
    c = normalizar_ci(codigo)
    if not c:
        return None
    return db.query(models.Paciente).filter(
        or_(func.upper(models.Paciente.ci) == c, func.upper(models.Paciente.codigo_paciente) == c)
    ).order_by(models.Paciente.id).first()


def create_paciente(db: Session, data: dict):
    data = filtrar(models.Paciente, data)
    data["ci"] = normalizar_ci(data.get("ci"))
    data["codigo_paciente"] = data["ci"]
    for k in ("nombre", "apellido"):
        if data.get(k):
            data[k] = str(data[k]).strip().upper()
    existente = get_paciente_by_ci(db, data["ci"])
    if existente:
        for key, value in data.items(): setattr(existente, key, value)
        db.commit()
        db.refresh(existente)
        return existente
    db_obj = models.Paciente(**data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def upsert_filiacion(db: Session, data: dict):
    return _upsert_por_evaluacion(db, models.DeclaracionJurada, data)


def upsert_p2(db: Session, data: dict):
    return _upsert_por_evaluacion(db, models.AntecedentesP2, data)


def upsert_p3(db: Session, data: dict):
    return _upsert_por_evaluacion(db, models.HabitosRiesgosP3, data)


def create_enfermera(db: Session, data: dict):
    data = filtrar(models.Enfermera, data, ("id_enfe",))
    ci = data.get("ci_enfe")
    existente = db.query(models.Enfermera).filter(models.Enfermera.ci_enfe == ci).first()
    if existente:
        for key, value in data.items(): setattr(existente, key, value)
    else:
        existente = models.Enfermera(**data)
        db.add(existente)
    db.commit()
    db.refresh(existente)
    return existente

def create_doctor(db: Session, data: dict):
    data = filtrar(models.Doctor, data, ("id_doc",))
    ci = data.get("ci_doc")
    existente = db.query(models.Doctor).filter(models.Doctor.ci_doc == ci).first()
    if existente:
        for key, value in data.items(): setattr(existente, key, value)
    else:
        existente = models.Doctor(**data)
        db.add(existente)
    db.commit()
    db.refresh(existente)
    return existente

def delete_paciente(db: Session, paciente_id: int):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        return False
    try:
        for modelo in FICHAS_POR_ID:
            db.query(modelo).filter(modelo.paciente_id == paciente_id).delete(synchronize_session=False)
        codigos = {c for c in (paciente.codigo_paciente, paciente.ci) if c}
        for modelo in FICHAS_POR_CODIGO:
            db.query(modelo).filter(modelo.codigo_paciente.in_(codigos)).delete(synchronize_session=False)
        db.delete(paciente)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise

def create_ficha_psicologia(db: Session, data: dict):
    valid_keys = [col.name for col in models.FichaPsicologia.__table__.columns]
    data_filtered = {k: v for k, v in data.items() if k in valid_keys}
    
    db_obj = models.FichaPsicologia(**data_filtered)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def upsert_electro(db: Session, data: dict):
    # Filtro de seguridad: solo toma columnas que existen en la tabla
    valid_keys = [col.name for col in models.FichaElectroencefalograma.__table__.columns]
    data_filtered = {k: v for k, v in data.items() if k in valid_keys}
    
    db_obj = models.FichaElectroencefalograma(**data_filtered)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


PROFESIONAL_ACTUAL = contextvars.ContextVar("profesional_actual", default=None)
EVALUACION_ACTUAL = contextvars.ContextVar("evaluacion_actual", default=None)
RESPONSABLE_ACTUAL = contextvars.ContextVar("responsable_actual", default=None)


def nombre_profesional(connection, clave):
    try:
        tipo, ident = str(clave).split(":", 1)
        ident = int(ident)
    except (ValueError, TypeError):
        return None
    if tipo == "usr":
        t = models.Base.metadata.tables.get("usuarios")
        f = connection.execute(t.select().where(t.c.id == ident)).mappings().first() if t is not None else None
        if f:
            return f["nombre"] + (f" · {f['cargo']}" if f["cargo"] else "")
    if tipo == "doc":
        t = models.Doctor.__table__
        f = connection.execute(t.select().where(t.c.id_doc == ident)).mappings().first()
        if f:
            return " ".join(x for x in ["DR(A).", f["nombre_doc"], f["appaterno_doc"], f["apmaterno_doc"]] if x) + (f" · {f['especialidad']}" if f["especialidad"] else "")
    if tipo == "enf":
        t = models.Enfermera.__table__
        f = connection.execute(t.select().where(t.c.id_enfe == ident)).mappings().first()
        if f:
            return " ".join(x for x in ["LIC.", f["nombre_enfe"], f["appaterno_enfe"], f["apmaterno_enfe"]] if x) + " · ENFERMERÍA"
    return None


def _usuario_responsable(connection, uid):
    t = models.Base.metadata.tables.get("usuarios")
    if t is None or not uid:
        return None
    f = connection.execute(t.select().where(t.c.id == int(uid))).mappings().first()
    if f and f["activo"] and f["rol"] in ("MEDICO", "ESPECIALISTA"):
        return f
    return None


def _asignar_responsable(connection, target, al_crear):
    if not hasattr(target, "responsable_id"):
        return
    pedido = RESPONSABLE_ACTUAL.get()
    if pedido == 0:
        target.responsable_id = None
        target.responsable = None
        return
    f = _usuario_responsable(connection, pedido)
    if f is None and al_crear and not target.responsable_id:
        clave = PROFESIONAL_ACTUAL.get() or ""
        if clave.startswith("usr:"):
            f = _usuario_responsable(connection, clave[4:])
    if f is not None:
        target.responsable_id = f["id"]
        detalle = f["especialidad"] or f["cargo"]
        target.responsable = f["nombre"] + (f" · {detalle}" if detalle else "")


def registrar_profesional(mapper, connection, target):
    clave = PROFESIONAL_ACTUAL.get()
    if clave and not getattr(target, "registrado_por", None):
        nombre = nombre_profesional(connection, clave)
        if nombre:
            target.registrado_por = nombre
    _asignar_responsable(connection, target, True)


def actualizar_responsable(mapper, connection, target):
    _asignar_responsable(connection, target, False)


def asignar_evaluacion(mapper, connection, target):
    registrar_profesional(mapper, connection, target)
    if getattr(target, "evaluacion_id", None) or not getattr(target, "paciente_id", None):
        return
    tabla = models.Evaluacion.__table__
    fila = connection.execute(
        tabla.select().with_only_columns(tabla.c.id).where(tabla.c.paciente_id == target.paciente_id).order_by(tabla.c.id.desc()).limit(1)
    ).first()
    if fila:
        target.evaluacion_id = fila[0]
    else:
        target.evaluacion_id = connection.execute(tabla.insert().values(paciente_id=target.paciente_id, tipo="INICIAL").returning(tabla.c.id)).scalar()


for _modelo in FICHAS_POR_ID:
    if _modelo is not models.Evaluacion:
        event.listen(_modelo, "before_insert", asignar_evaluacion)
        event.listen(_modelo, "before_update", actualizar_responsable)
