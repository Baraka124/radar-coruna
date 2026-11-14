# RADAR-CORUÑA · v0.35 — Rediseño de jerarquía clínica y UI proporcional

**Base inalterada:** aplicación v0.34. **Naturaleza del cambio:** presentación, estructura visual, microtexto contextual y pruebas de interfaz. **Entorno:** exclusivamente datos sintéticos.

## Por qué v0.34 seguía sin sentirse prémium

Reducir la anchura de los campos no bastaba. La vista de evaluación contenía encabezados repetidos, un contenedor principal con otros recuadros innecesarios, texto demasiado pequeño, título de sección alineado a la derecha del desplegable, acciones separadas de la información que facilitaban y una barra de progreso que interrumpía el formulario a lo ancho. En móvil, los enlaces contextuales podían repartirse en varias líneas y desplazar el trabajo hacia abajo.

## Cambios reales en v0.35

- **Sistema de diseño:** paleta clínico-institucional blanca y azul, superficies tranquilas, contraste de texto más claro y tamaños de etiqueta más legibles; se evita aumentar el tamaño de botones sin necesidad.
- **Espacio y jerarquía:** navegación lateral compacta, cabeceras menos repetitivas, panel de edición con una sola jerarquía visual, sin cajas dentro de otras cajas; título de bloque correctamente alineado a la izquierda y chevrón al extremo derecho.
- **Entrada de datos:** primera sección de visita organizada por la importancia y longitud de cada dato; campos cortos siguen cortos, sin estiramiento artificial. Botón «Usar último tabaquismo» ubicado junto al estado que explica.
- **Portátil frente a escritorio amplio:** flujo de una columna en portátil; en escritorio amplio, resumen de completitud en una columna auxiliar estrecha, evitando una tarjeta de progreso de ancho completo entre las preguntas.
- **Móvil:** navegación contextual compacta («Evaluación clínica / Ficha / Excel»); campos de lectura larga a ancho disponible, CAT y mMRC en dos columnas; botones del pie compactos y utilizables.
- **Resto del estudio:** tokens visuales comunes en cohorte, CRD, tablas, menús, métricas, navegación y elementos de formulario.

El archivo `static/DESIGN_SYSTEM_V35.css` conserva el diseño como referencia modular; las reglas se incluyen también al final de la hoja principal en `static/index.html` para compatibilidad con el empaquetado HTML existente y con las pruebas sintéticas.

## Verificación realizada

- **48/48 pruebas Python focalizadas**: 32 correspondientes a la aceptación científica/captura inteligente/inteligencia clínica, y 16 de concordancia CRD, episodios, contactos, viaje longitudinal y Excel.
- **Playwright v0.35:** PASS a **320, 390, 768, 1057 y 1440 px**; rutas Participantes, Visitas y CRD, ausencia de desbordamiento horizontal, anchura de selector proporcionada en escritorio, disposición lateral de completitud en 1440 px, funcionamiento de menú móvil y guardado real de V1 con base sintética temporal.
- **Playwright v0.34 sobre v0.35:** PASS en cinco anchos, con guardado clínico.
- Una tentativa de ejecutar la totalidad del conjunto Python histórico por archivos no terminó en tiempo útil. **No se afirma que toda la suite histórica haya sido certificada en v0.35**; las pruebas finalizadas se distinguen de esa tentativa incompleta.

## Sin cambios

No se altera el contrato API, los códigos R001–R107, las validaciones clínicas, la estructura de la base de datos, las fórmulas RADAR, la lógica de seguimiento o la exportación. v0.34 se conserva sin modificación. El ZIP no incluye archivos de base de datos ni claves de acceso.

## Evidencias visuales

- `docs/v35/v35_evaluacion_escritorio.png`: escritorio de 1440 px, con rail de completitud.
- `docs/v35/v35_evaluacion_portatil.png`: portátil 1057 px, jerarquía de campos.
- `docs/v35/v35_evaluacion_movil.png`: móvil 390 px, contexto sin saltos de línea.
- `docs/v35/v35_cohorte_escritorio.png`: diseño general de la cohorte.
- `docs/v35/v35_crd_escritorio.png`: diseño general del CRD.

**Estado de liberación:** versión local de demostración, no desplegada. La evaluación visual definitiva requiere feedback con el producto abierto en el entorno destino.
