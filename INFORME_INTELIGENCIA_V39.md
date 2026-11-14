# RADAR-CORUÑA · v0.39 · Inteligencia de datos de investigación

**Fecha:** 12/11/2026  
**Base:** v0.38 · Red multicéntrica  
**Alcance:** plataforma local, exclusivamente sintética, sin despliegue remoto ni datos clínicos reales.

## 1. Objetivo y resultado

v0.39 integra lectura de cohortes y revisión de integridad sobre los datos existentes. **No modifica el CRD, los tratamientos, las reglas clínicas, la visita V0–V2 ni la gestión de permisos de v0.38.** Los resultados analíticos se generan en el servidor a partir de una instantánea filtrada al centro de la sesión.

### Funcionalidad incorporada

- **Vista «Inteligencia de datos»**: cuatro indicadores compactos; cobertura de V0/V1/V2 por instrumento; comparación descriptiva por centro; revisiones de calidad; trayectoria longitudinal de cada participante, con enlaces a su ficha.
- **Poblaciones y denominadores**: separación explícita entre cribado, inclusión, visitas registradas, visitas realizadas, y RADAR/CAT/mMRC evaluables. El porcentaje de mal control basal es RADAR ≥4 **entre V0 con los cuatro ítems válidos**. La ausencia de denominador produce «No estimable».
- **Trayectorias**: V0, V1, V2 y cambio V2−V0 de RADAR, CAT y mMRC **solo con dos mediciones válidas de cada escala**, sin imputación ni atribución causal.
- **Revisión de calidad**: alertas trazables por participante (fechas, evaluaciones completas con RADAR incompleto, motivos de ausencia contradictorios, vínculos episodio-contacto). Las ventanas de 6±1 y 12±1 meses generan observaciones, **no declaran visitas vencidas**.
- **Centro autorizado**: resultados de centro aplicados **en la API y en los archivos de exportación**, no solo a través de un filtro de pantalla.
- **CSV de análisis**: cuatro datasets con esquema fijo: `centres`, `stages`, `longitudinal`, `quality`; las celdas potencialmente interpretables como fórmulas están protegidas.
- **Libro Excel ampliado**: cinco hojas adicionales (`V39_CENTROS`, `V39_COBERTURA`, `V39_LONGITUDINAL`, `V39_REVISION`, `V39_METODOS`), conservando las 41 hojas anteriores para administración (46 en total). Las cuentas sin administración siguen sin recibir las dos hojas históricas de auditoría (44 en total).

## 2. API

| Ruta | Acceso | Comportamiento |
|---|---|---|
| `GET /api/study/intelligence` | Sesión válida | Analítica de sólo lectura, filtrada por centro autorizado |
| `GET /api/export/intelligence.csv?table=centres` | Sesión válida | Serie por centro autorizado |
| `GET /api/export/intelligence.csv?table=stages` | Sesión válida | Cobertura y denominadores por etapa |
| `GET /api/export/intelligence.csv?table=longitudinal` | Sesión válida | Una fila por participante incluido |
| `GET /api/export/intelligence.csv?table=quality` | Sesión válida | Alertas de calidad revisables |
| `GET /api/export/xlsx` | Sesión válida | Libro existente y cinco hojas v0.39 |

Todos los datasets son derivados, sin nuevos campos clínicos de captura. Para los CSV se usa `Content-Disposition: attachment`, `Cache-Control: private, no-store` y una lista permitida de esquemas.

## 3. Evidencia técnica

- **11/11 pruebas nuevas v0.39**: vacíos, tres denominadores independientes, CAT pareado sin RADAR, visitas no realizadas, calendario de ventanas, ausencia contradictoria, no duplicación de episodios/contactos, autenticación, aislamiento por centro, CSV, Excel y acceso de revisor.
- **83/83 pruebas de Python**, reunidas en una misma ejecución focalizada de 15 archivos históricos y actuales, después de actualizar únicamente las expectativas antiguas sobre número de hojas.
- **Navegador v0.39:** 320, 390, 768, 1057 y 1440 px; visualización, filtros, ausencia de errores JavaScript y sin desbordamiento horizontal de la página.
- **Navegador v0.37:** recorrido clínico y guardado desde visita al CRD, cinco anchuras, sin regresión detectada.
- **Navegador v0.38:** invitación y alta, aislamiento por centro, cinco anchuras, sin regresión detectada.
- **No certificado:** suite histórica completa de 25 archivos. Una ejecución extensiva quedó sin terminar; las pruebas anteriores completadas no permiten afirmar que esa suite completa está verde.

Los tests son realizados con bases SQLite temporales y participantes sintéticos; los archivos de datos de las pruebas no se distribuyen en el ZIP.

## 4. Límites científicos y técnicos

1. Los indicadores son **descriptivos**. No confirman eficacia, inferencia causal ni cumplimiento de todos los criterios de calidad de un estudio clínico real.
2. Las reglas de elegibilidad y consistencia siguen necesitando revisión con el protocolo/CRD acordado; las alertas de v0.39 complementan los controles ya existentes, no sustituyen la revisión del investigador.
3. No existe inferencia de pérdida de seguimiento o retraso de visitas sin calendario individual documentado y metodología aprobada.
4. Falta un denominador completo de consultas elegibles para estimar de manera válida la implantación de RADAR en AP.
5. El servicio sigue ligado a localhost/SQLite de demostración y **no permite trabajo remoto de centros reales** ni garantiza operación concurrente sostenida.

## 5. Qué falta para finalizar la hoja de ruta

**v0.40: Preparación técnica operacional**, única fase de desarrollo pendiente del itinerario acordado v0.36–v0.40:
- Despliegue central accesible por los centros, configuración de entorno real, cuentas seguras y dominios/TLS.
- Evaluación de base de datos transaccional y de concurrencia (preferentemente PostgreSQL para despliegue multicéntrico); migraciones probadas y restauración.
- Seguridad integral: sesiones, MFA/recuperación de cuentas, caducidad, controles de acceso y registros de auditoría.
- Pruebas de concurrencia, carga, tolerancia a fallos, reinicio, copias y restauración, sin pérdida de integridad de datos.
- Congelación de versión, ejecución verificable de toda la regresión, monitorización, alertas operativas y guía de explotación.

**Después de esa fase técnica** todavía serán necesarias pruebas de aceptación con investigadores y las validaciones científicas/organizativas aplicables. Esas actividades no están sustituidas por el software.
