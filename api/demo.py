import random

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from . import models
from .database import SessionLocal
from .crud import filtrar, create_paciente, delete_paciente
from .auditoria import guardar_en_evaluacion, registrar_eliminacion

router = APIRouter()

MARCA = "DATOS FICTICIOS DE DEMOSTRACIÓN"
PRIMER_CI = 9100001

NOMBRES = [
    ("CARLOS", "MAMANI QUISPE", "M"), ("ROSA", "CONDORI LIMACHI", "F"), ("JORGE", "QUISPE HUANCA", "M"),
    ("ANA", "CHOQUE APAZA", "F"), ("LUIS", "FLORES TICONA", "M"), ("MARTA", "GUTIÉRREZ ROJAS", "F"),
    ("PEDRO", "VARGAS COPA", "M"), ("ELENA", "HUANCA MAMANI", "F"), ("RAÚL", "POMA CALLISAYA", "M"),
    ("SONIA", "LAURA CHAMBI", "F"), ("MIGUEL", "TARQUI ALANOCA", "M"), ("LUCÍA", "PAREDES SIRPA", "F"),
    ("FREDDY", "CUSI MACHACA", "M"), ("GLADYS", "YUJRA NINA", "F"), ("RENÉ", "ARUQUIPA CHOQUE", "M"),
    ("PATRICIA", "COLQUE VILLCA", "F"), ("WILFREDO", "MENDOZA ARCE", "M"), ("CARMEN", "TORREZ QUISBERT", "F"),
    ("JUAN CARLOS", "ALIAGA PATZI", "M"), ("NANCY", "FERNÁNDEZ CRUZ", "F"), ("EDWIN", "SURCO GUARACHI", "M"),
    ("VERÓNICA", "QUENTA APAZA", "F"), ("DANIEL", "ROMERO CHURA", "M"), ("SILVIA", "MAYTA LUNA", "F"),
]

EMPRESAS = [
    ("MINERA CERRO AZUL (DEMO)", ["OPERADOR DE PERFORADORA", "AYUDANTE DE MINA", "CONDUCTOR DE VOLQUETA", "TÉCNICO DE SEGURIDAD"], "espirometria"),
    ("CONSTRUCTORA ALTIPLANO SUR (DEMO)", ["ALBAÑIL", "OPERADOR DE GRÚA", "SOLDADOR", "ENCOFRADOR"], "altura"),
    ("CEMENTOS PAMPA GRANDE (DEMO)", ["OPERADOR DE HORNO", "ESTIBADOR", "MECÁNICO", "ASISTENTE DE LABORATORIO"], "osteomuscular"),
]

APTITUDES = ["APTO", "APTO", "APTO", "APTO", "APTO", "APTO CON RESTRICCIONES", "NO APTO", None]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def guardar(db, modelo, datos):
    return guardar_en_evaluacion(db, modelo(**filtrar(modelo, datos)))


def evaluacion(db, p, empresa, puesto, tipo, fecha, requeridas=None):
    ev = models.Evaluacion(paciente_id=p.id, empresa=empresa, puesto=puesto, tipo=tipo, fecha=fecha,
                           observaciones=MARCA, fichas_requeridas=requeridas)
    db.add(ev)
    db.flush()
    return ev


