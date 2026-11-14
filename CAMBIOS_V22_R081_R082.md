# RADAR-CORUÑA · v0.22 · Valoración R081/R082 y conciliación de actuaciones

**Alcance:** demostración local con datos sintéticos exclusivamente. Se conserva íntegra la funcionalidad v0.21.

## Cambios
- R081 (Urgencias) y R082 (ingreso) se registran por episodio como **Sí / No / NC / Sin registrar**, con fecha opcional de primer contacto documentado, revisión, comprobación de acceso por centro y auditoría de cambios.
- Se distingue el estado del episodio de los contactos individuales registrados. La ausencia de contactos es **Sin registrar**, nunca «No».
- Crear un contacto vinculado **y con relación EPOC = Sí** actualiza automáticamente a «Sí» el tipo de asistencia correspondiente en su episodio, con cambio auditado. No transforma el contacto en una nueva agudización.
- Migración no destructiva desde v0.21: solo los contactos históricos vinculados proporcionan evidencia positiva; el resto permanece sin respuesta. Los identificadores históricos y vínculos se mantienen.
- Se impide registrar «No» o «NC» si ya existe un contacto positivo del mismo tipo. La edición respeta revisiones para evitar sobrescrituras concurrentes.
- Se actualiza la trazabilidad R081/R082 en el catálogo de 107 variables y se incluyen advertencias de calidad por respuestas ausentes o afirmativas sin fecha/contacto documentado.
- En CRD complementario se muestran las antiguas acciones Visit.action / Visit.inhaler / Visit.education / Visit.referral para revisión explícita y eventual captura de R090–R099. **No se convierten automáticamente** por falta de equivalencias semánticas aprobadas.
- R055/R056 IANUS continúa como proxy de dispensación, con periodo de referencia sin definir: no se ha inventado ninguna ventana.

## Límites
- Se requiere ratificación por IP del significado de contacto, fecha de primer contacto y tratamiento de desconocidos.
- Las 107 variables no están todas capturadas ni científicamente validadas; la aplicación es un MVP incremental.
- Prohibido introducir datos identificativos o clínicos reales; no está autorizado para atención clínica, reclutamiento o despliegue institucional.
