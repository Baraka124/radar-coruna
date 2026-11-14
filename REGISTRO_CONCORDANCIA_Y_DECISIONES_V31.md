# RADAR-CORUÑA · Matriz de concordancia y decisiones · 12/11/2026

**Principio:** diferenciar **documentado en el protocolo actualizado**, **implementado y probado**, y **aprobado formalmente por los responsables**. Estas tres cosas no son automáticamente equivalentes.

| Ref. | Asunto | Fuente / situación actual | Estado para el piloto | Acción previa a aceptación |
|---|---|---|---|---|
| DC-01 | Estimación principal | Protocolo 09/11: proporción de mal control basal RADAR≥4 entre V0 con cuatro componentes válidos. El catálogo `study_spec_v09` todavía plantea D01 como pregunta | **Concordancia documental pendiente de actualizar** | IP ratifica y versiona catálogo |
| DC-02 | Estabilidad clínica | Cuatro semanas sin agudización, confirmado por coordinación; distinto de look-back RADAR de tres meses | **Resuelto clínicamente; implementado** | Verificar en U04 |
| DC-03 | Edad ≥40 | Protocolo exige ≥40; el formulario admite incluidas <40 en la versión actual | **Bloqueador científico de diseño** | IP confirma regla y se implementa/valida antes de datos reales |
| DC-04 | Espirometría | Pos-BD FEV1/FVC<0,70; en aplicación ratio no se exige y naturaleza pos-BD no se acredita | **Bloqueador científico de diseño** | Especificar evidencia y validación |
| DC-05 | Consulta AP previa | Requiere control EPOC durante 12 meses anteriores; `regular` no incluye comprobante fechado | **Falta evidencia digital** | Definir cómo verificar/documentar |
| DC-06 | Consentimiento | Firmado antes de inclusión; fecha digital opcional | **Falta regla de obligatoriedad y contraste** | IP/ética acuerdan contrato documental |
| DC-07 | Exclusiones | R017/R019/R020 y agudización activa; campos vacíos aceptados parcialmente | **Revisión** | Decidir si «sin contestar» impide inclusión |
| DC-08 | Dosis RADAR | R066 3, R067 2, R068 2, R069 1; 0–8, mal control ≥4 | **Técnicamente verificado** | Validación con clínicos y ejemplos de cuatro respuestas |
| DC-09 | R055/R056 IANUS | Verificación y prescripciones recogidas son campos separados; no equivalen al nivel subjetivo antiguo | **Ventana temporal pendiente** | Fijar período exacto, fuente y no disponible |
| DC-10 | Tratamiento | Categorías basales según CRD clínico; representaciones heredadas combinadas | **Conciliación a confirmar** | Revisar equivalencias y duplicados al exportar |
| DC-11 | Vacunas / medidas longitudinales | R049–R052 especialmente V1/V2 según catálogo histórico | **Pendiente** | Ratificar hitos de captura y reglas de actualización |
| DC-12 | Evaluador | R065 almacenado por visita; vínculo con registro R005 pendiente | **Pendiente** | Acordar codificación y ámbito del profesional |
| DC-13 | Episodio y atención | R074 consecutivo por paciente; R081/R082 no crean otro episodio | **Técnicamente verificado** | Ejecución clínica U09-U10 |
| DC-14 | R107 ausencias | Mapa NR/ND/NP/NA papel frente a categorías digitales, conservar historia | **Pendiente** | Homologar códigos; no convertir automáticamente |
| DC-15 | V1/V2 ±1 mes | Protocolo orienta fechas; aplicación permite fechas fuera; preflight ahora advierte | **Pendiente regla analítica** | SAP y protocolo de incidencias, sin borrar visitas |
| DC-16 | Tamaño de cohorte y centros | Aproximadamente 100; centros interesados no equivalen a centros activados | **Pendiente registro maestro y puesta en marcha** | IP valida sedes y tamaños de análisis |
| DC-17 | Plataforma real / privacidad | v0.31 local y sintética; cuatro credenciales demostrativas | **No preparada para datos reales** | Aprobación institucional, autenticación real, RGPD y controles |
| DC-18 | CEIm/CEIC | Inicio enero 2027 condicionado | **Autorización no documentada en paquete** | Obtener dictamen y permisos antes de reclutamiento |

**Propuesta de priorización:** DC-03, 04, 05, 06, 07 y 17 son requisitos críticos para una futura puesta en marcha; DC-01, 09, 10, 11, 12, 14 y 15 necesitan revisión científica/documental; DC-02, 08 y 13 han sido probados técnicamente, pero requieren aceptación de uso por los profesionales.

**Las «decisiones pendientes» del `study_spec_v09.json` son históricas.** No deben interpretarse de forma automática como si deshicieran una decisión clínica posterior y documentada. En particular D01 y D03 tienen resolución documental posterior; versionar su estado antes de congelar el CRD definitivo.
