from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from api.models import FichaElectroencefalograma, Paciente 
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import SessionLocal, engine, Base
from .crud import create_doctor, create_enfermera
from . import models
from .models import FichaAptitudFisica 
from .database import get_db
from sqlalchemy import desc

Base.metadata.create_all(bind=engine)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()


# ----------- BLOQUE P1: FILIACION -----------
@app.post("/filiacion/")
def guardar_filiacion(data: dict, db: Session = Depends(get_db)):
    nueva = models.DeclaracionJurada(**data); db.add(nueva); db.commit(); db.refresh(nueva); return nueva

@app.get("/api/paciente-completo/{paciente_id}")
def obtener_paciente_completo(paciente_id: int, db: Session = Depends(get_db)):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente: raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return {
        "paciente": paciente,
        "filiacion": db.query(models.DeclaracionJurada).filter(models.DeclaracionJurada.paciente_id == paciente_id).first(),
        "antecedentes": db.query(models.AntecedentesP2).filter(models.AntecedentesP2.paciente_id == paciente_id).first(),
        "habitos": db.query(models.HabitosRiesgosP3).filter(models.HabitosRiesgosP3.paciente_id == paciente_id).first()
    }
    
@app.get("/verificar_estado_paciente/{paciente_id}")
def verificar_estado_paciente(paciente_id: int, db: Session = Depends(get_db)):
    return {
        "aptitud": db.query(models.Aptitud).filter(models.Aptitud.paciente_id == paciente_id).first() is not None,
        "oftalmo": db.query(models.Oftalmologia).filter(models.Oftalmologia.paciente_id == paciente_id).first() is not None,
        "psicologia": db.query(models.Psicologia).filter(models.Psicologia.paciente_id == paciente_id).first() is not None,
        "laboratorio": db.query(models.Laboratorio).filter(models.Laboratorio.paciente_id == paciente_id).first() is not None,
        "radiografia": db.query(models.Radiografia).filter(models.Radiografia.paciente_id == paciente_id).first() is not None,
        "odontologia": db.query(models.Odontologia).filter(models.Odontologia.paciente_id == paciente_id).first() is not None,
        "otorrino": db.query(models.Otorrino).filter(models.Otorrino.paciente_id == paciente_id).first() is not None,
        "neurologia": db.query(models.Neurologia).filter(models.Neurologia.paciente_id == paciente_id).first() is not None,
        "cardiologia": db.query(models.Cardiologia).filter(models.Cardiologia.paciente_id == paciente_id).first() is not None,
        "traumatologia": db.query(models.Traumatologia).filter(models.Traumatologia.paciente_id == paciente_id).first() is not None,
        "medicina": db.query(models.Medicina).filter(models.Medicina.paciente_id == paciente_id).first() is not None
    }
# ----------- BLOQUE P2 y P3 -----------
@app.post("/p2/")
def guardar_p2(data: dict, db: Session = Depends(get_db)):
    nueva = models.AntecedentesP2(**data); db.add(nueva); db.commit(); db.refresh(nueva); return nueva

@app.post("/p3/")
def guardar_p3(data: dict, db: Session = Depends(get_db)):
    nueva = models.HabitosRiesgosP3(**data); db.add(nueva); db.commit(); db.refresh(nueva); return nueva

# ----------- GESTION PACIENTES -----------
@app.get("/pacientes/")
def listar_pacientes(db: Session = Depends(get_db)):
    return db.query(models.Paciente).all()

@app.post("/pacientes/")
def registrar_paciente(data: dict, db: Session = Depends(get_db)):
    nuevo = models.Paciente(**data); db.add(nuevo); db.commit(); db.refresh(nuevo); return nuevo

@app.get("/buscar-id-por-codigo/{codigo}")
def buscar_id_por_codigo(codigo: str, db: Session = Depends(get_db)):
    # Usamos func.upper para normalizar la búsqueda contra el modelo
    p = db.query(models.Paciente).filter(func.upper(models.Paciente.codigo_paciente) == codigo.upper().strip()).first()
    
    if not p: 
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    return {"id": p.id}

# ----------- FICHA MÉDICA -----------
@app.post("/ficha-oftalmo/")
def guardar_ficha_oftalmo(data: dict, db: Session = Depends(get_db)):
    nueva = models.FichaOftalmologica(**data); db.add(nueva); db.commit(); db.refresh(nueva); return nueva

@app.get("/ficha-oftalmo/{paciente_id}")
def obtener_ficha_oftalmo(paciente_id: int, db: Session = Depends(get_db)):
    ficha = db.query(models.FichaOftalmologica).filter(models.FichaOftalmologica.paciente_id == paciente_id).first()
    if not ficha: raise HTTPException(status_code=404, detail="Ficha no encontrada")
    return ficha

# ----------- FICHA PSICOLOGICA -----------
@app.post("/guardar-psicologia")
async def guardar_psicologia(data: dict, db: Session = Depends(get_db)):
    codigo_input = str(data.get("codigo_paciente", "")).strip().upper()
    if not codigo_input:
        raise HTTPException(status_code=400, detail="El código del paciente es obligatorio")

    # Búsqueda normalizada
    paciente = db.query(models.Paciente).filter(
        func.upper(models.Paciente.codigo_paciente) == codigo_input
    ).first()
    
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado en el sistema")

    try:
        nueva_ficha = models.FichaPsicologia(
            paciente_id=paciente.id,
            historia_familiar=data.get("historia_familiar"),
            personalidad=data.get("personalidad"),
            conducta_sexual=data.get("conducta_sexual"),
            habitos_alcohol=data.get("habitos_alcohol"),
            habitos_tabaco=data.get("habitos_tabaco"),
            habitos_drogas=data.get("habitos_drogas"),
            habitos_coquear=data.get("habitos_coquear"),
            otras_observaciones=data.get("otras_observaciones"),
            presentacion=data.get("presentacion"),
            postura=data.get("postura"),
            discurso=data.get("discurso"),
            pensamiento=data.get("pensamiento"),
            percepcion=data.get("percepcion"),
            resultado_psicologico=data.get("resultado_psicologico")
        )
        db.add(nueva_ficha)
        db.commit()
        db.refresh(nueva_ficha)
        return {"message": "GUARDADO EXITOSAMENTE"}
    except Exception as e:
        print(f"Error al guardar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ficha-psicologia/{paciente_id}")
def obtener_ficha_psicologia(paciente_id: int, db: Session = Depends(get_db)):
    ficha = db.query(models.FichaPsicologia).filter(models.FichaPsicologia.paciente_id == paciente_id).first()
    if not ficha: raise HTTPException(status_code=404, detail="Ficha no encontrada")
    return ficha

