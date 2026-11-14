# RADAR-CORUÑA · v0.33 · Auditoría de captura clínica inteligente

> 107 definiciones conservadas. Se ha revisado el flujo digital sobre el diccionario v0.27 y la implementación v0.32. La clasificación siguiente no constituye ratificación científica de los campos pendientes.

## Principios de diseño

- **Una fuente, una captura**: no pedir manualmente un valor que pueda reproducirse de forma inequívoca desde datos ya registrados.
- **Mediciones nuevas, confirmación nueva**: el historial ayuda, pero no sustituye la observación correspondiente a V1 o V2.
- **No fabricar fechas, resultados o ceros**: desconocido, pendiente, no verificable y no son estados diferentes.
- **Cálculos sin edición independiente**: edad, GOLD, componentes de pauta, escala y resultados longitudinales.
- **Entidad correcta**: seguimiento es una visita; una exacerbación un episodio; Urgencias/ingresos contactos ligados al episodio.
- **No aumentar información identificativa**: no se incorpora domicilio del paciente, teléfono ni otros datos que no aparezcan en el alcance pactado.

## Cambios verificables en v0.33

1. **R034**: grado GOLD calculado instantáneamente en la ficha desde FEV1 % teórico y FEV1/FVC pos-BD, solo con obstrucción válida. Sigue siendo distinto de GOLD A/B/E y no se almacena como otro campo editable.
2. **R022, R085, R086, R064 y monoterapia/IANUS**: mostrar únicamente cuando su respuesta previa lo haga pertinente. Si ya contienen datos, siguen visibles hasta corrección explícita; no se borran al ocultar apartados.
3. **R062**: fecha real de V1/V2 vacía al crear una visita; mostrar ventana orientativa 6±1 / 12±1 meses respecto a V0, sin asignar automáticamente fecha.
4. **R029 y pauta R045–R048**: opción explícita para proponer los valores de la última visita; no copia dosis, datos IANUS, RADAR ni actuaciones. Solo llena campos aún vacíos y exige guardar conscientemente.
5. **R068**: mMRC puede sugerir una respuesta equivalente, pero se necesita pulsar **Confirmar respuesta**; las discrepancias se indican sin sobrescribir.
6. **R026**: se corrige la referencia equivocada en la documentación. R026 significa fecha de inclusión, no fecha de nacimiento.
7. **R055/R056**: IANUS no se presenta como adherencia comprobada; la ventana de consulta permanece abierta hasta definición científica.

## Decisiones que no debemos automatizar aún

- Índice de Charlson R044 sin historia y pesos suficientes; no se obtiene de cuatro comorbilidades básicas.
- Clasificación de severidad de agudización a partir de corticoides o antibióticos sin definición clínica.
- Prescripciones IANUS a partir de reglas temporales que no se hayan aprobado.
- Recomendaciones terapéuticas automáticas en función de RADAR.
- Respuestas de V1/V2 heredadas automáticamente sin nueva verificación.
- Captura de un domicilio residencial no exigido en el catálogo R001–R107.

## Inventario completo (R001–R107)

