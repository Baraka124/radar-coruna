# RADAR-CORUÑA · v0.36 — Sistema visual coherente en toda la aplicación

**Base preservada:** RADAR-CORUÑA v0.35. **Alcance:** interfaz y pruebas de presentación; únicamente se sincroniza la versión técnica del servidor (`0.36.0`) con el frontend y el estado API (`0.36`). **Entorno de aceptación:** datos íntegramente sintéticos en SQLite temporal.

## Problema resuelto

La versión anterior tenía una hoja visual nueva superpuesta a varios estilos históricos, de modo que distintos módulos seguían usando densidades, botones, filtros, tablas y anchuras de campos diferentes. Las fichas de episodio y el CRD complementario todavía aplicaban geometrías expansivas a respuestas breves. Se ha introducido un contrato común de componentes, con especial atención a la proporción y a la legibilidad.

## Cambios de v0.36

- **Navegación y cabecera:** jerarquía más compacta y consistente, grupos laterales claros, navegación activa legible; controles discretos, sin barras de botones grandes.
- **Espacio de trabajo:** un criterio común de títulos, subtítulos, márgenes, fondos blancos y bordes ligeros, con un fondo general gris muy tenue y colores azul institucional/neutros. No se añade relleno decorativo innecesario.
- **Tablas y listados:** cabeceras, altura de fila, microtipografía, resaltados, enlaces de acción, badges y bordes con una misma densidad, manteniendo desplazamiento horizontal *dentro* de las tablas cuando haga falta en móvil.
- **Filtros y acciones:** campos de búsqueda/selección con ancho máximo medido y botones del tamaño del contenido. Los botones primarios son ligeros en vez de bloques azules sólidos.
- **Fichas clínicas:** participantes, evaluaciones, episodios y contactos comparten reglas de controles y espacios. Los campos de fecha y número siguen siendo cortos.
- **CRD complementario:** rejilla **proporcionada** de campos breves (tres columnas en escritorio amplio; dos cuando cabe; una en móvil), sin el estiramiento previo de las selecciones Sí/No.
- **Evolución, calidad, análisis y exportación:** mismas superficies, tipografía, densidad de indicadores y tratamiento de estados.
- **Accesibilidad:** foco visible del teclado, hit targets adecuados, soporte de movimiento reducido y ausencia de scroll horizontal de página al navegar por los módulos.

Implementación: `static/DESIGN_SYSTEM_V36.css`, reproducida al final de `static/index.html` para mantener el formato de distribución autocontenido existente. Se deja `static/DESIGN_SYSTEM_V35.css` como referencia histórica; no se reemplaza el original.

## Pruebas terminadas

- **Playwright v0.36:** **12 rutas × 5 anchos** (320, 390, 768, 1057 y 1440 px) sin errores JavaScript ni desbordamiento horizontal de página. Incluye Resumen, Participantes, Visitas, Seguimiento CRD, CRD, Episodios, Resultados, Implantación, Análisis, Calidad, Diccionario y Excel.
- **Editores adicionales:** fichas de participante y de episodio, además de la evaluación V1, verificadas con controles proporcionados; guardar V1 sigue funcionando; apertura/cierre con Escape del menú móvil.
- **Regresión Python:** pruebas focalizadas finalizadas para aceptación científica, captura inteligente, inteligencia del flujo, concordancia CRD, episodios/contactos, seguimiento longitudinal, fiabilidad de versión y release histórico. **55 pruebas distintas superadas** en las baterías finalizadas (65 ejecuciones incluyendo repetición de `test_phase33_workflow_intelligence.py`).
- Un intento de ejecutar todos los archivos históricos individualmente dejó una ejecución colgada y no se completó. Se conservan los resultados positivos finalizados, **sin afirmar certificación integral de toda la suite histórica**.

## Sin cambios clínicos

No se modifican las definiciones R001–R107, fórmulas RADAR, validación de elegibilidad, correcciones, auditoría, esquemas de base de datos, controles de acceso ni modelo de exportación. No se despliega a un servidor ni se incluye ninguna base de datos.

## Capturas reales

En `docs/v36/` se incluyen vistas de las **12 rutas**, las evaluaciones en 390/1057/1440, los formularios de participante y episodio en escritorio/móvil y capturas móviles de cohorte, CRD, eventos, calidad y resumen. Todas se tomaron ejecutando el mismo frontend con un registro sintético temporal.

**Estado:** versión local, apta para revisión de UI y continuación del desarrollo. Su calidad visual definitiva debe revisarse también en el portátil y navegador reales del equipo investigador.
