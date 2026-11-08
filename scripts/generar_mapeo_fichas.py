import json
import re
import sys

PAGINAS = {
    "doc_cardiologia.html": "cardiologia", "doc_psicologia.html": "psicologia", "doc_espirometria.html": "espirometria",
    "doc_electroencefalograma.html": "electroencefalograma", "doc_aptitud.html": "aptitud", "doc_aptifi.html": "aptitud_fisica",
    "doc_osteomuscular.html": "osteomuscular", "doc_oftalmologia.html": "oftalmologia", "doc_hiscli.html": "historial_clinico",
}

PATRONES = [
    (r"""(\w+)\s*:\s*document\.getElementById\(['"]([\w-]+)['"]\)\??\.checked\s*\?\s*['"]([^'"]*)['"]\s*:\s*['"]([^'"]*)['"]""",
     lambda m: {"tipo": "check", "id": m[2], "si": m[3], "no": m[4]}),
    (r"""(\w+)\s*:\s*document\.querySelector\(['"]input\[name=["'](\w+)["']\]\[value=["']([^"']+)["']\]:checked['"]\)\s*\?\s*['"]([^'"]*)['"]""",
     lambda m: {"tipo": "check_name", "name": m[2], "valor": m[3], "si": m[4]}),
    (r"""(\w+)\s*:\s*document\.querySelector\(['"]input\[name=["'](\w+)["']\]:checked['"]\)""",
     lambda m: {"tipo": "radio", "name": m[2]}),
    (r"""(\w+)\s*:\s*document\.getElementById\(['"]([\w-]+)['"]\)\??\.value""",
     lambda m: {"tipo": "id", "id": m[2]}),
    (r"""(\w+)\s*:\s*getVal\(['"]([\w-]+)['"]\)""",
     lambda m: {"tipo": "getval", "id": m[2]}),
]


def mapeo(html):
    res = {}
    for patron, f in PATRONES:
        for m in re.finditer(patron, html):
            clave = m.group(1)
            if clave in res or clave == "codigo_paciente":
                continue
            g = [None] + list(m.groups())
            res[clave] = f(g)
    return {k: v for k, v in res.items() if not (v["tipo"] in ("id", "getval") and v["id"] == k)}


salida = {}
for archivo, clave in PAGINAS.items():
    m = mapeo(open(archivo, encoding="utf-8").read())
    if m:
        salida[clave] = m
json.dump(salida, sys.stdout, ensure_ascii=False, separators=(",", ":"))
