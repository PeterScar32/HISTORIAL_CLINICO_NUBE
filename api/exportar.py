import datetime
import io

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session

from . import models, semaforo
from .auditoria import FICHAS, Auditoria, get_db, usuario_actual

router = APIRouter()
BOLIVIA = datetime.timezone(datetime.timedelta(hours=-4))

TITULOS = {
    "declaracion": "P1 Filiación", "antecedentes": "P2 Antecedentes", "habitos": "P3 Hábitos y riesgos",
    "oftalmologia": "Oftalmología", "psicologia": "Psicología", "espirometria": "Espirometría", "cardiologia": "Cardiología",
    "altura": "Trabajo en altura", "electroencefalograma": "Electroencefalograma", "aptitud": "Aptitud ocupacional",
    "aptitud_fisica": "Aptitud física y psicológica", "historial_clinico": "Historia clínica", "osteomuscular": "Osteomuscular",
}
INTERNOS = {"id", "paciente_id", "evaluacion_id", "codigo_paciente", "responsable_id", "creado_en", "registrado_por", "responsable"}
CABECERA = PatternFill("solid", fgColor="1F3864")
TONOS = {"ROJO": "F8B4B4", "AMARILLO": "FDE68A", "VERDE": "BBF7D0", "GRIS": "E5E7EB", "REALIZADO": "DCFCE7", "PENDIENTE": "FEF3C7"}
COLOR_TEXTO = {"ROJO": "ROJO · alerta prioritaria", "AMARILLO": "AMARILLO · requiere revisión", "VERDE": "VERDE · sin alertas", "GRIS": "GRIS · sin conclusión"}
BLANCO = Font(bold=True, color="FFFFFF")


def etiqueta(campo: str) -> str:
    return campo.replace("_", " ").strip().capitalize()


def valor(v):
    if isinstance(v, datetime.datetime):
        if v.tzinfo is None:
            v = v.replace(tzinfo=datetime.timezone.utc)
        return v.astimezone(BOLIVIA).replace(tzinfo=None)
    if isinstance(v, str):
        return ILLEGAL_CHARACTERS_RE.sub("", v)
    return v


