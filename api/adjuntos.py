import base64
import binascii
import re
import unicodedata
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import desc
from sqlalchemy.orm import Session

from . import models
from .auditoria import Auditoria, get_db, usuario_actual

router = APIRouter()

MAX_BYTES = 5 * 1024 * 1024
FIRMAS = [(b"%PDF-", "application/pdf"), (b"\xff\xd8\xff", "image/jpeg"), (b"\x89PNG\r\n\x1a\n", "image/png")]
EXTENSION = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png"}


def tipo_real(datos: bytes):
    for firma, tipo in FIRMAS:
        if datos.startswith(firma):
            return tipo
    return None


def nombre_seguro(nombre: str, tipo: str) -> str:
    base = re.sub(r"[^\w.\- ]", "_", (nombre or "").strip())[:120].strip(" .") or "archivo"
    if not base.lower().endswith(EXTENSION[tipo]) and not (tipo == "image/jpeg" and base.lower().endswith(".jpeg")):
        base += EXTENSION[tipo]
    return base


def ascii_de(nombre: str) -> str:
    return unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().replace('"', "") or "archivo"


def a_dict(a: models.Adjunto) -> dict:
    return {"id": a.id, "paciente_id": a.paciente_id, "evaluacion_id": a.evaluacion_id, "nombre": a.nombre, "tipo": a.tipo,
            "tamano": a.tamano, "descripcion": a.descripcion, "subido_por": a.subido_por, "creado_en": a.creado_en}


def paciente_o_404(db: Session, paciente_id: int) -> models.Paciente:
    p = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return p


@router.get("/pacientes/{paciente_id}/adjuntos")
def listar_adjuntos(paciente_id: int, db: Session = Depends(get_db)):
    paciente_o_404(db, paciente_id)
    filas = db.query(models.Adjunto).filter(models.Adjunto.paciente_id == paciente_id).order_by(desc(models.Adjunto.id)).all()
    return [a_dict(a) for a in filas]


@router.post("/pacientes/{paciente_id}/adjuntos")
def subir_adjunto(paciente_id: int, data: dict, db: Session = Depends(get_db)):
    p = paciente_o_404(db, paciente_id)
    contenido = str(data.get("contenido") or "")
    if "," in contenido[:100] and contenido.startswith("data:"):
        contenido = contenido.split(",", 1)[1]
    try:
        datos = base64.b64decode(contenido, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="El archivo no se recibió correctamente")
    if not datos:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    if len(datos) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="El archivo supera el límite de 5 MB")
    tipo = tipo_real(datos)
    if not tipo:
        raise HTTPException(status_code=415, detail="Solo se aceptan archivos PDF, JPG o PNG")
    ev_id = data.get("evaluacion_id")
    q = db.query(models.Evaluacion).filter(models.Evaluacion.paciente_id == p.id)
    ev = q.filter(models.Evaluacion.id == int(ev_id)).first() if str(ev_id or "").isdigit() else None
    if ev_id and not ev:
        raise HTTPException(status_code=404, detail="La evaluación no pertenece a este paciente")
    ev = ev or q.order_by(desc(models.Evaluacion.id)).first()
    usuario = usuario_actual(db.connection())
    a = models.Adjunto(paciente_id=p.id, evaluacion_id=ev.id if ev else None, nombre=nombre_seguro(data.get("nombre"), tipo), tipo=tipo,
                       tamano=len(datos), descripcion=(str(data.get("descripcion") or "").strip()[:300] or None),
                       contenido=base64.b64encode(datos).decode(), subido_por=usuario)
    db.add(a)
    db.flush()
    db.add(Auditoria(usuario=usuario, accion="ADJUNTO", tabla="adjuntos", registro_id=a.id, paciente_id=p.id,
                     evaluacion_id=a.evaluacion_id, valor_nuevo=f"{a.nombre} · {a.tamano} bytes"))
    db.commit()
    db.refresh(a)
    return a_dict(a)


@router.get("/adjuntos/{adjunto_id}")
def descargar_adjunto(adjunto_id: int, db: Session = Depends(get_db)):
    a = db.query(models.Adjunto).filter(models.Adjunto.id == adjunto_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return Response(content=base64.b64decode(a.contenido), media_type=a.tipo,
                    headers={"Content-Disposition": f"inline; filename=\"{ascii_de(a.nombre)}\"; filename*=UTF-8''{quote(a.nombre)}", "X-Content-Type-Options": "nosniff",
                             "Cache-Control": "no-store"})


@router.delete("/adjuntos/{adjunto_id}")
def eliminar_adjunto(adjunto_id: int, db: Session = Depends(get_db)):
    a = db.query(models.Adjunto).filter(models.Adjunto.id == adjunto_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    db.add(Auditoria(usuario=usuario_actual(db.connection()), accion="ELIMINACION", tabla="adjuntos", registro_id=a.id,
                     paciente_id=a.paciente_id, evaluacion_id=a.evaluacion_id, valor_anterior=f"{a.nombre} · {a.tamano} bytes"))
    db.delete(a)
    db.commit()
    return {"eliminado": True}
