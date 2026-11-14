# RADAR-CORUÑA · Fase 4 — UI clínica premium y responsive · v0.30

**Fecha de revisión:** 12 de noviembre de 2026  
**Base inalterada:** `RADAR_CORUNA_MVP_v29_Fase3_Fiabilidad.zip`.  
**Alcance:** ergonomía visual y respuesta en distintos tamaños de pantalla. Entorno local con datos exclusivamente sintéticos; no desplegado.

## Principios aplicados

- **Proporción antes que volumen:** los botones se ajustan a sus etiquetas y contexto; no se expanden a todo el ancho por defecto. Altura ordinaria de 34–35 px, relleno moderado y foco visible.
- **Jerarquía tranquila:** las acciones primarias usan un tratamiento de bajo peso visual (tinte azul clínico tenue y borde) en lugar de grandes bloques sólidos. Las secundarias permanecen blancas.
- **Búsqueda de tamaño razonable:** campo de búsqueda de participantes de 294 px y selección de centro de 236 px como máximos en escritorio; en móvil se adaptan al ancho disponible sin desbordar.
- **Campos proporcionados:** entradas de número limitadas a 188 px y fechas a 205 px en escritorio; en móvil recuperan el ancho completo para facilitar la lectura y el tacto. Las descripciones y controles con texto largo no se truncan artificialmente.
- **Formularios clínicos:** disposición, salto entre apartados, barra de guardado, CRD y navegación de V0/V1/V2 conservados; espaciado de acciones y encabezados más contenido.
- **Acceso:** fondo blanco/gris pálido, tarjeta de lectura clara y botón de entrada compacto (154 px en comprobación), sin franja oscura/verdosa ni botón expandido.
- **Accesibilidad:** contornos visibles de foco para controles principales, respeto de `prefers-reduced-motion`, navegación móvil con cierre por Escape; sin scroll horizontal de página en las anchuras verificadas.

## Resultado de pruebas

| Prueba | Resultado |
|---|---|
| Batería Python completa (`pytest -q tests/test_*.py --disable-warnings`) | **90/90 correctas** en una ejecución |
| Navegador histórico seleccionado (v0.20–v0.28) | **9/9 itinerarios correctos** |
| Navegador nuevo v0.30 | **1/1 prueba integral correcta** |
| Anchos auditados con navegador | **320, 390, 768, 1024, 1440 px** |
| Vistas del test nuevo | **Resumen, Participantes, Visitas, CRD, Episodios, Análisis y ficha de participante** |
| Sintaxis Python y ausencia de SQLite/cachés en el paquete | **Verificado** |

Las capturas de escritorio y móvil están en `docs/v30/` y el test reproducible es `tests/browser_phase30_premium.py`. En uno de los scripts históricos, el cierre de Playwright emite una advertencia asíncrona `TargetClosedError` tras declarar el resultado correcto; el script terminó con código 0 y no produjo un fallo de interfaz.

## Superficie de modificación

- `static/index.html`: hoja de estilo adicional v0.30, sin reescribir estructura de componentes ni manejadores; título, pie y datos de demo actualizados a la versión de presentación.
- `server.py`: **sólo metadatos de versión** (`0.30.0` y versión de la respuesta de colección). Sin modificación de endpoints, permisos, modelo de datos ni lógica clínica.
- `tests/browser_phase30_premium.py`: test nuevo, con base temporal y participantes sintéticos.
- `LEEME.md`: instrucciones e historial actualizados.

**Sin cambios funcionales:** puntuación RADAR, visitas, R074, R081/R082, R107, manejo de episodios y contactos, decisiones de elegibilidad, accesos por centro, exportación Excel, reglas de integridad y trazabilidad de v0.29.

## Límites de aceptación

La prueba automatizada no sustituye evaluación real con investigadores de atención primaria, validación científica, test de carga, auditoría de seguridad institucional, integración externa ni autorización CEIC. Las cuestiones metodológicas aún abiertas (incluida la ventana exacta IANUS) **no se han decidido en el código**. El arranque de estudio previsto para enero de 2027 sigue condicionado a las aprobaciones correspondientes.

**Siguiente paso:** Fase 5 — aceptación científica, prueba guiada con profesionales, documentación para el centro y criterios de preparación, sin introducir pacientes reales antes de autorizaciones.
