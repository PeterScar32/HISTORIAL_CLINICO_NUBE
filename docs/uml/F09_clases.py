from lienzo import Lienzo, clase

L = Lienzo(1180, 920)
pac = clase(L, 470, 20, "Paciente", ["-id: int", "-nombre: str", "-apellido: str", "-ci: str {unique}", "-codigo_paciente: str"])
eva = clase(L, 455, 190, "Evaluacion", ["-id: int", "-paciente_id: int", "-fecha: date", "-empresa: str", "-puesto: str", "-tipo: str", "-fichas_requeridas: str", "-creado_en: datetime"])
fic = clase(L, 440, 425, "FichaClinica", ["-id: int", "-paciente_id: int", "-evaluacion_id: int", "-creado_en: datetime", "-registrado_por: str", "-responsable_id: int", "-responsable: str"], abstracta=True)
usu = clase(L, 860, 400, "Usuario", ["-id: int", "-usuario: str {unique}", "-nombre: str", "-rol: str", "-especialidad: str", "-fichas_permitidas: str", "-pass_hash: str", "-activo: bool", "-debe_cambiar: bool"])
aud = clase(L, 860, 20, "Auditoria", ["-id: int", "-fecha: datetime", "-usuario: str", "-accion: str", "-tabla: str", "-paciente_id: int", "-evaluacion_id: int", "-campo: str", "-valor_anterior: text", "-valor_nuevo: text"])
pap = clase(L, 30, 20, "Papelera", ["-id: int", "-paciente_id: int", "-ci: str", "-nombre: str", "-eliminado_en: datetime", "-eliminado_por: str", "-datos: text (JSON)", "-restaurado_en: datetime", "-restaurado_por: str"])
reg = clase(L, 30, 250, "ReglaSemaforo", ["-id: int", "-patron: str", "-tipo: str", "-color: str", "-prioridad: int", "-activo: bool"])
doc = clase(L, 30, 425, "Doctor", ["-id_doc: int", "-ci_doc: str {unique}", "-nombre_doc: str", "-especialidad: str"], estereotipo="tabla heredada")
enf = clase(L, 230, 425, "Enfermera", ["-id_enfe: int", "-ci_enfe: str {unique}", "-nombre_enfe: str", "-especialidad: str"], estereotipo="tabla heredada")

subs = [("DeclaracionJurada", ["-edad: str", "-sexo: str"], "P1 filiación"), ("AntecedentesP2", ["-vista: str", "-alergias: str"], "P2 antecedentes"),
        ("HabitosRiesgosP3", ["-fuma: str", "-alcohol: str"], "P3 hábitos"), ("FichaOftalmologica", ["-lentes: str", "-od_l_cc, oi_l_cc: str"], None),
        ("FichaPsicologia", ["-resultado_psicologico: str"], None), ("FichaEspirometria", ["-criterios_exclusion_1: str"], None),
        ("HistorialClinico", ["-empresa: str", "-puesto: str"], None),
        ("FichaAltura", ["-acrofobia: str", "-hipertension: str"], None), ("FichaElectroencefalograma", ["-epilepsia: str", "-convulsiones: str"], None),
        ("FichaAptitud", ["-tipo_examen: str", "-resultado: str"], None), ("FichaAptitudFisica", ["-resultado_fisico: str", "-resultado_psicologico: str"], None),
        ("FichaOsteomuscular", ["-concepto_aptitud: str"], None), ("FichaCardiologia", ["-hta: str", "-diagnostico_recomendaciones"], None)]
bus1, bus2 = 650, 805
cajas = []
xs1 = [15, 180, 345, 510, 680, 850, 1010]
xs2 = [15, 210, 405, 600, 800, 995]
for i, (n, at, es) in enumerate(subs):
    if i < 7:
        b = clase(L, xs1[i], 680, n, at, estereotipo=es, w=155)
        L.flecha([(b[0] + b[2] / 2, 680), (b[0] + b[2] / 2, bus1)], punta=None)
    else:
        b = clase(L, xs2[i - 7], 840, n, at, w=180)
        L.flecha([(b[0] + b[2] / 2, 840), (b[0] + b[2] / 2, bus2)], punta=None)
    cajas.append(b)
cx = fic[0] + fic[2] / 2
L.flecha([(cajas[0][0] + cajas[0][2] / 2, bus1), (cajas[6][0] + cajas[6][2] / 2, bus1)], punta=None)
L.flecha([(cajas[7][0] + cajas[7][2] / 2, bus2), (cajas[12][0] + cajas[12][2] / 2, bus2)], punta=None)
L.flecha([(7, bus2), (7, bus1), (cajas[0][0] + cajas[0][2] / 2, bus1)], punta=None)
L.flecha([(cajas[7][0] + cajas[7][2] / 2, bus2), (7, bus2)], punta=None)
L.flecha([(cx, bus1), (cx, fic[1] + fic[3])], punta="triangulo")

def rombo_comp(x, y):
    L.svg.append(f'<polygon points="{x},{y} {x + 6},{y + 10} {x},{y + 20} {x - 6},{y + 10}" fill="#000" stroke="#000"/>')

pcx = pac[0] + pac[2] / 2
rombo_comp(pcx, pac[1] + pac[3])
L.flecha([(pcx, pac[1] + pac[3] + 20), (pcx, eva[1])], punta=None)
L.texto(pcx + 8, pac[1] + pac[3] + 30, "1", ancla="start"); L.texto(pcx + 8, eva[1] - 10, "0..*", ancla="start")
ecx = eva[0] + eva[2] / 2
rombo_comp(ecx, eva[1] + eva[3])
L.flecha([(ecx, eva[1] + eva[3] + 20), (ecx, fic[1])], punta=None)
L.texto(ecx + 8, eva[1] + eva[3] + 30, "1", ancla="start"); L.texto(ecx + 8, fic[1] - 10, "0..*  {una por tipo de ficha}", ancla="start")
L.flecha([(pac[0], pac[1] + 70), (420, pac[1] + 70), (420, fic[1] + 40), (fic[0], fic[1] + 40)], punta=None)
L.texto(412, pac[1] + 62, "1", ancla="end"); L.texto(412, fic[1] + 32, "0..*", ancla="end")
L.flecha([(fic[0] + fic[2], fic[1] + 95), (usu[0], fic[1] + 95)], discontinua=True, etiqueta="responsable_id (sin FK)", pos_etq=(780, fic[1] + 85))
L.flecha([(aud[0], 80), (pac[0] + pac[2], 80)], discontinua=True, etiqueta="«registra cambios»", pos_etq=(735, 70))
L.flecha([(pap[0] + pap[2], 80), (pac[0], 60)], discontinua=True, etiqueta="«conserva copia»", pos_etq=(330, 58))
L.guardar("F09_clases")
