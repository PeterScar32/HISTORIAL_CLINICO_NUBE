# Bitácora técnica de desarrollo — HC Nube OHS

Registro de los problemas encontrados, los riesgos, las decisiones, las modificaciones y las pruebas de cada incremento. Sirve de evidencia para documentar los ciclos del modelo espiral en el Capítulo III.

Todas las pruebas se ejecutaron con **pacientes ficticios** en una base PostgreSQL de prueba. Ningún dato de pacientes reales se utilizó durante el desarrollo.

Repositorio: `PeterScar32/HISTORIAL_CLINICO_NUBE`. Cada incremento se desarrolló en la rama `desarrollo` y se integró a `main` mediante una solicitud de cambios (*pull request*, PR) después de pasar sus pruebas.

---

## Incremento 1 · Estabilización (07-11-2026, PR #1)

**Problemas detectados**
- **Servidores distintos:** el frontend apuntaba a tres servidores; 27 páginas usaban un servicio de otra cuenta.
- **Servicio caído:** el servicio propio en Render fallaba al iniciar. La base gratuita se había eliminado y SQLAlchemy 2.1 exigía el controlador `psycopg`, que no estaba instalado.
- **Errores de la API:**
  - P1, P2 y P3 insertaban filas duplicadas en cada guardado;
  - P3 reenviaba un P2 vacío;
  - no existía la ruta para borrar pacientes;
  - tres consultas fallaban siempre (error 500);
  - el historial clínico descartaba campos sin aviso.
- **Integridad de datos:** había fichas sin clave foránea hacia el paciente.

**Riesgos considerados**
- Elegir un servidor equivocado haría que los datos quedaran invisibles.
- Las migraciones sin respaldo podían perder datos. La base solo contenía datos de prueba.

**Decisiones**
- Usar una sola URL de API en `config.js`.
- Crear una base nueva en la cuenta propia.
- Fijar las versiones de las dependencias.
- Usar el CI como código visible del paciente, con un identificador interno aparte.

**Pruebas:** 12 pruebas de la API (pytest) y un flujo completo en el navegador (Playwright): 12/12.

## Incremento 2 · Evaluaciones por visita (07-11-2026, PR #2)

**Problema:** al actualizar P1, P2 y P3, una segunda visita sobrescribía la primera.

**Decisión:** crear la tabla `evaluaciones`, con la que cada visita es un episodio. La declaración y las fichas se vinculan a una evaluación y P1 se hereda de la visita anterior.

**Riesgo:** cambio de estructura sobre una base existente. Se mitigó con una migración aditiva (`api/migraciones.py`), probada sobre una copia con el esquema anterior.

**Pruebas:** 16 de la API y 20 en el navegador. Incluyen registrar dos veces el mismo CI y verificar que la evaluación anterior queda intacta.

## Incremento 3 · Semáforo (07-11-2026, PR #2 y #4)

**Decisiones**
- El color refleja la conclusión que registra el profesional; el sistema no diagnostica.
- Las reglas se configuran en la tabla `reglas_semaforo`.
- A partir de las observaciones de la revisión metodológica, hay dos indicadores independientes:
  - **alertas**, según las conclusiones registradas;
  - **cumplimiento**, sobre las fichas requeridas por evaluación.

  También se registran el profesional y la fecha de cada ficha, y se muestran el detalle por ficha y el estado por especialidad.

**Pruebas:** 20 de la API y 15 en el navegador.

## Incremento 4 · Acceso por perfiles (07-11-2026, PR #5)

**Problemas detectados**
- La clave del portal estaba fija en el código público.
- La API no exigía autenticación.
- CORS aceptaba cualquier origen (`*`).

**Decisiones**
- Cuatro perfiles médicos con acceso completo y un perfil de Enfermería que solo registra datos.
- Contraseñas protegidas con PBKDF2. Las claves temporales se cargan desde variables de entorno y se exige cambiarlas en el primer ingreso.
- Token firmado de 12 horas.
- La API verifica los permisos en el servidor, no solo en la interfaz.
- CORS restringido al dominio de GitHub Pages.

