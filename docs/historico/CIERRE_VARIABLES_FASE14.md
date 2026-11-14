# RADAR-CORUÑA · Cierre de brechas de variables · Fase 14

**Objeto:** dar una ubicación operativa a las 28 variables del catálogo que carecían de implementación en la fase 13, respetando su carácter propuesto, exploratorio u operativo.

| Bloque | Variables completadas | Localización |
|---|---|---|
| Centro | `center_start_date`, `center_end_use` | Formulario centro y CENTROS_V14 |
| Profesionales | `clinician_code`, `clinician_role`, `training_date`, `survey_utilidad`, `survey_factibilidad` | Registro de profesionales y PROFESIONALES_V14 |
| Cribado | `screen_code`, `screen_date`, `alternative_diagnosis`, `serious_decompensation`, `interfering_trial`, `consent_date` | Registro complementario por participante y CRIBADO_V14 |
| Basal y medidas opcionales | `other_comorb`, `charlson_index`, `flu_vax_up_to_date`, `pneumo_vax_up_to_date`, `ccq_score`, `bode_score` | Ficha basal y BASAL_V14; vacunación/CCQ también por visita |
| Visita | `assessor_code`, `clinical_notes_structured` | Ficha de visita complementaria y VISITA_ADICIONAL_V14 |
| Eventos | `event_type`, `interval_urgent` | EVENTOS_CLASIF_V14; RESULTADOS_INTERVALO_V13 |
| Implantación | `eligible_copd_visits`, `visits_with_radar`, `centers_activated`, `professionals_trained`, `retention_v2` | IMPLANTACION_MENSUAL_V14 e INDICADORES_IMPL_V14 |

**Criterios:** las variables directamente observadas no se infieren de respuestas faltantes. Un CAT, CCQ, mMRC, número de consultas o score RADAR igual a cero es un valor válido cuando se ha registrado. Una agudización con contacto en Urgencias no pasa a representar dos agudizaciones. El cociente de consultas con RADAR se calcula solo sobre meses-centro con ambos recuentos documentados; si el denominador es 0, el porcentaje figura como no estimable.

**Pendiente de la revisión de los investigadores:** definición definitiva de los criterios de inclusión, escalas exploratorias y adherencia, calendario, denominadores asistenciales, definiciones de eventos y análisis científico. Véase **DECISIONES_20** en el libro descargable.
