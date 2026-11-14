# RADAR-CORUÑA · Concordancia documental y electrónica v0.27

Referencia: CRD clínico consolidado, 4 páginas (09/11/2026); catálogo original R001–R107.

**107 variables catalogadas. 85 identificadores referenciados explícita o implícitamente en el CRD de cuatro páginas.**

Los restantes códigos pertenecen a gestión del estudio, mediciones adicionales, derivadas o al antiguo R024 retirado del formulario impreso.

## Estado de implementación por variable

| ID | Variable técnica | Papel | Implementación | Origen |
|---|---|---|---|---|
| R001 | `center_code` | Sí | Campo principal | Patient.center |
| R002 | `center_name` | No | Campo principal | CENTRES.name |
| R003 | `center_start_date` | No | Registro auxiliar | phase14_records.centre.center_start_date |
| R004 | `center_end_use` | No | Registro auxiliar | phase14_records.centre.center_end_use |
| R005 | `clinician_code` | Sí | Registro auxiliar | phase14_records.professional.key |
| R006 | `clinician_role` | No | Registro auxiliar | phase14_records.professional.clinician_role |
| R007 | `training_date` | No | Registro auxiliar | phase14_records.professional.training_date |
| R008 | `survey_utilidad` | No | Registro auxiliar | phase14_records.professional.survey_utilidad |
| R009 | `survey_factibilidad` | No | Registro auxiliar | phase14_records.professional.survey_factibilidad |
| R010 | `screen_code` | Sí | Registro auxiliar | phase14_records.screening.screen_code |
| R011 | `screen_date` | Sí | Registro auxiliar | phase14_records.screening.screen_date |
| R012 | `confirmed_copd` | Sí | Campo principal | Patient.copd |
| R013 | `age_eligible` | Sí | Cálculo | Patient.age >= 40; no decisión automática |
| R014 | `regular_ap_followup` | Sí | Campo principal | Patient.regular |
| R015 | `stable_weeks` | Sí | Campo principal | Patient.weeks |
| R016 | `can_answer` | Sí | Campo principal | Patient.capacity |
| R017 | `alternative_diagnosis` | Sí | Campo principal | Patient.alternativeDiagnosis |
| R018 | `active_exacerbation` | Sí | Campo principal | Patient.activeExacerb |
| R019 | `serious_decompensation` | Sí | Campo principal | Patient.seriousDecompensation |
| R020 | `interfering_trial` | Sí | Campo principal | Patient.interferingTrial |
| R021 | `consent_status` | Sí | Campo principal | Patient.consent |
| R022 | `consent_date` | Sí | Campo principal | Patient.consentDate |
| R023 | `eligible_final` | Sí | Campo principal | Patient.eligibilityDecision (decisión del investigador) |
| R024 | `screen_failure_reason` | No | Conservado por compatibilidad · fuera del CRD | Patient.screenFailureReason |
| R025 | `participant_code` | Sí | Campo principal | Patient.id |
| R026 | `enrolment_date` | Sí | Campo principal | Patient.enrolDate |
| R027 | `age_years` | Sí | Campo principal | Patient.age |
| R028 | `sex_recorded` | Sí | Campo principal | Patient.sex |
| R029 | `smoking_status` | Sí | Campo principal | Patient.smoking |
| R030 | `pack_years` | Sí | Campo principal | Patient.packs |
| R031 | `spiro_date` | Sí | Campo principal | Patient.spiroDate |
| R032 | `fev1_fvc_postbd` | Sí | Campo principal | Patient.ratio |
| R033 | `fev1_pct_pred` | Sí | Campo principal | Patient.fev1 |
| R034 | `gold_airflow_grade` | Sí | Cálculo | FEV1 % predicho y cociente pos-BD <0.70, GOLD 1-4; revisión clínica |
| R035 | `comorb_htn` | Sí | Campo principal | Patient.comorbHtn |
| R036 | `comorb_ihd` | Sí | CRD complementario | study_observations.comorb_ihd |
| R037 | `comorb_hf` | Sí | Campo principal | Patient.comorbHf |
| R038 | `comorb_diabetes` | Sí | Campo principal | Patient.comorbDm |
| R039 | `comorb_depression` | Sí | CRD complementario | study_observations.comorb_depression |
| R040 | `comorb_anxiety` | Sí | CRD complementario | study_observations.comorb_anxiety |
| R041 | `comorb_osa` | Sí | Campo principal | Patient.comorbOsa |
| R042 | `comorb_cachexia` | Sí | CRD complementario | study_observations.comorb_cachexia |
| R043 | `other_comorb` | Sí | Campo principal | Patient.otherComorbidities |
| R044 | `charlson_index` | Sí | Campo principal | Patient.charlson |
| R045 | `inhaler_lama` | Sí | Campo principal · verificar mapeo | Visit.lama |
| R046 | `inhaler_laba` | Sí | Campo principal · verificar mapeo | Visit.laba |
| R047 | `inhaler_ics` | Sí | Campo principal · verificar mapeo | Visit.ics |
| R048 | `rescue_med_current` | Sí | Campo principal | Visit.rescuePrescription; legacy study_observations:rescue_med_current |
| R049 | `longterm_oxygen` | Sí | CRD complementario | study_observations.longterm_oxygen |
| R050 | `pulm_rehab` | Sí | CRD complementario | study_observations.pulm_rehab |
| R051 | `flu_vax_up_to_date` | Sí | Campo principal · solo V0 | Patient.fluVaccination (V0; V1/V2 documental pendiente) |
| R052 | `pneumo_vax_up_to_date` | Sí | Campo principal · solo V0 | Patient.pneumococcalVaccination (V0; V1/V2 documental pendiente) |
| R053 | `prior_exacerb_12m` | Sí | Campo principal · verificar mapeo | Patient.priorEx |
| R054 | `prior_hosp_12m` | Sí | Campo principal | Patient.priorHosp |
| R055 | `adherence_method` | Sí | Campo principal · significado actualizado | Visit.ianusVerified; legacy study_observations:adherence_method (otro significado) |
| R056 | `adherence_level` | Sí | Campo principal · significado actualizado | Visit.ianusCollected; legacy study_observations:adherence_level (otro significado) |
| R057 | `cat_score` | Sí | Campo principal | Visit.cat |
| R058 | `mmrc_grade` | Sí | Campo principal | Visit.mmrc |
| R059 | `ccq_score` | No | Registro auxiliar | phase14_records.visit.ccq_score |
| R060 | `bode_score` | No | Registro auxiliar | phase14_records.baseline.bode_score |
| R061 | `visit_code` | No | Campo principal | Visit.type |
| R062 | `visit_date` | Sí | Campo principal | Visit.date |
| R063 | `visit_status` | Sí | Campo principal | Visit.status |
| R064 | `visit_missing_reason` | Sí | Campo principal | Visit.reason |
| R065 | `assessor_code` | Sí | Campo principal · verificar mapeo | Visit.assessorCode |
| R066 | `radar_rescue` | Sí | Campo principal | Visit.rescue |
| R067 | `radar_exacerb` | Sí | Campo principal | Visit.exacerb |
| R068 | `radar_dyspnea` | Sí | Campo principal | Visit.dyspnea |
| R069 | `radar_activity` | Sí | Campo principal | Visit.activity |
| R070 | `radar_total` | Sí | Cálculo | Score(3,2,2,1), solo cuatro respuestas completas |
| R071 | `radar_class` | Sí | Cálculo | 0–1 / 2–3 / >=4, solo RADAR completo |
| R072 | `change_radar_v0_v2` | No | Cálculo | Diferencia V2-V0 en pareja completa |
| R073 | `change_cat_v0_v2` | No | Cálculo | Diferencia CAT V2-V0 en pareja con ambos CAT |
| R074 | `event_code` | Sí | Campo principal | Episode.episodeNo (R074); ID técnico: Episode.id |
| R075 | `event_date` | Sí | Campo principal | Episode.date |
| R076 | `event_type` | Sí | Campo principal · verificar mapeo | Tipo obtenido de episodio, urgencias, ingreso o estado vital |
| R077 | `event_copd_related` | Sí | Campo principal | Episode.copd |
| R078 | `exacerbation_severity` | Sí | Campo principal | Episode.severity |
| R079 | `exacerb_treat_steroid` | Sí | Campo principal | Episode.steroids |
| R080 | `exacerb_treat_antibiotic` | Sí | Campo principal | Episode.antibiotics |
| R081 | `emergency_attendance` | Sí | Campo principal | Episode.emergencyStatus (R081) y emergencyDate; contactos separados |
| R082 | `hospital_admission` | Sí | Campo principal | Episode.admissionStatus (R082) y admissionDate; contactos separados |
| R083 | `event_source` | Sí | Campo principal | Episode.source |
| R084 | `vital_status` | Sí | Campo principal | Patient.vitalStatus |
| R085 | `death_date` | Sí | Campo principal | Patient.deathDate |
| R086 | `death_cause_class` | Sí | Campo principal | Patient.deathCause |
| R087 | `interval_exacerbations` | No | Cálculo | Episodios EPOC por intervalos observados entre visitas |
| R088 | `interval_urgent` | No | Cálculo | Urgencias EPOC entre visitas documentadas |
| R089 | `interval_admissions` | No | Cálculo | Contactos de ingreso EPOC por intervalos observados |
| R090 | `action_inhaler_tech` | Sí | CRD complementario | study_observations.action_inhaler_tech |
| R091 | `action_adherence_counsel` | Sí | CRD complementario | study_observations.action_adherence_counsel |
| R092 | `action_smoking_counsel` | Sí | CRD complementario | study_observations.action_smoking_counsel |
| R093 | `action_activity_counsel` | Sí | CRD complementario | study_observations.action_activity_counsel |
| R094 | `action_vaccine_review` | Sí | CRD complementario | study_observations.action_vaccine_review |
| R095 | `action_comorb_review` | Sí | CRD complementario | study_observations.action_comorb_review |
| R096 | `action_pulm_rehab_offer` | Sí | CRD complementario | study_observations.action_pulm_rehab_offer |
| R097 | `action_inhaled_change` | Sí | CRD complementario | study_observations.action_inhaled_change |
| R098 | `action_specialty_referral` | Sí | CRD complementario | study_observations.action_specialty_referral |
| R099 | `action_plan_documented` | Sí | CRD complementario | study_observations.action_plan_documented |
| R100 | `clinical_notes_structured` | No | Registro auxiliar | phase14_records.visit.clinical_notes_structured |
| R101 | `eligible_copd_visits` | No | Registro auxiliar | phase14_records.implementation.eligible_copd_visits |
| R102 | `visits_with_radar` | No | Registro auxiliar | phase14_records.implementation.visits_with_radar |
| R103 | `assessment_seconds` | Sí | CRD complementario | study_observations.assessment_seconds |
| R104 | `centers_activated` | No | Cálculo | Centros con fecha de activación documentada |
| R105 | `professionals_trained` | No | Cálculo | Profesionales con fecha de formación documentada |
| R106 | `retention_v2` | No | Cálculo | V2 registradas / participantes con V2 vencida según fecha de corte |
| R107 | `data_missing_reason` | Sí | Captura parcial · conciliación pendiente | missing_data:participant/visit_type/field_code/reason |

