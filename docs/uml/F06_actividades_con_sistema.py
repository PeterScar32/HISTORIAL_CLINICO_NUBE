from lienzo import Lienzo, carriles, rombo, inicio, fin

W, H = 250, 850
L = Lienzo(4 * W, H)
carriles(L, ["Enfermería", "Profesional de especialidad", "Sistema", "Médico responsable"], W, H)


def act(cx, cy, t):
    return L.caja(cx, cy, t, rx=12, minw=170)


def baja(c):
    return c[1] + c[3] / 2


def sube(c):
    return c[1] - c[3] / 2


inicio(L, 125, 65)
a1 = act(125, 115, "Iniciar sesión")
a2 = act(125, 180, "Ingresar el CI\ndel trabajador")
s1 = act(625, 180, "Buscar el CI\nentre los registrados")
rombo(L, 625, 255)
a3 = act(125, 255, "Registrar nombres,\napellidos y CI")
rombo(L, 125, 330)
a4 = act(125, 395, "Registrar la evaluación\n(empresa, puesto, tipo\ny fichas requeridas)")
a5 = act(125, 470, "Registrar la declaración\njurada (P1, P2, P3)")
rombo(L, 375, 545)
rombo(L, 375, 605)
L.texto(392, 580, "¿Faltan fichas\nrequeridas?", ancla="start")
b1 = act(375, 680, "Abrir la ficha\ndel trabajador")
b2 = act(375, 750, "Registrar los resultados\ny elegir al responsable")
s2 = act(625, 750, "Guardar la ficha en la\nevaluación y registrar\nla autoría y los cambios")
c1 = act(875, 665, "Revisar el semáforo\ny el expediente")
c2 = act(875, 735, "Generar el informe\no el certificado")
fin(L, 875, 805)

F = L.flecha
F([(125, 75), (125, sube(a1))])
F([(125, baja(a1)), (125, sube(a2))])
F([(125 + a2[2] / 2, 180), (625 - s1[2] / 2, 180)])
F([(625, baja(s1)), (625, 242)])
F([(612, 255), (125 + a3[2] / 2, 255)], etiqueta="[CI no registrado]", pos_etq=(420, 245))
F([(625, 268), (625, 330), (138, 330)], etiqueta="[CI registrado]", pos_etq=(560, 320))
F([(125, baja(a3)), (125, 317)])
F([(125, 343), (125, sube(a4))])
F([(125, baja(a4)), (125, sube(a5))])
F([(125, baja(a5)), (125, 515), (375, 515), (375, 532)])
F([(375, 558), (375, 592)])
F([(375, 618), (375, sube(b1))], etiqueta="[Sí]", pos_etq=(380, 632, "start"))
F([(375, baja(b1)), (375, sube(b2))])
F([(375 + b2[2] / 2, 750), (625 - s2[2] / 2, 750)])
F([(625, baja(s2)), (625, 812), (268, 812), (268, 545), (362, 545)])
F([(388, 605), (875, 605), (875, sube(c1))], etiqueta="[No]", pos_etq=(430, 615, "start"))
F([(875, baja(c1)), (875, sube(c2))])
F([(875, baja(c2)), (875, 794)])
L.guardar("F06_actividades_con_sistema")
