# RADAR-CORUÑA · Cierre funcional del MVP

**Versión:** v0.19  
**Fecha:** 27 de octubre de 2026  
**Tipo de aceptación:** técnica y funcional sobre datos ficticios  
**Resultado:** MVP cerrado como versión de referencia para la siguiente entrega documental

## Alcance verificado

| Componente | Verificación |
| --- | --- |
| Arranque sin registros precargados | Prueba de inicio con base nueva: cero participantes, visitas, episodios y contactos |
| Cribado e inclusión | Validaciones, persistencia y recuperación de ficha |
| Visitas V0, V1 y V2 | Orden cronológico, RADAR, CAT, mMRC, plan clínico y registro por etapa |
| Regla RADAR 3–2–2–1 | Casos de prueba con 0, valores completos e incompletos |
| Visita «no realizada» | No contribuye a puntuación RADAR, CAT/mMRC analítico ni porcentaje clasificable |
| Seguimiento clínico | CRD, episodios EPOC y contactos asistenciales diferenciados |
| Evolución y resultados | Pares V0–V2 de RADAR/CAT/mMRC independientes y categorías de control |
| Registro de cambios | Valor anterior, valor nuevo, motivo y revisión en modificaciones |
| Excel descargable | 41 hojas de administración; 39 por centro; variables, cohortes, indicadores y auditoría |
| Ámbito por centro | Respuestas y exportación limitadas a los registros del centro |
| Interfaz | Navegación clínica, completitud visible y presentación adaptable |

## Pruebas ejecutadas

- **69 pruebas automatizadas** de la aplicación, ejecutadas con éxito en lotes aislados. El lanzamiento monolítico de toda la suite puede quedarse bloqueado en el test de backup por una interacción entre fixtures, aunque el test individual de backup termina correctamente.
- **Dos recorridos interactivos en Chromium**: interfaz clínica desktop/móvil e informe científico con puntuación RADAR 0/8. Ambos han finalizado sin errores de página.
- **Plantilla Excel de estudio vacío**: archivo XLSX válido, 41 hojas y cero celdas de error Excel detectadas; catálogo y estructuras de análisis presentes sin introducir pacientes ficticios.
- **Prueba adicional de corrección v0.19**: una visita no realizada conserva la trazabilidad del formulario y queda fuera de los cálculos analíticos.

## Corrección de cierre

En las versiones previas era posible que una visita marcada **no realizada**, pero con respuestas anteriores aún almacenadas, generase puntuaciones en determinadas vistas derivadas. En v0.19 se unifica la exclusión de esa visita en el cálculo del servidor, la interfaz, las tablas longitudinales, la salida Excel y los informes.

## Criterio de cierre

El objetivo de Phase 19 ha sido completar y verificar la funcionalidad ya acordada, sin añadir nuevas áreas de producto ni aumentar el volumen de datos de ejemplo. La versión entregada constituye el MVP funcional de referencia. Las cuestiones metodológicas abiertas en el protocolo no se han presentado como decisiones científicas aprobadas.

## Siguiente entregable

**Fase 20: RADAR-CORUÑA — Manual técnico y operativo para la recogida de datos y el seguimiento clínico de pacientes con EPOC en Atención Primaria.**

El manual debe orientar a los investigadores sobre qué medir, cuándo recoger cada variable, cómo registrar los eventos, cómo utilizar el CRD y qué criterios son comunes entre centros.
