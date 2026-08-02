from sqlalchemy.orm import Session
from . import models

def get_paciente_by_ci(db: Session, ci: str):
    return db.query(models.Paciente).filter(models.Paciente.ci == ci).first()

def create_paciente(db: Session, data: dict):
    existente = db.query(models.Paciente).filter(models.Paciente.ci == data.get("ci")).first()
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
    valid_keys = [col.name for col in models.AntecedentesP2.__table__.columns]
    data_filtered = {k: v for k, v in data.items() if k in valid_keys}
    
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
    valid_keys = [col.name for col in models.HabitosRiesgosP3.__table__.columns]
    data_filtered = {k: v for k, v in data.items() if k in valid_keys}
    
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
    try:
        db.query(models.DeclaracionJurada).filter(models.DeclaracionJurada.paciente_id == paciente_id).delete()
        db.query(models.AntecedentesP2).filter(models.AntecedentesP2.paciente_id == paciente_id).delete()
        db.query(models.HabitosRiesgosP3).filter(models.HabitosRiesgosP3.paciente_id == paciente_id).delete()
        db_obj = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return True
        return False
    except Exception:
        db.rollback()
        return False

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
