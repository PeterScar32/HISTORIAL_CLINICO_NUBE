import html
import math
from PIL import ImageFont

NEGRO = "#000000"
GRIS = "#F2F2F2"
FUENTE = "Liberation Serif"
_F = {False: ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf", 12),
      True: ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf", 12)}
LINEA = 14


def ancho(texto, negrita=False, tam=12):
    return max(_F[negrita].getlength(l) for l in texto.split("\n")) * tam / 12


class Lienzo:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.svg = []
        self.cel = []
        self.n = 0

    def _id(self, pref="c"):
        self.n += 1
        return f"{pref}{self.n}"

    def texto(self, x, y, t, ancla="middle", negrita=False, tam=12, cursiva=False, celda=True):
        lineas = t.split("\n")
        y0 = y - (len(lineas) - 1) * LINEA / 2 + tam * 0.35
        ts = "".join(f'<tspan x="{x:.1f}" dy="{0 if i == 0 else LINEA}">{html.escape(l)}</tspan>' for i, l in enumerate(lineas))
        self.svg.append(f'<text x="{x:.1f}" y="{y0:.1f}" font-size="{tam}" text-anchor="{ancla}" font-weight="{"bold" if negrita else "normal"}" font-style="{"italic" if cursiva else "normal"}">{ts}</text>')
        if celda:
            w = ancho(t, negrita, tam) + 8
            h = len(lineas) * LINEA + 4
            x0 = x - w / 2 if ancla == "middle" else (x - w if ancla == "end" else x)
            al = {"middle": "center", "end": "right", "start": "left"}[ancla]
            self.cel.append(f'<mxCell id="{self._id("t")}" value="{html.escape(t).replace(chr(10), "&lt;br&gt;")}" style="text;html=1;align={al};verticalAlign=middle;fontFamily={FUENTE};fontSize={tam};fontStyle={1 if negrita else (2 if cursiva else 0)};" vertex="1" parent="1"><mxGeometry x="{x0:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" as="geometry"/></mxCell>')

    def rect(self, x, y, w, h, titulo=None, rx=0, relleno="#FFFFFF", grosor=1, discontinuo=False, id_=None):
        da = ' stroke-dasharray="5,4"' if discontinuo else ""
        self.svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{relleno}" stroke="{NEGRO}" stroke-width="{grosor}"{da}/>')
        i = id_ or self._id("r")
        self.cel.append(f'<mxCell id="{i}" value="" style="rounded={1 if rx else 0};arcSize={rx * 2};whiteSpace=wrap;html=1;fillColor={relleno};strokeColor={NEGRO};strokeWidth={grosor};{"dashed=1;" if discontinuo else ""}" vertex="1" parent="1"><mxGeometry x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" as="geometry"/></mxCell>')
        if titulo:
            self.texto(x + w / 2, y + 14, titulo, negrita=True)
        return i

    def caja(self, cx, cy, t, w=None, h=None, rx=6, relleno=GRIS, negrita=False, minw=0, id_=None):
        lineas = t.split("\n")
        w = w or max(minw, ancho(t, negrita) + 22)
        h = h or len(lineas) * LINEA + 14
        x, y = cx - w / 2, cy - h / 2
        self.svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{relleno}" stroke="{NEGRO}" stroke-width="1"/>')
        i = id_ or self._id("b")
        self.cel.append(f'<mxCell id="{i}" value="{html.escape(t).replace(chr(10), "&lt;br&gt;")}" style="rounded={1 if rx else 0};arcSize={min(50, rx * 3)};whiteSpace=wrap;html=1;fillColor={relleno};strokeColor={NEGRO};fontFamily={FUENTE};fontSize=12;fontStyle={1 if negrita else 0};" vertex="1" parent="1"><mxGeometry x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" as="geometry"/></mxCell>')
        self.texto(cx, cy, t, negrita=negrita, celda=False)
        return (cx, cy, w, h)

    def elipse(self, cx, cy, t, w=None, h=None):
        lineas = t.split("\n")
        w = w or ancho(t) + 46
        h = h or len(lineas) * LINEA + 22
        self.svg.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{w / 2:.1f}" ry="{h / 2:.1f}" fill="{GRIS}" stroke="{NEGRO}" stroke-width="1"/>')
        self.cel.append(f'<mxCell id="{self._id("e")}" value="{html.escape(t).replace(chr(10), "&lt;br&gt;")}" style="ellipse;whiteSpace=wrap;html=1;fillColor={GRIS};strokeColor={NEGRO};fontFamily={FUENTE};fontSize=12;" vertex="1" parent="1"><mxGeometry x="{cx - w / 2:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" as="geometry"/></mxCell>')
        self.texto(cx, cy, t, celda=False)
        return (cx, cy, w, h)

    def actor(self, cx, cy, t):
        s = [f'<circle cx="{cx}" cy="{cy - 26}" r="8" fill="#FFFFFF" stroke="{NEGRO}"/>',
             f'<line x1="{cx}" y1="{cy - 18}" x2="{cx}" y2="{cy + 6}" stroke="{NEGRO}"/>',
             f'<line x1="{cx - 13}" y1="{cy - 10}" x2="{cx + 13}" y2="{cy - 10}" stroke="{NEGRO}"/>',
             f'<line x1="{cx}" y1="{cy + 6}" x2="{cx - 11}" y2="{cy + 24}" stroke="{NEGRO}"/>',
             f'<line x1="{cx}" y1="{cy + 6}" x2="{cx + 11}" y2="{cy + 24}" stroke="{NEGRO}"/>']
        self.svg.extend(s)
        self.cel.append(f'<mxCell id="{self._id("a")}" value="{html.escape(t).replace(chr(10), "&lt;br&gt;")}" style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;fontFamily={FUENTE};fontSize=12;" vertex="1" parent="1"><mxGeometry x="{cx - 13}" y="{cy - 34}" width="26" height="58" as="geometry"/></mxCell>')
        n = len(t.split("\n"))
        self.texto(cx, cy + 34 + (n - 1) * LINEA / 2, t, celda=False)

    def cilindro(self, cx, cy, t, w=120, h=70):
        x, y, e = cx - w / 2, cy - h / 2, 9
        self.svg.append(f'<path d="M{x},{y + e} L{x},{y + h - e} A{w / 2},{e} 0 0 0 {x + w},{y + h - e} L{x + w},{y + e}" fill="{GRIS}" stroke="{NEGRO}"/>')
        self.svg.append(f'<ellipse cx="{cx}" cy="{y + e}" rx="{w / 2}" ry="{e}" fill="{GRIS}" stroke="{NEGRO}"/>')
        self.cel.append(f'<mxCell id="{self._id("d")}" value="{html.escape(t).replace(chr(10), "&lt;br&gt;")}" style="shape=cylinder3;whiteSpace=wrap;html=1;size=9;fillColor={GRIS};strokeColor={NEGRO};fontFamily={FUENTE};fontSize=12;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        self.texto(cx, cy + 5, t, celda=False)

    def flecha(self, pts, punta="abierta", discontinua=False, etiqueta=None, pos_etq=None, inicio=None, grosor=1):
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        da = ' stroke-dasharray="6,4"' if discontinua else ""
        self.svg.append(f'<polyline points="{d}" fill="none" stroke="{NEGRO}" stroke-width="{grosor}"{da}/>')
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        ang = math.atan2(y2 - y1, x2 - x1)
        self._punta(x2, y2, ang, punta)
        if inicio:
            (a1, b1), (a2, b2) = pts[1], pts[0]
            self._punta(a2, b2, math.atan2(b2 - b1, a2 - a1), inicio)
        estilo_fin = {"abierta": "endArrow=open;endSize=10;", "triangulo": "endArrow=block;endFill=0;endSize=12;", "llena": "endArrow=block;endFill=1;endSize=8;", None: "endArrow=none;",
                      "rombo": "endArrow=diamondThin;endFill=1;endSize=12;", "pata": "endArrow=ERmany;endSize=10;", "uno": "endArrow=ERmandOne;endSize=10;", "cero_muchos": "endArrow=ERzeroToMany;endSize=10;"}[punta]
        estilo_ini = {None: "startArrow=none;", "uno": "startArrow=ERmandOne;startSize=10;", "cero_muchos": "startArrow=ERzeroToMany;startSize=10;", "abierta": "startArrow=open;startSize=10;"}[inicio]
        medios = "".join(f'<mxPoint x="{x:.1f}" y="{y:.1f}"/>' for x, y in pts[1:-1])
        val = html.escape(etiqueta) if etiqueta else ""
        self.cel.append(f'<mxCell id="{self._id("f")}" value="" style="{estilo_fin}{estilo_ini}html=1;rounded=0;strokeColor={NEGRO};{"dashed=1;" if discontinua else ""}" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="{pts[0][0]:.1f}" y="{pts[0][1]:.1f}" as="sourcePoint"/><mxPoint x="{pts[-1][0]:.1f}" y="{pts[-1][1]:.1f}" as="targetPoint"/><Array as="points">{medios}</Array></mxGeometry></mxCell>')
        if etiqueta:
            if pos_etq:
                ex, ey, anc = pos_etq if len(pos_etq) == 3 else (*pos_etq, "middle")
            else:
                ex, ey, anc = (pts[0][0] + pts[-1][0]) / 2, (pts[0][1] + pts[-1][1]) / 2 - 8, "middle"
            self.svg.append(f'<rect x="{ex - ancho(etiqueta) / 2 - 2 if anc == "middle" else (ex - 2 if anc == "start" else ex - ancho(etiqueta) - 2):.1f}" y="{ey - 8:.1f}" width="{ancho(etiqueta) + 4:.1f}" height="15" fill="#FFFFFF"/>')
            self.texto(ex, ey, etiqueta, ancla=anc)

    def _punta(self, x, y, ang, tipo):
        def p(r, da):
            return x + r * math.cos(ang + math.pi + da), y + r * math.sin(ang + math.pi + da)
        if tipo == "abierta":
            a, b = p(10, 0.45), p(10, -0.45)
            self.svg.append(f'<polyline points="{a[0]:.1f},{a[1]:.1f} {x:.1f},{y:.1f} {b[0]:.1f},{b[1]:.1f}" fill="none" stroke="{NEGRO}"/>')
        elif tipo in ("triangulo", "llena"):
            a, b = p(13, 0.42), p(13, -0.42)
            self.svg.append(f'<polygon points="{a[0]:.1f},{a[1]:.1f} {x:.1f},{y:.1f} {b[0]:.1f},{b[1]:.1f}" fill="{"#FFFFFF" if tipo == "triangulo" else NEGRO}" stroke="{NEGRO}"/>')
        elif tipo in ("uno", "pata", "cero_muchos"):
            perp = ang + math.pi / 2
            def q(r, s):
                bx, by = x + r * math.cos(ang + math.pi), y + r * math.sin(ang + math.pi)
                return bx + s * math.cos(perp), by + s * math.sin(perp)
            if tipo == "uno":
                for r in (6, 10):
                    a, b = q(r, 6), q(r, -6)
                    self.svg.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{NEGRO}"/>')
            else:
                o = q(12, 0)
                for s in (-7, 0, 7):
                    a = q(0, s)
                    self.svg.append(f'<line x1="{o[0]:.1f}" y1="{o[1]:.1f}" x2="{a[0]:.1f}" y2="{a[1]:.1f}" stroke="{NEGRO}"/>')
                if tipo == "cero_muchos":
                    c = q(18, 0)
                    self.svg.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="4" fill="#FFFFFF" stroke="{NEGRO}"/>')

    def guardar(self, nombre):
        cab = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" '
               f'font-family="{FUENTE}, Times New Roman, serif" fill="{NEGRO}"><rect width="{self.w}" height="{self.h}" fill="#FFFFFF"/>')
        svg = cab + "\n".join(self.svg) + "</svg>"
        open(nombre + ".svg", "w", encoding="utf-8").write(svg)
        xml = (f'<mxfile host="app.diagrams.net"><diagram id="{nombre}" name="{nombre}"><mxGraphModel dx="{self.w}" dy="{self.h}" grid="0" gridSize="10" guides="1" page="1" pageScale="1" '
               f'pageWidth="{self.w}" pageHeight="{self.h}" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(self.cel) + "</root></mxGraphModel></diagram></mxfile>")
        open(nombre + ".drawio", "w", encoding="utf-8").write(xml)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": self.w, "height": self.h}, device_scale_factor=3)
            pg.set_content(f'<html><body style="margin:0">{svg}</body></html>')
            pg.wait_for_timeout(200)
            pg.locator("svg").screenshot(path=nombre + ".png")
            b.close()


def carriles(L, nombres, ancho_carril, alto, cab=36):
    L.rect(0.5, 0.5, ancho_carril * len(nombres) - 1, cab, relleno="#E6E6E6")
    for i, n in enumerate(nombres):
        L.texto(i * ancho_carril + ancho_carril / 2, cab / 2 + 1, n, negrita=True)
        if i:
            L.svg.append(f'<line x1="{i * ancho_carril}" y1="0" x2="{i * ancho_carril}" y2="{alto}" stroke="#000"/>')
    L.svg.append(f'<rect x="0.5" y="0.5" width="{ancho_carril * len(nombres) - 1}" height="{alto - 1}" fill="none" stroke="#000"/>')
    for i, n in enumerate(nombres):
        L.cel.append(f'<mxCell id="carril{i}" value="{n}" style="swimlane;html=1;startSize={cab};fillColor=#E6E6E6;fontFamily={FUENTE};fontSize=12;swimlaneFillColor=none;" vertex="1" parent="1"><mxGeometry x="{i * ancho_carril}" y="0" width="{ancho_carril}" height="{alto}" as="geometry"/></mxCell>')


def rombo(L, cx, cy, r=13):
    L.svg.append(f'<polygon points="{cx},{cy - r} {cx + r},{cy} {cx},{cy + r} {cx - r},{cy}" fill="#FFFFFF" stroke="#000"/>')
    L.cel.append(f'<mxCell id="{L._id("m")}" value="" style="rhombus;html=1;fillColor=#FFFFFF;strokeColor=#000000;" vertex="1" parent="1"><mxGeometry x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" as="geometry"/></mxCell>')


def inicio(L, cx, cy, r=10):
    L.svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#000"/>')
    L.cel.append(f'<mxCell id="{L._id("i")}" value="" style="ellipse;fillColor=#000000;strokeColor=#000000;" vertex="1" parent="1"><mxGeometry x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" as="geometry"/></mxCell>')


def fin(L, cx, cy, r=11):
    L.svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFF" stroke="#000" stroke-width="1.2"/><circle cx="{cx}" cy="{cy}" r="{r - 4}" fill="#000"/>')
    L.cel.append(f'<mxCell id="{L._id("x")}" value="" style="ellipse;shape=endState;fillColor=#000000;strokeColor=#000000;" vertex="1" parent="1"><mxGeometry x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" as="geometry"/></mxCell>')


def paquete(L, x, y, w, h, nombre, ancho_pest=None):
    ap = ancho_pest or ancho(nombre, True) + 20
    L.svg.append(f'<path d="M{x},{y + 22} L{x},{y} L{x + ap},{y} L{x + ap + 8},{y + 22} Z" fill="#E6E6E6" stroke="#000"/>')
    L.svg.append(f'<rect x="{x}" y="{y + 22}" width="{w}" height="{h - 22}" fill="#FFFFFF" stroke="#000"/>')
    L.texto(x + 8, y + 11, nombre, ancla="start", negrita=True, celda=False)
    L.cel.append(f'<mxCell id="{L._id("p")}" value="{html.escape(nombre)}" style="shape=folder;fontStyle=1;spacingTop=10;tabWidth={ap:.0f};tabHeight=22;tabPosition=left;html=1;whiteSpace=wrap;verticalAlign=top;align=left;spacingLeft=6;fillColor=#FFFFFF;strokeColor=#000000;fontFamily={FUENTE};fontSize=12;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')


def componente(L, cx, cy, t, w=None, h=None):
    c = L.caja(cx, cy, t, rx=0, w=w or ancho(t) + 60, h=h, minw=150)
    x, y = cx + c[2] / 2 - 22, cy - c[3] / 2 + 6
    L.svg.append(f'<rect x="{x}" y="{y}" width="14" height="16" fill="#FFF" stroke="#000"/><rect x="{x - 4}" y="{y + 3}" width="8" height="4" fill="#FFF" stroke="#000"/><rect x="{x - 4}" y="{y + 9}" width="8" height="4" fill="#FFF" stroke="#000"/>')
    return c


def clase(L, x, y, nombre, atributos, estereotipo=None, w=None, abstracta=False):
    cab = ([f"«{estereotipo}»"] if estereotipo else []) + [nombre + (" {abstract}" if abstracta else "")]
    w = w or max([ancho(nombre, True) + 20] + [ancho(a) + 16 for a in atributos])
    hc = len(cab) * LINEA + 8
    ha = max(1, len(atributos)) * LINEA + 8
    L.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{hc + ha}" fill="#FFF" stroke="#000"/>')
    L.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{hc}" fill="#E6E6E6" stroke="#000"/>')
    for i, c in enumerate(cab):
        L.texto(x + w / 2, y + 4 + LINEA / 2 + i * LINEA + 1, c, negrita=(c == cab[-1]), cursiva=(abstracta and c == cab[-1]) or c.startswith("«"), celda=False)
    for i, a in enumerate(atributos):
        L.texto(x + 7, y + hc + 4 + LINEA / 2 + i * LINEA, a, ancla="start", celda=False)
    val = "&lt;br&gt;".join(html.escape(c) for c in cab)
    filas = "&lt;br&gt;".join(html.escape(a) for a in atributos)
    i_ = L._id("k")
    L.cel.append(f'<mxCell id="{i_}" value="{val}" style="swimlane;fontStyle={3 if abstracta else 1};align=center;startSize={hc};html=1;fillColor=#E6E6E6;strokeColor=#000000;fontFamily={FUENTE};fontSize=12;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{hc + ha}" as="geometry"/></mxCell>')
    L.cel.append(f'<mxCell id="{L._id("ka")}" value="{filas}" style="text;html=1;align=left;verticalAlign=top;spacingLeft=6;fontFamily={FUENTE};fontSize=12;" vertex="1" parent="{i_}"><mxGeometry y="{hc}" width="{w}" height="{ha}" as="geometry"/></mxCell>')
    return (x, y, w, hc + ha)