# NUEVO ENDPOINT PARA CONSULTAS (El que faltaba)
@app.get("/ficha-psicologia-filtrada/{estado}")
def obtener_fichas_por_estado(estado: str, db: Session = Depends(get_db)):
    fichas = db.query(models.FichaPsicologia).filter(models.FichaPsicologia.resultado_psicologico == estado).all()
    resultados = []
    for f in fichas:
        paciente = db.query(models.Paciente).filter(models.Paciente.id == f.paciente_id).first()
        if paciente:
            resultados.append({
                "codigo": paciente.codigo_paciente,
                "nombre": f"{paciente.apellido} {paciente.nombre}",
                "estado": f.resultado_psicologico
            })
    return resultados


# ----------- PERSONAL: DOCTORES -----------
@app.get("/personal/")
def obtener_personal(db: Session = Depends(get_db)):
    return {"doctores": db.query(models.Doctor).all(), "enfermeras": db.query(models.Enfermera).all()}

@app.post("/doctores/")
def registrar_doctor(data: dict, db: Session = Depends(get_db)): return create_doctor(db, data)

@app.get("/doctores/{id_doc}")
def obtener_doctor(id_doc: int, db: Session = Depends(get_db)):
    d = db.query(models.Doctor).filter(models.Doctor.id_doc == id_doc).first()
    if not d: raise HTTPException(status_code=404, detail="No encontrado")
    return d

@app.put("/doctores/{id_doc}")
def actualizar_doctor(id_doc: int, data: dict, db: Session = Depends(get_db)):
    d = db.query(models.Doctor).filter(models.Doctor.id_doc == id_doc).first()
    if not d: raise HTTPException(status_code=404, detail="No encontrado")
    for k, v in data.items(): setattr(d, k, v)
    db.commit(); db.refresh(d); return d

@app.delete("/doctores/{id_doc}")
def borrar_doctor(id_doc: int, db: Session = Depends(get_db)):
    d = db.query(models.Doctor).filter(models.Doctor.id_doc == id_doc).first()
    if not d: raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(d); db.commit(); return {"message": "Eliminado"}

# ----------- PERSONAL: ENFERMERAS -----------
@app.post("/enfermeras/")
def registrar_enfermera(data: dict, db: Session = Depends(get_db)): return create_enfermera(db, data)

@app.get("/enfermeras/{id_enfe}")
def obtener_enfermera(id_enfe: int, db: Session = Depends(get_db)):
    e = db.query(models.Enfermera).filter(models.Enfermera.id_enfe == id_enfe).first()
    if not e: raise HTTPException(status_code=404, detail="No encontrada")
    return e

@app.put("/enfermeras/{id_enfe}")
def actualizar_enfermera(id_enfe: int, data: dict, db: Session = Depends(get_db)):
    e = db.query(models.Enfermera).filter(models.Enfermera.id_enfe == id_enfe).first()
    if not e: raise HTTPException(status_code=404, detail="No encontrada")
    for k, v in data.items(): setattr(e, k, v)
    db.commit(); db.refresh(e); return e

@app.delete("/enfermeras/{id_enfe}")
def borrar_enfermera(id_enfe: int, db: Session = Depends(get_db)):
    e = db.query(models.Enfermera).filter(models.Enfermera.id_enfe == id_enfe).first()
    if not e: raise HTTPException(status_code=404, detail="No encontrada")
    db.delete(e); db.commit(); return {"message": "Eliminada"}


# ----------- FICHA CARDIOLOGIA -----------
@app.post("/guardar-cardiologia")
async def guardar_cardiologia(data: dict, db: Session = Depends(get_db)):
    codigo_input = str(data.get("codigo_paciente", "")).strip().upper()
    paciente = db.query(models.Paciente).filter(func.upper(models.Paciente.codigo_paciente) == codigo_input).first()
    
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    nueva_ficha = models.FichaCardiologia(
        paciente_id=paciente.id,
        ninez=data.get("ninez"),
        tabaquismo=data.get("tabaquismo"),
        hta=data.get("hta"),
        adolescente=data.get("adolescente"),
        hiperlipidemias=data.get("hiperlipidemias"),
        diabetes=data.get("diabetes"),
        adultez=data.get("adultez"),
        asma_bronquial=data.get("asma_bronquial"),
        bronquitis=data.get("bronquitis"),
        obs_antecedentes=data.get("obs_antecedentes"),
        padre=data.get("padre"),
        madre=data.get("madre"),
        hermanos=data.get("hermanos"),
        abuelos=data.get("abuelos"),
        hijos=data.get("hijos"),
        obs_familiares=data.get("obs_familiares"),
        anamnesis=data.get("anamnesis"),
        presion_arterial=data.get("presion_arterial"),
        frecuencia_cardiaca=data.get("frecuencia_cardiaca"),
        pulso=data.get("pulso"),
        frecuencia_respiratoria=data.get("frecuencia_respiratoria"),
        talla=data.get("talla"),
        peso=data.get("peso"),
        imc=data.get("imc"),
        sat_o2=data.get("sat_o2"),
        examen_clinico=data.get("examen_clinico"),
        resultado_electro=data.get("resultado_electro"),
        diagnostico_recomendaciones=data.get("diagnostico_recomendaciones")
    )
    db.add(nueva_ficha)
    db.commit()
    return {"status": "success"}



@app.get("/ficha-cardiologia/{paciente_id}")
def obtener_ficha_cardiologia(paciente_id: int, db: Session = Depends(get_db)):
    ficha = db.query(models.FichaCardiologia).filter(models.FichaCardiologia.paciente_id == paciente_id).first()
    if not ficha: raise HTTPException(status_code=404, detail="Ficha no encontrada")
    return ficha

@app.get("/consulta-cardiologia/{diagnostico}")
def consultar_cardiologia(diagnostico: str, db: Session = Depends(get_db)):
    # Buscamos fichas que contengan el texto en el diagnóstico
    fichas = db.query(models.FichaCardiologia).filter(
        models.FichaCardiologia.diagnostico_recomendaciones.contains(diagnostico)
    ).all()
    
    resultados = []
    for f in fichas:
        p = db.query(models.Paciente).filter(models.Paciente.id == f.paciente_id).first()
        if p:
            resultados.append({
                "codigo": p.codigo_paciente,
                "nombre": f"{p.apellido} {p.nombre}",
                "diagnostico": f.diagnostico_recomendaciones
            })
    return resultados

