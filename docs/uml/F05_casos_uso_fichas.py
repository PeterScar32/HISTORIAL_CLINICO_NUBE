from lienzo import Lienzo

L = Lienzo(1060, 560)
L.rect(170, 20, 870, 520)
L.texto(185, 37, "Módulo de fichas clínico-ocupacionales", ancla="start", negrita=True)
cu04 = L.elipse(520, 110, "CU-04 Registrar ficha\nde especialidad")
cu05 = L.elipse(870, 110, "CU-05 Buscar trabajador\npor CI o nombre")
L.flecha([(cu04[0] + cu04[2] / 2, 110), (cu05[0] - cu05[2] / 2, 110)], punta="abierta", discontinua=True, etiqueta="«include»", pos_etq=(705, 100))
L.actor(80, 120, "Profesional de\nespecialidad")
L.actor(80, 270, "Enfermería")
L.flecha([(98, 112), (cu04[0] - cu04[2] / 2, 110)], punta=None)
L.flecha([(98, 262), (452, 127)], punta=None)
fichas = ["Oftalmología", "Evaluación\npsicológica", "Espirometría", "Cardiología", "Trabajo\nen altura",
          "Electroencefalograma", "Aptitud médico\nocupacional", "Aptitud física\ny psicológica", "Evaluación\nosteomuscular", "Historia\nclínica"]
xs = [300, 485, 670, 855, 1000]
bus = 235
L.flecha([(520, bus), (520, cu04[1] + cu04[3] / 2)], punta="triangulo")
L.flecha([(300, bus), (920, bus)], punta=None)
for i, f in enumerate(fichas):
    fila = i // 5
    x = [300, 455, 610, 765, 920][i % 5]
    y = 320 if fila == 0 else 450
    e = L.elipse(x, y, f, w=145, h=50)
    if fila == 0:
        L.flecha([(x, y - 25), (x, bus)], punta=None)
    else:
        L.flecha([(x, y - 25), (x, 385)], punta=None)
L.flecha([(300, 385), (920, 385)], punta=None)
L.flecha([(205, 385), (300, 385)], punta=None)
L.flecha([(205, 385), (205, bus), (300, bus)], punta=None)
L.texto(600, 525, "Cada ficha especializa a CU-04: comparte su flujo y registra los campos propios de su especialidad.", cursiva=True, tam=11)
L.guardar("F05_casos_uso_fichas")
