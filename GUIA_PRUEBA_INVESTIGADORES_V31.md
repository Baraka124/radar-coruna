# RADAR-CORUÑA · Guía de evaluación por investigadores · UAT v0.31

**Destinatarios:** investigadores de Atención Primaria, IP, coordinación científica de Neumología y apoyo técnico.  
**Objeto:** observar el flujo y validar la semántica clínica y la experiencia de uso, **sin datos reales ni autorización implícita para despliegue**.

## Antes de la sesión

- Preparar un equipo con Python y una **base SQLite nueva** dedicada exclusivamente a UAT. Ejecutar `python start_local.py` para una base vacía o `RADAR_SEED_DEMO=1` para demostración inicial (siempre en una base nueva).
- Acceder a `http://127.0.0.1:8878/`; usar cuentas ficticias `admin`, `costa`, `interior`, `revisor` y contraseñas publicadas en `LEEME.md`.
- Identificar quién realiza cada escenario, dispositivo y fecha. Registrar dudas y capturas sin datos identificativos.
- Para el ejercicio manual, crear códigos `SIM-UAT-01` y `SIM-UAT-02` (Costa e Interior), sin nombres ni historia clínica real.

## Secuencia de observación

| ID | Perfil / recorrido | Qué debe comprobar el investigador | Aceptación | Resultado |
|---|---|---|---|---|
| U01 | Administrador / centros | Ver 3 centros sintéticos, entrar en participantes, no confundir rol global con investigador | Centros y permisos distinguibles | ☐ P ☐ I ☐ NA |
| U02 | Investigador Costa / cohorte | Ver sólo pacientes de Costa; intentar abrir el de Interior por enlace directo | 403, sin contenido ajeno | ☐ P ☐ I ☐ NA |
| U03 | Revisor / lectura | Consultar vista longitudinal y exportación; intentar editar | Lectura permitida; escritura 403 | ☐ P ☐ I ☐ NA |
| U04 | Cribado / consentimiento | Registrar 4 semanas de estabilidad, exclusiones y consentimiento anterior a V0 | Identificar datos imprescindibles; no inferir vacíos como Sí/No | ☐ P ☐ I ☐ NA |
| U05 | Inclusión / edad y espirometría | Simular 38 años y FEV1/FVC 0,75; revisar preflight | Incidencias científicas visibles en informe; no considerar elegible | ☐ P ☐ I ☐ NA |
| U06 | V0 / RADAR | Cuatro respuestas «No»; CAT=0 y mMRC=0 | RADAR **0 válido**; cero no equivale a ausente | ☐ P ☐ I ☐ NA |
| U07 | V1 / V2 / tiempos | Realizar visita a seis y doce meses; probar V1 fuera de ventana | Conservar fechas reales, señalar desvío sin modificar visita | ☐ P ☐ I ☐ NA |
| U08 | CRD y R107 | Registrar IANUS verificado y prescripciones recogidas; indicar falta de R056 | Significados diferenciados; motivo ausente asociado a campo/visita | ☐ P ☐ I ☐ NA |
| U09 | Episodios / contactos | Introducir un episodio EPOC con Urgencias y posterior ingreso | Un episodio R074, dos contactos; sin triple recuento | ☐ P ☐ I ☐ NA |
| U10 | Otros eventos | Introducir evento no EPOC y contacto sin vínculo EPOC | No computa como agudización EPOC | ☐ P ☐ I ☐ NA |
| U11 | Corrección documentada | Corregir CAT tras guardar; inspeccionar trazabilidad y conflictos de revisión | Motivo obligatorio, valor anterior/nuevo y versión | ☐ P ☐ I ☐ NA |
| U12 | Evolución + exportación | Revisar V0–V2, diferencias calculadas sólo con evaluaciones válidas, y libro Excel | Denominadores y fichas consistentes con datos originales | ☐ P ☐ I ☐ NA |
| U13 | Móvil 390 px / espacio clínico | Abrir/cerrar menú, cambiar visita y guardar; inspeccionar campos y botones | Sin scroll horizontal ni botones sobredimensionados | ☐ P ☐ I ☐ NA |
| U14 | Cierre de sesión y retorno | Salir y reentrar; comprobar que datos guardados persisten y que los borradores no guardados no son datos persistidos | Estado persistente correcto; sin mezclas de sesiones | ☐ P ☐ I ☐ NA |

**P** = supera, **I** = incidencia, **NA** = no aplicable / no ejecutado (explicar). Registrar tiempo y fricciones reales, no sólo funcionamiento del botón.

## Preguntas para el evaluador (sin respuesta prefabricada)

1. ¿Puede identificar rápidamente qué paciente, centro y visita está editando? ¿El siguiente paso está claro sin entrenamiento técnico?
2. ¿Hay preguntas clínicas cuyo significado no coincide con el CRD de papel, incluidas R055/R056 o los estados de ausencia?
3. ¿Los términos «agudización», «Urgencias», «ingreso» y «otro evento» llevan a interpretaciones inequívocas?
4. ¿La vista longitudinal permite explicar la evolución del participante sin volver a todas las pantallas?
5. ¿La exportación contiene lo que necesitan el IP y el análisis, sin duplicar unidades de episodio o mezclar centros?

## Registro de incidencias

Para cada incidencia recoger: **Uxx · perfil · versión · fecha · dispositivo/ancho · pasos · resultado observado · resultado esperado · gravedad · responsable · resolución · retest**.

**Gravedad:** crítico (riesgo científico, integridad o datos entre centros), mayor (bloquea tarea), menor (fricción/cosmética), propuesta (mejora). Un fallo crítico suspende aceptación hasta resolución y repetición de la prueba.

## Cierre

Completar `ACTA_ACEPTACION_V31.md`. Una sesión UAT exitosa sólo valida lo realmente probado. No reemplaza la aprobación metodológica del IP, revisión institucional de seguridad, activación de sedes ni dictamen ético.
