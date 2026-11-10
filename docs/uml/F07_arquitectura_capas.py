from lienzo import Lienzo, paquete

L = Lienzo(620, 640)
paquete(L, 60, 20, 500, 165, "Presentación «capa»")
L.caja(310, 115, "41 páginas HTML5, CSS3 y JavaScript\n(Bootstrap 5, Tailwind CSS)\n\nconfig.js: dirección de la API, sesión, token\ny comprobación de permisos por página", rx=4)
paquete(L, 60, 235, 500, 175, "Lógica y servicios «capa»")
L.caja(310, 335, "Python 3.13, FastAPI y Uvicorn\n\ncontrol de acceso por token y rol, rutas REST,\nreglas del semáforo, auditoría y respaldo", rx=4)
paquete(L, 60, 460, 500, 160, "Persistencia «capa»")
L.caja(310, 550, "SQLAlchemy 2.1 (psycopg2) y PostgreSQL\n\n21 tablas: trabajadores, evaluaciones, fichas,\nusuarios, auditoría, papelera y reglas", rx=4)
L.flecha([(310, 185), (310, 235)], discontinua=True, etiqueta="HTTPS / JSON + token", pos_etq=(320, 210, "start"))
L.flecha([(310, 410), (310, 460)], discontinua=True, etiqueta="ORM / SQL", pos_etq=(320, 435, "start"))
L.guardar("F07_arquitectura_capas")
