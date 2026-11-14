# RADAR-CORUÑA · Acta técnica parcial · v0.21 · 10/11/2026

## Trabajo realizado

Actualización incremental del MVP v0.20, conservando la versión 0.19 histórica. Backend local Python/SQLite, interfaz HTML/JS, catálogo de 107 variables y libro Excel de 41 hojas.

- R074: numeración consecutiva por participante asignada automáticamente por el servidor, con migración auditada de episodios sintéticos anteriores. ID técnico independiente.
- R076: diferenciación entre agudización y otro evento. La gravedad «No aplica» solo se admite en otros eventos; los indicadores de exacerbación se calculan sin contar «otros eventos».
- Contactos: Urgencias e ingreso se vinculan a episodios del mismo participante por ID interno; la interfaz presenta el número R074. Dos contactos del mismo episodio no cuentan como dos agudizaciones. Se documentan fecha de contacto, alta opcional y centro ficticio.
- Se preservan múltiples contactos legítimos en la misma fecha. La vinculación entre centros distintos se rechaza.
- R090–R099: opciones Sí/No/No aplica/No consta habilitadas por V0/V1/V2 en CRD complementario, con trazabilidad, permisos y exportación ya existente de observaciones.
- Exportación: columnas episodeNo, kind, relatedEpisodeNo, dischargeDate y careCentre en las tablas correspondientes; sin desplazar columnas preexistentes.
- Vista Episodios/Contactos a ancho completo para evitar recorte de columnas.

## Verificación reproducida

- Grupo focal: `tests/test_phase21_episodes_actions.py`, `tests/test_pilot.py`, `tests/test_phase20_crd_alignment.py`, `tests/test_phase13_outcomes.py`: **21 pruebas superadas** en ejecución conjunta.
- Grupo de integración v0.19–v0.21: siete módulos de pruebas, **32 pruebas superadas** en ejecución conjunta.
- Comprobación adicional del catálogo y CRD: **15 pruebas superadas**.
- Recorrido de navegador (`tests/browser_phase21_events.py`): **superado** con paciente ficticio, episodio 01, contacto Urgencias vinculado, alta, R090 y R099.
- Libro Excel generado sin pacientes, **41 hojas**; archivo ZIP interno validado.
- No se certifica la ejecución de la suite completa: su ejecución integral se interrumpió por el bloqueo ya conocido del runner, tras 31/25 pruebas parciales en intentos distintos. Los grupos indicados arriba sí terminaron correctamente.

## Límites / pendientes

El sistema sigue siendo exclusivamente **demo local con datos sintéticos**, sin condiciones de seguridad, integración sanitaria ni autorización ética para datos reales.

La sección 11 del CRD contempla la posibilidad de registrar Sí/No/NC por contacto. La aplicación v0.21 representa los contactos realizados como registros positivos, pero aún no codifica de manera completa las respuestas negativas/NC por episodio. No confundir ausencia de contacto con «No». La vinculación de episodios, los 107 campos, las fuentes y algunas definiciones requieren validación clínica; el periodo IANUS no está aprobado. Las actuaciones antiguas Visit.inhaler/referral se conservan por compatibilidad y no se interpretan automáticamente como observaciones R090/R098.

**No es una validación clínica ni una aprobación para reclutamiento.**
