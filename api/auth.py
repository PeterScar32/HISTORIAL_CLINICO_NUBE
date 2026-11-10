import re
import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import Session

from .database import Base, SessionLocal

router = APIRouter()

SECRETO = os.getenv("SECRET_KEY") or secrets.token_hex(32)
DURACION_TOKEN = 12 * 3600
ITERACIONES = 200_000

ROL_MEDICO = "MEDICO"
ROL_ESPECIALISTA = "ESPECIALISTA"
ROL_ENFERMERIA = "ENFERMERIA"
ROL_LECTURA = "LECTURA"
ROLES = (ROL_MEDICO, ROL_ESPECIALISTA, ROL_ENFERMERIA, ROL_LECTURA)
ROLES_RESPONSABLES = (ROL_MEDICO, ROL_ESPECIALISTA)

RUTAS_FICHA = {
    "declaracion": "/filiacion/", "antecedentes": "/p2/", "habitos": "/p3/",
    "cardiologia": "/guardar-cardiologia", "psicologia": "/guardar-psicologia", "espirometria": "/guardar-espirometria",
    "altura": "/guardar-altura", "electroencefalograma": "/guardar-electro", "aptitud": "/guardar-aptitud",
    "aptitud_fisica": "/guardar-aptitud-fisica", "historial_clinico": "/guardar-historial-clinico",
    "osteomuscular": "/guardar-osteomuscular", "oftalmologia": "/ficha-oftalmo/",
}


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    cargo = Column(String)
    rol = Column(String, nullable=False)
    especialidad = Column(String)
    fichas_permitidas = Column(String)
    foto = Column(String)
    orden = Column(Integer, default=100)
    pass_hash = Column(String)
    debe_cambiar = Column(Boolean, default=True)
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, server_default=func.now())


PERFILES_INICIALES = [
    ("mecondarco", "MARÍA ELENA CONDARCO CASTELLÓN", "Gerente Técnico · Higiene Ocupacional y Medio Ambiente", ROL_MEDICO, "img/mecondarco.jpg", 1),
    ("knoya", "KARLA NOYA BARRERA", "Gerente · Salud Ocupacional y Medicina Preventiva", ROL_MEDICO, "img/knoya.jpg", 2),
    ("rcervantes", "RAFAEL CERVANTES MORANT", "Gerente · Asistencia Técnica (Medicina del Trabajo)", ROL_MEDICO, "img/rcervantes.jpg", 3),
    ("lquinteros", "LUIS QUINTEROS AILLÓN", "Gerente General", ROL_MEDICO, "img/lquinteros.jpg", 4),
    ("enfermeria", "ENFERMERÍA", "Registro de datos y fichas", ROL_ENFERMERIA, None, 5),
]

RUTAS_PUBLICAS = {"/", "/auth/perfiles", "/auth/login"}

PREFIJOS_ADMIN = ("/admin", "/auth/usuarios", "/papelera")

PREFIJOS_SOLO_MEDICO = (
    "/semaforo", "/reglas-semaforo", "/empresas", "/api/informe-consolidado", "/verificar_estado_paciente",
    "/filtrar", "/buscar-cardiologia", "/ficha-psicologia-filtrada", "/espirometria-filtrada", "/listar-espirometria",
    "/consultar-electro-por-campo", "/historial-filtrado", "/api/reporte-unificado", "/auditoria", "/api/expediente",
    "/consultas",
)


def hash_clave(clave: str, sal: str = None) -> str:
    sal = sal or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal.encode(), ITERACIONES)
    return f"pbkdf2${ITERACIONES}${sal}${dk.hex()}"


def verificar_clave(clave: str, guardado: str) -> bool:
    try:
        _, iters, sal, h = guardado.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal.encode(), int(iters))
        return hmac.compare_digest(dk.hex(), h)
    except (ValueError, AttributeError):
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def crear_token(u: Usuario) -> str:
    carga = _b64(json.dumps({"uid": u.id, "rol": u.rol, "exp": int(time.time()) + DURACION_TOKEN}).encode())
    firma = _b64(hmac.new(SECRETO.encode(), carga.encode(), hashlib.sha256).digest())
    return f"{carga}.{firma}"


