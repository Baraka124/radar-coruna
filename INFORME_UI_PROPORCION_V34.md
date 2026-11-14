# RADAR-CORUÑA · v0.34 — Proporción y densidad de controles clínicos

**12 de noviembre de 2026 · Incremento puramente de interfaz sobre v0.33.**

## Problema verificado

En `Datos de visita y síntomas`, la clase `fields three` usaba `grid-template-columns:repeat(3,minmax(0,1fr))`. Esto expandía las cajas del participante, tipo de visita, evaluador, mMRC y tabaquismo hasta llenar un tercio de la fila, pese a que su contenido no lo requería. Limitar el ancho *interno* de algunos inputs numéricos no corregía el tamaño de la columna y dejaba una composición desequilibrada. La captura de referencia lo hacía visible en portátil.

## Corrección implementada

- Los contenedores de campos `fields three` de **participante y visita** se distribuyen ahora por ancho funcional con `flex-wrap`, medidas consistentes y gaps de 14–16 px. El espacio sobrante queda deliberadamente libre, no convertido en controles gigantes.
- Medidas de referencia en escritorio: **252 px participante, 190 px tipo de visita, 180 px fecha, 190 px evaluador, 135 px CAT, 134 px mMRC, 194 px tabaquismo**.
- Tipos de campo complementarios también ajustados (monoterapia, tratamiento, IANUS, fechas, medidas de función pulmonar, indicadores derivados). Los textos descriptivos mantienen espacio suficiente.
- Altura de controles desktop de 38 px, móvil de 42 px. En teléfonos, controles de lectura larga a ancho disponible; CAT y mMRC pueden convivir en una fila, sin desbordamiento.
- Un atributo de presentación estable `data-field-id` permite ajustar la medida sin depender del orden del DOM. Se conservan los `id`, nombre, contenido y semántica de cada control.

## Verificación ejecutada

| Prueba | Resultado |
|---|---|
| Playwright v0.34, medidas reales de campos, scroll horizontal, guardado V1 | **PASS** a 320, 390, 768, 1057, 1440 px |
| Playwright v0.33, navegación y acciones de inteligencia clínica | **PASS** a 320, 390, 768, 1024, 1440 px |
| Python (v0.33/v0.32/v0.31/v0.29/exportación) | **40/40 PASS** |
| Navegador histórico adicional v0.30 | No verificable en esta ejecución: bloqueo de cierre del driver; no se computa como éxito |

Se verificó que no había errores JS capturados ni scroll horizontal en los cinco tamaños del test nuevo. La prueba `browser_phase34_proportions.py` verifica límites máximos por campo y el guardado real de una evaluación V1 usando base de datos sintética temporal. El cambio se limita a CSS, un atributo de presentación, metadatos de versión y pruebas; **no cambia ninguna regla clínica, endpoint, exportación, esquema SQL ni lógica de persistencia**.

## Archivos

- `static/index.html` — nueva hoja de estilo v0.34 y `data-field-id` por control.
- `tests/browser_phase34_proportions.py` — aceptación de proporción y flujo guardado.
- `server.py` — metadatos de versión salud/estado (`0.34.0`/`0.34`).
- `tests/test_phase31_scientific_uat.py`, `tests/test_phase32_intelligent_capture.py`, `tests/test_phase33_workflow_intelligence.py` — afirmaciones de versión vinculadas a `server.app.version` para que el cambio visual no las deje obsoletas.
- `docs/v34` — capturas reales de escritorio y móvil, sin datos de pacientes reales.

**Limitación:** verificación local sintética, no ensayo de despliegue productivo ni carga multicéntrica.
