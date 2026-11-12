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

## Incremento 6 · Revisión y modificación 2: personal, autoría, informes, integridad y permisos (08-11-2026)

Origen: documento «Revisión y modificación 2 de sistema». No se reconstruyó ningún módulo; todos los cambios de la base de datos son aditivos (columnas nuevas y tabla `papelera`).

- **Personal médico.** La lista estaba vacía porque leía las tablas antiguas `doctores` y `enfermeras`, mientras que las identidades reales viven en `usuarios`. La pantalla Personal ahora administra `usuarios`:
  - alta de profesionales con rol, especialidad, cargo y fichas que llena;
  - edición;
  - contraseña temporal;
  - activar y desactivar.
  - Roles nuevos: ESPECIALISTA (solo sus fichas) y LECTURA (solo consulta). `registro_personal.html` redirige a Personal.
- **Autoría.** Cada ficha distingue tres datos:
  - quién la registró (`registrado_por`);
  - el profesional responsable (`responsable`, elegido en un selector y validado en el servidor);
  - quién la modificó después (auditoría).
  - Una ficha cargada por enfermería ya no se atribuye a un médico.
- **Informes.**
  - Búsqueda por CI o nombre (`/pacientes/busqueda`) y selección de la evaluación.
  - Cada ficha muestra el responsable, el registro y la última modificación.
  - El certificado muestra el responsable de la conclusión y avisa si falta.
  - El informe consolidado quedó ligado a una evaluación concreta y tiene selector de evaluación.
- **PDF.**
  - Las filas y los títulos no se cortan entre páginas.
  - Esquema de color claro forzado.
  - Prueba automática que compara el texto del PDF con la vista previa.
- **Semáforo.** El detalle añade las columnas Responsable, Registrado por y Última modificación.
- **Integridad.**
  - Eliminar un paciente exige escribir su CI.
  - El expediente completo pasa a una papelera restaurable y queda auditado.
- **Permisos.** El servidor valida el rol en cada petición (no confía en el token para el rol); el menú oculta las fichas que el perfil no puede abrir.
- **Nombres.** Las especialidades y el nombre del sistema se unificaron en menús, consultas e informes.
- **Pruebas:**
  - API: 42/42, incluidas `tests/test_verificacion.py` V01–V11.
  - Navegador: flujo 25/25, semáforo 15/15, login 15/15, fichas 51/51, informe 22/22.
- **Error encontrado por las pruebas:** al editar `lista_historial.html` se había perdido la llamada que carga la lista de pacientes; se restauró.

## Incremento 7 · Revisión técnica integral de la tesis frente al sistema (09-11-2026)

Origen: encargo de revisión técnica integral (correspondencia entre tesis, UML, requisitos, base de datos y código).

- **Fallas encontradas y corregidas:**
  - Registrar un CI existente sobrescribía el nombre del paciente.
  - P1, P2 y P3 con un paciente inexistente producían un error 500.
  - La aptitud con un paciente inexistente respondía «guardado».
  - Ocho rutas devolvían al cliente el detalle interno de la base de datos.
  - El botón «Historia clínica» de Consultas abría la consulta osteomuscular.
  - Faltaba la ruta para corregir el nombre o el CI (RF-04): se agregó `PUT /api/pacientes/{id}`, con 409 si el CI pertenece a otro paciente, y el diálogo 🪪 en Pacientes.
- **Pruebas nuevas:** `tests/test_tesis.py`, con los identificadores CP, ID, FO y SE citados en la tesis.
- **Diagramas UML:** se rehicieron a partir del código en `docs/uml` (PNG, SVG y fuentes .drawio, .puml y .py).
- **Anexos C y D:** se generaron desde los modelos y el esquema OpenAPI.
- **Resultado:** API 86/86; navegador 129/129 (`docs/evidencias/registro_pruebas_*.txt`).

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
- Datos de la enfermera.
- Comparación campo por campo con las fichas originales de OHS.
- Prueba de usabilidad (SUS) con el personal.

## Incremento 8 · Archivos adjuntos y búsqueda en consultas (10-11-2026)

**Pedido:** subir PDF o fotos en cada paciente y buscar por CI o nombre completo en las consultas por especialidad.