## Cuestiones identificadas para conciliación

**R016:** Ayuda se registra como opción distinta de Sí/No.

**R024:** Campo heredado en Patient.screenFailureReason: eliminado del CRD en papel por indicación clínica; no recapturar.

**R043:** Texto libre de otras comorbilidades; si el catálogo controlado se aprueba, definir codificación antes de análisis.

**R045:** LAMA/LABA/ICS se derivan de la pauta inhalada de V0/V1/V2; en monoterapia se selecciona la clase.

**R046:** Véase R045: régimen combinado y bandera individual compatibles.

**R047:** Véase R045: régimen combinado y bandera individual compatibles.

**R048:** Entrada principal en Visit.rescuePrescription; medición complementaria heredada no debe duplicarse.

**R049:** El CRD impreso lo solicita en basal; el catálogo histórico admite seguimiento. Confirmar capturas posteriores.

**R050:** El CRD impreso lo solicita en basal; el catálogo histórico admite seguimiento. Confirmar capturas posteriores.

**R051:** Captura integrada en V0; el catálogo anterior también menciona V1/V2, pendiente de ratificar.

**R052:** Captura integrada en V0; el catálogo anterior también menciona V1/V2, pendiente de ratificar.

**R053:** Las agudizaciones moderadas y graves se registran por separado; Patient.priorEx se deriva de ambos cuando se informan.