| Código | Definición | Captura idónea | Comportamiento / nota |
|:---|:---|:---|:---|
| R001 | Código del centro | Record source once | Select centre from existing code list; never type a free centre name. |
| R002 | Nombre del centro | Reference / linked record | Resolve centre name from R001; do not re-enter. |
| R003 | Fecha de activación | Auxiliary / centre register | Use authorised auxiliary/centre register; do not recapture in each patient form. |
| R004 | Uso de RADAR al cierre | Auxiliary / centre register | Use authorised auxiliary/centre register; do not recapture in each patient form. |
| R005 | Código de profesional | Auxiliary / centre register | Use authorised auxiliary/centre register; do not recapture in each patient form. |
| R006 | Rol | Auxiliary / centre register | Use authorised auxiliary/centre register; do not recapture in each patient form. |
| R007 | Fecha de formación RADAR | Auxiliary / centre register | Use authorised auxiliary/centre register; do not recapture in each patient form. |
| R008 | Utilidad percibida al cierre | Auxiliary / centre register | Use authorised auxiliary/centre register; do not recapture in each patient form. |
| R009 | Facilidad de integración | Auxiliary / centre register | Use authorised auxiliary/centre register; do not recapture in each patient form. |
| R010 | Código de cribado | Auxiliary / centre register | Screening identifier is distinct from longitudinal participant identifier; do not synthesize identity from patient name. |
| R011 | Fecha de cribado | Auxiliary / centre register | Use authorised auxiliary/centre register; do not recapture in each patient form. |
| R012 | EPOC espirométricamente confirmada | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R013 | Edad ≥40 años | Derive / read-only | Calculate ≥40 from complete birth date and V0; retain unknown until both dates exist. |
| R014 | Seguimiento habitual en centro | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R015 | Semanas desde última agudización | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R016 | Capacidad para responder escalas | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R017 | Diagnóstico alternativo excluyente | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R018 | Agudización activa | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R019 | Comorbilidad grave descompensada | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R020 | Ensayo concurrente interferente | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R021 | Consentimiento informado | Record source once | Consent status is a clinician-documented fact; never derive signature. |
| R022 | Fecha del consentimiento | Conditional / explicit | Ask for consent date only if status signed/withdrawn; preserve dates already entered until explicitly corrected. |
| R023 | Elegibilidad final | Record source once | Investigator must decide eligibility; preflight may flag but must not self-approve. |
| R024 | Motivo de no inclusión | Conditional / explicit | Removed from paper CRD; preserve legacy data but do not solicit the old free-text reason. |
| R025 | Código seudonimizado de participante | Reference / linked record | Keep stable unique pseudocode across V0–V2 and episode/contact records. |
| R026 | Fecha de inclusión | Record source once | R026 is DATE OF INCLUSION; birthDate is separate technical source. Never label DOB as R026. |
| R027 | Edad | Derive / read-only | Recalculate full-year age at V0 from DOB and R026. No editable age field. |
| R028 | Sexo registrado | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R029 | Situación tabáquica | Re-evaluate each visit | Tobacco status can change; show prior value as optional proposal requiring explicit confirmation. |
| R030 | Consumo acumulado de tabaco | Record source once | Pack-years depend on exposure history; do not infer from tobacco status alone. |
| R031 | Fecha última espirometría | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R032 | FEV1/FVC posbroncodilatador | Record source once | FEV1/FVC post-BD is a measurement, not a derived value from FEV1 % predicted. |
| R033 | FEV1 posbroncodilatador (% teórico) | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R034 | Grado GOLD de obstrucción | Derive / read-only | Calculate obstruction grade only when FEV1 % and post-BD FEV1/FVC <0.70 are present; not GOLD A/B/E. |
| R035 | Hipertensión arterial | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R036 | Cardiopatía isquémica | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R037 | Insuficiencia cardiaca | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R038 | Diabetes | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R039 | Depresión | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R040 | Ansiedad | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R041 | Apnea obstructiva del sueño | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R042 | Caquexia | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R043 | Otra comorbilidad relevante | Conditional / explicit | Only ask when relevant to the clinical event or preceding answer; preserve unknown separately from No. |
| R044 | Índice de Charlson | Record source once | Charlson requires full weighted comorbidity history; four simple checkbox comorbidities cannot calculate it. |
| R045 | Tratamiento con LAMA | Derive / read-only | Derive LAMA from the single inhaled-regimen selection and monotherapy class. |
| R046 | Tratamiento con LABA | Derive / read-only | Derive LABA from regimen; do not prompt for a second conflicting flag. |
| R047 | Tratamiento con ICS | Derive / read-only | Derive ICS from regimen; do not prompt for a second conflicting flag. |
| R048 | Medicamento de rescate prescrito | Conditional / explicit | Use one prescribed rescue-medication field; RADAR rescue USE is an independent question. |
| R049 | Oxigenoterapia domiciliaria | Conditional / explicit | Use source evaluation at indicated stage; never silently carry a previous clinical answer forward. |
| R050 | Rehabilitación respiratoria | Conditional / explicit | Use source evaluation at indicated stage; never silently carry a previous clinical answer forward. |
| R051 | Vacunación antigripal al día | Conditional / explicit | Use source evaluation at indicated stage; never silently carry a previous clinical answer forward. |
| R052 | Vacunación neumocócica al día | Conditional / explicit | Use source evaluation at indicated stage; never silently carry a previous clinical answer forward. |
| R053 | Agudizaciones EPOC último año | Derive / read-only | Derive 12m total only when BOTH moderate and severe counts exist; null must not become zero. |
| R054 | Hospitalizaciones previas por EPOC | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R055 | Método de valoración de adherencia | Conditional / explicit | IANUS verified/not-verifiable is not an adherence score. |
| R056 | Adherencia a inhaladores | Conditional / explicit | Collected prescription status is NOT verified inhaler adherence; exact IANUS window is unresolved. |
| R057 | CAT total | Re-evaluate each visit | CAT remains its own valid scale even when RADAR is incomplete. |
| R058 | mMRC | Re-evaluate each visit | mMRC remains an ordinal clinical observation; do not silently overwrite response R068. |
| R059 | CCQ | Auxiliary / centre register | Use authorised auxiliary/centre register; do not recapture in each patient form. |
| R060 | Índice BODE | Auxiliary / centre register | Use authorised auxiliary/centre register; do not recapture in each patient form. |
| R061 | Visita de estudio | Reference / linked record | Assign V0/V1/V2 from visit record; no duplicated manual visit code. |
| R062 | Fecha real de evaluación | Re-evaluate each visit | Record ACTUAL visit date; expected six/twelve-month window is only contextual guidance. |
| R063 | Estado de visita | Re-evaluate each visit | Preserve partial, complete and not-performed as different statuses. |
| R064 | Motivo de visita no realizada | Conditional / explicit | Collect reason only if visit is not performed; preserve old value when status changes pending reconciliation. |
| R065 | Código de evaluador | Reference / linked record | Use source evaluation at indicated stage; never silently carry a previous clinical answer forward. |
| R066 | RADAR · rescate >3 veces/semana | Re-evaluate each visit | RADAR rescue-use >3/week: not derived from rescue PRESCRIPTION R048. |
| R067 | RADAR · agudización últimos 3 meses | Re-evaluate each visit | RADAR exacerbation recall is 3m before EACH assessment; not equivalent to 4-week screening stability or all event counts. |
| R068 | RADAR · disnea en llano | Re-evaluate each visit | mMRC≥2 provides an equivalent suggestion; clinician explicitly confirms R068. |
| R069 | RADAR · caminar <30 min/día | Re-evaluate each visit | Use source evaluation at indicated stage; never silently carry a previous clinical answer forward. |
| R070 | Puntuación RADAR | Derive / read-only | Score 3+2+2+1 only with four valid items, including valid all-No = 0. |
| R071 | Clasificación RADAR | Derive / read-only | RADAR category 0–1 / 2–3 / ≥4 from evaluable score only. |
| R072 | Cambio RADAR 12 meses | Derive / read-only | V2 minus V0 only when both RADAR scores evaluable; never impute missing as zero. |
| R073 | Cambio CAT 12 meses | Derive / read-only | V2 minus V0 only when both CAT valid. |
| R074 | Código único de evento | Reference / linked record | Assign next episode number per participant on server; different participants can both have 01. |
| R075 | Fecha del evento | Reference / linked record | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R076 | Tipo de evento | Record source once | Clinical episode type must not be confused with an emergency contact. |
| R077 | Relación con EPOC | Record source once | COPD attribution is independent of episode type, source, and severity. |
| R078 | Gravedad agudización | Conditional / explicit | Show severity only for actual exacerbation; no auto-diagnosis from steroid/antibiotic therapy. |
| R079 | Corticoides sistémicos por agudización | Conditional / explicit | Steroid treatment does not automatically establish severity. |
| R080 | Antibióticos por agudización | Conditional / explicit | Antibiotics do not automatically establish COPD attribution. |
| R081 | Urgencias por EPOC | Reference / linked record | Link ED contact to same episode (R074) when appropriate; do not create another exacerbation. |
| R082 | Ingreso hospitalario por EPOC | Reference / linked record | Link hospital admission to same episode (R074); distinguish no, not recorded and not verifiable. |
| R083 | Fuente de constatación | Record source once | Record observed value once in the proper entity; avoid a parallel copy elsewhere. |
| R084 | Situación vital | Record source once | Vital status documented at closure; not inferred from absence of follow-up. |
| R085 | Fecha de fallecimiento | Conditional / explicit | Ask for date only when status deceased; previously recorded date stays visible until corrected. |
| R086 | Causa de fallecimiento | Conditional / explicit | Cause only when status deceased; no inference from last COPD episode. |
| R087 | N.º agudizaciones entre visitas | Derive / read-only | Count distinct COPD exacerbation episodes per defined interval, not urgent/hospital contacts. |
| R088 | N.º urgencias por EPOC entre visitas | Derive / read-only | Count COPD-related emergency contacts in interval; distinguish visits from episodes. |
| R089 | N.º ingresos por EPOC entre visitas | Derive / read-only | Count COPD-related hospital contacts in interval; do not double count exacerbations. |
| R090 | Revisión de técnica inhalatoria | Conditional / explicit | Use source evaluation at indicated stage; never silently carry a previous clinical answer forward. |
| R091 | Educación sobre adherencia | Conditional / explicit | Use source evaluation at indicated stage; never silently carry a previous clinical answer forward. |
| R092 | Consejo de abandono tabáquico | Conditional / explicit | Use source evaluation at indicated stage; never silently carry a previous clinical answer forward. |
| R093 | Consejo de actividad física | Conditional / explicit | Use source evaluation at indicated stage; never silently carry a previous clinical answer forward. |
| R094 | Revisión de vacunación | Conditional / explicit | Use source evaluation at indicated stage; never silently carry a previous clinical answer forward. |
| R095 | Revisión de comorbilidades | Conditional / explicit | Use source evaluation at indicated stage; never silently carry a previous clinical answer forward. |
| R096 | Valoración de rehabilitación | Conditional / explicit | Use source evaluation at indicated stage; never silently carry a previous clinical answer forward. |
| R097 | Cambio de tratamiento inhalado | Conditional / explicit | Treatment change is an ACTUAL documented action, never inferred from changing regimen fields alone. |
| R098 | Derivación a Neumología | Conditional / explicit | Use source evaluation at indicated stage; never silently carry a previous clinical answer forward. |
| R099 | Plan de actuación documentado | Conditional / explicit | Plan documented needs explicit confirmation; do not infer from score/category. |
| R100 | Nota de actuación estandarizada | Conditional / explicit | Use source evaluation at indicated stage; never silently carry a previous clinical answer forward. |
| R101 | Consultas de EPOC elegibles para RADAR | Auxiliary / centre register | Centre-month eligible visits require a defined eligible-consultation denominator; no implicit all-attendance count. |
| R102 | Consultas con RADAR completo | Auxiliary / centre register | Centre-month RADAR completions must use a consistent consultation definition. |
| R103 | Duración de aplicación RADAR | Conditional / explicit | Do not fabricate completion duration from UI time unless approved instrumentation exists. |
| R104 | Centros con implantación | Derive / read-only | Count centers with verified activation date, not interested centers. |
| R105 | Profesionales formados | Derive / read-only | Count professionals with documented training date, not invited professionals. |
| R106 | Retención a 12 meses | Derive / read-only | V2 retention denominator must be fixed scientifically; do not include participants whose V2 is not yet due. |
| R107 | Razón de dato ausente | Conditional / explicit | Capture explicit reason for a truly missing measurement; never replace null with No or zero. |

## Decisiones científicas aún abiertas

Los códigos con definición o alcance pendiente según el registro base: R024, R043, R044, R049, R050, R051, R052, R055, R056, R059, R060, R100, R101, R102, R103, R106.

La recomendación de interfaz no sustituye una revisión clínica; ningún campo pendiente ha recibido un nuevo valor predeterminado en v0.33.

## Identidad semántica de campos auxiliares

- `birthDate`: fecha completa de nacimiento, dato de apoyo para edad; **no corresponde a R026**.
- `lastCopdReviewDate`: prueba de seguimiento AP previa a V0, sin crear un nuevo código R.
- Las derivaciones R013, R027, R034, R045–R047, R053, R070–R073 y R087–R089 sólo existen si sus fuentes son suficientes.
