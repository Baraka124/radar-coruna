# RADAR-CORUÑA v0.40 · Operación sintética y fiabilidad

**Última versión: v0.40.** Para staging de simulación, consulte **OPERACION_V40.md**. La ejecución local se mantiene con `python start_local.py`; el entorno remoto requiere secretos, dominio HTTPS y volumen persistente. Este paquete no habilita producción clínica.

**v0.39 · Inteligencia de datos:** ver `INFORME_INTELIGENCIA_V39.md` y `GUIA_ANALISIS_V39.md`. Incluye API y exports centro-restringidos, cinco hojas Excel nuevas y pruebas de aceptación.

# RADAR-CORUÑA · MVP v0.38 · colaboración multicéntrica

**Actualización v0.38:** sección Red de centros, invitaciones únicas con caducidad, activación de cuentas de investigadores/revisores, control de accesos y suspensión. Consulte `INFORME_MULTICENTRO_V38.md` y `GUIA_CENTROS_V38.md`. El enlace funciona sólo en este servidor local; no hay correo ni acceso remoto.

**Actualización v0.37:** flujo contextual por participante V0–V2, acceso desde la cohorte a la siguiente etapa disponible, consulta de visitas previas, reutilización explícita de evaluador/tabaquismo/tratamiento, control de campos faltantes con navegación al campo, protección de cambios no guardados, descarte deliberado y «Guardar y abrir CRD». No se ha cambiado la lógica clínica ni la base de datos.

**Base técnica:** v0.19 (27/10/2026). **Actualizaciones:** v0.20–v0.22 (CRD, episodios, contactos y actuaciones); v0.23–v0.25 (navegación y diseño de espacio clínico); v0.26 (CRD complementario conectado); v0.27 (concordancia de formulario y catálogo); v0.28 (revisión longitudinal por participante); v0.29 (regresión histórica y protección de consistencia de registros); v0.30 (controles proporcionados, interfaz clara y pruebas responsive); v0.31 (auditoría científica no destructiva, matrices de validación y batería UAT); v0.32 (campos derivados y validación fuerte de inclusión); v0.33 (auditoría 107 variables, GOLD calculado, arrastre optativo, campos condicionales y fechas no ficticias). Compatibilidad parcial con el CRD revisado.

Aplicación local de investigación para el estudio RADAR-CORUÑA. Integra cribado e inclusión, recogida longitudinal V0/V1/V2, puntuación RADAR, datos clínicos complementarios, eventos y contactos asistenciales, seguimiento de centros y profesionales, revisión de calidad, informes descriptivos y exportación Excel generada a partir de los registros guardados.

El estudio se inicia **sin participantes ni visitas precargadas**. Utilizar exclusivamente datos ficticios durante las pruebas. Las definiciones científicas propuestas se recogen en el diccionario del propio Excel y requieren acuerdo del equipo investigador.

## Inicio rápido

1. Extraer el ZIP conservando la carpeta `RADAR_CORUNA_MVP_v38`.
2. Abrir una terminal en dicha carpeta y ejecutar:

   ```bash
   python -m pip install -r requirements.txt
   python start_local.py
   ```
3. Abrir `http://127.0.0.1:8878/` en el navegador.
4. Para una prueba local ficticia: usuario `admin`, contraseña `radar-demo-admin`.

La base SQLite se crea en la carpeta de la aplicación al iniciarse, sin una cohorte inicial. Las cuentas preconfiguradas son **únicamente de demostración**.

## Recorrido de trabajo

**Cohorte → Cribado/inclusión → V0 → CRD complementario → V1 → V2 → Episodios/contactos → Análisis científico → Exportación Excel.**

El sistema conserva los componentes individuales de RADAR, calcula su puntuación solamente con las cuatro respuestas completas y separa los resultados de las visitas no realizadas. Las variables CAT y mMRC se analizan de forma pareada independientemente de la completitud de RADAR. El Excel mantiene las mediciones, denominadores, decisiones metodológicas y registro de correcciones en hojas separadas.

