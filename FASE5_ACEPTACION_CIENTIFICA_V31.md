# RADAR-CORUÑA · Fase 5 · Candidato de aceptación científica v0.31

**Fecha:** 12/11/2026  
**Base:** v0.30 de Fase 4; conservada y sin sobrescritura.  
**Ámbito:** prueba local con datos exclusivamente ficticios.  
**Resultado de esta entrega:** **paquete listo para prueba guiada por investigadores; aceptación científica formal NO emitida**.

## 1. Alcance realizado

1. Revisión de la v0.30 frente al **protocolo y el informe técnico reconciliados el 09/11/2026**, junto con `CONCORDANCIA_CRD_V27.md` y el catálogo `study_spec_v09.json`.
2. Nueva auditoría **no destructiva** de concordancia de inclusión y ventanas longitudinales (`scientific_preflight.py` y `scripts/phase5_readonly_audit.py`). Accede a una SQLite sintética en modo lectura; no cambia registros, puntuación RADAR, permisos ni exportaciones.
3. Ocho pruebas automatizadas de preflight, límites clínicos, aislamiento multicéntrico, exportación y no mutación (`tests/test_phase31_scientific_uat.py`).
4. Material operativo para prueba estructurada: `GUIA_PRUEBA_INVESTIGADORES_V31.md`, `REGISTRO_CONCORDANCIA_Y_DECISIONES_V31.md`, `ACTA_ACEPTACION_V31.md`.
5. Versionado del candidato de evaluación a **v0.31.0**; interfaz v0.30, misma densidad de controles, sin nueva lógica de inclusión obligatoria ni despliegue.

## 2. Evaluación de la concordancia científica

| Regla del protocolo | Observado en v0.30/v0.31 | Resultado para aceptación |
|---|---|---|
| Estabilidad sin agudización en **4 semanas previas** | Incluido con `weeks<4` rechazado; 4 aceptado | Alineado técnicamente; verificar ausencia activa |
| Edad **≥40 años** | Se deriva edad cuando existe nacimiento, pero no bloquea inclusión por edad | **Pendiente de decisión y corrección** |
| EPOC con FEV1/FVC posbroncodilatador **<0,70** | Fecha y cociente disponibles; no se obliga ratio menor de 0,70, ni se acredita carácter pos-BD | **Pendiente de decisión y corrección** |
| Control habitual AP y al menos una consulta EPOC en año anterior | `regular` disponible, pero sin fecha estructurada de esa consulta | Evidencia externa/digital por acordar |
| Consentimiento previo | Estado Sí exigido, fecha opcional en registro | Formalizar evidencia y regla de obligatoriedad |
| Ausencia de exclusiones R017/R019/R020 | Campos existentes, respuestas vacías pueden llegar a inclusión | Acordar manejo de ausencias antes de aprobación |
| V1 a seis meses ±1 y V2 a doce meses ±1 | Se conservan fechas reales; UAT señala visitas fuera de ventana sin editarlas | Decidir análisis de desvíos con IP |
| RADAR 3–2–2–1, total 0–8, corte ≥4 | Funcionalidad probada en fases anteriores | Corroborar por clínicos con casos trazados |
| Episodio R074 distinto de Urgencias R081 e ingreso R082 | Vinculación y desduplicación automatizadas probadas | Revisar con casos clínicos guiados |
| R055/R056, proxy de últimas prescripciones IANUS | Datos diferenciados del legado | **Ventana exacta pendiente** |
| Diccionario R001–R107 | Catálogo 107 y concordancia electrónica disponibles | Mantener pendientes R049–R052, R065, R107 |
| Objetivo principal | Protocolo 09/11: proporción basal RADAR ≥4 entre V0 con 4 ítems válidos | Corregir advertencia histórica D01 en catálogo antes de congelar especificación |

**Interpretación:** un alta admitida por la API o un test de regresión correcto **no certifica elegibilidad clínica**. El preflight identifica indicios para revisión humana, pero tampoco sustituye el juicio clínico ni la comprobación de documentos originales.

## 3. Puertas de aceptación

| Puerta | Estado a 12/11/2026 | Evidencia requerida |
|---|---|---|
| A. Integridad y recorridos técnicos | Verificado en pruebas automatizadas | Logs de v0.31 y pruebas anteriores |
| B. Protocolo ↔ CRD ↔ aplicación | **Abierta** | Resolver discrepancias de criterios y diccionario; aprobación IP |
| C. Prueba guiada AP / Neumología | **Pendiente de ejecución por investigadores** | Escenarios UAT firmados, problemas y decisiones |
| D. Centros, perfiles y soporte operativo | **Parcial: simulación de roles validada** | Roles nominales y sedes autorizadas, formación, responsables |
| E. Seguridad, RGPD y entorno | **Abierta** | Plataforma institucional aprobada, evaluación de riesgos, acceso y gestión de correspondencias |
| F. Dictamen ético y autorizaciones | **No aportados** | Dictamen CEIC/CEIm favorable y autorizaciones antes de reclutamiento |

No se activa recogida con personas reales por completar una fase técnica. La fecha de enero de 2027 permanece **planificada y condicionada**.

## 4. Comprobaciones reproducibles

```bash
python -m pytest -q tests/test_*.py --disable-warnings
python tests/browser_phase30_premium.py
```

La segunda línea requiere Playwright/Chromium configurado localmente. Auditoría de una base **ficticia existente**:

```bash
python scripts/phase5_readonly_audit.py --db ruta/a/radar_uat.sqlite3 --out resultado_uat.json
```

El informe JSON indica registros con **bloqueo documental** y **revisión necesaria**; no da órdenes clínicas ni modifica fichas. No introducir datos de pacientes reales en el entorno de demostración.

## 5. Resultado de verificación automatizada

En cuatro lotes reproducibles sobre v0.31 se han superado **98/98 pruebas Python**: 23, 27, 14 y 34, sin fallos. `tests/browser_phase30_premium.py` pasó en 5 tamaños y 6 rutas. La ejecución monolítica no finalizó fiablemente; no se presenta como certificación corrida de una sola vez. Detalle en `RESULTADOS_PRUEBAS_FASE5.txt`.

## 6. Criterio real de cierre de Fase 5

Esta entrega **cierra el trabajo de preparación técnica y documental para aceptación**, no la aceptación científica institucional. Sólo después de ejecutar la guía, resolver incidencias críticas, ratificar definiciones, confirmar el entorno autorizado y recoger el visto bueno del IP y coordinación podrá emitirse un acta afirmativa, con el alcance exactamente autorizado.
