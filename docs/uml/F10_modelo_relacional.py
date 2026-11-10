from lienzo import Lienzo, clase

L = Lienzo(1250, 820)
izq = [("usuarios", ["PK id", "UQ usuario NN", "nombre NN", "rol NN", "especialidad", "fichas_permitidas", "pass_hash", "activo"]),
       ("auditoria", ["PK id", "fecha", "usuario", "accion NN", "tabla NN", "paciente_id", "evaluacion_id", "campo, valor_anterior,", "valor_nuevo"]),
       ("papelera", ["PK id", "paciente_id", "ci", "datos NN (JSON)", "eliminado_en, eliminado_por"]),
       ("reglas_semaforo", ["PK id", "patron NN", "color NN", "prioridad"]),
       ("doctores", ["PK id_doc", "UQ ci_doc"]),
       ("enfermeras", ["PK id_enfe", "UQ ci_enfe"])]
y = 15
for n, at in izq:
    b = clase(L, 15, y, n, at, w=200)
    y += b[3] + 12
L.texto(115, y + 8, "Tablas sin claves foráneas", cursiva=True, tam=11)

pac = clase(L, 470, 20, "pacientes", ["PK id", "nombre", "apellido", "UQ ci", "codigo_paciente"], w=170)
eva = clase(L, 860, 20, "evaluaciones", ["PK id", "FK paciente_id NN", "fecha", "empresa, puesto, tipo", "fichas_requeridas"], w=190)
L.flecha([(pac[0] + pac[2], 80), (eva[0], 80)], punta="cero_muchos", inicio="uno")

fichas = [("declaraciones_p1", ""), ("antecedentes_p2", ""), ("habitos_p3", ""), ("ficha_oftalmologica", ""), ("fichas_psicologia", ""),
          ("ficha_espirometria", ""), ("ficha_cardiologia", " NN"), ("ficha_altura", ""), ("ficha_electroencefalograma", ""),
          ("ficha_aptitud", " NN"), ("ficha_aptitud_fisica", ""), ("ficha_osteomuscular", ""), ("historial_clinico", "")]
filas = [fichas[0:5], fichas[5:9], fichas[9:13]]
W, GAP, X0 = 182, 12, 268
ys = [270, 450, 630]
pa_x = pac[0] + pac[2] / 2
ev_x = eva[0] + eva[2] / 2
TA, TB = 252, 1240
L.flecha([(pa_x, pac[1] + pac[3]), (pa_x, 205), (TA, 205), (TA, ys[2] - 50)], punta=None, inicio="uno")
L.flecha([(ev_x, eva[1] + eva[3]), (ev_x, 180), (TB, 180), (TB, ys[2] - 32)], punta=None, inicio="uno")
for fila, y0 in zip(filas, ys):
    ya, yb = y0 - 50, y0 - 32
    xs = [X0 + i * (W + GAP) for i in range(len(fila))]
    L.flecha([(TA, ya), (xs[-1] + 40, ya)], punta=None)
    L.flecha([(xs[0] + W - 40, yb), (TB, yb)], punta=None)
    for x, (n, nn) in zip(xs, fila):
        clase(L, x, y0, n, ["PK id", f"FK paciente_id{nn}", "FK evaluacion_id", "creado_en, registrado_por", "responsable_id, responsable"], w=W)
        L.flecha([(x + 40, ya), (x + 40, y0)], punta="cero_muchos")
        L.flecha([(x + W - 40, yb), (x + W - 40, y0)], punta="cero_muchos")
L.texto(268, 800, "PK: clave primaria · FK: clave foránea (ON DELETE CASCADE) · UQ: valor único · NN: no admite nulos. "
        "Las fichas tienen además los campos propios de cada formulario (Anexo C).", ancla="start", cursiva=True, tam=11)
L.guardar("F10_modelo_relacional")
