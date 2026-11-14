# RADAR-CORUÑA · v0.20 · Primera reconciliación del MVP con el CRD de 4 páginas

**Origen:** ZIP final v0.19, 27/10/2026. **Ámbito:** desarrollo local con datos sintéticos; no habilitado para datos reales.

## Implementado en esta actualización
- Nuevo campo de fecha completa de nacimiento (solo fechas ficticias); edad derivada al guardar cuando hay fecha de inclusión. La edad heredada sigue admitida para compatibilidad.
- Recuento basal separado de agudizaciones moderadas y graves, sin eliminar el campo total previo; total derivado solo cuando ambos recuentos están disponibles.
- Inclusión con estabilidad de al menos cuatro semanas cuando se informa el intervalo; sin inventar fechas de agudización.
- En visitas V0/V1/V2: cinco pautas inhaladas **exactamente** según las opciones 1–5 indicadas por Pedro; roflumilast y azitromicina adicionales (6–7). La monoterapia exige aclarar LAMA frente a LABA; se derivan banderas históricas R045–R047.
- Rescate **prescrito** por separado del uso de rescate **real** que puntúa RADAR.
- Comprobación IANUS (R055), prescripciones recogidas (R056) y fecha; No verificable no puede tratarse como No. Se deja explícitamente abierta la ventana de «últimas prescripciones».
- Las nuevas columnas se **añaden al final** de las tablas Participantes/Visitas en Excel sin desplazar columnas usadas por indicadores históricos.

## Pendiente de la siguiente iteración
- Concordancia completa de las secciones 1–13 y de las 107 variables del catálogo digital.
- Migración científica y validación de R053, R045–R047, R055–R056; aprobar V1 IANUS; evitar declarar una clasificación final antes de aprobación.
- Número de episodio 01,02,... por participante (R074) y correcta vinculación en contactos, incluido manejo de múltiples contactos por episodio.
- Actualización de detalles restantes de comorbilidades, actuaciones clínicas, protocolo de datos ausentes y fuentes.
- Validación con investigadores, revisión ética y seguridad institucional antes de cualquier dato real o despliegue clínico.

## Seguridad
El MVP conserva contraseñas de demostración y SQLite local; no es un sistema clínico en producción. No introducir nombres, NHC, CIP ni fechas de nacimiento reales.
