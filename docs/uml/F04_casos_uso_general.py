import math
from lienzo import Lienzo


def borde(e, x, y):
    cx, cy, w, h = e
    a, b = w / 2, h / 2
    dx, dy = x - cx, y - cy
    t = 1 / math.sqrt((dx / a) ** 2 + (dy / b) ** 2)
    return cx + dx * t, cy + dy * t


L = Lienzo(1200, 880)
L.rect(190, 125, 830, 630)
L.texto(205, 142, "Sistema de Gestión de Historias Clínicas Digitales — OHS", ancla="start", negrita=True)

cu = {}
cu["01"] = L.elipse(605, 175, "CU-01 Iniciar sesión")
cu["02"] = L.elipse(330, 245, "CU-02 Registrar trabajador\ny evaluación")
cu["10"] = L.elipse(560, 255, "CU-10 Verificar CI\nregistrado")
cu["03"] = L.elipse(330, 325, "CU-03 Registrar declaración\njurada (P1, P2, P3)")
cu["12"] = L.elipse(250, 520, "CU-12 Corregir datos\nde identificación")
cu["05"] = L.elipse(600, 430, "CU-05 Buscar trabajador\npor CI o nombre")
cu["04"] = L.elipse(600, 560, "CU-04 Registrar ficha\nde especialidad")
cu["07"] = L.elipse(870, 200, "CU-07 Consultar fichas\npor especialidad")
cu["11"] = L.elipse(870, 275, "CU-11 Consultar semáforo\nde alertas")
cu["08"] = L.elipse(870, 350, "CU-08 Consultar expediente\ndel trabajador")
cu["09"] = L.elipse(870, 430, "CU-09 Generar informe\ny certificado")
cu["15"] = L.elipse(870, 520, "CU-15 Consultar historial\nde modificaciones")
cu["06"] = L.elipse(285, 705, "CU-06 Gestionar personal\ny perfiles")
cu["13"] = L.elipse(640, 700, "CU-13 Eliminar y restaurar\nexpediente")
cu["14"] = L.elipse(475, 688, "CU-14 Descargar\nrespaldo")

L.actor(605, 52, "Usuario del sistema")
L.actor(80, 330, "Enfermería")
L.actor(1120, 300, "Usuario de\nconsulta")
L.actor(1120, 650, "Profesional de\nespecialidad")
L.actor(760, 812, "Médico responsable")


def asoc(xa, ya, c):
    L.flecha([(xa, ya), borde(cu[c], xa, ya)], punta=None)


asoc(605, 100, "01")
for c in ("02", "03", "12", "04"):
    asoc(98, 318, c)
for c in ("07", "11", "08", "09"):
    asoc(1102, 288, c)
asoc(1102, 638, "04")
for c in ("06", "13", "14", "15"):
    asoc(760, 778, c)


def incluye(a, b, etq="«include»", pos=None):
    pa = borde(cu[a], cu[b][0], cu[b][1])
    pb = borde(cu[b], cu[a][0], cu[a][1])
    L.flecha([pa, pb], punta="abierta", discontinua=True, etiqueta=etq, pos_etq=pos)


incluye("02", "10")
incluye("04", "05", pos=(645, 495))
incluye("08", "05", pos=(735, 375))
incluye("09", "05", pos=(735, 445))
incluye("15", "09", "«extend»", pos=(905, 476, "start"))

L.flecha([(80, 290), (80, 26), (583, 26)], punta="triangulo")
L.flecha([(1120, 262), (1120, 26), (627, 26)], punta="triangulo")
L.flecha([(1120, 616), (1120, 368)], punta="triangulo")
L.flecha([(740, 830), (40, 830), (40, 322), (66, 322)], punta="triangulo")
L.flecha([(780, 830), (1165, 830), (1165, 642), (1134, 642)], punta="triangulo")
L.guardar("F04_casos_uso_general")
