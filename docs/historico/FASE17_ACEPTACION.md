# RADAR-CORUÑA — Fase 17

## Alcance

Refinamiento de experiencia de uso para investigadores sin cambios en el modelo científico o la exportación de datos.

## Resultados esperados y comprobaciones

1. Tres secciones principales de navegación, con todos los módulos existentes accesibles.
2. Ruta contextual con acceso al Excel y retorno a la ficha del participante.
3. Formularios con bloques clínicos claramente delimitados y campos complementarios disponibles sin dominar la vista inicial.
4. Indicador de completitud del núcleo: CAT, mMRC, cuatro ítems RADAR y plan clínico. Un valor 0 cuenta como observado.
5. Guardado de V0 sin alterar puntuaciones; el flujo lleva a la ficha y la siguiente visita.
6. Adaptación a pantallas estrechas, manteniendo los controles y la navegación.
7. Excel generado por el mismo endpoint de la versión 0.16 y sin modificaciones en sus 36 hojas.

## Verificación

- Sintaxis de JavaScript comprobada con Node.
- Prueba interactiva `tests/browser_phase17_usability.py`: pasó; cubre inicio vacío, navegación, alta sintética, V0, cálculo 0/8, completitud, regreso a la ficha y presentación móvil.
- Las pruebas backend heredadas de la fase 16 no se han modificado salvo la continuidad del número de versión.

## Entrega

La aplicación arranca sin registros de participantes. La fase 18 se centra en cierre analítico; la 19, en aceptación final del software; la 20, en el informe técnico-científico independiente solicitado para la documentación del trabajo.
