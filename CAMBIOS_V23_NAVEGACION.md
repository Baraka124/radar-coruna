# RADAR-CORUÑA · v0.23 — Navegación refinada

**Alcance:** mejora exclusivamente visual y de navegación a partir de v0.22. Se conservan rutas, modelos, permisos, reglas clínicas, persistencia, auditoría y Excel.

- Barra lateral clara, alineada con el lienzo blanco de la aplicación; sin introducir botones llenos o efectos decorativos.
- Navegación organizada en Área clínica, Seguimiento, Análisis y recursos.
- Iconografía vectorial uniforme y contraste de texto revisado.
- La opción activa muestra una línea fina y un fondo neutro suave, sin bloques intensos.
- Sidebar comprimible a un rail de 74 px en escritorio; los títulos de cada icono permanecen accesibles por tooltip.
- En tablet/móvil, menú lateral superpuesto con botón de apertura, cierre al navegar y tecla Escape.
- En formularios de detalle o edición se mantiene marcada la sección padre en la navegación.
- Pie de barra más compacto para no consumir espacio útil.
- La versión de API se identifica como 0.23.0; sin cambios a tablas, campos, validadores ni migraciones.

## Verificación
- Pruebas de navegación en Chromium para escritorio 1440 × 900 y móvil 390 × 844, incluidos colapso y menú móvil.
- Reutilización de la batería de regresión anterior para comprobar que los cambios visuales no alteran el dominio clínico.
