# RADAR-CORUÑA · v0.32 · Captura inteligente e integridad de inclusión

**12 de noviembre de 2026 · rama independiente desde v0.31.** La v0.31 permanece conservada. Entorno local exclusivamente sintético.

## 1. Problema corregido

La pantalla anterior solicitaba la **fecha de nacimiento** y mostraba una **edad editable**. Eso permitía duplicar la captura o presentar un valor manual contrario a la fecha real. Igualmente mostraba el **total histórico de agudizaciones** pese a almacenar las cifras moderadas y graves por separado.

En v0.32, el investigador registra la fuente clínica y el programa deriva los resultados:

- **Edad en V0** = años cumplidos entre fecha completa de nacimiento (R026) y fecha de inclusión/V0. El resultado es inmediato y de solo lectura. No se infiere un dato preciso a partir del año de nacimiento aislado. Los cumpleaños y años bisiestos se han probado.
- **Total de agudizaciones** = moderadas + graves del periodo basal, pero únicamente si ambos recuentos están disponibles. Se conserva el valor histórico anterior cuando aún faltan las fuentes, con indicación de que no ha sido recalculado.
- La nueva ficha de **cribado** comienza sin una fecha V0 prefijada; guardar cribado no inventa el inicio clínico.

El servidor vuelve a calcular y verificar la edad y el recuento. El usuario no puede cambiar esos resultados mediante una petición directa de API enviando números diferentes.

## 2. Inclusión validada también en el servidor

Para pasar a `incluido`, una ficha nueva o corregida debe registrar los criterios estructurados del protocolo reconciliado:

| Criterio | Implementación v0.32 |
|---|---|
| Edad ≥ 40 años | Cálculo obligatorio desde nacimiento completo y fecha V0; no basta la edad manual |
| EPOC | Confirmación afirmativa, fecha de espirometría y FEV1/FVC pos-BD < 0,70 |
| Seguimiento AP | Seguimiento habitual afirmativo y **fecha de última consulta EPOC previa** dentro de los 12 meses anteriores a V0 |
| Estabilidad | Al menos cuatro semanas y ausencia explícita de agudización activa |
| Capacidad | Sí o Con ayuda |
| Exclusiones | No explícito a exclusión general, diagnóstico alternativo, comorbilidad descompensada y ensayo interferente |
| Consentimiento | Sí firmado, con fecha no posterior a inclusión |
| Decisión de elegibilidad | `elegible` confirmada por investigador |

Cuando no se cumple, **se guarda como cribado**, no como participante incluido. El error explica lo que falta sin escribir valores implícitos. El servidor valida aunque se altere la petición o no se use el navegador.

El campo `lastCopdReviewDate` complementa la evidencia estructurada y se incluye en la exportación. Es un campo de soporte digital **nuevo, no un código adicional R108**: el catálogo publicado R001–R107 conserva su identidad. El dato clínico original y la procedencia del cociente pos-BD requieren verificación profesional; el sistema comprueba lo declarado, no puede certificar por sí solo un documento clínico externo.

## 3. Compatibilidad y no regresión

- La UI mantiene la composición clínica clara, controles medidos, navegación y CRD complementario previos.
- No hay nueva tabla SQL obligatoria: `lastCopdReviewDate` se incorpora al JSON versionado del participante.
- La vista existente y las exportaciones siguen leyendo fichas heredadas. Si un **incluido histórico** carece de datos exigidos en v0.32, debe completarse para corregirlo; **no se reescribe automáticamente ni se declara validado**.
- Los valores históricos de edad y total sin fuentes actuales se conservan como **legado de solo lectura** en la pantalla. Para recalcularlos, introducir fecha de nacimiento completa o ambos recuentos.
- Se conserva el control de versión y el conflicto de revisiones simultáneas (409). El resto de funciones longitudinales y permisos no cambia.
- No se han modificado las fórmulas RADAR (3 + 2 + 2 + 1), ni se han inferido valores ausentes como cero.

## 4. Verificación

Tests v0.32: `python -m pytest -q tests/test_phase32_intelligent_capture.py`

Prueba UI automatizada: `python tests/browser_phase32_intelligent_capture.py` (requiere Playwright y Chromium instalados localmente). Se comprueban **320, 390, 768, 1024 y 1440 px**, ausencia de overflow, campos derivados no editables, recálculo inmediato y un registro completo creado desde la interfaz.

Regresión responsive del v0.30, con caso sintético compatible: `python tests/browser_phase30_premium.py`.

La batería histórica tiene test de dominio actualizados a la nueva inclusión, sin flexibilizar las reglas del servidor. La ejecución de cada fichero por separado evita el bloqueo por estado compartido observado anteriormente. Ver el registro de pruebas incluido.

## 5. Alcance pendiente estrictamente técnico

El paso a una **recogida multicéntrica de pacientes reales** todavía exige pruebas en su entorno de alojamiento definitivo: concurrencia y rendimiento bajo carga real, recuperación desde copias de seguridad y comprobación de la cadena de despliegue, controles de seguridad de producción, preservación de integridad en fallos de red, ciclo de soporte y migración gobernada de los datos. No se ha simulado un despliegue institucional ni se certifica una base clínica real en esta entrega.

Además, la ventana exacta para interpretar «últimas prescripciones» en IANUS continúa siendo una definición clínica abierta, no un campo que deba automatizarse por suposición. Las ventanas V1/V2 se avisan, pero no se prohíben automáticamente: la fecha real debe conservarse.

**Estado:** captura clínica y validación de elegibilidad mejoradas y probadas en piloto local sintético; infraestructura multicéntrica productiva todavía no certificada.