@app.get("/filtrar-cardiologia")
async def filtrar_cardiologia(query: str, db: Session = Depends(get_db)):
    # Buscamos en la tabla ficha_cardiologia filtrando por diagnostico_recomendaciones
    resultados = db.query(models.FichaCardiologia, models.Paciente).join(
        models.Paciente
    ).filter(
        models.FichaCardiologia.diagnostico_recomendaciones.ilike(f"%{query}%")
    ).all()
    
    return [
        {
            "codigo_paciente": p.codigo_paciente,
            "nombre_paciente": p.nombre_completo,
            "diagnostico": f.diagnostico_recomendaciones
        } for f, p in resultados
    ]


@app.get("/buscar-cardiologia")
async def buscar_cardiologia(antecedente: str, db: Session = Depends(get_db)):
    # Mapeo directo a los atributos del modelo
    columnas = {
        "NINEZ": models.FichaCardiologia.ninez,
        "ADOLESCENTE": models.FichaCardiologia.adolescente,
        "ADULTEZ": models.FichaCardiologia.adultez,
        "TABAQUISMO": models.FichaCardiologia.tabaquismo,
        "HIPERLIPIDEMIAS": models.FichaCardiologia.hiperlipidemias,
        "ASMA_BRONQUIAL": models.FichaCardiologia.asma_bronquial,
        "HTA": models.FichaCardiologia.hta,
        "DIABETES": models.FichaCardiologia.diabetes,
        "BRONQUITIS": models.FichaCardiologia.bronquitis
    }
    
    columna_modelo = columnas.get(antecedente.upper().strip())
    if not columna_modelo:
        return []

    # EJECUCIÓN: Query sin el alias de modelo confuso, referenciando las tablas desde la sesión
    query = db.query(models.Paciente.codigo_paciente, models.Paciente.nombre, models.Paciente.apellido).\
               join(models.FichaCardiologia, models.FichaCardiologia.paciente_id == models.Paciente.id).\
               filter(columna_modelo == "SI").all()

    # Formateo de salida para que el frontend reciba algo que entienda
    return [{"codigo": r[0], "nombre": f"{r[1]} {r[2]}", "detalle": "CONFIRMADO"} for r in query]

# ----------- FICHA ESPIROMETRÍA (SOLUCIÓN DEFINITIVA) -----------
@app.post("/guardar-espirometria")
async def guardar_espirometria(data: dict, db: Session = Depends(get_db)):
    try:
        codigo = str(data.get("codigo_paciente", "")).strip().upper()
        paciente = db.query(models.Paciente).filter(func.upper(models.Paciente.codigo_paciente) == codigo).first()
        
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")

        # Mapeo exacto basado en tu models.py
        nueva_ficha = models.FichaEspirometria(
            paciente_id=paciente.id,
            criterios_exclusion_1=data.get("criterios_exclusion_1"),
            criterios_exclusion_2=data.get("criterios_exclusion_2"),
            criterios_exclusion_3=data.get("criterios_exclusion_3"),
            criterios_exclusion_4=data.get("criterios_exclusion_4"),
            criterios_exclusion_5=data.get("criterios_exclusion_5"),
            
            hemoptisis=data.get("hemoptisis"),
            infarto_reciente=data.get("infarto_reciente"),
            neumotorax=data.get("neumotorax"),
            fiebre_nauseas=data.get("fiebre_nauseas"),
            traqueostomia=data.get("traqueostomia"),
            embarazo_avanzado=data.get("embarazo_avanzado"),
                  
            infeccion_respiratoria=data.get("infeccion_respiratoria"),
            infeccion_oido=data.get("infeccion_oido"),
            uso_aerosoles=data.get("uso_aerosoles"),
            uso_aerosoles_detalle=data.get("uso_aerosoles_detalle"),
            fumo_ultimas_horas=data.get("fumo_ultimas_horas"),
            fumo_cantidad_detalle=data.get("fumo_cantidad_detalle"),
            ejercicio_fisico=data.get("ejercicio_fisico"),
            comio_ultima_hora=data.get("comio_ultima_hora"),
            tos_flemas=data.get("tos_flemas"),
            tos_flemas_detalle=data.get("tos_flemas_detalle"),
            equipo_proteccion=data.get("equipo_proteccion")
        )
        db.add(nueva_ficha)
        db.commit()
        db.refresh(nueva_ficha)
        return {"status": "success", "message": "GUARDADO EXITOSAMENTE"}
    except Exception as e:
        # Esto imprimirá el error real en los logs de Render
        print(f"ERROR DETALLADO: {str(e)}") 
        raise HTTPException(status_code=500, detail=str(e))
# ----------------------------
@app.get("/consultar-espirometria/{codigo_paciente}")
async def consultar_espirometria(codigo_paciente: str, db: Session = Depends(get_db)):
    # Buscamos al paciente
    paciente = db.query(models.Paciente).filter(func.upper(models.Paciente.codigo_paciente) == codigo_paciente.upper().strip()).first()
    if not paciente:
        return {"status": "error", "message": "Paciente no encontrado"}
    
    # Buscamos la ficha en la tabla correcta
    ficha = db.query(models.FichaEspirometria).filter(models.FichaEspirometria.paciente_id == paciente.id).first()
    if not ficha:
        return {"status": "error", "message": "Ficha no encontrada"}
        
    return ficha

# -------
@app.get("/listar-espirometria")
async def listar_espirometria(filtro: str = ""):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM espirometria WHERE codigo_paciente LIKE ?", (f"%{filtro.strip().upper()}%",))
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ----------- ENDPOINT PARA CONSULTA FILTRADA ESPIROMETRÍA -----------
@app.get("/espirometria-filtrada/{sintoma}")
def obtener_espirometria_por_sintoma(sintoma: str, db: Session = Depends(get_db)):
    # Filtramos la tabla FichaEspirometria donde el síntoma sea "SI"
    # Mapeamos los valores del frontend a los campos del modelo
    mapeo = {
        "hemoptisis": models.FichaEspirometria.hemoptisis,
        "infarto_reciente": models.FichaEspirometria.infarto_reciente,
        "neumotorax": models.FichaEspirometria.neumotorax,
        "fiebre_nauseas": models.FichaEspirometria.fiebre_nauseas,
        "traqueostomia": models.FichaEspirometria.traqueostomia,
        "embarazo_avanzado": models.FichaEspirometria.embarazo_avanzado
    }
    
    campo = mapeo.get(sintoma.lower())
    if not campo:
        return []

    fichas = db.query(models.FichaEspirometria).filter(campo == "SI").all()
    
    resultados = []
    for f in fichas:
        paciente = db.query(models.Paciente).filter(models.Paciente.id == f.paciente_id).first()
        if paciente:
            resultados.append({
                "codigo": paciente.codigo_paciente,
                "nombre": f"{paciente.apellido} {paciente.nombre}",
                "estado": sintoma.upper()
            })
    return resultados

