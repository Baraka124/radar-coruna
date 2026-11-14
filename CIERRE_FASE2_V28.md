# RADAR-CORUÑA · Fase 2 cerrada · Integración longitudinal v0.28

**Fecha de comprobación:** 12 de noviembre de 2026  
**Estado:** aceptación técnica para evaluación **local con datos sintéticos**.  
**Base:** paquete RADAR_CORUNA_MVP_v28_Recorrido_Integral.zip (no cambia su comportamiento clínico).

## Alcance comprobado

- Alta de participante y lectura conjunta de visitas **V0, V1 y V2**.
- Puntuación RADAR completa, incluido **0 válido**, y diferencia **V2 − V0** únicamente cuando ambas visitas son evaluables.
- Datos CAT/mMRC, registro complementario por visita y ausencias **R107** ligadas a variables concretas.
- Episodios con número **R074**; dos contactos (Urgencias e ingreso) ligados al mismo episodio; eventos no EPOC separados del recuento de agudizaciones EPOC.
- Revisión longitudinal **solo lectura** con avisos de calidad sin corrección automática.
- Lectura por centro autorizada; persistencia de registros tras reinicio; exportación de investigación en Excel con los datos guardados.
- Vista longitudinal de escritorio **1440 px** y móvil **390 px**, sin error JavaScript ni desbordamiento horizontal en la prueba de aceptación.

## Verificación realizada en esta revisión

- `pytest -q tests/test_phase28_journey.py tests/test_phase27_concordance.py tests/test_phase22_episode_care.py tests/test_phase21_episodes_actions.py tests/test_phase20_crd_alignment.py` → **16 pruebas correctas**.
- `pytest -q tests/test_export.py` → **3 pruebas correctas**.
- `python tests/browser_phase28_journey.py` → **escritorio y móvil correctos en tres ejecuciones consecutivas**.
- Aceptación incluida en el paquete de origen: lotes de **34 y 27 pruebas**, con **2 comunes (59 distintas)**. Estos resultados son los consignados en el artefacto de origen, no una repetición íntegra en esta revisión.

## Único ajuste introducido

La prueba de navegador `tests/browser_phase28_journey.py` utilizaba el mismo cliente HTTP ya autenticado para inicializar la aplicación y, simultáneamente, enviaba un segundo inicio de sesión manual. Ambas restauraciones de sesión podían terminar en distinto orden, cerrando el menú móvil justo después de abrirlo. La prueba ahora espera la recuperación automática de la sesión existente antes de navegar. También espera a que termine la transición del panel móvil antes de pulsar «Participantes».

**No se ha cambiado el código clínico ni el comportamiento de la aplicación**, las tablas, las autorizaciones, el estilo blanco ni el catálogo de variables.

## Delimitación del cierre

Este cierre corresponde exclusivamente a **Fase 2: recorrido e integración**. No es una certificación de toda la batería histórica en una sola ejecución, ni una validación científica, ni una habilitación para datos reales. La ejecución agrupada completa de pruebas heredadas quedó sin finalizar en esta revisión y corresponde al trabajo de **Fase 3: regresión y fiabilidad**.

Siguen abiertas las decisiones científicas documentadas en el catálogo sobre la ventana exacta de IANUS, la conciliación histórica de adherencia y algunos campos longitudinales de tratamiento/vacunación. No se han inventado reglas para rellenar esos vacíos. El inicio previsto del estudio en enero de 2027 está condicionado a las aprobaciones éticas pertinentes; este prototipo no autoriza reclutamiento.

## Ejecución local

Consultar `LEEME.md`. Con las dependencias instaladas, iniciar con `python start_local.py`, y abrir `http://127.0.0.1:8878/`. Usar únicamente códigos y pacientes ficticios.