El archivo Excel descargable se construye **en el momento de solicitarlo** desde los registros del servidor. Incluye **41 hojas en la vista de administración** y **39 en la vista del investigador de un centro** (sin las hojas administrativas de auditoría).

## Pruebas reproducibles

```bash
python -m pytest -q tests/test_phase21_episodes_actions.py tests/test_phase20_crd_alignment.py
python tests/browser_phase21_events.py
```

Las pruebas automatizadas heredadas están en `tests/test_*.py`. La aceptación integral está documentada en `ACEPTACION_FINAL_FASE19.md`. El paquete no incluye pacientes reales ni ficheros de base de datos de las pruebas.

## Documentación del proyecto

- `ACEPTACION_FINAL_FASE19.md`: aceptación histórica de la versión de referencia.
- `ACEPTACION_PARCIAL_FASE20.md`: pruebas y límites de esta reconciliación parcial.
- `docs/historico/`: decisiones técnicas y pruebas anteriores conservadas como referencia.
- `study_spec_v09.json`: catálogo versionado de 107 variables y 20 cuestiones científicas por revisar.
- `plantilla_final_v23.xlsx`: libro vacío de referencia generado con las columnas v0.22.

**Fase 20 histórica, ya documentada:** `RADAR-CORUÑA — Manual técnico y operativo para la recogida de datos y el seguimiento clínico de pacientes con EPOC en Atención Primaria`. Ese documento será una guía para los profesionales participantes, no una memoria personal sobre el desarrollo del software.

## Actualización v0.20
Consulte `RECONCILIACION_CRD_V20.md`. Esta es una primera reconciliación de campos; no constituye validación clínica ni habilita datos reales.

## v0.22 · R074 y vínculos
Consulte `CAMBIOS_V21_EPISODIOS.md` para el alcance y las limitaciones.

**Importante para actualización:** no sobreescribir el archivo SQLite de una instancia anterior. El módulo asigna números R074 a episodios sintéticos antiguos la primera vez que se inicia, conserva los IDs internos y registra esa asignación en auditoría. Hacer antes una copia de seguridad local. No existe autorización para datos reales.


## Continuación v0.22 · R081/R082

En **Episodios y contactos**, pulsar **Revisar R081/R082** para registrar por episodio Sí, No, No consta o Sin registrar y las fechas opcionales; los contactos EPOC confirmados pueden actualizar automáticamente la evidencia afirmativa, con auditoría. Los contactos no relacionados con EPOC nunca se interpretan como asistencia por EPOC. La pantalla CRD complementario presenta las actuaciones anteriores que necesitan revisión manual: no se han creado equivalencias científicas artificiales. Consulte `CAMBIOS_V22_R081_R082.md` y `ACEPTACION_PARCIAL_FASE22.md`.


## v0.23 · Navegación y barra lateral

La barra lateral mantiene las doce secciones existentes con un diseño claro. En escritorio se puede contraer mediante el icono situado junto a la marca RADAR-CORUÑA; en móvil se abre mediante el botón de menú superior y se cierra al elegir una sección, pulsar fuera o usar Escape. Los flujos clínicos de v0.22 permanecen intactos.

## v0.24 · Espacio principal e interfaz clínica

Se conserva la barra lateral clara de v0.23 y se armonizan la vista Resumen, Participantes, Visitas V0–V2 y Análisis con paneles blancos, tablas más legibles, controles de densidad uniforme y jerarquía visual más contenida. El aviso de contexto permanece disponible en una nota informativa desplegable en vez de un panel reiterativo. En Participantes se muestran resultados de filtrado y se ofrece **Limpiar filtros**; cuando no hay registros, Resumen y Visitas presentan mensajes de inicio útiles. No hay cambios en las reglas clínicas, tablas de SQLite, autorizaciones, cálculos ni exportaciones. Consulte `CAMBIOS_V24_ESPACIO_CLINICO.md`.