**Decisiones**
- **Tabla `adjuntos`:** el archivo se guarda en la base (Render gratuito no tiene disco persistente), en base64, con límite de 5 MB. El tipo se valida por la firma de los bytes (PDF, JPG o PNG), no por la extensión.
- Las fotos de más de 1,5 MB se reducen en el navegador (2000 px, JPEG) antes de subirse.
- Cada archivo queda vinculado a la evaluación vigente y su alta o eliminación se registra en `auditoria`.
- Los archivos se incluyen en la papelera (se restauran con el expediente) y en el respaldo JSON.
- Permisos: suben médico, enfermería y especialista; consulta solo ve; solo el médico elimina.
- **Búsqueda en consultas:** ruta `GET /consultas/{ficha}/buscar?q=` (por CI o por todas las palabras del nombre, en cualquier orden) y un buscador común en las 11 páginas `co_*.html`, con enlace al informe de la evaluación.

**Pruebas:** API 96/96 (`tests/test_adjuntos.py`: AD01–AD08, CS01–CS02); navegador 147/147 (nuevo `tests/e2e_adjuntos.py`, 18).

## Incremento 9 · Exportación a Excel (10-11-2026)

**Pedido:** que el médico y Enfermería puedan ver los datos en una planilla, porque el respaldo JSON no se abre con un programa común.

**Decisiones**
- Ruta `GET /exportar/excel` con openpyxl: hojas de pacientes, evaluaciones, una por cada ficha (declaración jurada P1–P3 y las diez especialidades) y la lista de archivos adjuntos (sin su contenido).
- Encabezados legibles, filtros, primera fila fija y fechas en hora de Bolivia.
- Solo médico y Enfermería; cada exportación queda en `auditoria` (acción EXPORTACION).
- El respaldo JSON se mantiene como copia de recuperación; el Excel es para consulta.

**Pruebas:** API 99/99 (`tests/test_exportar.py`); navegador 153/153 (nuevo `tests/e2e_exportar.py`, 6).

## Incremento 10 · Comentarios de OHS del 10-11-2026

**Pedidos** (documento `comentarios_software_10_11_2026.docx` y mensaje de la Dra. Condarco):
1. P3 solo admitía un trabajo anterior en la historia laboral.
2. El certificado de aptitud y las demás fichas pedían escribir otra vez los datos del trabajador.
3. Quitar «Occupational Health Services» donde aparezca.
4. Que el Excel muestre qué exámenes se hicieron.

**Decisiones**
- P3: filas dinámicas («+ Agregar otro trabajo» y ✕). Se guardan en el mismo campo `historia_laboral`, una línea por trabajo, sin cambiar la base. Al editar P3 se recuperan los trabajos y los riesgos marcados (antes se perdían).
- Ficha nueva de aptitud, aptitud física, historia clínica y osteomuscular: se completan apellidos, nombres, CI, edad, sexo, empresa, puesto, fecha y tipo de evaluación desde el registro y la P1. Solo se llenan campos vacíos y nunca se tocan fichas ya guardadas.
- El informe y el certificado dicen solo «Historial Clínico Nube».
- Excel: hoja «Exámenes por evaluación» con semáforo, cumplimiento, exámenes pendientes y una columna por examen (REALIZADO con su conclusión o PENDIENTE).

**Pruebas:** API 100/100; navegador 171/171 (nuevo `tests/e2e_comentarios.py`, 18).

## Incremento 11 · Verificación pedida por la revisión de tesis (11-11-2026)

**Pedido:** revisar el autocompletado (prioridad alta), los resultados por especialidad y dejar evidencias para la tesis.

**Problemas detectados**
- Si en una ficha se cambiaba el CI por el de otro trabajador, los datos ya autocompletados del primero podían quedar en el formulario.
- El informe mostraba el semáforo, pero no un resumen de qué exámenes se hicieron y su resultado, ni la lista de evaluaciones del trabajador.

**Decisiones**
- Al cambiar de trabajador dentro de una ficha, la página se recarga con el nuevo trabajador, de modo que no se mezclan datos.
- Osteomuscular: la fecha de firma también se completa con la fecha de la evaluación.
- Informe: secciones «Exámenes realizados y resultados principales» (estado, conclusión registrada por el profesional, responsable y fecha) y «Evaluaciones del trabajador». No se calculan ni modifican conclusiones.

**Pruebas:** API 100/100; navegador 176/176 (`tests/e2e_comentarios.py`, 23).
