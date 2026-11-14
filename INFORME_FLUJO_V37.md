# RADAR-CORUÑA · v0.37 — Flujo clínico inteligente

**Base:** v0.36 (conservada). **Fecha:** 12/11/2026. **Uso:** piloto local únicamente con datos sintéticos. **Objetivo:** cinco mejoras integradas sin modificar definiciones clínicas R001–R107 ni modelos de almacenamiento.

## 1. Espacio unificado por participante

- En fichas relacionadas se muestra el mismo contexto de participante codificado y centro, sin duplicar datos identificativos.
- Barra compacta V0/V1/V2 con estados reales: Sin registrar, Parcial, Completa, No realizada. Una visita futura sin registrar no se marca automáticamente como vencida.
- Acceso directo desde la cohorte a cribado o a la siguiente etapa disponible, conservando el acceso a la ficha longitudinal.
- El estado de cada visita se obtiene de los registros del servidor, sin crear información ni modificar el historial.

## 2. Reutilización explícita, nunca automática

- Se muestran RADAR, CAT, mMRC y tratamiento de la visita de referencia, con fecha de procedencia.
- Se conserva el arrastre optativo previo de tabaquismo y tratamiento, y se añade reutilización optativa del código R065 del evaluador anterior.
- Ninguno de esos valores se traslada sin pulsar el control correspondiente; los valores actuales no se sobrescriben si ya están introducidos.
- No se copian dosis, fechas, prescripciones IANUS, respuestas RADAR ni actuaciones clínicas; el profesional debe validarlas en la visita actual.
- No se ha añadido una nueva columna de procedencia a la base de datos. La referencia se muestra en la interfaz; una trazabilidad persistente de valores reutilizados sigue siendo un desarrollo separado.

## 3. Visita contextual

- El recorrido muestra solo etapas accesibles con la secuencia existente: V0, luego V1, luego V2.
- Se mantiene el comportamiento condicional de campos aprobado en versiones anteriores (monoterapia, IANUS, motivo de visita no realizada, etc.).
- La vista anterior sirve de **referencia**, no de decisión clínica automática.

## 4. Completitud que conduce a la acción

- Evaluación realizada: fecha real + CAT + mMRC + cuatro respuestas RADAR + plan; cada falta aparece como enlace que abre la sección correspondiente y enfoca el campo.
- Visita no realizada: fecha real y motivo; no se exigen falsamente RADAR, CAT o mMRC.
- El indicador es una orientación de captura. Un 100 % no sustituye reglas de consistencia y validación del servidor ni evaluación científica.

## 5. Continuidad, guardado y seguridad frente a pérdida de trabajo

- Acción «Guardar y abrir CRD»: guarda mediante la API existente, recibe confirmación del servidor y solo después navega al CRD correspondiente.
- Acceso directo a episodios y a la ficha del participante desde el contexto de visita.
- Se bloquea la navegación accidental desde visita o ficha con cambios sin guardar. «Descartar y volver» permite salir explícitamente.
- La navegación móvil y el estilo compacto blanco/azul se mantienen. No se han introducido botones de ancho completo innecesarios.

## Verificación terminada

- **42/42** pruebas Python en seis módulos focalizados (inteligencia del flujo, fiabilidad, recorrido longitudinal, captura inteligente, concordancia CRD y UAT científico).
- **v0.37 Playwright, cinco anchos (320, 390, 768, 1057, 1440):** contexto V0/V1/V2, referencia previa, reutilización explícita, faltantes con foco, bloqueo de pérdida de cambios, guardado y apertura CRD, API confirmada.
- **v0.33 Playwright histórico:** pasa en 320, 390, 768, 1024 y 1440 tras actualizar una secuencia de prueba para descartar explícitamente un borrador, conforme al nuevo contrato.
- **v0.36 Playwright histórico:** 12 pantallas × 5 anchos sin errores JS ni scroll horizontal de página, con guardado V1, editores y menú móvil.
- Nueve archivos adicionales de pruebas Python históricas terminaron con resultados positivos antes de un atasco posterior. La suite Python histórica integral **no** terminó y **no** se declara certificada.

## Límites

- No se ha probado el comportamiento de varios usuarios concurrentes en infraestructura desplegada, recuperaciones reales tras interrupción de red ni cargas sostenidas; forman parte de la siguiente fase operativa.
- No se ha realizado validación clínica por el equipo investigador; los algoritmos y criterios existentes se conservan.
- Los usuarios, contraseñas y códigos incluidos son exclusivamente ficticios y de demostración. No utilizar este paquete con datos clínicos reales.
- No se ha desplegado a producción ni se incluyen bases de datos de pacientes en el ZIP.

## Inicio

Extrae `RADAR_CORUNA_MVP_v37`, instala `requirements.txt`, ejecuta `python start_local.py` y abre `http://127.0.0.1:8878/`. Para pruebas locales sintéticas: `admin` / `radar-demo-admin`.
