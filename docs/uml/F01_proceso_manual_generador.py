import html
from PIL import ImageFont

AZUL = "#1F2A44"
CABECERA = "#E9EDF3"
FUENTE = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Regular.otf", 12)
TAM, LINEA, PAD_X, PAD_Y = 12, 16, 12, 9

CARRILES = [
    ("Enfermería", 0, 280),
    ("Profesionales de especialidad", 280, 560),
    ("Responsable del informe\nmédico-ocupacional", 560, 790),
]
ALTO_CABECERA, ALTO_TOTAL = 44, 820

ACCIONES = {
    "a1": (140, 125, "Recibir al trabajador\ny verificar su identificación"),
    "a2": (140, 200, "Registrar datos personales y laborales\nen el formulario físico"),
    "a3": (140, 275, "Registrar antecedentes de salud\nen la declaración jurada física"),
    "a4": (140, 343, "Derivar a las especialidades requeridas"),
    "b1": (420, 560, "Realizar la evaluación\npor especialidad"),
    "b2": (420, 640, "Registrar los resultados\nen la ficha física correspondiente"),
    "c1": (675, 655, "Revisar y consolidar\nlas fichas de evaluación"),
    "c2": (675, 730, "Elaborar el informe\nmédico-ocupacional"),
}
INICIO = (140, 72, 11)
FIN = (675, 785, 12, 7)
UNION = (420, 420, 13)
DECISION = (420, 480, 13)


def caja(clave):
    x, y, texto = ACCIONES[clave]
    lineas = texto.split("\n")
    w = max(FUENTE.getlength(l) for l in lineas) + 2 * PAD_X
    h = len(lineas) * LINEA + 2 * PAD_Y
    return x - w / 2, y - h / 2, w, h, lineas


def flechas():
    ux, uy, ur = UNION
    dx, dy, dr = DECISION
    a4 = caja("a4"); b1 = caja("b1"); b2 = caja("b2"); c1 = caja("c1")
    return [
        ("inicio-a1", [(INICIO[0], INICIO[1] + INICIO[2]), (140, caja("a1")[1])], None),
        ("a1-a2", [(140, caja("a1")[1] + caja("a1")[3]), (140, caja("a2")[1])], None),
        ("a2-a3", [(140, caja("a2")[1] + caja("a2")[3]), (140, caja("a3")[1])], None),
        ("a3-a4", [(140, caja("a3")[1] + caja("a3")[3]), (140, a4[1])], None),
        ("a4-union", [(140, a4[1] + a4[3]), (140, 382), (ux, 382), (ux, uy - ur)], None),
        ("union-decision", [(ux, uy + ur), (dx, dy - dr)], None),
        ("decision-b1", [(dx, dy + dr), (dx, b1[1])], ("[Sí]", dx + 7, dy + dr + 17, "start")),
        ("b1-b2", [(420, b1[1] + b1[3]), (420, b2[1])], None),
        ("b2-union", [(b2[0], b2[1] + b2[3] / 2), (292, b2[1] + b2[3] / 2), (292, uy), (ux - ur, uy)], None),
        ("decision-c1", [(dx + dr, dy), (675, dy), (675, c1[1])], ("[No]", dx + dr + 8, dy - 6, "start")),
        ("c1-c2", [(675, c1[1] + c1[3]), (675, caja("c2")[1])], None),
        ("c2-fin", [(675, caja("c2")[1] + caja("c2")[3]), (675, FIN[1] - FIN[2])], None),
    ]


def texto_svg(x, y, lineas, ancla="start", peso="normal"):
    t = "".join(f'<tspan x="{x:.1f}" dy="{0 if i == 0 else LINEA}">{html.escape(l)}</tspan>' for i, l in enumerate(lineas))
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{TAM}" font-weight="{peso}" text-anchor="{ancla}">{t}</text>'


def svg():
    W = CARRILES[-1][2]
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{ALTO_TOTAL}" viewBox="0 0 {W} {ALTO_TOTAL}" font-family="Inter, Arial, Helvetica, sans-serif" fill="{AZUL}">',
         '<defs><marker id="punta" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">'
         f'<path d="M0,0 L10,5 L0,10 L3,5 z" fill="{AZUL}"/></marker></defs>',
         f'<rect width="{W}" height="{ALTO_TOTAL}" fill="white"/>',
         f'<rect x="0" y="0" width="{W}" height="{ALTO_CABECERA}" fill="{CABECERA}"/>']
    for nombre, x0, x1 in CARRILES:
        lineas = nombre.split("\n")
        y = ALTO_CABECERA / 2 - (len(lineas) - 1) * LINEA / 2 + 4
        p.append(texto_svg((x0 + x1) / 2, y, lineas, "middle", "bold"))
    for x in sorted({c[1] for c in CARRILES} | {CARRILES[-1][2]}):
        xx = min(max(x, 0.5), W - 0.5)
        p.append(f'<line x1="{xx}" y1="0" x2="{xx}" y2="{ALTO_TOTAL}" stroke="{AZUL}" stroke-width="1"/>')
    for clave in ACCIONES:
        x, y, w, h, lineas = caja(clave)
        p.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="11" fill="white" stroke="{AZUL}" stroke-width="1"/>')
        p.append(texto_svg(x + PAD_X, y + PAD_Y + 12, lineas))
    for cx, cy, r in (UNION, DECISION):
        p.append(f'<polygon points="{cx},{cy - r} {cx + r},{cy} {cx},{cy + r} {cx - r},{cy}" fill="white" stroke="{AZUL}" stroke-width="1"/>')
    p.append(texto_svg(DECISION[0] - DECISION[2] - 6, DECISION[1] - 4, ["¿Faltan", "evaluaciones?"], "end"))
    p.append(f'<circle cx="{INICIO[0]}" cy="{INICIO[1]}" r="{INICIO[2]}" fill="{AZUL}"/>')
    p.append(f'<circle cx="{FIN[0]}" cy="{FIN[1]}" r="{FIN[2]}" fill="white" stroke="{AZUL}" stroke-width="1.2"/>')
    p.append(f'<circle cx="{FIN[0]}" cy="{FIN[1]}" r="{FIN[3]}" fill="{AZUL}"/>')
    for _, pts, etiqueta in flechas():
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        p.append(f'<polyline points="{d}" fill="none" stroke="{AZUL}" stroke-width="1.1" marker-end="url(#punta)"/>')
        if etiqueta:
            t, x, y, a = etiqueta
            p.append(texto_svg(x, y, [t], a))
    p.append("</svg>")
    return "\n".join(p)