## v0.26 · Espacio de trabajo del participante

Navegación compacta entre apartados de la ficha de inclusión y las visitas V0/V1/V2, con controles de acceso a la ficha del participante desde la visita y corrección del contexto al abrir visitas existentes desde el listado. La navegación de apartados no crea, guarda ni altera datos por sí misma. Mantiene las reglas, el esquema, los permisos y las exportaciones de v0.24. Consulte `CAMBIOS_V25_TRAYECTORIA_CLINICA.md`.


## v0.26 · CRD complementario conectado

- Navegación interna por grupos de variables, con conteo de respuestas por grupo.
- V0/V1/V2 y enlaces contextuales a la evaluación principal, ficha y episodios.
- Borradores no guardados conservados en memoria al cambiar de apartado, visita o participante dentro de la sesión de navegador.
- La modificación se guarda **solo** al pulsar «Guardar mediciones»; los borradores no se escriben automáticamente en la base de datos.
- Al editar una medición ya guardada, el motivo de corrección y el control de revisión existentes siguen siendo obligatorios.
- Sin cambios de tablas, cálculos clínicos ni formato de exportación.


## v0.27 · Concordancia de CRD y formularios

Se integran campos de inclusión/basal y el evaluador de cada visita; R107 admite categorías NR/ND/NP/NA y referencia directa de variable. Consulte `CONCORDANCIA_CRD_V27.md` y `CRD_CONCORDANCIA_V27.json` para el mapa de 107 identificadores. No hay cambio destructivo de esquema; la exportación Excel incluye las nuevas columnas.


## v0.28 · Revisión longitudinal integrada

Desde la ficha del participante se accede a la revisión conjunta V0/V1/V2, RADAR, CRD complementario, episodios, contactos y desenlaces. La vista es de solo lectura y muestra las incidencias documentales sin cambiar automáticamente los datos; ver `CAMBIOS_V28_RECORRIDO_INTEGRAL.md`, `ACEPTACION_V28.md` y `ACTUALIZACION_V28.md`.


## v0.29 · Fase 3: regresión y fiabilidad

Se mantiene la interfaz clínica y el CRD v0.28. En la edición del participante se evita que una corrección posterior cambie la fecha de inclusión si ya existe una V0 con otra fecha, y que el participante vuelva a «cribado» conservando visitas o eventos clínicos: ambas operaciones se rechazan con un aviso explícito sin alterar la base ni el registro de auditoría. La conciliación coordinada de fecha basal/V0 continúa pendiente de un flujo específico; no se realiza automáticamente.

Se actualizan las pruebas históricas que dependían de versiones exactas antiguas o de la visibilidad simultánea de los apartados del CRD. Las nuevas pruebas protegen las correcciones, permisos, lectura longitudinal y versión de aplicación.

Para ejecutar todas las pruebas de API, exportación, auditoría, migración y permisos:

```bash
python -m pytest -q tests/test_*.py
```

Las pruebas visuales con Playwright/Chromium (adicionales a requirements.txt) se ejecutan por separado, por ejemplo `python tests/browser_phase28_journey.py`. Consulte `FASE3_REGRESION_FIABILIDAD_V29.md` para evidencias, cobertura y límites de la aceptación. **No se habilitan datos reales ni se obtiene autorización ética por este cierre técnico.**


## v0.30 · Fase 4: interfaz clínica premium

La mejora visual preserva las rutas, el CRD, los cálculos y la lógica de persistencia. Los botones de acción son compactos, los filtros tienen medidas máximas razonables en escritorio y las fechas/números no se alargan por ocupar una columna. La interfaz se verifica en 320, 390, 768, 1024 y 1440 px; el inicio de sesión y los formularios siguen disponibles en móvil.

Para reproducir el cierre técnico:

```bash
python -m pytest -q tests/test_*.py --disable-warnings
python tests/browser_phase30_premium.py
```

Ver `FASE4_UI_PREMIUM_V30.md` para resultados, capturas y límites.


## v0.31 · Fase 5: candidato de aceptación científica (NO firmado)

La versión conserva la UI v0.30 y la lógica clínica. Incorpora una comparación read-only frente al protocolo del 09/11, una batería de 8 escenarios automatizados y guía de validación para investigadores. Los requisitos científicos potencialmente no aplicados (edad ≥40, cociente pos-BD <0,70, visita AP previa y documentación de consentimiento) permanecen identificados como *pendientes de corrección/ratificación*, no se silencian ni se dan por superados.

- Leer `FASE5_ACEPTACION_CIENTIFICA_V31.md` y `REGISTRO_CONCORDANCIA_Y_DECISIONES_V31.md`.
- Para sesión guiada: `GUIA_PRUEBA_INVESTIGADORES_V31.md` y `ACTA_ACEPTACION_V31.md` (sin firmas).
- Verificar pruebas: `python -m pytest -q tests/test_*.py --disable-warnings`.
- Auditar datos ficticios ya presentes, **sin modificar SQLite**: `python scripts/phase5_readonly_audit.py --db ruta/a/base_sintetica.sqlite3 --out informe_uat.json`.

**No autoriza datos clínicos reales**. El equipo investigador, el servicio de protección de datos y el CEIm/CEIC mantienen sus competencias respectivas.


## v0.32 · Captura inteligente

La edad en V0 y el total de agudizaciones pasan a ser **derivados de solo lectura**, sin doble introducción. La inclusión requiere validación estructurada de edad, espirometría, seguimiento habitual con consulta EPOC fechada en el año previo, estabilidad, exclusiones, consentimiento y decisión del investigador. Los cribados pueden permanecer incompletos y la fecha V0 no se inventa. Las fichas históricas siguen siendo legibles, pero un incluido con información incompleta debe reconciliarse antes de actualizarse. Consúltese `FASE6_CAPTURA_INTELIGENTE_V32.md`.


## v0.33 · Inteligencia del flujo clínico

Consulte `AUDITORIA_INTELIGENCIA_R001_R107_V33.md` y `AUDITORIA_INTELIGENCIA_R001_R107_V33.json` para el análisis explícito de los 107 códigos. Cambios de interfaz: R034 calculado en la captura, campos condicionados que no borran datos previos, fecha V1/V2 real siempre indicada por el usuario, propuesta opcional de tratamiento/tabaquismo desde la visita anterior, y confirmación voluntaria R068 desde mMRC. No se deriva adherencia desde IANUS ni se duplican entradas GOLD/RADAR.


## v0.34 · Proporción real de formularios en portátil y móvil

- Sustitución exclusiva en los formularios de participante y visita de la disposición de columnas homogéneas expandibles por medidas de campo según su función (código, fecha, escala, selección o descripción). No se obliga a un campo corto a estirarse al ancho de una columna de un tercio.
- Visita: participante 252 px; hito 190 px; fecha 180 px; evaluador 190 px; CAT 135 px; mMRC 134 px; tabaquismo 194 px (máximos de referencia en escritorio; los controles pueden ajustarse al ancho disponible).
- Teléfono: los controles de lectura larga aprovechan el espacio y CAT/mMRC pueden ocupar media fila; no se genera desplazamiento horizontal.
- Se conserva el formulario, las validaciones, la persistencia, la auditoría, la exportación y la navegación. Versión de estado y salud: 0.34.
- Pruebas: `python tests/browser_phase34_proportions.py` y `python -m pytest -q tests/test_phase33_workflow_intelligence.py tests/test_phase32_intelligent_capture.py tests/test_phase29_reliability.py tests/test_phase31_scientific_uat.py tests/test_export.py`.

Ver `INFORME_UI_PROPORCION_V34.md` y capturas `docs/v34/`.