# ------------------- FICHA ALTURA --------------------------
@app.post("/guardar-altura")
async def guardar_altura(data: dict, db: Session = Depends(get_db)):
    try:
        codigo = str(data.get("codigo_paciente", "")).strip().upper()
        paciente = db.query(models.Paciente).filter(func.upper(models.Paciente.codigo_paciente) == codigo).first()
        
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")

        nueva_ficha = models.FichaAltura(
            paciente_id=paciente.id,
            agorafobia=data.get("agorafobia"),
            diabetes=data.get("diabetes"),
            acrofobia=data.get("acrofobia"),
            insuficiencia_cardiaca=data.get("insuficiencia_cardiaca"),
            arritmia=data.get("arritmia"),
            hipertension=data.get("hipertension"),
            consumo_drogas=data.get("consumo_drogas"),
            meniere=data.get("meniere"),
            enfermedad_psiquiatrica=data.get("enfermedad_psiquiatrica"),
            ametropia=data.get("ametropia"),
            trauma_encefalo=data.get("trauma_encefalo"),
            esteropsis=data.get("esteropsis"),
            convulsiones=data.get("convulsiones"),
            asma_bronquial=data.get("asma_bronquial"),
            vertigo=data.get("vertigo"),
            hipoacusia=data.get("hipoacusia"),
            sincope=data.get("sincope"),
            accidentes_fracturas=data.get("accidentes_fracturas"),
            mioclonias=data.get("mioclonias"),
            deformidades=data.get("deformidades"),
            cefaleas=data.get("cefaleas"),
            obs_antecedentes=data.get("obs_antecedentes"),
            soplo_cardiaco=data.get("soplo_cardiaco"),
            sustentacion_pie=data.get("sustentacion_pie"),
            arritmias_cardiacas=data.get("arritmias_cardiacas"),
            camina_libre=data.get("camina_libre"),
            nistagmus=data.get("nistagmus"),
            adiacocinesia=data.get("adiacocinesia"),
            test_romberg=data.get("test_romberg"),
            audicion=data.get("audicion"),
            test_barany=data.get("test_barany"),
            marcha_ojos_cerrados=data.get("marcha_ojos_cerrados"),
            test_babinsky=data.get("test_babinsky"),
            extremidades=data.get("extremidades"),
            obs_examen=data.get("obs_examen")
        )
        db.add(nueva_ficha)
        db.commit()
        db.refresh(nueva_ficha)
        return {"status": "success", "message": "GUARDADO EXITOSAMENTE"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/consultar-altura/{codigo_paciente}")
async def consultar_altura(codigo_paciente: str, db: Session = Depends(get_db)):
    paciente = db.query(models.Paciente).filter(func.upper(models.Paciente.codigo_paciente) == codigo_paciente.upper().strip()).first()
    if not paciente:
        return {"status": "error", "message": "Paciente no encontrado"}
    
    ficha = db.query(models.FichaAltura).filter(models.FichaAltura.paciente_id == paciente.id).first()
    if not ficha:
        return {"status": "error", "message": "Ficha no encontrada"}
        
    return ficha

@app.get("/filtrar-altura/{campo}")
def filtrar_altura(campo: str, db: Session = Depends(get_db)):
    # Mapeo exacto a las columnas de la tabla FichaAltura
    mapeo = {
        "soplo_cardiaco": models.FichaAltura.soplo_cardiaco,
        "arritmias_cardiacas": models.FichaAltura.arritmias_cardiacas,
        "nistagmus": models.FichaAltura.nistagmus,
        "test_romberg": models.FichaAltura.test_romberg,
        "test_barany": models.FichaAltura.test_barany,
        "test_babinsky": models.FichaAltura.test_babinsky
    }
    columna = mapeo.get(campo)
    if not columna: return []

    # Consulta corregida con join explícito
    fichas = db.query(models.FichaAltura, models.Paciente).join(
        models.Paciente, models.FichaAltura.paciente_id == models.Paciente.id
    ).filter(columna == "SI").all()
    
    return [{"codigo": f.Paciente.codigo_paciente, "nombre": f"{f.Paciente.apellido} {f.Paciente.nombre}", "estado": "ANORMAL"} for f in fichas]

# ----------- FICHA ELECTROENCEFALOGRAMA -----------

@app.post("/guardar-electro")
async def guardar_electro(data: dict, db: Session = Depends(get_db)):
    # 1. Buscar paciente primero
    codigo = str(data.get("codigo_paciente", "")).strip().upper()
    paciente = db.query(models.Paciente).filter(func.upper(models.Paciente.codigo_paciente) == codigo).first()
    
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    # 2. Crear instancia con nombres exactos de columnas (ajustados a tu BD)
    try:
        nueva_ficha = models.FichaElectroencefalograma(
            paciente_id=paciente.id,
            cefaleas=data.get("cefaleas"),
            epilepsia=data.get("epilepsia"),
            convulsiones=data.get("convulsiones"),
            accidente=data.get("accidente"),
            perdida_conocimiento=data.get("perdida_conocimiento"),
            paralisis=data.get("paralisis"),
            otros_antecedentes=data.get("otros_antecedentes"),
            derrame_cerebral=data.get("derrame_cerebral"),
            quirurgicos=data.get("quirurgicos"),
            observaciones_antecedentes=data.get("observaciones_antecedentes"),
            marcha=data.get("marcha"),
            reflejos=data.get("reflejos"),
            coordinacion_dedo_nariz=data.get("coordinacion_dedo_nariz"),
            coordinacion_talon_rodilla=data.get("coordinacion_talon_rodilla"),
            romberg=data.get("romberg"),
            vertigo_nistagmo=data.get("vertigo_nistagmo"),
            vertigo_adaptacion=data.get("vertigo_adaptacion"),
            observaciones_examen=data.get("observaciones_examen"),
            descripcion_estudio=data.get("descripcion_estudio"),
            resultado_estudio=data.get("resultado_estudio"),
            observaciones_estudio=data.get("observaciones_estudio"),
            reposo=data.get("reposo"),
            fotoestimulacion=data.get("fotoestimulacion"),
            hipernea=data.get("hipernea"),
            diagnostico_recomendaciones=data.get("diagnostico_recomendaciones")
        )
        
        # 3. Guardar
        db.add(nueva_ficha)
        db.commit()
        db.refresh(nueva_ficha)
        return {"status": "success"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/consultar-electro-por-campo/{campo}")
async def consultar_electro_por_campo(campo: str, db: Session = Depends(get_db)):
    # Traemos todos los registros sin filtros complejos para evitar errores
    registros = db.query(models.FichaElectroencefalograma).all()
    lista = []
    
    for r in registros:
        # Obtenemos el valor de forma segura
        valor = getattr(r, campo, None)
        # Si el valor existe y no es "NO", lo agregamos
        if valor and str(valor).strip().upper() != 'NO':
            paciente = db.query(models.Paciente).filter(models.Paciente.id == r.paciente_id).first()
            lista.append({
                "codigo_paciente": paciente.codigo_paciente if paciente else "N/A",
                "nombre_paciente": f"{paciente.nombre} {paciente.apellido}" if paciente else "Desconocido",
                "valor": valor
            })
    return lista # Esto siempre será una lista, nunca dará error al iterar

# ----------- FICHA APTITUD MÉDICO OCUPACIONAL -----------
@app.post("/guardar-aptitud")
async def guardar_aptitud(data: dict, db: Session = Depends(get_db)):
    try:
        # Validación: buscar paciente
        codigo = str(data.get("codigo_paciente", "")).strip().upper()
        paciente = db.query(models.Paciente).filter(func.upper(models.Paciente.codigo_paciente) == codigo).first()
        if not paciente:
            return {"status": "error", "message": "Paciente no encontrado"}

        # Crear objeto con mapeo estricto
        nueva_ficha = models.FichaAptitud(
            paciente_id=paciente.id,
            razon_social=data.get("razon_social"),
            actividad_economica=data.get("actividad_economica"),
            dia=data.get("dia"),
            mes=data.get("mes"),
            anio=data.get("anio"),
            tipo_examen=data.get("tipo_examen"),
            detalle_otros=data.get("detalle_otros"),
            apellido_paterno=data.get("apellido_paterno"),
            apellido_materno=data.get("apellido_materno"),
            nombres=data.get("nombres"),
            edad=data.get("edad"),
            genero=data.get("genero"),
            nro_doc_identidad=data.get("nro_doc_identidad"),
            puesto_trabajo=data.get("puesto_trabajo"),
            resultado=str(data.get("resultado", "")).upper(),
            detalle_conclusion=data.get("detalle_conclusion"),
            recomendacion_1=data.get("recomendacion_1"),
            recomendacion_2=data.get("recomendacion_2"),
            recomendacion_3=data.get("recomendacion_3"),
            recomendacion_4=data.get("recomendacion_4")
        )
        db.add(nueva_ficha)
        db.commit()
        return {"status": "success"}
    except Exception as e:
        print(f"ERROR: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/consultar-aptitud/{codigo_paciente}")
async def consultar_aptitud(codigo_paciente: str, db: Session = Depends(get_db)):
    paciente = db.query(models.Paciente).filter(func.upper(models.Paciente.codigo_paciente) == codigo_paciente.upper().strip()).first()
    if not paciente:
        return {"status": "error", "message": "Paciente no encontrado"}
    
    ficha = db.query(models.FichaAptitud).filter(models.FichaAptitud.paciente_id == paciente.id).first()
    if not ficha:
        return {"status": "error", "message": "Ficha no encontrada"}
        
    return ficha

@app.get("/filtrar-aptitud/{resultado}")
def filtrar_aptitud_por_resultado(resultado: str, db: Session = Depends(get_db)):
    # Consulta optimizada para el listado de pacientes según su resultado
    fichas = db.query(models.FichaAptitud).filter(models.FichaAptitud.resultado == resultado.upper()).all()
    resultados = []
    for f in fichas:
        paciente = db.query(models.Paciente).filter(models.Paciente.id == f.paciente_id).first()
        if paciente:
            resultados.append({
                "codigo": paciente.codigo_paciente,
                "nombre": f"{paciente.apellido} {paciente.nombre}",
                "resultado": f.resultado
            })
    return resultados


# ----------- FICHA APTITUD FISICA Y PSICOLOGICA -----------
@app.post("/guardar-aptitud-fisica")
def guardar_aptitud_fisica(data: dict, db: Session = Depends(get_db)):
    # Verificación de existencia del paciente para evitar registros huérfanos
    paciente_existente = db.query(Paciente).filter(Paciente.codigo_paciente == data.get("codigo_paciente")).first()
    
    if not paciente_existente:
        raise HTTPException(status_code=404, detail="El Código del Paciente no existe en la base de datos.")
    
    try:
        nueva_ficha = FichaAptitudFisica(
            codigo_paciente=data.get("codigo_paciente"),
            razon_social=data.get("razon_social"),
            actividad_economica=data.get("actividad_economica"),
            dia=data.get("dia"),
            mes=data.get("mes"),
            anio=data.get("anio"),
            tipo_examen=data.get("tipo_examen"),
            otros_tipo=data.get("otros_tipo"),
            ape_pat=data.get("ape_pat"),
            ape_mat=data.get("ape_mat"),
            nombres=data.get("nombres"),
            edad=data.get("edad"),
            genero=data.get("genero"),
            doc_id=data.get("doc_id"),
            puesto_trabajo=data.get("puesto_trabajo"),
            resultado_fisico=data.get("resultado_fisico"),
            resultado_psicologico=data.get("resultado_psicologico"),
            conclusion_general=data.get("conclusion_general"),
            rec1=data.get("rec1"),
            rec2=data.get("rec2"),
            rec3=data.get("rec3"),
            rec4=data.get("rec4"),
            rec5=data.get("rec5"),
            rec6=data.get("rec6")
        )
        db.add(nueva_ficha)
        db.commit()
        db.refresh(nueva_ficha)
        return {"status": "success", "id": nueva_ficha.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/buscar-aptitud-fisica/{codigo_paciente}")
def buscar_aptitud_fisica(codigo_paciente: str, db: Session = Depends(get_db)):
    ficha = db.query(FichaAptitudFisica).filter(FichaAptitudFisica.codigo_paciente == codigo_paciente).order_by(FichaAptitudFisica.id.desc()).first()
    if not ficha:
        raise HTTPException(status_code=404, detail="No se encontró registro para este código.")
    return ficha

@app.get("/filtrar-aptitud/{fisico}/{psico}")
def filtrar_aptitud(fisico: str, psico: str, db: Session = Depends(get_db)):
    resultados = db.query(FichaAptitudFisica).filter(
        FichaAptitudFisica.resultado_fisico == fisico,
        FichaAptitudFisica.resultado_psicologico == psico
    ).all()
    
    return [
        {
            "codigo": f.codigo_paciente,
            "nombre": f"{f.nombres} {f.ape_pat} {f.ape_mat}",
            "resultado": f"Físico: {f.resultado_fisico} / Psico: {f.resultado_psicologico}"
        } for f in resultados
    ]


# ----------- FICHA HISTORIAL CLÍNICO (COMPLETO) -----------------------------------------------
@app.post("/guardar-historial-clinico")
async def guardar_historial_clinico(data: dict, db: Session = Depends(get_db)):
    try:
        # Validación estricta del código
        codigo = str(data.get("codigo_paciente", "")).strip().upper()
        if not codigo:
            raise HTTPException(status_code=400, detail="Código paciente es obligatorio")
        
        paciente = db.query(models.Paciente).filter(func.upper(models.Paciente.codigo_paciente) == codigo).first()
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")

        campos_permitidos = {
            "empresa", "nombre", "fecha", "ci", "sexo", "edad", "puesto", "area", "anos", "riesgos",
            "ruido", "radiacion", "vibracion", "mecanicos", "temp_ext", "otros_fis", "polvo", "humos",
            "gases", "metales", "otros_quim", "mov_rep", "lev_carga", "otros_erg", "psicologicos", "biologicos", 
            "altura", "confinados", "antecedentes_det", "enf1", "si1", "no1", "fecha1", "dias1", "enf2", "si2", 
            "no2", "fecha2", "dias2", "hab_anamnesis", "anamnesis_det", "ta_m", "ta_cm", "fc", "peso", "talla", 
            "imc", "sat", "pam", "piel_n", "piel_a", "piel_d", "cabello_n", "cabello_a", "cabello_d", "ojos_n", 
            "ojos_a", "ojos_d", "oidos_n", "oidos_a", "oidos_d", "nariz_n", "nariz_a", "nariz_d", "boca_n", 
            "boca_d", "faringe_a", "faringe_d", "cuello_n", "cuello_a", "cuello_d", "resp_n", "resp_a", "resp_d", 
            "cardio_n", "cardio_a", "cardio_d", "dig_n", "dig_a", "dig_d", "gen_n", "gen_a", "gen_d", "loc_n", 
            "loc_a", "loc_d", "col_n", "col_a", "col_d", "linf_n", "linf_a", "linf_d", "nerv_n", "nerv_a", 
            "nerv_d", "hem_n", "hem_a", "hem_d", "glu_na", "glu_n", "glu_a", "glu_d", "ure_na", "ure_n", 
            "ure_a", "ure_d", "aur_na", "aur_n", "aur_a", "cre_na", "cre_n", "cre_a", "cre_d", "per_na", 
            "per_n", "per_a", "per_d", "vdr_na", "vdr_n", "vdr_a", "vdr_d", "cha_na", "cha_n", "cha_a", 
            "cha_d", "ego_na", "ego_n", "ego_a", "ego_d", "psa_na", "psa_n", "psa_a", "psa_d", "rxt_na", 
            "rxt_n", "rxt_a", "rxt_d", "ecg_na", "ecg_n", "ecg_a", "ecg_d", "esp_na", "esp_n", "esp_a", 
            "esp_d", "aud_na", "aud_n", "aud_a", "aud_d", "teq_na", "teq_n", "teq_a", "teq_d", "diag1", 
            "diag2", "diag3", "diag4", "diag5", "diag6", "diag7", "aptitud_apto", "aptitud_no_apto", 
            "aptitud_restriccion", "observaciones", "rec_nutricion", "rec_especialidad", "rec_laboratorio", 
            "rec_otras", "medidas_higiene", "codigo_paciente"
        }

        # Filtrar datos y asegurar que el código paciente siempre esté presente
        datos_a_guardar = {k: v for k, v in data.items() if k in campos_permitidos}
        datos_a_guardar["codigo_paciente"] = codigo
        datos_a_guardar["paciente_id"] = paciente.id

        nueva_ficha = models.HistorialClinico(**datos_a_guardar)
        db.add(nueva_ficha)
        db.commit()
        db.refresh(nueva_ficha)
        
        return {"status": "success", "message": "HISTORIAL CLÍNICO GUARDADO EXITOSAMENTE"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/historial-filtrado/{estado}")
async def filtrar_historial(estado: str, db: Session = Depends(get_db)):
    # Mapeo: el frontend envía 'aptitud_apto', el DB tiene 'APTO'
    query = db.query(models.HistorialClinico)
    
    if estado == "aptitud_apto":
        query = query.filter(models.HistorialClinico.aptitud_apto == 'APTO')
    elif estado == "aptitud_no_apto":
        query = query.filter(models.HistorialClinico.aptitud_no_apto == 'NO APTO')
    elif estado == "aptitud_restriccion":
        query = query.filter(models.HistorialClinico.aptitud_restriccion == 'APTO CON RESTRICCIÓN')

    resultados = query.all()
    
    return [{"codigo_paciente": r.codigo_paciente, "nombre": r.nombre, "estado": r.aptitud_apto or r.aptitud_no_apto or r.aptitud_restriccion} for r in resultados]


# ----------- FICHA OSTEOMUSCULAR (COMPLETO) -----------
@app.post("/guardar-osteomuscular")
async def guardar_osteomuscular(data: dict, db: Session = Depends(get_db)):
    try:
        codigo = str(data.get("codigo_paciente", "")).strip().upper()
        paciente = db.query(models.Paciente).filter(func.upper(models.Paciente.codigo_paciente) == codigo).first()
        
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")

        nueva_ficha = models.FichaOsteomuscular(
            codigo_paciente=codigo,
            nombre_completo=data.get("nombre_completo"),
            edad=data.get("edad"),
            sexo=data.get("sexo"),
            ci=data.get("ci"),
            fecha=data.get("fecha"),
            
            # I. PUESTO
            carga_menor_25=data.get("carga_menor_25"),
            carga_25_50=data.get("carga_25_50"),
            carga_mayor_50=data.get("carga_mayor_50"),
            postura_pie=data.get("postura_pie"),
            postura_sentado=data.get("postura_sentado"),
            mov_cabeza=data.get("mov_cabeza"),
            mov_tronco=data.get("mov_tronco"),
            mov_mms=data.get("mov_mms"),
            mov_mmi=data.get("mov_mmi"),

            # II. ANTECEDENTES
            ant1_fecha=data.get("ant1_fecha"),
            ant1_diagnostico=data.get("ant1_diagnostico"),
            ant1_tratamiento=data.get("ant1_tratamiento"),
            ant1_comentario=data.get("ant1_comentario"),
            ant2_fecha=data.get("ant2_fecha"),
            ant2_diagnostico=data.get("ant2_diagnostico"),
            ant2_tratamiento=data.get("ant2_tratamiento"),
            ant2_comentario=data.get("ant2_comentario"),
            ant3_fecha=data.get("ant3_fecha"),
            ant3_diagnostico=data.get("ant3_diagnostico"),
            ant3_tratamiento=data.get("ant3_tratamiento"),
            ant3_comentario=data.get("ant3_comentario"),

            # III. HOMBRO
            hombro_dx_desde=data.get("hombro_dx_desde"),
            hombro_ix_desde=data.get("hombro_ix_desde"),
            dolor_ant_der=data.get("dolor_ant_der"),
            dolor_lat_der=data.get("dolor_lat_der"),
            dolor_pos_der=data.get("dolor_pos_der"),
            flexion_der=data.get("flexion_der"),
            abduccion_der=data.get("abduccion_der"),
            rotacion_int_der=data.get("rotacion_int_der"),
            rotacion_ext_der=data.get("rotacion_ext_der"),
            dolor_ant_izq=data.get("dolor_ant_izq"),
            dolor_lat_izq=data.get("dolor_lat_izq"),
            dolor_pos_izq=data.get("dolor_pos_izq"),
            flexion_izq=data.get("flexion_izq"),
            abduccion_izq=data.get("abduccion_izq"),
            rotacion_int_izq=data.get("rotacion_int_izq"),
            rotacion_ext_izq=data.get("rotacion_ext_izq"),
            arco_der_presente=data.get("arco_der_presente"),
            arco_der_ausente=data.get("arco_der_ausente"),
            arco_izq_presente=data.get("arco_izq_presente"),
            arco_izq_ausente=data.get("arco_izq_ausente"),
            biceps_der_presente=data.get("biceps_der_presente"),
            biceps_der_ausente=data.get("biceps_der_ausente"),
            biceps_izq_presente=data.get("biceps_izq_presente"),
            biceps_izq_ausente=data.get("biceps_izq_ausente"),
            grave_hombro_der=data.get("grave_hombro_der"),
            grave_hombro_izq=data.get("grave_hombro_izq"),
            observaciones_hombro=data.get("observaciones_hombro"),

            # CODO
            codo_dx_desde=data.get("codo_dx_desde"),
            codo_ix_desde=data.get("codo_ix_desde"),
            edema_localizado_der=data.get("edema_localizado_der"),
            edema_nolocalizado_der=data.get("edema_nolocalizado_der"),
            epicondilio_der=data.get("epicondilio_der"),
            epitroclea_der=data.get("epitroclea_der"),
            olecranon_der=data.get("olecranon_der"),
            musculo_epicondilio_der=data.get("musculo_epicondilio_der"),
            musculo_epitroclea_der=data.get("musculo_epitroclea_der"),
            edema_localizado_izq=data.get("edema_localizado_izq"),
            edema_nolocalizado_izq=data.get("edema_nolocalizado_izq"),
            epicondilio_izq=data.get("epicondilio_izq"),
            epitroclea_izq=data.get("epitroclea_izq"),
            olecranon_izq=data.get("olecranon_izq"),
            musculo_epicondilio_izq=data.get("musculo_epicondilio_izq"),
            musculo_epitroclea_izq=data.get("musculo_epitroclea_izq"),
            epicondilitis_der_presente=data.get("epicondilitis_der_presente"),
            epicondilitis_der_ausente=data.get("epicondilitis_der_ausente"),
            parestesia_der=data.get("parestesia_der"),
            gravedad_codo_der=data.get("gravedad_codo_der"),
            epicondilitis_izq_presente=data.get("epicondilitis_izq_presente"),
            epicondilitis_izq_ausente=data.get("epicondilitis_izq_ausente"),
            parestesia_izq=data.get("parestesia_izq"),
            gravedad_codo_izq=data.get("gravedad_codo_izq"),
            observaciones_codo=data.get("observaciones_codo"),

            # MUÑECA
            muneca_dx_desde=data.get("muneca_dx_desde"),
            muneca_ix_desde=data.get("muneca_ix_desde"),
            quiste_dorsal_der=data.get("quiste_dorsal_der"),
            quiste_ventral_der=data.get("quiste_ventral_der"),
            edema_dorsal_der=data.get("edema_dorsal_der"),
            edema_ventral_der=data.get("edema_ventral_der"),
            edema_estiloide_radial_der=data.get("edema_estiloide_radial_der"),
            edema_estiloide_ulnar_der=data.get("edema_estiloide_ulnar_der"),
            hipotrofia_der=data.get("hipotrofia_der"),
            deformidades_der=data.get("deformidades_der"),
            quiste_dorsal_izq=data.get("quiste_dorsal_izq"),
            quiste_ventral_izq=data.get("quiste_ventral_izq"),
            edema_dorsal_izq=data.get("edema_dorsal_izq"),
            edema_ventral_izq=data.get("edema_ventral_izq"),
            edema_estiloide_radial_izq=data.get("edema_estiloide_radial_izq"),
            edema_estiloide_ulnar_izq=data.get("edema_estiloide_ulnar_izq"),
            hipotrofia_izq=data.get("hipotrofia_izq"),
            deformidades_izq=data.get("deformidades_izq"),
            trapecio_dx=data.get("trapecio_dx"),
            trapecio_ix=data.get("trapecio_ix"),
            estiloide_radial_dx=data.get("estiloide_radial_dx"),
            estiloide_radial_ix=data.get("estiloide_radial_ix"),
            clic_dx=data.get("clic_dx"),
            clic_ix=data.get("clic_ix"),
            finkelsten_der=data.get("finkelsten_der"),
            cr_der=data.get("cr_der"),
            mp_der=data.get("mp_der"),
            cr_resistencia_der=data.get("cr_resistencia_der"),
            dolor_extension_der=data.get("dolor_extension_der"),
            finkelsten_izq=data.get("finkelsten_izq"),
            cr_izq=data.get("cr_izq"),
            mp_izq=data.get("mp_izq"),
            cr_resistencia_izq=data.get("cr_resistencia_izq"),
            dolor_extension_izq=data.get("dolor_extension_izq"),
            sintomatologia_si=data.get("sintomatologia_si"),
            sintomatologia_no=data.get("sintomatologia_no"),
            apofisis_espinoza=data.get("apofisis_espinoza"),
            trapecio_sup=data.get("trapecio_sup"),
            paravertebral=data.get("paravertebral"),
            flexion_muneca=data.get("flexion_muneca"),
            extension_muneca=data.get("extension_muneca"),
            fatiga1_derecha=data.get("fatiga1_derecha"),
            fatiga2_derecha=data.get("fatiga2_derecha"),
            fatiga1_izquierda=data.get("fatiga1_izquierda"),
            fatiga2_izquierda=data.get("fatiga2_izquierda"),
            phalen_mediano_der=data.get("phalen_mediano_der"),
            phalen_cubital_der=data.get("phalen_cubital_der"),
            phalen_noterr_der=data.get("phalen_noterr_der"),
            presion_mediano_der=data.get("presion_mediano_der"),
            presion_cubital_der=data.get("presion_cubital_der"),
            presion_noterr_der=data.get("presion_noterr_der"),
            phalen_mediano_izq=data.get("phalen_mediano_izq"),
            phalen_cubital_izq=data.get("phalen_cubital_izq"),
            phalen_noterr_izq=data.get("phalen_noterr_izq"),
            presion_mediano_izq=data.get("presion_mediano_izq"),
            presion_cubital_izq=data.get("presion_cubital_izq"),
            presion_noterr_izq=data.get("presion_noterr_izq"),
            grado_codo_der=data.get("grado_codo_der"),
            grado_codo_izq=data.get("grado_codo_izq"),
            observaciones_muneca=data.get("observaciones_muneca"),

            # COLUMNA Y FINAL
            cervical_desde=data.get("cervical_desde"),
            dorsal_desde=data.get("dorsal_desde"),
            lumbar_desde=data.get("lumbar_desde"),
            conclusiones_diagnostica=data.get("conclusiones_diagnostica"),
            gravedad_cuadro=data.get("gravedad_cuadro"),
            concepto_aptitud=data.get("concepto_aptitud"),
            observaciones_final=data.get("observaciones_final"),
            restricciones=data.get("restricciones"),
            fecha_firma=data.get("fecha_firma")
        )
        
        db.add(nueva_ficha)
        db.commit()
        db.refresh(nueva_ficha)
        return {"status": "success", "message": "GUARDADO EXITOSAMENTE"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/filtrar-osteomuscular/{estado}")
async def filtrar_osteomuscular(estado: str, db: Session = Depends(get_db)):
    # Buscamos en la tabla ficha_osteomuscular
    resultados = db.query(models.FichaOsteomuscular).filter(models.FichaOsteomuscular.concepto_aptitud == estado).all()
    
    # Mapeamos los campos a lo que espera tu tabla HTML (codigo, nombre, resultado)
    return [{"codigo": r.codigo_paciente, "nombre": r.nombre_completo, "resultado": r.concepto_aptitud} for r in resultados]

@app.get("/api/informe-consolidado/{codigo_paciente}")
async def obtener_informe_consolidado(codigo_paciente: str, db: Session = Depends(get_db)):
    p = db.query(models.Paciente).filter(models.Paciente.codigo_paciente == codigo_paciente).first()
    if not p: raise HTTPException(status_code=404, detail="Paciente no encontrado")

    apt = db.query(models.FichaAptitud).filter(models.FichaAptitud.paciente_id == p.id).order_by(desc(models.FichaAptitud.id)).first()
    fis = db.query(models.FichaAptitudFisica).filter(models.FichaAptitudFisica.codigo_paciente == p.codigo_paciente).first()
    ost = db.query(models.FichaOsteomuscular).filter(models.FichaOsteomuscular.codigo_paciente == p.codigo_paciente).first()
    esp = db.query(models.FichaEspirometria).filter(models.FichaEspirometria.paciente_id == p.id).first()
    oft = db.query(models.FichaOftalmologica).filter(models.FichaOftalmologica.paciente_id == p.id).first()
    car = db.query(models.FichaCardiologia).filter(models.FichaCardiologia.paciente_id == p.id).first()
    ele = db.query(models.FichaElectroencefalograma).filter(models.FichaElectroencefalograma.paciente_id == p.id).first()
    alt = db.query(models.FichaAltura).filter(models.FichaAltura.paciente_id == p.id).first()
    dec = db.query(models.AntecedentesP2).filter(models.AntecedentesP2.paciente_id == p.id).first()
    his = db.query(models.HistorialClinico).filter(models.HistorialClinico.paciente_id == p.id).first()
    psi = db.query(models.FichaPsicologia).filter(models.FichaPsicologia.paciente_id == p.id).first()

    return {
        "datos_generales": {"codigo": p.codigo_paciente, "nombre": f"{p.nombre} {p.apellido}"},
        "resultados_medicos": {
            "01_aptitud_ocupacional": apt.resultado if apt and hasattr(apt, 'resultado') else "SIN EXAMEN",
            "02_aptitud_fisica_psicologica": {
                "fisico": fis.resultado_fisico if fis else "Sin examén", 
                "psico": fis.resultado_psicologico if fis else "Sin examén"
            },
            "03_osteomuscular": ost.concepto_aptitud if ost else "Sin examén",
            "04_espirometria": "Examen realizado" if esp else "Sin examén",
            "05_oftalmologia": f"LENTES: {oft.lentes or 'NO'}, ESTRABISMO: {oft.estrabismo or 'NO'}, DALTONISMO: {oft.daltonismo or 'NO'}" if oft else "SIN EXAMEN",
            "06_cardiologia": f"NIÑEZ: {car.ninez or 'NO'}, ADOLESCENTE: {car.adolescente or 'NO'}, ADULTEZ: {car.adultez or 'NO'}" if car else "SIN EXAMEN",
            "07_electroencefalograma": f"CEFALEAS: {ele.cefaleas or 'NO'}, EPILEPSIA: {ele.epilepsia or 'NO'}, CONVULSIONES: {ele.convulsiones or 'NO'}" if ele else "SIN EXAMEN",
            "08_altura": f"SOPLO CARDIACO: {alt.soplo_cardiaco or 'NO'}, ARRITMIAS: {alt.arritmias_cardiacas or 'NO'}" if alt else "SIN EXAMEN",
            "09_declaracion_jurada": "Completada" if dec else "Sin examén",
            "10_historial_clinico": "Completado" if his else "Sin examén",
            "11_psicologia_detallada": psi.resultado_psicologico if psi and psi.resultado_psicologico else "SIN EXAMEN"
        }
    }
