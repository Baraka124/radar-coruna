# RADAR-CORUÑA v0.39 · Guía breve de inteligencia de datos

**Entorno:** demostración local con datos sintéticos. No utilizar datos personales reales.

1. Acceda con una cuenta de prueba e introduzca sus credenciales.
2. Abra **Inteligencia de datos** desde «Análisis y recursos».
3. Interprete los cuatro indicadores principales junto con su denominador: inclusión, RADAR V0 evaluable, mal control entre V0 evaluables y revisiones pendientes.
4. En **Cobertura por visita**, distinga visitas registradas/realizadas y mediciones válidas. CAT y mMRC tienen sus propios denominadores; V1/V2 ausentes no se consideran vencidas automáticamente.
5. En **Comparación por centro**, compruebe que la sesión investigadora solo presenta su centro; coordinación administrativa puede ver los tres centros sintéticos.
6. En **Revisión de calidad**, filtre por nivel, centro y participante; «Ficha» abre el registro original. Son comprobaciones para revisión humana, no correcciones automáticas.
7. En **Trayectorias longitudinales**, compruebe que la diferencia V2−V0 solo aparece con ambas mediciones válidas.
8. Descargue **CSV longitudinal**, **CSV incidencias** o el **Libro Excel**. Los informes reflejan únicamente el alcance del usuario que exporta y conservan los vacíos sin convertirlos en cero.

**Definiciones esenciales**: mal control basal = RADAR ≥4 / V0 con cuatro componentes válidos. Un episodio EPOC puede tener contactos de Urgencias e ingreso sin crear dos nuevos episodios. Una observación fuera de ventana no altera la fecha real.

**Limitación**: los enlaces de invitación existentes funcionan en un único servidor local. La colaboración real entre centros distantes requiere la fase v0.40.
