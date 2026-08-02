from pydantic import BaseModel, ConfigDict
from typing import Optional

class PacienteBase(BaseModel):
    nombre: str
    apellido: str
    ci: str
    codigo_paciente: str
    model_config = ConfigDict(from_attributes=True)

class DeclaracionJuradaBase(BaseModel):
    paciente_id: int
    edad: Optional[str] = None
    sexo: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    lugar_nacimiento: Optional[str] = None
    domicilio: Optional[str] = None
    n_casa: Optional[str] = None
    zona_barrio: Optional[str] = None
    ciudad: Optional[str] = None
    pais: Optional[str] = None
    telefono: Optional[str] = None
    estado_civil: Optional[str] = None
    profesion_oficio: Optional[str] = None
    model_config = ConfigDict(from_attributes=True, extra='allow')

class AntecedentesP2Base(BaseModel):
    paciente_id: int
    vista: Optional[str] = None
    auditivo: Optional[str] = None
    respiratorio: Optional[str] = None
    cardiovasculares: Optional[str] = None
    digestivos: Optional[str] = None
    sangre: Optional[str] = None
    genitourinario: Optional[str] = None
    sistema_nervioso: Optional[str] = None
    psiquiatricos: Optional[str] = None
    osteomusculares: Optional[str] = None
    reumatologicos: Optional[str] = None
    dermatologicos: Optional[str] = None
    alergias: Optional[str] = None
    cirugias: Optional[str] = None
    infecciones: Optional[str] = None
    accidentes_pers: Optional[str] = None
    accidentes_trab: Optional[str] = None
    medicamentos: Optional[str] = None
    endocrino: Optional[str] = None
    antecedentes_fam: Optional[str] = None
    otros_especificos: Optional[str] = None
    generales: Optional[str] = None
    model_config = ConfigDict(from_attributes=True, extra='allow')

class HabitosRiesgosP3Base(BaseModel):
    paciente_id: int
    fuma: Optional[str] = None
    fuma_cantidad: Optional[str] = None
    alcohol: Optional[str] = None
    alcohol_frecuencia: Optional[str] = None
    drogas: Optional[str] = None
    drogas_tipo: Optional[str] = None
    coca: Optional[str] = None
    deporte: Optional[str] = None
    deporte_detalle: Optional[str] = None
    grupo_sanguineo: Optional[str] = None
    historia_laboral: Optional[str] = None
    riesgos_expuestos: Optional[str] = None
    observaciones: Optional[str] = None
    model_config = ConfigDict(from_attributes=True, extra='allow')

class EnfermeraBase(BaseModel):
    ci_enfe: str
    appaterno_enfe: str
    apmaterno_enfe: str
    nombre_enfe: str
    turno_enfe: str
    edu_enfe: str
    model_config = ConfigDict(from_attributes=True)

class DoctorBase(BaseModel):
    ci_doc: str
    appaterno_doc: str
    apmaterno_doc: str
    nombre_doc: str
    turno_doc: str
    especialidad: str
    model_config = ConfigDict(from_attributes=True)