def leer_token(token: str):
    try:
        carga, firma = token.split(".")
        esperada = _b64(hmac.new(SECRETO.encode(), carga.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(firma, esperada):
            return None
        datos = json.loads(_unb64(carga))
        if datos.get("exp", 0) < time.time():
            return None
        return datos
    except Exception:
        return None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def sembrar_usuarios(db: Session):
    try:
        claves = json.loads(os.getenv("OHS_CLAVES_INICIALES", "{}"))
    except ValueError:
        claves = {}
    for usuario, nombre, cargo, rol, foto, orden in PERFILES_INICIALES:
        u = db.query(Usuario).filter(Usuario.usuario == usuario).first()
        if not u:
            u = Usuario(usuario=usuario, nombre=nombre, cargo=cargo, rol=rol, foto=foto, orden=orden, debe_cambiar=True)
            db.add(u)
        if not u.pass_hash and claves.get(usuario):
            u.pass_hash = hash_clave(claves[usuario])
            u.debe_cambiar = True
    db.commit()


def publico(u: Usuario):
    return {"id": u.id, "usuario": u.usuario, "nombre": u.nombre, "cargo": u.cargo, "rol": u.rol,
            "especialidad": u.especialidad, "fichas_permitidas": [f for f in (u.fichas_permitidas or "").split(",") if f],
            "foto": u.foto, "debe_cambiar": bool(u.debe_cambiar)}


def permitido(u: Usuario, metodo: str, ruta: str) -> bool:
    if u.rol == ROL_MEDICO:
        return True
    if ruta.startswith(PREFIJOS_ADMIN):
        return False
    if ruta.startswith("/exportar"):
        return u.rol == ROL_ENFERMERIA and metodo == "GET"
    if u.rol == ROL_LECTURA:
        return metodo == "GET" and not ruta.startswith("/auditoria")
    if u.rol == ROL_ESPECIALISTA:
        if metodo == "GET":
            return not ruta.startswith("/auditoria")
        if metodo == "POST" and re.fullmatch(r"/pacientes/\d+/adjuntos", ruta):
            return True
        propias = [f for f in (u.fichas_permitidas or "").split(",") if f]
        return any(ruta == RUTAS_FICHA[f] or ruta.rstrip("/") == RUTAS_FICHA[f].rstrip("/") for f in propias if f in RUTAS_FICHA)
    if metodo == "DELETE":
        return False
    if ruta.startswith(PREFIJOS_SOLO_MEDICO):
        return False
    if ruta.startswith(("/doctores", "/enfermeras", "/reglas-semaforo")) and metodo != "GET":
        return False
    return True


async def control_acceso(request: Request, call_next, db_factory=SessionLocal):
    ruta = request.url.path
    if request.method == "OPTIONS" or ruta in RUTAS_PUBLICAS:
        return await call_next(request)
    auth = request.headers.get("authorization", "")
    datos = leer_token(auth[7:]) if auth.lower().startswith("bearer ") else None
    if not datos:
        return JSONResponse({"detail": "Sesión no iniciada o vencida"}, status_code=401)
    with db_factory() as db:
        u = db.query(Usuario).filter(Usuario.id == datos["uid"], Usuario.activo.is_(True)).first()
        if not u:
            return JSONResponse({"detail": "Usuario no válido o desactivado"}, status_code=401)
        if ruta not in ("/auth/cambiar-clave", "/auth/yo"):
            if u.debe_cambiar:
                return JSONResponse({"detail": "Debe cambiar su contraseña"}, status_code=403)
            if not permitido(u, request.method, ruta):
                return JSONResponse({"detail": "Su perfil no tiene permiso para esta acción"}, status_code=403)
        resp = request.headers.get("x-responsable", "")
        if resp and resp != "0" and request.method in ("POST", "PUT"):
            r = db.query(Usuario).filter(Usuario.id == int(resp) if resp.isdigit() else False).first()
            if not r or not r.activo or r.rol not in ROLES_RESPONSABLES:
                return JSONResponse({"detail": "El profesional responsable indicado no es válido"}, status_code=400)
        datos["rol"] = u.rol
    request.state.usuario = datos
    return await call_next(request)


def usuario_actual(request: Request, db: Session = Depends(get_db)) -> Usuario:
    datos = getattr(request.state, "usuario", None)
    u = db.query(Usuario).filter(Usuario.id == datos["uid"]).first() if datos else None
    if not u:
        raise HTTPException(status_code=401, detail="Sesión no iniciada")
    return u


@router.get("/auth/perfiles")
def perfiles(db: Session = Depends(get_db)):
    us = db.query(Usuario).filter(Usuario.activo.is_(True)).order_by(Usuario.orden, Usuario.id).all()
    return [{"usuario": u.usuario, "nombre": u.nombre, "cargo": u.cargo, "rol": u.rol, "foto": u.foto} for u in us]


@router.post("/auth/login")
def login(data: dict, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter(Usuario.usuario == str(data.get("usuario", "")), Usuario.activo.is_(True)).first()
    if not u or not u.pass_hash or not verificar_clave(str(data.get("clave", "")), u.pass_hash):
        time.sleep(0.5)
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    return {"token": crear_token(u), "usuario": publico(u)}


@router.get("/auth/yo")
def yo(u: Usuario = Depends(usuario_actual)):
    return publico(u)


@router.post("/auth/cambiar-clave")
def cambiar_clave(data: dict, u: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    actual, nueva = str(data.get("actual", "")), str(data.get("nueva", ""))
    if not verificar_clave(actual, u.pass_hash or ""):
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta")
    if len(nueva) < 8:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe tener al menos 8 caracteres")
    if nueva == actual:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe ser distinta de la temporal")
    u.pass_hash = hash_clave(nueva)
    u.debe_cambiar = False
    db.commit()
    return {"token": crear_token(u), "usuario": publico(u)}


@router.get("/auth/profesionales")
def profesionales(db: Session = Depends(get_db)):
    us = db.query(Usuario).filter(Usuario.activo.is_(True), Usuario.rol.in_(ROLES_RESPONSABLES)).order_by(Usuario.orden, Usuario.nombre).all()
    return [{"id": u.id, "nombre": u.nombre, "cargo": u.cargo, "especialidad": u.especialidad, "rol": u.rol} for u in us]


@router.get("/auth/usuarios")
def listar_usuarios(db: Session = Depends(get_db)):
    return [publico(u) | {"activo": u.activo} for u in db.query(Usuario).order_by(Usuario.orden, Usuario.id).all()]


def _datos_usuario(data: dict):
    campos = {}
    for k in ("nombre", "cargo", "especialidad"):
        if k in data:
            campos[k] = " ".join(str(data[k] or "").split()).upper() or None
    if "rol" in data:
        if data["rol"] not in ROLES:
            raise HTTPException(status_code=400, detail="Rol no válido")
        campos["rol"] = data["rol"]
    if "fichas_permitidas" in data:
        lista = data["fichas_permitidas"] or []
        if any(f not in RUTAS_FICHA for f in lista):
            raise HTTPException(status_code=400, detail="Ficha no válida")
        campos["fichas_permitidas"] = ",".join(lista)
    if "activo" in data:
        campos["activo"] = bool(data["activo"])
    return campos


def _usuario_unico(db: Session, nombre: str) -> str:
    partes = [p for p in "".join(c for c in nombre.lower() if c.isalpha() or c == " ").split() if p]
    base = ((partes[0][0] if partes else "u") + (partes[1] if len(partes) > 1 else "")).translate(str.maketrans("áéíóúñü", "aeiounu"))[:20] or "usuario"
    cand, n = base, 2
    while db.query(Usuario).filter(Usuario.usuario == cand).first():
        cand, n = f"{base}{n}", n + 1
    return cand


@router.post("/auth/usuarios")
def crear_usuario(data: dict, db: Session = Depends(get_db)):
    campos = _datos_usuario(data)
    if not campos.get("nombre") or not campos.get("rol"):
        raise HTTPException(status_code=400, detail="Nombre y rol son obligatorios")
    if campos["rol"] == ROL_ESPECIALISTA and not campos.get("fichas_permitidas"):
        raise HTTPException(status_code=400, detail="Indique las fichas que llena el especialista")
    temporal = secrets.token_urlsafe(6)
    u = Usuario(usuario=_usuario_unico(db, campos["nombre"]), orden=50, pass_hash=hash_clave(temporal), debe_cambiar=True, **campos)
    db.add(u)
    db.commit()
    db.refresh(u)
    return publico(u) | {"activo": u.activo, "temporal": temporal}


@router.put("/auth/usuarios/{usuario_id}")
def editar_usuario(usuario_id: int, data: dict, request: Request, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    campos = _datos_usuario(data)
    actual = getattr(request.state, "usuario", {}).get("uid")
    if u.id == actual and (campos.get("activo") is False or campos.get("rol", ROL_MEDICO) != ROL_MEDICO):
        raise HTTPException(status_code=400, detail="No puede desactivarse ni quitarse el rol de médico a sí mismo")
    for k, v in campos.items():
        setattr(u, k, v)
    if u.rol == ROL_ESPECIALISTA and not u.fichas_permitidas:
        raise HTTPException(status_code=400, detail="Indique las fichas que llena el especialista")
    if not db.query(Usuario).filter(Usuario.rol == ROL_MEDICO, Usuario.activo.is_(True)).count():
        db.rollback()
        raise HTTPException(status_code=400, detail="Debe quedar al menos un médico activo")
    db.commit()
    return publico(u) | {"activo": u.activo}


@router.post("/auth/usuarios/{usuario_id}/restablecer")
def restablecer(usuario_id: int, data: dict, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    temporal = str(data.get("temporal", "")) or secrets.token_urlsafe(6)
    u.pass_hash = hash_clave(temporal)
    u.debe_cambiar = True
    if data.get("nombre"):
        u.nombre = str(data["nombre"]).strip().upper()
    db.commit()
    return {"usuario": u.usuario, "temporal": temporal}