**Pruebas:** 24 de la API y 15 del flujo de inicio de sesión. Incluyen la denegación de rutas a Enfermería y el cierre de sesión.

## Incremento 5 · Historial de modificaciones, edición de fichas, informe PDF y respaldo (08-11-2026)

**Problemas detectados**
- Cada guardado de una ficha creaba una fila nueva, así que no había edición real ni se sabía qué había cambiado.
- Las fichas no recuperaban sus datos al abrirse.
- Seis formularios usan en la página nombres distintos a los de la base. Por ejemplo, `ape_pat` en la página corresponde a `apellido_paterno` en la base, y en el electroencefalograma la casilla marcada se guarda como `NORMAL`.
- El formulario osteomuscular tenía un error de JavaScript al cargar (buscaba un elemento inexistente).
- Las horas se guardaban sin zona horaria.

**Riesgos considerados**
- Precargar mal un formulario podía sobrescribir datos con valores vacíos al guardar. Se mitigó con una prueba de ida y vuelta por ficha (abrir, guardar sin cambios y comparar).
- La regla del equipo exige una copia recuperable antes de cambiar la estructura de la base.

**Decisiones**
- **Respaldo lógico:** exportación JSON de todas las tablas, descargable desde el portal (solo médicos). Se acompaña de `scripts/restaurar_respaldo.py`, que restaura solo sobre una base vacía.
- **Una ficha por evaluación:** guardar de nuevo actualiza la ficha existente. Una nueva visita crea una ficha nueva, de modo que las evaluaciones anteriores se conservan.
- **Tabla `auditoria`:** registra creación, modificación (campo, valor anterior y nuevo, usuario, fecha y hora) y eliminación. Se captura automáticamente con eventos de SQLAlchemy, sin modificar cada formulario.
- **Precarga de fichas:** la equivalencia entre los nombres de la base y los de cada formulario se generó leyendo el código de cada página (`scripts/generar_mapeo_fichas.py`), en lugar de reescribir los formularios originales.
- **Horas en UTC:** se almacenan en UTC y se muestran en la hora local del navegador.
- **Informe PDF:** se genera en el navegador con «Imprimir / Guardar como PDF» y permite elegir por casillas las secciones y fichas. El certificado de aptitud es reducido y no muestra información clínica; su formato es provisional hasta recibir el modelo institucional de OHS.

**Pruebas**
- **API:** 30 pruebas, entre ellas:
  - la auditoría de las 10 fichas;
  - la edición dentro de la misma evaluación;
  - que una segunda visita no se vea afectada;
  - los permisos de las rutas nuevas;
  - que el borrado quede auditado.
- **Respaldo:** se descargó, se restauró en una base vacía y se comprobó el ingreso con las contraseñas cambiadas, los datos, la auditoría y el alta de pacientes nuevos.
- **Edición de fichas (navegador):** `tests/e2e_fichas.py`, 51/51. Cubre las 10 fichas: se llenan, se guardan, se reabren con aviso de ficha existente, se guardan sin cambios y se verifica que no se pierde ningún campo.
- **Informe (navegador):** `tests/e2e_informe.py`, 14/14. Comprueba:
  - las casillas;
  - la opción de omitir campos vacíos;
  - el historial de cambios;
  - que el certificado no contenga datos clínicos;
  - la descarga del respaldo.

## Cómo reproducir las pruebas

```bash
pip install -r requirements.txt pytest httpx playwright
DATABASE_URL=postgresql://usuario@host/base_de_prueba python -m pytest tests
python tests/e2e_flujo.py
python tests/e2e_semaforo.py
python tests/e2e_login.py
python tests/e2e_fichas.py
python tests/e2e_informe.py
```

Los flujos del navegador requieren la API local en el puerto 8000 y las páginas servidas en el puerto 8080.

## Pendiente

- Declaración jurada dinámica con firma táctil.
- Documentos adjuntos.
- Búsqueda por nombre.
- Datos de la enfermera.
- Pantalla para restablecer contraseñas.
- Comparación campo por campo con las fichas originales de OHS.
- Prueba de usabilidad (SUS) con el personal.