def fichas_basicas(db, p, ev, r, sexo, edad, aptitud, completa, adicional, puesto, empresa):
    base = {"paciente_id": p.id, "evaluacion_id": ev.id}
    guardar(db, models.DeclaracionJurada, {**base, "edad": str(edad), "sexo": "MASCULINO" if sexo == "M" else "FEMENINO",
                                            "fecha_nacimiento": f"{2026 - edad}-0{r.randint(1, 9)}-1{r.randint(0, 9)}",
                                            "lugar_nacimiento": r.choice(["LA PAZ", "EL ALTO", "ORURO", "POTOSÍ"]),
                                            "domicilio": f"CALLE {r.randint(1, 60)}", "zona_barrio": r.choice(["VILLA ADELA", "SENKATA", "ACHUMANI", "MIRAFLORES"]),
                                            "ciudad": r.choice(["LA PAZ", "EL ALTO"]), "pais": "BOLIVIA", "telefono": f"7{r.randint(1000000, 9999999)}",
                                            "estado_civil": r.choice(["SOLTERO/A", "CASADO/A", "CONVIVIENTE"]), "profesion": puesto})
    guardar(db, models.AntecedentesP2, {**base, "vista": r.choice(["NORMAL", "NORMAL", "USA LENTES"]), "cardio": "NORMAL",
                                         "digestivo": r.choice(["NORMAL", "NORMAL", "GASTRITIS"]), "alergias": r.choice(["NORMAL", "NORMAL", "PENICILINA"]),
                                         "medicamentos": "NORMAL", "familiares": r.choice(["NORMAL", "DIABETES (MADRE)", "HTA (PADRE)"])})
    guardar(db, models.HabitosRiesgosP3, {**base, "fuma": r.choice(["NO", "NO", "SI"]), "alcohol": r.choice(["NO", "OCASIONAL", "OCASIONAL"]),
                                           "drogas": "NO", "coca": r.choice(["NO", "SI"]), "grupo_sanguineo": r.choice(["ORH+", "ORH+", "ARH+", "BRH+"]),
                                           "riesgos_expuestos": r.choice(["POLVO, RUIDO", "ALTURA, CARGA", "RUIDO, VIBRACIÓN"])})
    if completa:
        guardar(db, models.HistorialClinico, {**base, "codigo_paciente": p.ci, "empresa": empresa, "ci": p.ci, "puesto": puesto,
                                               "ruido": "SI", "ta_m": f"{r.randint(105, 135)}/{r.randint(65, 85)}", "talla": f"1.{r.randint(55, 80)}",
                                               "piel_n": "NORMAL", "cardio_n": "NORMAL", "resp_n": "NORMAL", "tipo_control": "PERIODICO",
                                               "aptitud_apto": "APTO" if aptitud == "APTO" else None,
                                               "aptitud_restriccion": "APTO CON RESTRICCIÓN" if aptitud == "APTO CON RESTRICCIONES" else None,
                                               "aptitud_no_apto": "NO APTO" if aptitud == "NO APTO" else None})
    if aptitud:
        ap, am = (p.apellido.split(" ") + [""])[:2]
        rec = {"APTO": "", "APTO CON RESTRICCIONES": "USO OBLIGATORIO DE PROTECCIÓN AUDITIVA", "NO APTO": "CONTROL CON ESPECIALISTA ANTES DE REEVALUAR"}[aptitud]
        guardar(db, models.FichaAptitud, {**base, "razon_social": empresa, "tipo_examen": ev.tipo, "apellido_paterno": ap, "apellido_materno": am,
                                           "nombres": p.nombre, "edad": str(edad), "genero": "MASCULINO" if sexo == "M" else "FEMENINO",
                                           "nro_doc_identidad": p.ci, "puesto_trabajo": puesto, "resultado": aptitud, "recomendacion_1": rec})
    if adicional == "espirometria":
        guardar(db, models.FichaEspirometria, {**base, "hemoptisis": "NO", "tos_flemas": r.choice(["NO", "NO", "SI"]), "fumo_ultimas_horas": "NO", "equipo_proteccion": "SI"})
    if adicional == "altura":
        guardar(db, models.FichaAltura, {**base, "vertigo": "SI" if aptitud == "NO APTO" else "NO", "acrofobia": "NO", "hipertension": "NO",
                                          "test_romberg": "NORMAL", "soplo_cardiaco": "NO"})
    if adicional == "osteomuscular":
        guardar(db, models.FichaOsteomuscular, {**base, "codigo_paciente": p.ci, "nombre_completo": f"{p.apellido} {p.nombre}", "edad": edad,
                                                 "ci": p.ci, "concepto_aptitud": aptitud or "APTO"})
    if r.random() < 0.35:
        guardar(db, models.FichaOftalmologica, {**base, "lentes": "SI" if r.random() < 0.4 else "NO", "estrabismo": "NO"})
    if r.random() < 0.3:
        guardar(db, models.FichaCardiologia, {**base, "hta": r.choice(["NO", "NO", "SI"]), "presion_arterial": f"{r.randint(110, 140)}/{r.randint(70, 90)}",
                                               "frecuencia_cardiaca": str(r.randint(62, 88)), "diagnostico_recomendaciones": "SIN HALLAZGOS RELEVANTES"})


@router.post("/admin/datos-demo")
def cargar_demo(db: Session = Depends(get_db)):
    r = random.Random(2026)
    creados = 0
    for i, (nombre, apellido, sexo) in enumerate(NOMBRES):
        ci = str(PRIMER_CI + i)
        if db.query(models.Paciente).filter(models.Paciente.ci == ci).first():
            continue
        empresa, puestos, adicional = EMPRESAS[i % 3]
        puesto = puestos[(i // 3) % len(puestos)]
        p = create_paciente(db, {"nombre": nombre, "apellido": apellido, "ci": ci})
        edad = r.randint(22, 58)
        aptitud = APTITUDES[(i // 3) % len(APTITUDES)]
        if i % 6 == 0:
            previa = evaluacion(db, p, empresa, puesto, "PERIODICO", f"2026-05-{10 + i % 15:02d}")
            fichas_basicas(db, p, previa, r, sexo, edad - 1, "APTO", True, adicional, puesto, empresa)
        tipo = "PREOCUPACIONAL" if i % 5 == 0 else "PERIODICO"
        ev = evaluacion(db, p, empresa, puesto, tipo, f"2026-11-{2 + i % 6:02d}")
        completa = i % 4 != 3
        fichas_basicas(db, p, ev, r, sexo, edad, aptitud, completa, adicional, puesto, empresa)
        db.commit()
        if i % 6 == 0:
            car = db.query(models.FichaCardiologia).filter(models.FichaCardiologia.evaluacion_id == ev.id).first()
            if car is None:
                car = guardar(db, models.FichaCardiologia, {"paciente_id": p.id, "evaluacion_id": ev.id, "hta": "NO", "presion_arterial": "128/84"})
                db.commit()
            car.hta = "SI"
            car.presion_arterial = "142/92"
            db.commit()
        creados += 1
    return {"creados": creados, "total_demo": len(NOMBRES), "marca": MARCA}


@router.delete("/admin/datos-demo")
def borrar_demo(db: Session = Depends(get_db)):
    borrados = 0
    for i in range(len(NOMBRES)):
        p = db.query(models.Paciente).filter(models.Paciente.ci == str(PRIMER_CI + i)).first()
        if p:
            registrar_eliminacion(db, "pacientes", p.id, p.id, f"{p.apellido} {p.nombre} · CI {p.ci} · {MARCA}")
            delete_paciente(db, p.id)
            borrados += 1
    return {"borrados": borrados}
