from lienzo import Lienzo, paquete, componente

L = Lienzo(900, 900)
paquete(L, 20, 15, 860, 215, "Capa de presentación (GitHub Pages)", 260)
r = componente(L, 135, 85, "Registro\n(registro_paciente,\ndeclaracion_jurada_p1–p3)")
f = componente(L, 335, 85, "Fichas\n(doc_*.html, d_menu)")
c = componente(L, 535, 85, "Consultas e informes\n(co_*, informe, informes,\nsemaforo, lista_historial)")
a = componente(L, 750, 85, "Administración\n(index, lista_personal)")
cfg = componente(L, 445, 185, "config.js (sesión, token,\ncabeceras y permisos)", w=260)
for comp in (r, f, c, a):
    L.flecha([(comp[0], comp[1] + comp[3] / 2), (comp[0], 145)], punta=None, discontinua=True)
L.flecha([(r[0], 145), (a[0], 145)], punta=None, discontinua=True)
L.flecha([(445, 145), (445, 163)], discontinua=True)
L.texto(452, 153, "«use»", ancla="start", cursiva=True)
L.svg.append('<circle cx="445" cy="268" r="9" fill="#FFF" stroke="#000"/>')
L.flecha([(445, 207), (445, 259)], punta=None)
L.texto(460, 268, "API REST (HTTPS/JSON, Bearer)", ancla="start")
paquete(L, 20, 300, 860, 470, "Capa de servicios (Render, FastAPI)", 250)
m = componente(L, 445, 365, "main.py\n(middleware y rutas de trabajadores,\nevaluaciones, fichas e informes)", w=300)
L.flecha([(445, 277), (445, m[1] - m[3] / 2)], punta=None)
au = componente(L, 120, 470, "auth.py\n(inicio de sesión,\ntokens y roles)")
se = componente(L, 330, 470, "semaforo.py\n(semáforo, reglas\ny catálogo)")
ad = componente(L, 560, 470, "auditoria.py\n(cambios, expediente,\nrespaldo y papelera)")
de = componente(L, 770, 470, "demo.py\n(datos ficticios)")
cr = componente(L, 300, 585, "crud.py\n(operaciones y autoría)")
mi = componente(L, 600, 585, "migraciones.py\n(cambios aditivos)")
mo = componente(L, 300, 700, "models.py\n(modelos SQLAlchemy)")
db = componente(L, 600, 700, "database.py\n(conexión desde\nvariable de entorno)")
y0 = m[1] + m[3] / 2
for comp in (au, se, ad, de):
    L.flecha([(comp[0], y0 + 8) if False else (445, y0), (445, 415), (comp[0], 415), (comp[0], comp[1] - comp[3] / 2)], discontinua=True)
L.flecha([(300, y0), (300, 400)], punta=None) if False else None
for comp in (au, se, ad):
    L.flecha([(comp[0], comp[1] + comp[3] / 2), (comp[0], 535), (300, 535), (300, cr[1] - cr[3] / 2)], discontinua=True)
L.flecha([(300, cr[1] + cr[3] / 2), (300, mo[1] - mo[3] / 2)], discontinua=True)
L.flecha([(600, mi[1] + mi[3] / 2), (600, db[1] - db[3] / 2)], discontinua=True)
L.flecha([(300 + mo[2] / 2, 700), (600 - db[2] / 2, 700)], discontinua=True)
L.flecha([(ad[0] + 40, ad[1] + ad[3] / 2), (ad[0] + 40, 545), (300 + 70, 545), (300 + 70, mo[1] - mo[3] / 2)], discontinua=True) if False else None
L.cilindro(600, 830, "PostgreSQL (Render)\n21 tablas", w=170, h=62)
L.flecha([(600, db[1] + db[3] / 2), (600, 799)], etiqueta="SQL", pos_etq=(612, 783, "start"))
L.texto(870, 760, "«use»: dependencia entre componentes", ancla="end", cursiva=True, tam=11)
L.guardar("F08_componentes")
