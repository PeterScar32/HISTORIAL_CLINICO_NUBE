import unicodedata
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column, Integer, String, Boolean, desc
from sqlalchemy.orm import Session

from . import models
from .database import Base, SessionLocal

router = APIRouter()

ORDEN = {"GRIS": 0, "VERDE": 1, "AMARILLO": 2, "ROJO": 3}


class ReglaSemaforo(Base):
    __tablename__ = "reglas_semaforo"
    id = Column(Integer, primary_key=True, index=True)
    patron = Column(String, nullable=False)
    tipo = Column(String, default="CONTIENE")
    color = Column(String, nullable=False)
    prioridad = Column(Integer, default=100)
    descripcion = Column(String)
    activo = Column(Boolean, default=True)


REGLAS_INICIALES = [
    ("NO APTO", "CONTIENE", "ROJO", 10, "Conclusión NO APTO registrada por el profesional"),
    ("RESTRICCION", "CONTIENE", "AMARILLO", 20, "Apto con restricción: requiere seguimiento"),
    ("RECOMENDACION", "CONTIENE", "AMARILLO", 30, "Apto con recomendación: requiere seguimiento"),
    ("APTO", "IGUAL", "VERDE", 40, "Conclusión APTO registrada por el profesional"),
]

FUENTES = [
    ("aptitud", "Aptitud ocupacional", models.FichaAptitud, ["resultado"]),
    ("aptitud_fisica", "Aptitud física", models.FichaAptitudFisica, ["resultado_fisico", "resultado_psicologico"]),
    ("psicologia", "Psicología", models.FichaPsicologia, ["resultado_psicologico"]),
    ("osteomuscular", "Osteomuscular", models.FichaOsteomuscular, ["concepto_aptitud"]),
    ("historial_clinico", "Historia clínica", models.HistorialClinico, ["aptitud_no_apto", "aptitud_restriccion", "aptitud_apto"]),
]

