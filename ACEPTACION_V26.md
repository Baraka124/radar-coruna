# RADAR-CORUÑA · Verificación v0.26

## Alcance

Interfaz del CRD complementario, navegación por grupos, continuidad entre V0/V1/V2 y accesos contextuales a la evaluación principal. Sin alteración de reglas clínicas ni tablas de SQLite.

## Evidencia de prueba

- **40 pruebas automatizadas seleccionadas superadas** (CRD, modelo científico, episodios, contactos, informes y exportación). Comando: `python -m pytest -q tests/test_crd_workflow_v11.py tests/test_phase13_outcomes.py tests/test_phase14_completion.py tests/test_export.py tests/test_study_v09.py tests/test_phase20_crd_alignment.py tests/test_phase21_episodes_actions.py tests/test_phase22_episode_care.py tests/test_phase19_release.py -x`.
- **Recorrido de navegador v0.26 superado** con Playwright: sesión, visita V0/V1, respuestas no guardadas aisladas por visita, vuelta a V0 sin pérdida, guardado mediante API, revisión de un valor existente con motivo de corrección, accesos al formulario principal y comprobación móvil de 390 px sin desbordamiento horizontal.
- Validación de sintaxis del JavaScript con `node --check`.

## Decisiones de interfaz

- El guardado es **explícito**. Un borrador local no se interpreta como persistido en base de datos.
- Los borradores se descartan al cerrar sesión o abandonar por completo la página; un aviso nativo advierte al recargar con ediciones pendientes.
- Los campos de `study_spec_v09.json` y su ámbito por visita se conservan. El alcance de esta versión es de navegación/presentación, no una ratificación metodológica del catálogo.

## Aún fuera de alcance

Concordancia exhaustiva de todos los campos del CRD de 4 páginas con el catálogo de 107 variables y cierre de decisiones metodológicas pendientes de IANUS.
