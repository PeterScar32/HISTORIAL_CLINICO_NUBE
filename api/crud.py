from sqlalchemy.orm import Session
from . import models

from sqlalchemy import func, or_

FICHAS_POR_ID = [
    models.DeclaracionJurada, models.AntecedentesP2, models.HabitosRiesgosP3,
    models.FichaOftalmologica, models.FichaPsicologia, models.FichaEspirometria,
    models.FichaCardiologia, models.FichaAltura, models.FichaElectroencefalograma,
    models.FichaAptitud, models.FichaAptitudFisica, models.HistorialClinico,
    models.FichaOsteomuscular,
]
FICHAS_POR_CODIGO = [models.FichaAptitudFisica, models.FichaOsteomuscular, models.HistorialClinico]


def columnas(modelo):
    return {c.name for c in modelo.__table__.columns}


def filtrar(modelo, data: dict, excluir=("id",)):
    validas = columnas(modelo) - set(excluir)
    return {k: v for k, v in data.items() if k in validas}


def normalizar_ci(valor) -> str:
    return str(valor or "").strip().upper()


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
    data = filtrar(models.DeclaracionJurada, data)
    p_id = data.get("paciente_id")
    existente = db.query(models.DeclaracionJurada).filter(models.DeclaracionJurada.paciente_id == p_id).first()
    if existente:
        for key, value in data.items(): setattr(existente, key, value)
    else:
        existente = models.DeclaracionJurada(**data)
        db.add(existente)
    db.commit()
    db.refresh(existente)
    return existente

def upsert_p2(db: Session, data: dict):
    p_id = data.get("paciente_id")
    # Filtro de seguridad para evitar errores de columnas no existentes en BD
    data_filtered = filtrar(models.AntecedentesP2, data)
    
    existente = db.query(models.AntecedentesP2).filter(models.AntecedentesP2.paciente_id == p_id).first()
    if existente:
        for key, value in data_filtered.items(): setattr(existente, key, value)
    else:
        existente = models.AntecedentesP2(**data_filtered)
        db.add(existente)
    db.commit()
    db.refresh(existente)
    return existente

def upsert_p3(db: Session, data: dict):
    p_id = data.get("paciente_id")
    data_filtered = filtrar(models.HabitosRiesgosP3, data)
    
    existente = db.query(models.HabitosRiesgosP3).filter(models.HabitosRiesgosP3.paciente_id == p_id).first()
    if existente:
        for key, value in data_filtered.items(): setattr(existente, key, value)
    else:
        existente = models.HabitosRiesgosP3(**data_filtered)
        db.add(existente)
    db.commit()
    db.refresh(existente)
    return existente

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
