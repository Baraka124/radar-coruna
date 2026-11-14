# RADAR-CORUÑA · Fase 3 · Regresión y fiabilidad · v0.29

**Verificado:** 12 de noviembre de 2026  
**Procedencia:** paquete de Fase 2 `RADAR_CORUNA_MVP_v28_Fase2_Cerrada.zip`.  
**Alcance:** piloto local únicamente con datos sintéticos. No hay despliegue ni conexión a neumDESK, ni se modificó el paquete v0.28.

## Resultado

| Comprobación | Evidencia | Resultado |
|---|---|---|
| Batería histórica y nueva de Python | `python -m pytest -q tests/test_*.py --disable-warnings` | **90/90 correctas** en una ejecución (107,47 s) |
| Navegador | `browser_phase20_crd.py` a `browser_phase28_journey.py` | **9/9 itinerarios correctos** tras adaptar tres pruebas heredadas a la navegación actual |
| Sintaxis | `python -m compileall -q server.py tests` | **Correcto** |
| Integridad de empaquetado | Comprobación ZIP y exclusión de SQLite/cachés | **Correcto** |

La prueba de navegador v0.21 se volvió a ejecutar y pasó; la de v0.22 pasó tras abrir el elemento `details` de conciliación; la v0.25 pasó con el selector de regreso a la ficha más preciso. Los itinerarios v0.20, v0.23, v0.24, v0.26, v0.27 y v0.28 habían pasado en la primera ejecución. Este cierre no equivale a repetir todas las pruebas de navegador anteriores a v0.20.

## Cambios de fiabilidad realizados

1. **Protección de fecha basal:** si existe V0, la edición del participante no puede cambiar la fecha de inclusión dejando una V0 con fecha diferente. Respuesta explícita `409` y transacción sin cambios. No se modifica automáticamente la V0.
2. **Protección de la trayectoria:** el cambio de un participante incluido a `cribado` queda bloqueado cuando ya conserva visitas, episodios o contactos, evitando una cohorte longitudinal lógicamente huérfana.
3. **Correcciones normales preservadas:** cuando no existe V0 ni datos dependientes, el registro puede corregirse y una V0 posterior usa la fecha rectificada.
4. **Pruebas históricas compatibles con versiones futuras:** cuatro tests Python que exigían listas cerradas de versiones pasan a contrastar `/api/health` con `server.app.version` y mantienen la cota mínima de la versión histórica.
5. **Pruebas de navegador alineadas con la interfaz actual:** los tests históricos seleccionan explícitamente el grupo del CRD, despliegan la nota de conciliación y usan el botón concreto de regreso a la ficha. La interfaz **no fue revertida ni rediseñada**.

## Alcance de la regresión

Se comprobaron el alta y lectura de participantes, revisiones y justificación, V0/V1/V2, RADAR con cero válido y visitas no realizadas, CRD complementario, R074 y R081/R082, registro de ausencias R107, trazabilidad, eventos/contactos, estudio por centro, lectura por revisor, protección CSRF, exportación XLSX (incluidos permisos, fórmulas y textos), copia y restauración a una base nueva, y recorrido longitudinal en escritorio y móvil. Cinco nuevas pruebas (`tests/test_phase29_reliability.py`) cubren explícitamente las invariantes añadidas, el bloqueo por roles y la versión.

## Límites y decisiones pendientes

- **No se ha habilitado un sistema institucional ni se han utilizado datos clínicos reales.** El acceso sigue limitado a `localhost` y las contraseñas predefinidas son exclusivamente demostrativas.
- Cambios coordinados entre fecha de inclusión y V0 requieren un flujo de corrección clínica diseñado específicamente; en v0.29 se bloquea una corrección unilateral que rompería la consistencia.
- Las definiciones metodológicas aún no cerradas (p. ej., ventana exacta y conciliación de adherencia IANUS, ciertos campos longitudinales de tratamiento/vacunación) siguen pendientes de aprobación del equipo investigador. No se han inferido valores ni reglas clínicas nuevas.
- La comprobación automatizada no reemplaza prueba de carga multiusuario, revisión de seguridad institucional, validación científica, prueba de despliegue, ni aprobación del CEIC. El estudio se plantea para enero de 2027 **condicionado a las aprobaciones necesarias**.

## Siguiente etapa recomendada

**Fase 4: UI y usabilidad** — profundizar en navegación, formularios, densidad visual, responsive, comunicación de estado, y accesibilidad, manteniendo los flujos y los 90 tests de regresión como red de seguridad.
