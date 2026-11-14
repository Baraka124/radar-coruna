# RADAR-CORUÑA — Fase 18
## Informe descriptivo y resultados científicos del MVP

**Versión técnica:** v0.18 · **Estado:** especificación de análisis para revisión científica.

El objetivo es producir resultados reproducibles a partir de los registros persistidos, con el mismo cálculo en pantalla y en el Excel. La exportación se actualiza al descargar y no requiere volcado manual.

### Resultados que calcula la aplicación

- Distribución de la puntuación RADAR (buen, parcial y mal control) por visita V0, V1 y V2, con denominador formado exclusivamente por RADAR completos.
- Proporción de mal control en V0 (RADAR ≥4), con IC 95% de Wilson **ilustrativo**. Su inclusión definitiva requiere decisión estadística.
- Pares de RADAR V0–V2, pares de CAT V0–V2 y pares de mMRC V0–V2 **independientes**. Una ausencia de RADAR no invalida un par de CAT correctamente registrado.
- Diferencias V2 – V0 en mediciones válidas, con tamaño del subgrupo explícito.
- Tabla de nueve transiciones posibles entre las categorías RADAR basal y final.
- Registros de agudizaciones, urgencias e ingresos por separado; no se interpretan los recuentos como tasas de incidencia.
- Indicadores de implantación únicamente cuando sus numeradores y denominadores han sido registrados de forma explícita.

### Nuevas hojas de exportación

| Hoja | Función |
|---|---|
| `INFORME_V18` | Indicador, numerador, denominador, valor, unidad e interpretación |
| `RADAR_ETAPAS_V18` | Distribución 0–1, 2–3 y ≥4 por visita |
| `PAREJAS_INDEP_V18` | Mediciones longitudinales individuales sin mezclar muestras de análisis |
| `TRANSICIONES_V18` | Matriz basal/final de control clínico |
| `METODOLOGIA_V18` | Reglas y límites de cada análisis |

La pestaña `RESUMEN` muestra cinco indicadores clave con referencias a `INFORME_V18`. Se conservan las hojas de CRD, episodios, contactos, calidad, variable-dictionary, decisiones y auditoría.

### Reglas científicas relevantes

- Una puntuación RADAR **0** es válida. Cuestionario incompleto se mantiene sin clasificación.
- Los porcentajes no se presentan si falta un denominador válido; un campo vacío no equivale a cero.
- Las visitas registradas como *no realizada* no generan mediciones válidas.
- Las visitas futuras no se consideran automáticamente perdidas ni retrasadas.
- La interpretación de cambios es descriptiva; no se afirma efecto causal de RADAR.
- El estado científico de definiciones del CRD continúa **propuesto**, pendiente de discusión con Pedro y los investigadores.

### Aceptación

Pruebas unitarias específicas: cohorte vacía, puntuación cero, RADAR incompleto con CAT completo, muestras independientes, nueve transiciones, centro de origen, alcance de la exportación y no doble recuento de resultados. Prueba interactiva en Chromium realizada con **un solo participante sintético**. El paquete distribuido inicia con **cero participantes**.

**Siguiente hito:** Fase 19, aceptación y cierre funcional del software. **Fase 20:** informe técnico-científico institucional para Pedro; distinto del informe de resultados clínicos futuro.