FICHAS = {
    "declaracion": ("Declaración jurada P1", models.DeclaracionJurada),
    "antecedentes": ("Declaración jurada P2", models.AntecedentesP2),
    "habitos": ("Declaración jurada P3", models.HabitosRiesgosP3),
    "oftalmologia": ("Oftalmología", models.FichaOftalmologica),
    "psicologia": ("Psicología", models.FichaPsicologia),
    "espirometria": ("Espirometría", models.FichaEspirometria),
    "cardiologia": ("Cardiología", models.FichaCardiologia),
    "altura": ("Altura", models.FichaAltura),
    "electroencefalograma": ("Electroencefalograma", models.FichaElectroencefalograma),
    "aptitud": ("Aptitud ocupacional", models.FichaAptitud),
    "aptitud_fisica": ("Aptitud física", models.FichaAptitudFisica),
    "historial_clinico": ("Historia clínica", models.HistorialClinico),
    "osteomuscular": ("Osteomuscular", models.FichaOsteomuscular),
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def normalizar(texto) -> str:
    t = unicodedata.normalize("NFD", str(texto or "")).encode("ascii", "ignore").decode()
    return " ".join(t.upper().replace("_", " ").split())


def sembrar_reglas(db: Session):
    if db.query(ReglaSemaforo).count() == 0:
        for patron, tipo, color, prioridad, descripcion in REGLAS_INICIALES:
            db.add(ReglaSemaforo(patron=patron, tipo=tipo, color=color, prioridad=prioridad, descripcion=descripcion))
        db.commit()


def reglas_activas(db: Session):
    return db.query(ReglaSemaforo).filter(ReglaSemaforo.activo.is_(True)).order_by(ReglaSemaforo.prioridad, ReglaSemaforo.id).all()


def clasificar(valor, reglas):
    v = normalizar(valor)
    if not v:
        return None
    for r in reglas:
        p = normalizar(r.patron)
        if (r.tipo == "IGUAL" and v == p) or (r.tipo != "IGUAL" and p in v):
            return {"color": r.color, "regla": r.descripcion or r.patron, "regla_id": r.id}
    return {"color": "AMARILLO", "regla": "Valor sin regla definida: requiere revisión", "regla_id": None}


def ultima(db, modelo, evaluacion_id):
    return db.query(modelo).filter(modelo.evaluacion_id == evaluacion_id).order_by(desc(modelo.id)).first()


def semaforo_evaluacion(db: Session, ev, reglas):
    detalle = []
    for clave, nombre, modelo, campos in FUENTES:
        ficha = ultima(db, modelo, ev.id)
        if not ficha:
            continue
        for campo in campos:
            valor = getattr(ficha, campo, None)
            res = clasificar(valor, reglas)
            if res:
                detalle.append({"ficha": clave, "nombre": nombre, "campo": campo, "valor": valor, **res})
    color = max((d["color"] for d in detalle), key=lambda c: ORDEN.get(c, 0), default="GRIS")
    hechas = [k for k, (_, m) in FICHAS.items() if ultima(db, m, ev.id)]
    faltantes = [FICHAS[k][0] for k in FICHAS if k not in hechas]
    motivo = next((d for d in detalle if d["color"] == color), None)
    return {
        "color": color,
        "motivo": f'{motivo["nombre"]}: {motivo["valor"]}' if motivo else "Sin conclusión registrada",
        "detalle": detalle,
        "completitud": {"hechas": len(hechas), "total": len(FICHAS), "faltantes": faltantes},
    }


@router.get("/semaforo/evaluacion/{evaluacion_id}")
def ver_semaforo_evaluacion(evaluacion_id: int, db: Session = Depends(get_db)):
    ev = db.query(models.Evaluacion).filter(models.Evaluacion.id == evaluacion_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    return {"evaluacion_id": ev.id, **semaforo_evaluacion(db, ev, reglas_activas(db))}


@router.get("/semaforo")
def panel_semaforo(empresa: Optional[str] = None, desde: Optional[str] = None, hasta: Optional[str] = None,
                   solo_ultima: bool = False, db: Session = Depends(get_db)):
    q = db.query(models.Evaluacion, models.Paciente).join(models.Paciente, models.Evaluacion.paciente_id == models.Paciente.id)
    if empresa:
        q = q.filter(models.Evaluacion.empresa == normalizar_empresa(empresa))
    if desde:
        q = q.filter(models.Evaluacion.fecha >= desde)
    if hasta:
        q = q.filter(models.Evaluacion.fecha <= hasta)
    filas = q.order_by(desc(models.Evaluacion.fecha), desc(models.Evaluacion.id)).all()
    reglas = reglas_activas(db)
    vistos, items = set(), []
    for ev, p in filas:
        if solo_ultima and p.id in vistos:
            continue
        vistos.add(p.id)
        items.append({
            "evaluacion_id": ev.id, "paciente_id": p.id, "ci": p.ci,
            "nombre": f"{p.apellido or ''} {p.nombre or ''}".strip(),
            "fecha": ev.fecha, "empresa": ev.empresa, "puesto": ev.puesto, "tipo": ev.tipo,
            **semaforo_evaluacion(db, ev, reglas),
        })
    resumen = {c: sum(1 for i in items if i["color"] == c) for c in ("ROJO", "AMARILLO", "VERDE", "GRIS")}
    return {"total": len(items), "resumen": resumen, "items": items}


def normalizar_empresa(nombre: str) -> str:
    return " ".join(str(nombre).strip().upper().split())


@router.get("/empresas")
def listar_empresas(db: Session = Depends(get_db)):
    filas = db.query(models.Evaluacion.empresa).filter(models.Evaluacion.empresa.isnot(None)).distinct().all()
    return sorted({f[0] for f in filas if f[0]})


@router.get("/reglas-semaforo")
def listar_reglas(db: Session = Depends(get_db)):
    return db.query(ReglaSemaforo).order_by(ReglaSemaforo.prioridad, ReglaSemaforo.id).all()


@router.post("/reglas-semaforo")
def guardar_regla(data: dict, db: Session = Depends(get_db)):
    color = str(data.get("color", "")).upper()
    if color not in ("ROJO", "AMARILLO", "VERDE") or not str(data.get("patron", "")).strip():
        raise HTTPException(status_code=400, detail="Regla no válida")
    campos = {k: data[k] for k in ("patron", "tipo", "prioridad", "descripcion", "activo") if k in data}
    campos["color"] = color
    if data.get("id"):
        r = db.query(ReglaSemaforo).filter(ReglaSemaforo.id == int(data["id"])).first()
        if not r:
            raise HTTPException(status_code=404, detail="Regla no encontrada")
        for k, v in campos.items():
            setattr(r, k, v)
    else:
        r = ReglaSemaforo(**campos)
        db.add(r)
    db.commit()
    db.refresh(r)
    return r