def hoja(wb, titulo, cabecera, filas):
    ws = wb.create_sheet(titulo[:31])
    ws.append(cabecera)
    for f in filas:
        ws.append([valor(v) for v in f])
    for c in ws[1]:
        c.fill = CABECERA
        c.font = BLANCO
        c.alignment = Alignment(vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"
    if filas:
        ws.auto_filter.ref = ws.dimensions
    for i, nombre in enumerate(cabecera, 1):
        largo = max([len(str(nombre))] + [len(str(f[i - 1])) for f in filas[:300] if f[i - 1] is not None])
        ws.column_dimensions[get_column_letter(i)].width = min(max(10, largo + 2), 45)
        for celda in ws[get_column_letter(i)][1:]:
            if isinstance(celda.value, datetime.datetime):
                celda.number_format = "dd/mm/yyyy hh:mm"
            elif isinstance(celda.value, datetime.date):
                celda.number_format = "dd/mm/yyyy"
    return ws


@router.get("/exportar/excel")
def exportar_excel(db: Session = Depends(get_db)):
    pacientes = {p.id: p for p in db.query(models.Paciente).all()}
    evaluaciones = {e.id: e for e in db.query(models.Evaluacion).all()}
    nombre = lambda pid: f"{pacientes[pid].apellido or ''} {pacientes[pid].nombre or ''}".strip() if pid in pacientes else ""
    ci = lambda pid: pacientes[pid].ci if pid in pacientes else ""
    por_paciente = {}
    for e in evaluaciones.values():
        por_paciente.setdefault(e.paciente_id, []).append(e)

    wb = Workbook()
    wb.remove(wb.active)
    filas = []
    for p in sorted(pacientes.values(), key=lambda x: (x.apellido or "", x.nombre or "")):
        evs = sorted(por_paciente.get(p.id, []), key=lambda e: (e.fecha or datetime.date.min, e.id))
        ult = evs[-1] if evs else None
        filas.append([p.ci, p.apellido, p.nombre, len(evs), ult.fecha if ult else None, ult.tipo if ult else None,
                      ult.empresa if ult else None, ult.puesto if ult else None])
    hoja(wb, "Pacientes", ["CI", "Apellidos", "Nombres", "N.º evaluaciones", "Última evaluación", "Tipo", "Empresa", "Puesto"], filas)

    reglas = semaforo.reglas_activas(db)
    claves = list(semaforo.FICHAS)
    filas, colores = [], []
    for e in sorted(evaluaciones.values(), key=lambda e: (nombre(e.paciente_id), e.fecha or datetime.date.min, e.id)):
        sem = semaforo.semaforo_evaluacion(db, e, reglas)
        por_clave = {f["clave"]: f for f in sem["fichas"]}
        comp = sem["completitud"]
        celdas = []
        for clave in claves:
            f = por_clave.get(clave)
            if not f:
                celdas.append("")
            elif f["estado"] == "PENDIENTE":
                celdas.append("PENDIENTE")
            else:
                res = ", ".join(str(c["valor"]) for c in f["conclusiones"])
                celdas.append("REALIZADO" + (f" · {res}" if res else ""))
        hechas = [semaforo.FICHAS[c][0] for c in claves if por_clave.get(c, {}).get("estado") == "REGISTRADA"]
        filas.append([ci(e.paciente_id), nombre(e.paciente_id), e.fecha, e.tipo, e.empresa, e.puesto,
                      COLOR_TEXTO.get(sem["color"], sem["color"]), sem["motivo"],
                      f'{comp["estado"]} ({comp["registradas"]} de {comp["requeridas"]})', ", ".join(comp["faltantes"]) or "—",
                      len(hechas), ", ".join(hechas) or "—"] + celdas)
        colores.append(sem["color"])
    ws = hoja(wb, "Exámenes por evaluación", ["CI", "Paciente", "Fecha", "Tipo", "Empresa", "Puesto", "Semáforo", "Motivo",
                                              "Cumplimiento", "Exámenes pendientes", "N.º exámenes realizados", "Exámenes realizados"]
              + [semaforo.FICHAS[c][0].replace("Declaración jurada · ", "") for c in claves], filas)
    for i, color in enumerate(colores, 2):
        ws.cell(i, 7).fill = PatternFill("solid", fgColor=TONOS.get(color, "FFFFFF"))
        for j in range(13, 13 + len(claves)):
            v = str(ws.cell(i, j).value or "")
            if v:
                ws.cell(i, j).fill = PatternFill("solid", fgColor=TONOS["REALIZADO" if v.startswith("REALIZADO") else "PENDIENTE"])
    ws.column_dimensions["L"].width = 45

    filas = [[ci(e.paciente_id), nombre(e.paciente_id), e.fecha, e.tipo, e.empresa, e.puesto, e.fichas_requeridas, e.observaciones, e.creado_en]
             for e in sorted(evaluaciones.values(), key=lambda e: (nombre(e.paciente_id), e.fecha or datetime.date.min, e.id))]
    hoja(wb, "Evaluaciones", ["CI", "Paciente", "Fecha", "Tipo", "Empresa", "Puesto", "Fichas requeridas", "Observaciones", "Registrada"], filas)

    for clave, modelo in FICHAS.items():
        campos = [c.name for c in modelo.__table__.columns if c.name not in INTERNOS]
        filas = []
        for f in db.query(modelo).all():
            ev = evaluaciones.get(f.evaluacion_id)
            filas.append([ci(f.paciente_id), nombre(f.paciente_id), ev.fecha if ev else None, ev.tipo if ev else None, ev.empresa if ev else None,
                          getattr(f, "responsable", None), getattr(f, "registrado_por", None), getattr(f, "creado_en", None)] + [getattr(f, c) for c in campos])
        filas.sort(key=lambda x: (x[1] or "", x[2] or datetime.date.min))
        hoja(wb, TITULOS.get(clave, clave), ["CI", "Paciente", "Fecha evaluación", "Tipo", "Empresa", "Responsable", "Registrado por", "Registrada"]
             + [etiqueta(c) for c in campos], filas)

    filas = [[ci(a.paciente_id), nombre(a.paciente_id), evaluaciones[a.evaluacion_id].fecha if a.evaluacion_id in evaluaciones else None,
              a.nombre, "PDF" if a.tipo == "application/pdf" else "Imagen", round(a.tamano / 1024), a.descripcion, a.subido_por, a.creado_en]
             for a in db.query(models.Adjunto.paciente_id, models.Adjunto.evaluacion_id, models.Adjunto.nombre, models.Adjunto.tipo,
                                models.Adjunto.tamano, models.Adjunto.descripcion, models.Adjunto.subido_por, models.Adjunto.creado_en).all()]
    hoja(wb, "Archivos", ["CI", "Paciente", "Fecha evaluación", "Archivo", "Tipo", "Tamaño (KB)", "Descripción", "Subido por", "Fecha de subida"], filas)

    db.add(Auditoria(usuario=usuario_actual(db.connection()), accion="EXPORTACION", tabla="exportar",
                     valor_nuevo=f"Excel: {len(pacientes)} pacientes, {len(evaluaciones)} evaluaciones"))
    db.commit()
    salida = io.BytesIO()
    wb.save(salida)
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    return Response(content=salida.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="historial_clinico_nube_{hoy}.xlsx"', "Cache-Control": "no-store"})