**R055:** En el CRD vigente significa consulta IANUS verificada/no verificable. La variable antigua adherence_method NO es equivalente.

**R056:** En el CRD vigente significa últimas recetas recogidas Sí/No/NV; período exacto pendiente. La variable antigua adherence_level NO es equivalente.

**R065:** Código del evaluador de cada visita registrado en Visit.assessorCode. Revisar conexión con catálogo profesional R005.

**R076:** El tipo de episodio se registra en Episode.kind; el catálogo original puede describirlo como derivado.

**R083:** Fuente por episodio; lista validada de valores.

**R090:** Actuación por visita en el CRD complementario. No se sustituye automáticamente por el campo histórico de Visit.

**R099:** La actuación plan documentado (Sí/No/NA/NC) es distinta del texto Visit.action.

**R103:** Duración en segundos, opcional y vinculada a visita.

**R107:** Motivo de ausencia conservado en tabla missing_data; el CRD impreso usa NR/ND/NP/NA y las categorías digitales requieren conciliación.

## Verificación

La clasificación distingue los formularios principales, los registros complementarios, las métricas derivadas y los registros auxiliares. No transforma automáticamente registros antiguos en valores nuevos. La implementación sigue teniendo cuestiones documentadas, incluidas las definiciones IANUS y las reglas longitudinales de vacunación/oxigenoterapia/rehabilitación.