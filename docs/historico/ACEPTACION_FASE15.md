# RADAR-CORUÑA | Fase 15 · Acta de aceptación funcional (piloto)

**Versión:** v0.15 · **Ámbito:** aplicación local, base de datos inicialmente vacía · **Fecha de revisión:** 27 de octubre de 2026

## Objetivo

Comprobar la integridad funcional del recorrido investigador sin incorporar nuevos campos, gráficos ni registros de demostración a la aplicación distribuida.

## Pruebas realizadas

| Flujo | Comprobación | Resultado |
| --- | --- | --- |
| Creación de ficha | Nuevo participante ficticio, decisión de inclusión, fechas y edición | Conforme |
| Visita basal | V0 propone fecha basal de la ficha | Conforme |
| Visitas | V0, V1 y V2 separadas, con navegación contextual | Conforme |
| Escala RADAR | Cuatro respuestas, 3–2–2–1, puntuación cero válida | Conforme |
| Continuación CRD | Desde visita recién guardada y desde cada etapa registrada | Conforme |
| Episodios y contactos | Se crean por separado, con participante contextual | Conforme |
| Revisión | Ediciones con motivo, valores previo/nuevo y registro de cambios | Conforme |
| Resumen de implantación | Numerador y denominador del uso de RADAR | Conforme |
| Excel | Registro de cohorte, 3 visitas, CRD, episodio/contacto y corrección presente | Conforme |
| Visibilidad por centro | Exportación de investigador excluye otro centro | Conforme |
| Datos iniciales | Base distribuida sin registros precargados | Conforme |

**Resultados de verificación:** 57 pruebas automatizadas superadas; prueba adicional de interfaz Chromium con backend real a través de un transporte de pruebas en memoria superada; análisis sintáctico de JavaScript superado. Esta prueba DOM no sustituye a una sesión de navegador contra un servidor real en cada equipo.

## Mejoras v0.15

- Nuevo panel **Recorrido del participante** al comienzo de la ficha: acceso directo a V0, V1, V2 y los CRD asociados.
- Al guardar una visita aparece una confirmación visible y enlace directo al CRD de esa visita.
- V0 toma inicialmente la fecha basal registrada; se evita proponer incorrectamente la fecha del día.
- Acceso contextual desde la ficha a los formularios de episodios y contactos, con código de participante preseleccionado.
- La exportación deja de mostrar un número de hojas obsoleto.
- Hoja Excel vacía de base como artefacto complementario; ninguna historia simulada añadida a la distribución.

## Alcance pendiente de validación externa

Las 20 decisiones metodológicas de la versión científica anterior permanecen como propuestas pendientes de acuerdo con el equipo investigador. La presente aceptación es **funcional**, no una aprobación de los criterios clínicos ni del CRD definitivo.
