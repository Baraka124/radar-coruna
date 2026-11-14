# RADAR-CORUÑA · Aceptación técnica parcial v0.22 · 10/11/2026

**Objeto:** R081/R082 por episodio, fuentes positivas vinculadas, histórico de acciones, Excel y controles de migración.

## Pruebas ejecutadas
- Lote conjunto de pruebas v0.22, v0.21, v0.20, resultados, piloto, Excel, informes y fase14: **43 superadas**.
- Recorrido de navegador `tests/browser_phase22_care.py`: **superado**. Comprueba R081=No, R082=NC, creación de contacto de Urgencias relacionado con EPOC, revisión automática de R081=Sí, fecha y visualización de actuaciones históricas.
- Migración de v0.21 y contactos antiguos probada, incluidos eventos no relacionados con EPOC y contactos sin atribución confirmada.
- Excel sin participantes: **41 hojas** y estructura ZIP verificada.
- No se declara superación de toda la suite histórica: un intento de ejecución sistemática de módulos agotó el tiempo disponible por el bloqueo conocido del runner; los lotes especificados terminaron.

## Límites
- R081/R082 = respuesta por episodio y relación con EPOC. Un contacto no relacionado o sin confirmación EPOC **no** equivale a respuesta Sí.
- Un campo sin evaluar nunca se interpreta como No. R081/R082 conservan Sí / No / NC / Sin registrar, con fecha solo para Sí.
- Las acciones de versiones anteriores se muestran para revisión pero **no** se traducen automáticamente a R090–R099; la interpretación exige supervisión metodológica.
- IANUS sigue pendiente de definición de «últimas prescripciones»; no se implementan ventanas ni clasificaciones arbitrarias.
- Prototipo aislado, SQLite local, cuentas ficticias y validaciones de laboratorio. **No autorizado** para datos personales, práctica clínica o reclutamiento.