def drawio():
    celdas = []
    W = CARRILES[-1][2]
    for i, (nombre, x0, x1) in enumerate(CARRILES):
        celdas.append(f'<mxCell id="carril{i}" value="{html.escape(nombre).replace(chr(10), "&lt;br&gt;")}" style="swimlane;html=1;startSize={ALTO_CABECERA};fillColor={CABECERA};strokeColor={AZUL};fontStyle=1;fontSize=12;fontFamily=Inter;fontColor={AZUL};swimlaneFillColor=#FFFFFF;" vertex="1" parent="1"><mxGeometry x="{x0}" y="0" width="{x1 - x0}" height="{ALTO_TOTAL}" as="geometry"/></mxCell>')
    for clave in ACCIONES:
        x, y, w, h, lineas = caja(clave)
        valor = html.escape("<br>".join(lineas))
        celdas.append(f'<mxCell id="{clave}" value="{valor}" style="rounded=1;arcSize=30;whiteSpace=wrap;html=1;align=left;spacingLeft=8;fillColor=#FFFFFF;strokeColor={AZUL};fontFamily=Inter;fontSize=12;fontColor={AZUL};" vertex="1" parent="1"><mxGeometry x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" as="geometry"/></mxCell>')
    for nombre, (cx, cy, r) in (("union", UNION), ("decision", DECISION)):
        celdas.append(f'<mxCell id="{nombre}" value="" style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={AZUL};" vertex="1" parent="1"><mxGeometry x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" as="geometry"/></mxCell>')
    celdas.append(f'<mxCell id="pregunta" value="¿Faltan&lt;br&gt;evaluaciones?" style="text;html=1;align=right;verticalAlign=middle;fontFamily=Inter;fontSize=12;fontColor={AZUL};" vertex="1" parent="1"><mxGeometry x="{DECISION[0] - DECISION[2] - 104}" y="{DECISION[1] - 18}" width="100" height="36" as="geometry"/></mxCell>')
    cx, cy, r = INICIO
    celdas.append(f'<mxCell id="inicio" value="" style="ellipse;fillColor={AZUL};strokeColor={AZUL};" vertex="1" parent="1"><mxGeometry x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" as="geometry"/></mxCell>')
    cx, cy, r, _ = FIN
    celdas.append(f'<mxCell id="fin" value="" style="ellipse;shape=endState;fillColor={AZUL};strokeColor={AZUL};" vertex="1" parent="1"><mxGeometry x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" as="geometry"/></mxCell>')
    for nombre, pts, etiqueta in flechas():
        origen, destino = nombre.split("-")
        medios = "".join(f'<mxPoint x="{x:.1f}" y="{y:.1f}"/>' for x, y in pts[1:-1])
        valor = html.escape(etiqueta[0]) if etiqueta else ""
        celdas.append(f'<mxCell id="f_{nombre}" value="{valor}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=open;endSize=8;strokeColor={AZUL};fontFamily=Inter;fontSize=12;fontColor={AZUL};labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="{origen}" target="{destino}"><mxGeometry relative="1" as="geometry"><mxPoint x="{pts[0][0]:.1f}" y="{pts[0][1]:.1f}" as="sourcePoint"/><mxPoint x="{pts[-1][0]:.1f}" y="{pts[-1][1]:.1f}" as="targetPoint"/><Array as="points">{medios}</Array></mxGeometry></mxCell>')
    return ('<mxfile host="app.diagrams.net"><diagram id="figura4" name="Figura 4"><mxGraphModel dx="800" dy="900" grid="0" gridSize="10" guides="1" page="1" pageScale="1" '
            f'pageWidth="{W}" pageHeight="{ALTO_TOTAL}" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
            + "".join(celdas) + "</root></mxGraphModel></diagram></mxfile>")


if __name__ == "__main__":
    open("F01_proceso_manual.svg", "w", encoding="utf-8").write(svg())
    open("F01_proceso_manual.drawio", "w", encoding="utf-8").write(drawio())
