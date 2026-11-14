# RADAR-CORUÑA · v0.33 · Inteligencia de captura clínica

**12 de noviembre de 2026 · Incremento independiente sobre la v0.32**  
**Entorno de verificación: aplicación local con datos exclusivamente sintéticos.**

## Resultado

Se ha auditado el contrato de los **107 códigos R001–R107**, distinguiendo qué debe registrarse, qué puede derivarse, qué debe relacionarse con otra entidad y qué mediciones repetidas requieren nueva confirmación profesional. Se han implementado mejoras de interfaz y dos validaciones de coherencia sin modificar las fórmulas RADAR ni la estructura de las tablas SQL.

El inventario completo y verificable está en `AUDITORIA_INTELIGENCIA_R001_R107_V33.md` (lectura humana) y `AUDITORIA_INTELIGENCIA_R001_R107_V33.json` (registro estructurado). Clasificación principal: **31** registros de fuente, **17** derivados, **29** condicionales, **13** auxiliares/centro, **8** vinculados y **9** reevaluables por visita. Se identifican **16 códigos** con aspectos de definición o alcance por resolver, sin resolverlos por suposición.

## Cambios implementados

| Elemento | Comportamiento v0.33 | Salvaguarda |
|---|---|---|
| **R034 · GOLD de obstrucción** | Calculado en directo al introducir FEV1 % predicho y FEV1/FVC pos-BD válidos | Sólo con cociente inferior a 0,70; nunca es un campo independiente editable ni clasificación A/B/E |
| **R022 · Fecha de consentimiento** | La fecha se presenta cuando consta firmado o retirado | Si existe ya una fecha y cambia el estado, permanece visible hasta su corrección explícita |
| **R084–R086 · Estado vital** | Fecha/causa del fallecimiento se presentan cuando corresponde | No se deduce fallecimiento de pérdida de seguimiento y no se borran valores preexistentes |
| **R064 · Motivo de visita no realizada** | Se muestra al indicar `no_realizada` | El servidor no permite conservar ese motivo en una visita parcial o completada |
| **R045–R047 · Monoterapia** | Subtipo LAMA/LABA sólo cuando el régimen es monoterapia | No se arrastra un subtipo antiguo a un régimen nuevo incompatible; el servidor mantiene la comprobación de pauta |
| **R055–R056 · IANUS** | La captura de recogida y fecha se muestra en el contexto de la verificación | `Sí/No` en recogida requiere IANUS verificable; `NV` no equivale a ausencia de toma real |
| **R062 · Fecha V1/V2** | La ficha nueva **no introduce la fecha actual automáticamente**. Muestra ventana orientativa 6±1 o 12±1 meses respecto a V0 | Se conserva la fecha real incluso fuera de ventana. Un aviso no cambia las reglas científicas |
| **R029 y tratamiento de seguimiento** | Dos acciones optativas para reutilizar *como propuesta* tabaquismo o pauta de una visita previa | Sólo se completan controles vacíos; no se transfieren dosis, IANUS, síntomas, RADAR ni actuaciones. El investigador valida antes de guardar |
| **R068 · Disnea y mMRC** | mMRC muestra una propuesta equivalente con botón **Confirmar respuesta** | R068 nunca se autocompleta ni sobrescribe silenciosamente; una discrepancia se mantiene visible |
| **R026 · Identidad de variable** | El inventario y las etiquetas de exportación reconocen R026 = **fecha de inclusión** | `birthDate` es un dato técnico de apoyo al cálculo de la edad, **no** es R026 |
| **Campo `adherence` heredado** | La descripción de Excel advierte que es un dato histórico no equiparable a R056 | No se confunde prescripción recogida con consumo real ni adherencia validada |

No se han introducido nuevos códigos de CRD; no hay fórmulas terapéuticas ni sugerencias de prescripción automática.

## Comprobación técnica

- **Python:** 122/122 pruebas aprobadas en **23 procesos de fichero independientes**; los resultados por archivo y los comandos quedan en `RESULTADOS_PRUEBAS_V33.txt`. No afirmamos que se ejecutaran como una única suite monolítica sin bloqueo.
- **Interfaz:** escenario automatizado con Playwright/Chromium en **320, 390, 768, 1024 y 1440 px**. Comprobados campos condicionales, derivación GOLD, ventanas de seguimiento, sugerencia mMRC, reutilización explícita, no sobreescritura, ausencia de scroll horizontal y guardado de V1.
- **Datos:** controles de visita y tratamiento siguen entrando por los mismos endpoints auditados. No se crea una nueva tabla ni se reescriben registros anteriores.
- **Versión:** salud `0.33.0`, estado `0.33` y pie de aplicación actualizados.

## Límites técnicos que siguen abiertos

1. **Uso simultáneo multicentro y recuperación operativa** aún no se han ensayado en el alojamiento objetivo; la batería local no es una prueba de carga.
2. **Trazabilidad de propuestas de visita:** se requiere que el profesional confirme lo reutilizado antes de guardar, pero la procedencia precisa de cada campo propuesto todavía no se conserva como metadato de auditoría individual; sería una mejora posterior de integridad.
3. **Visitas no realizadas con mediciones residuales:** el sistema conserva compatibilidad con registros anteriores; una futura norma de saneamiento debe decidir cómo gestionar medidas preexistentes sin borrarlas ni falsearlas.
4. **IANUS R055/R056, Charlson R044 y variables de implantación** contienen definiciones pendientes que no deben automatizarse sin acuerdo metodológico.
5. **Despliegue real:** el prototipo es localhost y usa códigos ficticios. Esta entrega no trata ni valida datos de pacientes reales.

**Resultado:** se cierra una primera pasada exhaustiva del diccionario y una implementación dirigida de sus duplicaciones y dependencias más claras. **No** equivale aún a certificar una captura multicéntrica productiva sin más pruebas.
