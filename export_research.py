"""Portable, dependency-free OOXML research exports for the synthetic RADAR-CORUÑA pilot.
This Excel file is a read-only snapshot, not the study database.
"""
from __future__ import annotations
import io
import re
import json
import zipfile
from datetime import datetime, timezone
from xml.sax.saxutils import escape, quoteattr

NAVY='#142C43'; TEAL='#147B80'; PALE='#EAF4F4'; LIGHT='#F3F6F8'
WHITE='#FFFFFF'; INK='#213547'; MUTED='#617184'; WARN='#A45A16'; DANGER='#AC3F3F'

SPEC={
 'PARTICIPANTES':[
  ('id','ID seudónimo demo','Código sintético SIM-*'),('center','Centro','Código de centro'),('status','Estado','cribado / incluido'),
  ('age','Edad','años'),('sex','Sexo','Categoría'),('copd','EPOC confirmada','si/no/nc'),('regular','Seguimiento en AP','si/no/nc'),
  ('weeks','Estabilidad','Semanas desde agudización'),('capacity','Capacidad','si/no/nc'),('exclusion','Exclusión','si/no/nc'),
  ('consent','Consentimiento','si/no/nc'),('enrolDate','R026 · Fecha de inclusión/V0','aaaa-mm-dd'),('smoking','Tabaquismo','actual/ex/nunca/nc'),
  ('packs','Paquetes-año','paquetes-año'),('spiroDate','Fecha espirometría','aaaa-mm-dd'),('ratio','FEV1/FVC post-BD','cociente'),
  ('fev1','FEV1 predicho','%'),('priorEx','Agudizaciones previas','número'),('priorHosp','Ingresos previos','número'),
  ('comorbHtn','Hipertensión','si/no/nc'),('comorbHf','Insuficiencia cardíaca','si/no/nc'),('comorbDm','Diabetes','si/no/nc'),
  ('comorbOsa','SAOS','si/no/nc'),('created','Registro inicial','aaaa-mm-dd'),('rev','Versión','número'),
  ('created_by','Creado por','usuario demo'),('updated_at','Actualización UTC','ISO-8601'),
  ('birthDate','Fecha nacimiento ficticia · soporte edad (NO R026)','AAAA-MM-DD (simulación)'),('priorExModerate','Agudizaciones moderadas 12m','n'),('priorExSevere','Agudizaciones graves 12m','n'),
  ('alternativeDiagnosis','R017 · Diagnóstico alternativo','Sí/No/NC'),('seriousDecompensation','R019 · Comorbilidad descompensada','Sí/No/NC'),('interferingTrial','R020 · Ensayo interferente','Sí/No/NC'),
  ('consentDate','R022 · Fecha consentimiento','AAAA-MM-DD'),('lastCopdReviewDate','Fecha última revisión EPOC AP','AAAA-MM-DD'),('otherComorbidities','R043 · Otras comorbilidades','Texto'),('charlson','R044 · Charlson','n'),
  ('fluVaccination','R051 · Vacuna gripe V0','Sí/No/NC'),('pneumococcalVaccination','R052 · Vacuna neumococo V0','Sí/No/NC'),('lastInformationDate','Fecha última información vital','AAAA-MM-DD')
 ],
 'VISITAS':[
  ('id','ID visita','Código'),('patient','ID participante','Código sintético'),('center','Centro','Código de centro'),
  ('type','Visita','V0/V1/V2'),('date','Fecha','aaaa-mm-dd'),('status','Estado','parcial/completa/no_realizada'),
  ('cat','CAT','0 a 40'),('mmrc','mMRC','0 a 4'),('rescue','Rescate >3/semana','si/no/nc'),
  ('exacerb','Agudización 3 meses','si/no/nc'),('dyspnea','Disnea mMRC ≥2','si/no/nc'),
  ('activity','Actividad <30 min/día','si/no/nc'),('radar_score','RADAR · puntos','Cálculo 3+2+2+1'),
  ('radar_class','RADAR · control','Cálculo a partir del total'),('smoking','Tabaquismo','Categoría'),
  ('adherence','Adherencia heredada (NO usar como R056)','Campo histórico; NO equivale a recogida IANUS'),('action','Actuación','Categoría de actuación'),
  ('inhaler','Técnica inhalatoria','si/no/nc'),('education','Educación','si/no/nc'),('referral','Derivación','si/no/nc'),
  ('lama','Tratamiento LAMA','si/no/nc'),('laba','Tratamiento LABA','si/no/nc'),('ics','Tratamiento CI','si/no/nc'),
  ('reason','Motivo no realizada','Categoría'),('rev','Versión','número'),
  ('inhaledRegimen','Pauta inhalada 1–5','Pedro, categorías CRD'),('monotherapyClass','Monoterapia LAMA/LABA','Subtipo de opción 2'),
  ('roflumilast','Roflumilast opción 6','Sí/No/NC'),('azithromycin','Azitromicina opción 7','Sí/No/NC'),
  ('rescuePrescription','Tratamiento de rescate prescrito','R048; distinto de uso RADAR'),('medicationDetails','Fármaco, dosis y pauta','Datos de simulación'),
  ('ianusVerified','IANUS consultado R055','Sí/No'),('ianusCollected','Prescripciones recogidas R056','Sí/No/NV'),('ianusCheckedAt','Fecha consulta IANUS','AAAA-MM-DD'),('assessorCode','R065 · Código evaluador','Código de profesional')
 ],
 'EPISODIOS':[
  ('id','ID episodio interno','Identificador técnico'),('patient','ID participante','Código sintético'),('center','Centro','Código de centro'),
  ('episodeNo','R074 · N.º episodio','Consecutivo por participante'),('kind','R076 · Tipo','agudizacion/otro'),
  ('date','Fecha','aaaa-mm-dd'),('severity','Gravedad','moderada/grave/indeterminada/no_aplica'),('copd','Relacionado con EPOC','si/no/nc'),
  ('steroids','Corticoides','si/no/nc'),('antibiotics','Antibióticos','si/no/nc'),('source','Fuente','HCE/paciente/informe/otro')
 ],
 'CONTACTOS':[
  ('id','ID contacto','Código'),('patient','ID participante','Código sintético'),('center','Centro','Código de centro'),
  ('date','Fecha','aaaa-mm-dd'),('type','Tipo','urgencias/ingreso/otro'),('event','Episodio relacionado','ID episodio o vacío'),
  ('copd','Relacionado con EPOC','si/no/nc'),('source','Fuente','HCE/paciente/informe/otro'),
  ('dischargeDate','Fecha de alta','aaaa-mm-dd'),('careCentre','Centro asistencial','Sólo ficticio'),
  ('relatedEpisodeNo','R074 · N.º episodio vinculado','Derivado por vínculo, no código clínico')
 ],
 'TRAZABILIDAD':[
  ('id','ID movimiento','Secuencial'),('happened_at','Fecha/hora UTC','ISO-8601'),('username','Usuario demo','Cuenta'),
  ('role','Rol','admin/investigator/reviewer'),('centre','Centro','Código'),('verb','Operación','CREATE/UPDATE/EXPORT'),
  ('kind','Entidad','participant/visit/episode/contact/export'),('object_id','ID del registro','ID'),
  ('participant_id','Participante','Código sintético'),('revision_from','Versión anterior','Número'),
  ('revision_to','Versión posterior','Número'),('field_count','Campos modificados','Número'),
  ('reason','Motivo','Motivo de modificación o descarga'),('record_digest','Huella SHA-256','Huella diagnóstica, no firma'),
 ],
 'CAMBIOS_CAMPO':[
  ('id','ID detalle','Secuencial'),('audit_id','ID movimiento','Enlace a TRAZABILIDAD'),
  ('happened_at','Fecha/hora UTC','ISO-8601'),('username','Usuario demo','Cuenta'),
  ('centre','Centro','Código'),('kind','Entidad','patient/visit/episode/contact'),
  ('object_id','ID del registro','Código'),('participant_id','ID participante','Código sintético'),
  ('verb','Operación','CREATE / UPDATE'),('reason','Motivo','Texto declarativo'),
  ('revision_from','Versión anterior','Número'),('revision_to','Versión nueva','Número'),
  ('field_name','Variable','Nombre técnico'),('prior_value','Valor anterior (JSON)','Sin valor para altas'),
  ('new_value','Valor nuevo (JSON)','Preserva tipo y nulos')
 ],
 'CRD_MEDICIONES':[
  ('participant','Participante','Código sintético'),('visit_type','Visita','V0/V1/V2'),
  ('variable_code','Variable','Código técnico versionado'),('variable_label','Definición','Etiqueta clínica'),
  ('value','Valor actual','Categoría validada o número'),('rev','Versión','Versión de medición'),
  ('username','Registrado por','Cuenta ficticia'),('updated_at','Actualizado UTC','Timestamp'),
  ('spec_version','Versión del CRD','Versión de catálogo')
 ],
 'CATALOGO_107':[
  ('id','ID de estudio','Identificador estable'),('code','Código de variable','Código técnico'),
  ('label','Etiqueta','Nombre clínico'),('entity','Área','Ubicación conceptual'),
  ('priority_proposed','Prioridad propuesta','Núcleo/condicional/derivada/operativa/exploratoria'),
  ('type','Tipo de medición','Tipo lógico'),('values','Valores / unidades','Rango o catálogo'),
  ('definition','Definición operativa','Interpretación propuesta'),('moment','Momento','Visita o evento'),
  ('analysis','Utilidad analítica','Justificación'),('evidence','Fuente','Protocolo / propuesta técnica'),
  ('implementation','Estado técnico','Formulario / CRD ampliado / pendiente'),
  ('pending','Cuestión pendiente','Revisión o validación requerida'),
  ('validator','Revisión responsable','IP/clinician/statistician'),('approved','Aprobada','False hasta firma')
 ],
 'DECISIONES_20':[
  ('id','ID','Código'),('priority','Prioridad','Urgencia'),('severity','Criticidad','Nivel'),
  ('topic','Tema','Tema metodológico'),('question','Definición pendiente','Pregunta al investigador'),
  ('recommendation','Propuesta de trabajo','No equivale a aprobación'),
  ('reviewer','Responsable propuesto','IP/estadística/neumología'),('milestone','Antes de','Hito'),
  ('status','Estado','Pendiente por defecto')
 ],
 'PUERTAS_DE_USO':[('id','Código','Identificador'),('name','Condición','Control de entrada'),('status','Estado','Pendiente / No verificado / No implementado'),('requirement','Validación requerida','Requiere evidencia independiente')],
 'REVISION_CIENTIFICA':[('rule','Regla','Identificador de validación'),('severity','Prioridad','Prioritaria / Revisar / Informativa'),('patient','Participante','Código'),('item','Etapa','Visita u objeto'),('issue','Observación','Chequeo técnico, no decisión clínica'),('suggestion','Actuación propuesta','Requiere revisión del investigador')],
 'COBERTURA_VISITAS':[('patient','Participante','Código'),('visit','Visita','V0/V1/V2'),('date','Fecha','aaaa-mm-dd'),('visit_status','Estado visita','Parcial / Completa / No realizada'),('fields_present','Campos presentes','Núcleo propuesto'),('fields_expected','Campos esperados','Núcleo propuesto'),('completeness_pct','Completitud (%)','Solo control de campos, no aprobación'),('missing_fields','Campos pendientes','Vacío ≠ negativo')],
 'FLUJO_CRD_V11':[
  ('patient','Participante','Código sintético'),('centre','Centro','Ámbito autorizado'),('stage','Visita prevista','V0/V1/V2'),
  ('visit_status','Estado','Registrada / No registrada / No realizada'),('visit_date','Fecha real','AAAA-MM-DD'),
  ('core_present','Núcleo registrado','Siete campos propuestos'),('core_expected','Núcleo esperado','No aplicable a visitas ausentes'),
  ('core_pct','Porcentaje núcleo','No significa aprobación'),('core_missing','Campos núcleo ausentes','Listado'),
  ('baseline_present','Basales registrados','V0 únicamente'),('baseline_expected','Basales esperados','V0 según tabaquismo'),
  ('baseline_missing','Basales pendientes','Listado'),('alerts','Alertas de revisión','No excluyen pacientes'),
  ('episode_count','Episodios de seguimiento','Recuento sin deduplicación clínica'),
  ('contact_count','Contactos asistenciales','Recuento independiente de episodios')
 ],
 'GUIA_CRD_V11':[
  ('stage','Momento','V0 / V0-V1-V2'),('code','Campo técnico','Nombre estable'),
  ('label','Variable / campo','Descripción propuesta'),('source','Entidad fuente','paciente / visita / crd'),
  ('section','Sección','Cribado, núcleo, tratamiento u otras'),
  ('priority','Prioridad propuesta','No equivale a obligatoriedad aprobada'),
  ('approval','Aprobación científica','Pendiente por defecto')
 ],
 'CALIDAD':[
  ('severity','Prioridad','Revisar/Advertencia'),('patient','Participante','Código'),('item','Objeto','Visita / registro'),
  ('issue','Incidencia','Motivo técnico'),('suggestion','Revisión propuesta','Acción recomendada')
 ]
}

TITLES={'PARTICIPANTES':'Cohorte y datos basales','VISITAS':'Visitas longitudinales y puntuación RADAR',
        'EPISODIOS':'Agudizaciones clínicas','CONTACTOS':'Contactos sanitarios',
        'TRAZABILIDAD':'Historial de actividad y exportaciones','CAMBIOS_CAMPO':'Detalle de modificaciones por variable','CRD_MEDICIONES':'Mediciones clínicas adicionales por visita','CATALOGO_107':'Diccionario científico versionado · 107 campos','DECISIONES_20':'Decisiones científicas y de implementación pendientes','CALIDAD':'Observaciones de integridad','PUERTAS_DE_USO':'Requisitos para autorización de uso clínico','REVISION_CIENTIFICA':'Revisión técnica y científica de los registros','COBERTURA_VISITAS':'Completitud del núcleo RADAR por visita','FLUJO_CRD_V11':'Estado del CRD por participante y visita','GUIA_CRD_V11':'Guía técnica propuesta para V0 / V1 / V2'}


# Phase 12: exact data-availability inventory and analytical denominators.
SPEC.update({
 'ANALISIS_V12':[
   ('group','Bloque','Ámbito'),('indicator','Indicador','Definición del análisis descriptivo'),
   ('numerator','Numerador','Recuento observable, o vacío'),('denominator','Denominador','Solo si existe'),
   ('value','Valor','No estimable si vacío'),('unit','Unidad','%, n o puntos'),
   ('interpretation','Alcance y advertencias','No equivale a validación científica')],
 'PAREJAS_V12':[
   ('participant','Participante','Código SIM'),('center','Centro','Ámbito'),
   ('date_v0','Fecha basal','V0'),('date_v2','Fecha final','V2'),
   ('radar_v0','RADAR V0','0–8'),('radar_v2','RADAR V2','0–8'),
   ('delta_radar','Diferencia RADAR','V2 menos V0'),
   ('control_v0','Control V0','Categoría inicial'),('control_v2','Control V2','Categoría final'),
   ('cat_v0','CAT V0','0–40'),('cat_v2','CAT V2','0–40'),
   ('delta_cat','Diferencia CAT','V2 menos V0, solo datos pareados'),
   ('interpretation','Cautela','No inferir causalidad')],
 'BRECHAS_CRD_V12':[
   ('id','ID','ID del catálogo'),('code','Variable','Código científico'),
   ('label','Nombre','Variable propuesta'),('entity','Área','Entidad científica'),
   ('priority','Prioridad','Priorización candidata'),
   ('status','Cobertura técnica','Capturable / CRD / derivada / no implementada'),
   ('location','Origen real','Campo de almacenamiento o cálculo'),
   ('evidence','Fundamento','Protocolo / propuesta técnica'),
   ('pending','Pendiente científico','Necesita decisión o aprobación'),
   ('approver','Responsable de validar','IP / profesional / estadística')],
})
TITLES.update({
 'ANALISIS_V12':'Indicadores descriptivos y denominadores explícitos',
 'PAREJAS_V12':'Participantes con RADAR V0 y V2 completo',
 'BRECHAS_CRD_V12':'Cobertura técnica real de las 107 variables candidatas',
})

# Phase 16: analysis-ready, non-duplicative datasets and consultation worklist.
SPEC.update({
 'ANALISIS_LONG_V16':[
  ('participant','Participante','Código sintético'),('centre','Centro','Ámbito'),('visit','Etapa','V0/V1/V2'),
  ('date','Fecha visita','AAAA-MM-DD'),('visit_status','Estado de visita','Completa / parcial / no realizada'),
  ('radar_complete','RADAR completo','Sí solo con 4 respuestas si/no'),
  ('rescue','Rescate >3/semana','si/no/sin registrar'),('exacerb','Agudización 3 meses','si/no/sin registrar'),
  ('dyspnea','Disnea','si/no/sin registrar'),('activity','Actividad','si/no/sin registrar'),
  ('radar_score','Puntuación RADAR','0 a 8 / vacío'),('radar_class','Categoría','Solo si RADAR completo'),
  ('cat','CAT','0 a 40 / vacío'),('mmrc','mMRC','0 a 4 / vacío'),
  ('action','Actuación','Categoría documentada'),('age_v0','Edad basal','años'),
  ('sex','Sexo basal','Categoría'),('fev1_pct','FEV1 basal','% predicho'),
  ('fev1_fvc','FEV1/FVC basal','Cociente'),('smoking_baseline','Tabaquismo basal','Categoría')],
 'COHORTE_LONGITUD_V16':[
  ('participant','Participante','Código sintético'),('centre','Centro','Ámbito'),('status','Situación','cribado/incluido'),
  ('age_v0','Edad basal','años'),('sex','Sexo','Categoría'),
  ('v0_date','V0 fecha','AAAA-MM-DD'),('v1_date','V1 fecha','AAAA-MM-DD'),('v2_date','V2 fecha','AAAA-MM-DD'),
  ('radar_v0','RADAR V0','0–8/vacío'),('radar_v1','RADAR V1','0–8/vacío'),('radar_v2','RADAR V2','0–8/vacío'),
  ('radar_delta_v2_v0','Cambio RADAR','V2 menos V0; solo pares completos'),
  ('cat_v0','CAT V0','0–40/vacío'),('cat_v2','CAT V2','0–40/vacío'),
  ('cat_delta_v2_v0','Cambio CAT','V2 menos V0; solo pares completos'),
  ('ep_copd_recorded','Episodios EPOC','Recuento bruto, no tasa por periodo'),
  ('emergency_copd_recorded','Urgencias EPOC','Recuento bruto independiente'),
  ('admissions_copd_recorded','Ingresos EPOC','Recuento bruto independiente'),
  ('paired_radar','Par RADAR V0–V2','Sí solo ambas mediciones completas')],
 'PENDIENTES_V16':[
  ('participant','Participante','Código sintético'),('centre','Centro','Ámbito'),('visit','Etapa','V0/V1/V2'),
  ('priority','Estado','Pendiente/Próxima etapa/Sin pendientes'),
  ('step','Siguiente acción','Acción orientativa'),('detail','Información','Sin presumir vencimientos'),
  ('action','Tipo de acción','screen/visit/detail'),('status','Estado registro','cribado/incluido')]
})
TITLES.update({
 'ANALISIS_LONG_V16':'Análisis por visita · una fila por evaluación',
 'COHORTE_LONGITUD_V16':'Resumen longitudinal · una fila por participante',
 'PENDIENTES_V16':'Trabajo pendiente por participante · sin fechas inferidas',
})

# Phase 13 outcomes, explicit screening and missingness datasets.
SPEC.update({
 'ELEGIBILIDAD_V13':[
  ('participant','Participante','Código sintético'),('center','Centro','Código ficticio'),
  ('status','Inclusión','cribado / incluido'),('eligibility_decision','Decisión investigador','pendiente / elegible / no_elegible'),
  ('active_exacerbation','Agudización activa','Sí / No / No consta'),
  ('screen_failure_reason','Motivo no inclusión','Categoría'),('age_eligible','Edad ≥40','Derivada'),
  ('fev1_pct_pred','FEV1 pos-BD','Porcentaje predicho'),('ratio_postbd','FEV1/FVC pos-BD','Cociente'),
  ('gold_airflow_grade','GOLD obstrucción 1–4','Derivada, NO A/B/E'),
  ('vital_status','Estado vital','Categoría al cierre'),('death_date','Fecha fallecimiento','AAAA-MM-DD'),
  ('death_cause','Causa fallecimiento','Categoría'),('review','Señales de revisión','NO aprobación automatizada')],
 'RESULTADOS_INTERVALO_V13':[
  ('participant','Participante','Código sintético'),('center','Centro','Ficticio'),
  ('interval','Intervalo','V0→V1, V1→V2, V0→V2'),('date_from','Desde','Exclusiva'),('date_to','Hasta','Inclusiva'),
  ('exacerbations_copd','Exacerbaciones EPOC','Número episodios únicos'),
  ('exacerbations_moderate','Moderadas','Número'),('exacerbations_severe','Graves','Número'),
  ('exacerbations_indeterminate','Indeterminadas','Número'),('er_copd','Urgencias EPOC','Número de contactos'),
  ('admissions_copd','Ingresos EPOC','Número de contactos'),('note','Advertencia','Sin causalidad ni denominador externo')],
 'AUSENCIAS_V13':[
  ('participant','Participante','Código sintético'),('center','Centro','Ficticio'),
  ('visit_type','Visita','V0/V1/V2'),('field_code','Campo sin dato','Código técnico'),
  ('reason','Motivo de ausencia','Categoría estructurada'),('rev','Revisión','Entero'),
  ('username','Usuario','Cuenta ficticia'),('updated_at','Actualizado UTC','Fecha/hora'),
  ('conflict','Conflicto','Coincide con un valor registrado')],
})
TITLES.update({
 'ELEGIBILIDAD_V13':'Cribado explícito, GOLD y situación vital',
 'RESULTADOS_INTERVALO_V13':'Resultados por intervalos realmente observados',
 'AUSENCIAS_V13':'Motivos estructurados de valores ausentes',
})

# Phase 14: centre participation, professional training, supplementary CRD and denominators.
SPEC.update({
 'CENTROS_V14':[
   ('record_key','Centro','Código ficticio'),('center_start_date','Fecha activación','Fecha registrada'),
   ('center_end_use','Uso RADAR al cierre','Sí/No/No evaluable'),('rev','Revisión','Versión')],
 'PROFESIONALES_V14':[
   ('record_key','Profesional','Código ficticio'),('centre','Centro','Centro de adscripción'),
   ('clinician_role','Función','Medicina / Enfermería / Coordinación / Otro'),
   ('training_date','Formación RADAR','Fecha'),('survey_utilidad','Utilidad (1–5)','Escala propuesta'),
   ('survey_factibilidad','Factibilidad (1–5)','Escala propuesta'),('rev','Revisión','Versión')],
 'CRIBADO_V14':[
   ('record_key','Participante','Código'),('centre','Centro','Código'),('screen_code','ID cribado','ID específico'),
   ('screen_date','Fecha cribado','AAAA-MM-DD'),('alternative_diagnosis','Diagnóstico excluyente','Si/No/NC'),
   ('serious_decompensation','Comorbilidad descompensada','Si/No/NC'),
   ('interfering_trial','Ensayo interferente','Si/No/NC'),('consent_date','Fecha consentimiento','AAAA-MM-DD'),('rev','Revisión','Versión')],
 'BASAL_V14':[
   ('record_key','Participante','Código'),('centre','Centro','Código'),
   ('other_comorb','Otra comorbilidad','Categoría propuesta'),('charlson_index','Índice Charlson','0-37'),
   ('flu_vax_up_to_date','Antigripal','Si/No/NC'),('pneumo_vax_up_to_date','Neumocócica','Si/No/NC'),
   ('ccq_score','CCQ','0-6 opcional'),('bode_score','BODE','0-10 opcional'),('rev','Revisión','Versión')],
 'VISITA_ADICIONAL_V14':[
   ('record_key','Participante y visita','Paciente:Visita'),('centre','Centro','Código'),
   ('assessor_code','Evaluador','Código de profesional'),
   ('flu_vax_up_to_date','Vacuna gripe','Actualizada'),('pneumo_vax_up_to_date','Vacuna neumocócica','Actualizada'),
   ('ccq_score','CCQ','0-6'),('clinical_notes_structured','Actuación codificada','Clasificación provisional'),('rev','Revisión','Versión')],
 'IMPLANTACION_MENSUAL_V14':[
   ('record_key','Centro:mes','Código:AAAA-MM'),('centre','Centro','Código'),
   ('eligible_copd_visits','Consultas EPOC elegibles','Denominador'),
   ('visits_with_radar','Consultas con RADAR','Numerador'),('rev','Revisión','Versión')],
 'INDICADORES_IMPL_V14':[
   ('indicator','Indicador','Etiqueta descriptiva'),('numerator','Numerador','Recuento cuando consta'),
   ('denominator','Denominador','Recuento cuando consta'),('value','Resultado','N o %'),
   ('unit','Unidad','% / n'),('note','Regla de cálculo','Definición y cautela')],
 'EVENTOS_CLASIF_V14':[
   ('participant','Participante','Código'),('date','Fecha','AAAA-MM-DD'),
   ('event_type','Tipo','Agudización / Urgencias / Ingreso / Defunción'),
   ('source_id','ID origen','Identificador'),('related_episode','Episodio vinculado','No implica evento adicional'),
   ('copd','Relación EPOC','Si/No/No consta'),('note','Observación','Separación de eventos')],
 'COBERTURA_28_V14':[
   ('code','Variable','Código científico'),('label','Etiqueta','Nombre'),
   ('status','Implementación','Capturable / Derivada'),
   ('source','Origen','Tabla o cálculo'),('pending','Precisión científica','Revisión requerida')],
})
TITLES.update({
 'CENTROS_V14':'Centros y seguimiento de implantación',
 'PROFESIONALES_V14':'Equipo participante y formación',
 'CRIBADO_V14':'Variables ampliadas de cribado',
 'BASAL_V14':'Variables clínicas basales complementarias',
 'VISITA_ADICIONAL_V14':'Evaluador y actuación estandarizada',
 'IMPLANTACION_MENSUAL_V14':'Numeradores y denominadores documentados por mes y centro',
 'INDICADORES_IMPL_V14':'Indicadores operativos calculables',
 'EVENTOS_CLASIF_V14':'Tipos de evento y contactos sin duplicación de episodios',
 'COBERTURA_28_V14':'Cierre técnico de 28 variables antes pendientes',
})

# Phase 18: concise, analysis-oriented datasets backed by one shared reporting function.
SPEC.update({
 'INFORME_V18':[
  ('group','Área','Cohorte, RADAR, seguimiento, parejas, eventos o implantación'),
  ('indicator','Indicador','Nombre del indicador'),('numerator','Numerador','Recuento, si procede'),
  ('denominator','Denominador','Población elegible para el indicador'),
  ('value','Resultado','Vacío = no estimable'),('unit','Unidad','n / % / puntos'),
  ('population','Población analizada','Subgrupo y base del denominador'),
  ('interpretation','Definición y límites','Restricción de interpretación')],
 'RADAR_ETAPAS_V18':[
  ('visit','Visita','V0, V1 o V2'),('category','Categoría de control','Buen / parcial / mal'),
  ('n','Casos','RADAR completos en categoría'),('denominator','RADAR clasificables','Solo evaluaciones completas'),
  ('percent','Porcentaje','Vacío = sin denominador')],
 'PAREJAS_INDEP_V18':[
  ('participant','Participante','Código sintético'),('centre','Centro','Centro'),
  ('v0_date','Fecha V0','Fecha real'),('v2_date','Fecha V2','Fecha real'),
  ('radar_v0','RADAR V0','0 a 8 / vacío'),('radar_v2','RADAR V2','0 a 8 / vacío'),
  ('paired_radar','Par RADAR válido','si/no'),('delta_radar','Cambio RADAR','V2 – V0'),
  ('control_v0','Control V0','Categoría clasificada'),('control_v2','Control V2','Categoría clasificada'),
  ('cat_v0','CAT V0','0 a 40 / vacío'),('cat_v2','CAT V2','0 a 40 / vacío'),
  ('paired_cat','Par CAT válido','Independiente de RADAR'),('delta_cat','Cambio CAT','V2 – V0'),
  ('mmrc_v0','mMRC V0','0 a 4 / vacío'),('mmrc_v2','mMRC V2','0 a 4 / vacío'),
  ('paired_mmrc','Par mMRC válido','Independiente de RADAR'),('delta_mmrc','Cambio mMRC','V2 – V0')],
 'TRANSICIONES_V18':[
  ('control_v0','Categoría V0','Buen / parcial / mal'),('control_v2','Categoría V2','Buen / parcial / mal'),
  ('n','Número','Parejas RADAR clasificables'),('denominator','Total pareado','Total de pares V0 y V2'),
  ('percent','Porcentaje del total pareado','Vacío si no hay parejas')],
 'METODOLOGIA_V18':[
  ('rule','Criterio','Nombre de la regla'),('definition','Definición operativa','Límites de interpretación')],
})
TITLES.update({
 'INFORME_V18':'Informe descriptivo · denominadores y estimaciones',
 'RADAR_ETAPAS_V18':'Distribución RADAR en V0, V1 y V2',
 'PAREJAS_INDEP_V18':'Parejas longitudinales independientes RADAR, CAT y mMRC',
 'TRANSICIONES_V18':'Matriz de transición · control clínico V0–V2',
 'METODOLOGIA_V18':'Definiciones y restricciones de los análisis',
})

def clean(value):
    if value is None: return None
    if isinstance(value,str):
        # Protection against Excel formula injection in exported user-entered values.
        if value and (value[0] in '=+-@' or value[0] in '\t\r\n'):
            return "'"+value
        return value
    return value


def quality_issues(patients, visits, events, contacts):
    issues=[]
    def add(severity,pid,item,issue,suggestion):
        issues.append({'severity':severity,'patient':pid,'item':item,'issue':issue,'suggestion':suggestion})
    for p in patients:
        pid=p['id']; pv=[v for v in visits if v['patient']==pid]
        if p.get('status')=='incluido' and not any(v['type']=='V0' for v in pv):
            add('Revisar',pid,'Visitas','Incluido sin V0','Completar la visita basal')
        if p.get('age') is not None and p['age']<40:
            add('Revisar',pid,'Elegibilidad','Edad inferior a 40 años','Revisar inclusión con el IP')
        if p.get('status')=='incluido' and p.get('consent')!='si':
            add('Revisar',pid,'Consentimiento','Participante incluido sin consentimiento confirmado','Verificar consentimiento')
        if p.get('ratio') is not None and p['ratio']>=0.7 and p.get('copd')=='si':
            add('Advertencia',pid,'Espirometría','FEV1/FVC ≥0,70','Revisar interpretación clínica')
    for v in visits:
        if v.get('status')!='no_realizada' and any(v.get(k) not in ('si','no') for k in ('rescue','exacerb','dyspnea','activity')):
            add('Advertencia',v['patient'],v['id'],'RADAR incompleto','No clasificar hasta completar los cuatro ítems')
        if v.get('mmrc') is not None and v.get('dyspnea') in ('si','no'):
            if (v['mmrc']>=2) != (v['dyspnea']=='si'):
                add('Advertencia',v['patient'],v['id'],'mMRC y RADAR no concordantes','Verificar ambas mediciones')
    # Assessment is explicit: absent is unknown, never a negative response.
    by_event={}
    for contact in contacts:
        if contact.get('event'):
            by_event.setdefault(contact['event'],[]).append(contact)
    for episode in events:
        linked=by_event.get(episode['id'],[])
        for kind,sk,dk,code in (
            ('urgencias','emergencyStatus','emergencyDate','R081'),
            ('ingreso','admissionStatus','admissionDate','R082')):
            match=[x for x in linked if x.get('type')==kind and x.get('copd')=='si' and episode.get('copd')=='si']
            state=episode.get(sk,'')
            if match and state!='si':
                add('Revisar',episode['patient'],episode['id'],f'{code}: contacto registrado sin estado Sí','Conciliar los registros vinculados')
            if state=='si' and not episode.get(dk) and not match:
                add('Advertencia',episode['patient'],episode['id'],f'{code}: Sí sin fecha ni contacto','Completar evidencia o motivo de fecha ausente')
        if any(episode.get(k,'')=='' for k in ('emergencyStatus','admissionStatus')):
            add('Informativo',episode['patient'],episode['id'],'R081/R082: estado pendiente','No interpretar Sin registrar como No')
    # Historical Visit flags have a different semantic scope; clinicians must map them manually.
    for v in visits:
        if any(v.get(k) for k in ('action','inhaler','education','referral')):
            add('Informativo',v['patient'],v['id'],'Actuaciones legadas conservadas','Revisar R090–R099 por visita; no realizar conversión automática')
    return issues


def width_col(ix):
    col=''
    while ix:
        ix, rem=divmod(ix-1,26)
        col=chr(65+rem)+col
    return col


XMLNS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
RELNS='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKGREL='http://schemas.openxmlformats.org/package/2006/relationships'
CTYPE='http://schemas.openxmlformats.org/package/2006/content-types'


def safe_xml(value):
    text=str(value)
    return escape(''.join(ch for ch in text if ch in '\t\n\r' or (ord(ch)>=32 and not 0xD800<=ord(ch)<=0xDFFF and ord(ch)<=0xFFFD)))


def colname(n):
    letters=''
    while n:
        n,x=divmod(n-1,26)
        letters=chr(65+x)+letters
    return letters


def cell(ref, value=None, style=0, formula=None, cached=None):
    attrs=f' r="{ref}"'+(f' s="{style}"' if style else '')
    if formula is not None:
        # XLSX formulas are stored without their leading '='; cached results aid file preview.
        f=safe_xml(formula.lstrip('='))
        if isinstance(cached,str):
            return f'<c{attrs} t="str"><f>{f}</f><v>{safe_xml(cached)}</v></c>'
        if cached is None:
            return f'<c{attrs}><f>{f}</f><v></v></c>'
        return f'<c{attrs}><f>{f}</f><v>{cached}</v></c>'
    if value is None:
        return ''
    if isinstance(value,bool):
        return f'<c{attrs} t="b"><v>{int(value)}</v></c>'
    if isinstance(value,(int,float)):
        return f'<c{attrs}><v>{value}</v></c>'
    return f'<c{attrs} t="inlineStr"><is><t xml:space="preserve">{safe_xml(value)}</t></is></c>'


class Sheet:
    def __init__(self,name,widths=None,freeze=0,tab=None):
        self.name=name; self.rows={}; self.heights={}; self.merges=[]
        self.widths=widths or {}; self.freeze=freeze; self.filter=None; self.tab=tab
    def put(self,row,col,value=None,style=0,formula=None,cached=None):
        self.rows.setdefault(row,{})[col]=cell(f'{colname(col)}{row}',value,style,formula,cached)
    def line(self,row,values,style=0):
        for i,v in enumerate(values,1):
            self.put(row,i,v,style)
    def merge(self,start_row,end_row,start_col,end_col):
        self.merges.append(f'{colname(start_col)}{start_row}:{colname(end_col)}{end_row}')
    def xml(self):
        last_row=max(self.rows,default=1); last_col=max((max(r,default=1) for r in self.rows.values()),default=1)
        r=[f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="{XMLNS}">',
           f'<dimension ref="A1:{colname(last_col)}{last_row}"/>']
        if self.freeze:
            r.append(f'<sheetViews><sheetView workbookViewId="0"><pane ySplit="{self.freeze}" topLeftCell="A{self.freeze+1}" activePane="bottomLeft" state="frozen"/><selection pane="bottomLeft" activeCell="A{self.freeze+1}" sqref="A{self.freeze+1}"/></sheetView></sheetViews>')
        else:r.append('<sheetViews><sheetView workbookViewId="0"/></sheetViews>')
        r.append('<sheetFormatPr defaultRowHeight="17"/>')
        if self.widths:
            r.append('<cols>')
            for c,w in sorted(self.widths.items()):
                r.append(f'<col min="{c}" max="{c}" width="{w}" customWidth="1"/>')
            r.append('</cols>')
        r.append('<sheetData>')
        for row,values in sorted(self.rows.items()):
            ht=f' ht="{self.heights[row]}" customHeight="1"' if row in self.heights else ''
            r.append(f'<row r="{row}"{ht}>'+''.join(values[k] for k in sorted(values))+'</row>')
        r.append('</sheetData>')
        if self.filter:r.append(f'<autoFilter ref="{self.filter}"/>')
        if self.merges:r.append(f'<mergeCells count="{len(self.merges)}">'+''.join(f'<mergeCell ref="{m}"/>' for m in self.merges)+'</mergeCells>')
        r.append('<pageMargins left="0.4" right="0.4" top="0.6" bottom="0.6" header="0.3" footer="0.3"/>')
        r.append('</worksheet>')
        return ''.join(r).encode('utf-8')


def styles_xml():
    # Restrained clinical-research palette. All styles are simple standard OOXML.
    fills=['<fill><patternFill patternType="none"/></fill>',
           '<fill><patternFill patternType="gray125"/></fill>']
    for color in ('142C43','147B80','EAF4F4','F3F6F8','FFF2D8','FFFFFF','E6EFF2'):
        fills.append(f'<fill><patternFill patternType="solid"><fgColor rgb="FF{color}"/><bgColor indexed="64"/></patternFill></fill>')
    fonts=[
        '<font><sz val="10"/><name val="Aptos"/><color rgb="FF213547"/></font>',
        '<font><b/><sz val="21"/><name val="Aptos Display"/><color rgb="FFFFFFFF"/></font>',
        '<font><b/><sz val="10"/><name val="Aptos"/><color rgb="FFFFFFFF"/></font>',
        '<font><b/><sz val="11"/><name val="Aptos"/><color rgb="FF147B80"/></font>',
        '<font><sz val="10"/><name val="Aptos"/><color rgb="FF617184"/></font>',
        '<font><b/><sz val="12"/><name val="Aptos"/><color rgb="FF213547"/></font>',
        '<font><sz val="10"/><name val="Aptos"/><color rgb="FF213547"/></font>',
        '<font><b/><sz val="10"/><name val="Aptos"/><color rgb="FFAC3F3F"/></font>',
    ]
    # indices 0 normal, 1 title, 2 header, 3 section, 4 hint, 5 summary label,
    # 6 summary value, 7 alternating body, 8 body, 9 warning, 10 data accent.
    styles=[(0,0,0,0),(1,2,1,1),(2,2,1,1),(3,3,0,0),
            (4,4,0,0),(5,5,0,0),(3,4,0,0),(0,5,0,0),
            (0,0,0,0),(7,6,0,0),(3,4,0,0)]
    x=[f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="{XMLNS}">',
       '<numFmts count="0"/>',f'<fonts count="{len(fonts)}">'+''.join(fonts)+'</fonts>',
       f'<fills count="{len(fills)}">'+''.join(fills)+'</fills>',
       '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>',
       '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>',
       f'<cellXfs count="{len(styles)}">']
    for fontid,fillid,border,align in styles:
        x.append(f'<xf numFmtId="0" fontId="{fontid}" fillId="{fillid}" borderId="{border}" xfId="0" applyFill="1" applyFont="1"'+(' applyAlignment="1"><alignment wrapText="1" vertical="center"/></xf>' if align else '/>'))
    x.extend(['</cellXfs>','<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>','</styleSheet>'])
    return ''.join(x).encode('utf-8')


def package(sheets):
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as zipout:
        def put(name,value):zipout.writestr(name,value)
        overrides=['<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
                   '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
                   '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>']
        for i,_ in enumerate(sheets,1):
            overrides.append(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
        put('[Content_Types].xml',f'<?xml version="1.0" encoding="UTF-8"?><Types xmlns="{CTYPE}"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>{"".join(overrides)}</Types>')
        put('_rels/.rels',f'<Relationships xmlns="{PKGREL}"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>')
        sheets_xml=''.join(f'<sheet name={quoteattr(s.name)} sheetId="{i}" r:id="rId{i}"/>' for i,s in enumerate(sheets,1))
        put('xl/workbook.xml',f'<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="{XMLNS}" xmlns:r="{RELNS}"><sheets>{sheets_xml}</sheets><calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>')
        rels=''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i,_ in enumerate(sheets,1))
        put('xl/_rels/workbook.xml.rels',f'<Relationships xmlns="{PKGREL}">{rels}<Relationship Id="rId{len(sheets)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        put('xl/styles.xml',styles_xml())
        for i,s in enumerate(sheets,1):put(f'xl/worksheets/sheet{i}.xml',s.xml())
        put('docProps/core.xml',f'<?xml version="1.0" encoding="UTF-8"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>RADAR-CORUÑA | Exportación de investigación sintética</dc:title><dc:creator>RADAR-CORUÑA</dc:creator></cp:coreProperties>')
        put('docProps/app.xml',f'<?xml version="1.0" encoding="UTF-8"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>RADAR-CORUÑA</Application></Properties>')
    return mem.getvalue()


def tabular(name, rows, scope):
    fields=SPEC[name]; cols=len(fields); sh=Sheet(name,freeze=7,tab='147B80')
    sh.line(1,[TITLES[name]],1);sh.merge(1,2,1,cols);sh.heights[1]=33
    sh.line(3,[f'RADAR-CORUÑA  |  PILOTO SINTÉTICO  |  {scope}'],3);sh.merge(3,3,1,cols);sh.heights[3]=24
    sh.line(5,['Fuente: base de datos del servidor. Campos no registrados se mantienen vacíos; especificaciones científicas pendientes de validación.'],4)
    sh.merge(5,5,1,cols)
    sh.line(7,[label for _,label,_ in fields],2);sh.heights[7]=38
    for i,item in enumerate(rows,8):
        for col,(key,_,__) in enumerate(fields,1):
            if name=='VISITAS' and key=='radar_score':
                conditions=','.join(f'OR({x}{i}="si",{x}{i}="no")' for x in ('I','J','K','L'))
                formula=f'IF(F{i}="no_realizada","",IF(AND({conditions}),IF(I{i}="si",3,0)+IF(J{i}="si",2,0)+IF(K{i}="si",2,0)+IF(L{i}="si",1,0),""))'
                answers=[item.get(k) for k in ('rescue','exacerb','dyspnea','activity')]
                valid=item.get('status')!='no_realizada' and all(v in ('si','no') for v in answers)
                cached=sum(w for v,w in zip(answers,(3,2,2,1)) if v=='si') if valid else ''
                sh.put(i,col,style=10,formula=formula,cached=cached)
            elif name=='VISITAS' and key=='radar_class':
                cached_score=score_visit(item)
                cached=('Sin clasificar' if cached_score is None else 'Buen control' if cached_score<=1 else 'Control parcial' if cached_score<=3 else 'Mal control')
                sh.put(i,col,style=10,formula=f'IF(COUNT(M{i})=0,"Sin clasificar",IF(M{i}<=1,"Buen control",IF(M{i}<=3,"Control parcial","Mal control")))',cached=cached)
            else:
                sh.put(i,col,clean(item.get(key)),style=7 if i%2==0 else 8)
        sh.heights[i]=23
    if rows:sh.filter=f'A7:{colname(cols)}{7+len(rows)}'
    for j,(_,label,_) in enumerate(fields,1):
        sh.widths[j]=min(48,max(15,len(label)*1.1))
    if name=='CALIDAD':sh.widths.update({4:52,5:48})
    if name=='REVISION_CIENTIFICA':sh.widths.update({5:56,6:55})
    if name=='COBERTURA_VISITAS':sh.widths.update({8:65})
    if name=='PUERTAS_DE_USO':sh.widths.update({2:36,4:78})
    if name in ('TRAZABILIDAD','CAMBIOS_CAMPO'):sh.widths.update({2:32,14:50,15:44})
    return sh


def score_visit(v):
    answers=[v.get(k) for k in ('rescue','exacerb','dyspnea','activity')]
    if v.get('status')=='no_realizada' or not all(a in ('si','no') for a in answers):return None
    return sum(w for a,w in zip(answers,(3,2,2,1)) if a=='si')


def create_excel_snapshot(*,patients,visits,episodes,contacts,audit,changes=None,centres,user,exported_at=None,observations=None,study_spec=None,missing=None,phase14records=None):
    """Build a fully portable Excel 2007+ snapshot with filters, cached formulas and audit scope."""
    stamp=exported_at or datetime.now(timezone.utc).isoformat(timespec='seconds')
    changes=changes or []
    observations=observations or []
    missing=missing or []
    phase14records=phase14records or []
    if study_spec is None:
        from study_module import public_catalogue
        study_spec=public_catalogue()
    dictionary_rows=study_spec.get('variables',[])
    decision_rows=study_spec.get('decisions',[])
    label_by_code={x['code']:x['label'] for x in dictionary_rows}
    observation_rows=[{**o,'variable_label':label_by_code.get(o['variable_code'],o['variable_code']),
          'spec_version':study_spec.get('version','v0.9')} for o in observations]
    # Field-level audit remains separate; users should not mistake it for current clinical values.
    scope=f"{user.get('role','?')} / {user.get('centre') or 'todos los centros ficticios'}"
    lookup={p['id']:p['center'] for p in patients}
    visits=[{**v,'center':lookup.get(v['patient'],'')} for v in visits]
    episodes=[{**v,'center':lookup.get(v['patient'],'')} for v in episodes]
    episode_numbers={v['id']:v.get('episodeNo') for v in episodes}
    contacts=[{**v,'center':lookup.get(v['patient'],''),'relatedEpisodeNo':episode_numbers.get(v.get('event'))} for v in contacts]
    from clinical_review import make_review
    from crd_workflow import build_workflow
    workflow=build_workflow(patients,visits,observations,episodes,contacts)
    from phase12_analysis import make_analysis
    analysis=make_analysis(patients,visits,episodes,contacts)
    review=make_review(patients,visits,episodes,contacts,decision_rows)
    from phase13_outcomes import make_outcomes
    phase13=make_outcomes(patients,visits,episodes,contacts,missing)
    from phase14_completion import group_records, make_indicators, normalized_events, FIELD_LOCATION, DERIVED14, reconcile_legacy_analysis
    p14groups=group_records(phase14records)
    p14metrics=make_indicators(phase14records,patients,visits,centres,cutoff=stamp[:10])
    analysis=reconcile_legacy_analysis(analysis,p14metrics)
    selected28=set(FIELD_LOCATION)|set(DERIVED14)
    v14map=[{'code':v['code'],'label':v['label'],
              'status':'Capturable' if v['code'] in FIELD_LOCATION else 'Derivada / provisional',
              'source':(FIELD_LOCATION[v['code']][1] if v['code'] in FIELD_LOCATION else DERIVED14[v['code']][1]),
              'pending':v.get('pending','')} for v in dictionary_rows if v['code'] in selected28]
    assert len(v14map)==28
    from phase16_usability import analysis_long, cohort_wide, pending_work
    long_rows=analysis_long(patients,visits)
    cohort_rows=cohort_wide(patients,visits,episodes,contacts)
    pending_rows=pending_work(patients,visits)
    from phase18_reporting import make_report
    phase18=make_report(patients,visits,episodes,contacts,phase14records,
                       [c for c in centres if not user.get('centre') or c['code']==user['centre']],
                       cutoff=stamp[:10])
    issues=quality_issues(patients,visits,episodes,contacts)
    from research_intelligence_v39 import make_intelligence
    intelligence=make_intelligence(patients,visits,episodes,contacts,missing,observations,centres)
    cover=Sheet('PORTADA',widths={1:34,2:52,3:18,4:18,5:18,6:18,7:18,8:18})
    cover.line(1,['RADAR-CORUÑA'],1);cover.merge(1,3,1,8);cover.heights[1]=42
    cover.line(4,['EXTRACTO DE INVESTIGACIÓN  |  PILOTO SINTÉTICO  |  v0.39'],2);cover.merge(4,4,1,8);cover.heights[4]=34
    for r,(k,v) in enumerate([('Exportado (UTC)',stamp),('Ámbito autorizado',scope),('Base principal','SQLite local (datos sintéticos)'),('Generador','OOXML portátil · biblioteca estándar Python'),('Naturaleza','Instantánea de sólo lectura'),('IMPORTANTE','NO AUTORIZADO PARA DATOS DE PACIENTES REALES')],7):
        cover.put(r,1,k,5);cover.put(r,2,v,6 if r==12 else 0);cover.heights[r]=27
    cover.line(15,['GUÍA DE LECTURA DEL LIBRO'],2);cover.merge(15,15,1,8)
    info=['CRD_MEDICIONES: mediciones adicionales persistidas de V0, V1 y V2.',
          'FLUJO_CRD_V11: cobertura propuesta por participante y visita; GUIA_CRD_V11: origen y prioridad de campos. ANALISIS_V12: denominadores válidos y límites de interpretabilidad.',
          'REVISION_CIENTIFICA y COBERTURA_VISITAS: control orientativo, no validación médica.',
          'PUERTAS_DE_USO: autorizaciones pendientes, sin poder aprobatorio automático.',
          'CATALOGO_107 y DECISIONES_20: estructura científica y estado de validación.',
          'PARTICIPANTES: cribado, inclusión y datos de línea basal.',
          'VISITAS: V0/V1/V2, score RADAR con fórmula y resultado precalculado.',
          'EPISODIOS y CONTACTOS: entidades diferenciadas para evitar dobles recuentos.',
          'CALIDAD: incidencias automáticas, no sustituyen revisión clínica.',
          'DICCIONARIO: nombres técnicos, etiquetas y codificación de exportación.',
          'TRAZABILIDAD y CAMBIOS_CAMPO: disponibles exclusivamente para administrador.' if user.get('role')=='admin' else 'Historial de correcciones reservado al administrador.',
          'ELEGIBILIDAD_V13 / RESULTADOS_INTERVALO_V13: cribado explícito, GOLD 1–4 y desenlaces por intervalos registrados.',
          'AUSENCIAS_V13: causas documentadas de falta de medición; los conflictos se señalan, no se eliminan.',
          'CENTROS, PROFESIONALES, CRIBADO y BASAL_V14: campos complementarios de implantación y estudio.',
          'INDICADORES_IMPL_V14: proporciones solo con denominadores documentados; no inferir ceros ausentes.',
          'Los campos no registrados no se interpretan automáticamente como respuestas negativas.',
          'ANALISIS_LONG_V16: una fila por visita; COHORTE_LONGITUD_V16: una fila por participante; PENDIENTES_V16: trabajo pendiente sin asumir visitas vencidas.',
          'INFORME_V18, RADAR_ETAPAS_V18, PAREJAS_INDEP_V18 y TRANSICIONES_V18: indicadores, distribución y cambios con muestras correctas.',
          'METODOLOGIA_V18: reglas y precauciones de interpretación, incluyendo CAT independiente de RADAR.',
          'V39_CENTROS, V39_COBERTURA, V39_LONGITUDINAL, V39_REVISION y V39_METODOS: lectura analítica, denominadores y controles revisables.',
          'El libro es una instantánea; las correcciones se realizan en la aplicación.']
    for i,t in enumerate(info,17):cover.put(i,1,t,4);cover.merge(i,i,1,8);cover.heights[i]=24
    summary=Sheet('RESUMEN',widths={1:44,2:22,3:20,4:20,5:16},freeze=6)
    summary.line(1,['Indicadores de la extracción'],1);summary.merge(1,2,1,6)
    summary.line(3,['Datos sintéticos autorizados · Cifras descriptivas, no resultados validados.'],3);summary.merge(3,3,1,6)
    summary.line(6,['Indicador','Valor'],2)
    prow=max(8,7+len(patients));vrow=max(8,7+len(visits));erow=max(8,7+len(episodes));crow=max(8,7+len(contacts));qrow=max(8,7+len(issues))
    summary_rows=[
      ('Participantes registrados',f'COUNTA(PARTICIPANTES!A8:A{prow})',len(patients)),
      ('Participantes incluidos',f'COUNTIF(PARTICIPANTES!C8:C{prow},"incluido")',sum(p['status']=='incluido' for p in patients)),
      ('Pendientes de cribado',f'COUNTIF(PARTICIPANTES!C8:C{prow},"cribado")',sum(p['status']=='cribado' for p in patients)),
      ('Visitas registradas',f'COUNTA(VISITAS!A8:A{vrow})',len(visits)),
      ('Visitas completas',f'COUNTIF(VISITAS!F8:F{vrow},"completa")',sum(v['status']=='completa' for v in visits)),
      ('Visitas con RADAR clasificado',f'COUNT(VISITAS!M8:M{vrow})',sum(score_visit(v)is not None for v in visits)),
      ('Visitas sin clasificación RADAR',f'COUNTIF(VISITAS!N8:N{vrow},"Sin clasificar")',sum(score_visit(v)is None for v in visits)),
      ('Episodios',f'COUNTA(EPISODIOS!A8:A{erow})',len(episodes)),
      ('Contactos sanitarios',f'COUNTA(CONTACTOS!A8:A{crow})',len(contacts)),
      ('Incidencias de calidad',f'COUNTA(CALIDAD!D8:D{qrow})',len(issues)),
      ('Mediciones ampliadas registradas',f'COUNTA(CRD_MEDICIONES!A8:A{max(8,7+len(observation_rows))})',len(observation_rows)),
      ('Variables científicas candidatas',f'COUNTA(CATALOGO_107!A8:A{max(8,7+len(dictionary_rows))})',len(dictionary_rows)),
      ('Incidencias de revisión científica',f'COUNTA(REVISION_CIENTIFICA!E8:E{max(8,7+len(review["issues"]))})',len(review['issues'])),
      ('Visitas con núcleo completo',f'COUNTIF(COBERTURA_VISITAS!G8:G{max(8,7+len(review["visit_coverage"]))},100)',review['metrics']['core_visits_complete']),
      ('Decisiones aún sin acordar',f'COUNTIF(DECISIONES_20!I8:I{max(8,7+len(decision_rows))},"Sin acordar")',review['open_decisions']),
      ('Pares RADAR V0–V2 completos',f'COUNTIF(COHORTE_LONGITUD_V16!S8:S{max(8,7+len(cohort_rows))},"si")',sum(r['paired_radar']=='si' for r in cohort_rows)),
      ('V0 con RADAR clasificado',f'COUNTIFS(VISITAS!D8:D{vrow},"V0",VISITAS!M8:M{vrow},">=0")',sum(v['type']=='V0' and score_visit(v) is not None for v in visits)),
    ]
    for n,(lab,expr,cached) in enumerate(summary_rows,7):
        summary.put(n,1,lab,5);summary.put(n,2,style=10,formula=expr,cached=cached);summary.heights[n]=26
    summary.line(24,['Centro','Participantes','Incluidos','Visitas'],2)
    available=[c for c in centres if not user.get('centre') or user['centre']==c['code']]
    for r,c in enumerate(available,25):
        cd=c['code'];summary.put(r,1,cd)
        summary.put(r,2,style=10,formula=f'COUNTIF(PARTICIPANTES!B8:B{prow},A{r})',cached=sum(p['center']==cd for p in patients))
        summary.put(r,3,style=10,formula=f'COUNTIFS(PARTICIPANTES!B8:B{prow},A{r},PARTICIPANTES!C8:C{prow},"incluido")',cached=sum(p['center']==cd and p['status']=='incluido' for p in patients))
        summary.put(r,4,style=10,formula=f'COUNTIF(VISITAS!C8:C{vrow},A{r})',cached=sum(v['center']==cd for v in visits))
        summary.heights[r]=27
    # Front-page research digest, with live references to the v0.18 report.
    summary.line(31,['LECTURA CIENTÍFICA · FASE 18'],2);summary.merge(31,31,1,5)
    summary.line(32,['Los porcentajes requieren denominadores válidos; una celda vacía significa «no estimable».'],3)
    summary.merge(32,32,1,5)
    digest=[
        ('Mal control basal (%)','Mal control basal RADAR ≥4'),
        ('Parejas RADAR completas (%)','RADAR V0–V2 pareado'),
        ('Variación RADAR media (puntos)','Cambio medio RADAR V2−V0'),
        ('Parejas CAT completas (%)','CAT V0–V2 pareado'),
        ('Variación CAT media (puntos)','Cambio medio CAT V2−V0'),
    ]
    for line,(label,name) in enumerate(digest,34):
        idx=next(i for i,x in enumerate(phase18['indicators'],8) if x['indicator']==name)
        actual=next(x['value'] for x in phase18['indicators'] if x['indicator']==name)
        summary.put(line,1,label,5)
        summary.put(line,2,style=10,formula=f'IF(INFORME_V18!E{idx}=\"\",\"No estimable\",INFORME_V18!E{idx})',
                    cached=actual if actual is not None else 'No estimable')
        summary.heights[line]=26
    sheets=[cover,summary]
    for name,rows in [
        ('INFORME_V18',phase18['indicators']),
        ('RADAR_ETAPAS_V18',phase18['distributions']),
        ('PAREJAS_INDEP_V18',phase18['pairs']),
        ('TRANSICIONES_V18',phase18['transitions']),
        ('METODOLOGIA_V18',phase18['methodology']),
    ]:
        sheets.append(tabular(name,rows,scope))
    for title,rows in [('PARTICIPANTES',patients),('VISITAS',visits),('EPISODIOS',episodes),('CONTACTOS',contacts),('CALIDAD',issues),('REVISION_CIENTIFICA',review['issues']),('COBERTURA_VISITAS',review['visit_coverage']),('CRD_MEDICIONES',observation_rows),('CATALOGO_107',dictionary_rows),('DECISIONES_20',decision_rows),('PUERTAS_DE_USO',review['gates']),('FLUJO_CRD_V11',[{**r,'core_missing':'; '.join(r['core_missing']),'baseline_missing':'; '.join(r['baseline_missing']),'alerts':'; '.join(r['alerts'])} for r in workflow['rows']]),('GUIA_CRD_V11',workflow['manifest']),('ANALISIS_V12',analysis['metrics']),('PAREJAS_V12',analysis['paired']),('BRECHAS_CRD_V12',analysis['coverage']),('ELEGIBILIDAD_V13',phase13['eligibility']),('RESULTADOS_INTERVALO_V13',phase13['intervals']),('AUSENCIAS_V13',phase13['missing']),
     ('CENTROS_V14',[{'record_key':r['key'],'centre':r['centre'],**r['payload'],'rev':r['rev']} for r in p14groups['centre']]),
     ('PROFESIONALES_V14',[{'record_key':r['key'],'centre':r['centre'],**r['payload'],'rev':r['rev']} for r in p14groups['professional']]),
     ('CRIBADO_V14',[{'record_key':r['key'],'centre':r['centre'],**r['payload'],'rev':r['rev']} for r in p14groups['screening']]),
     ('BASAL_V14',[{'record_key':r['key'],'centre':r['centre'],**r['payload'],'rev':r['rev']} for r in p14groups['baseline']]),
     ('VISITA_ADICIONAL_V14',[{'record_key':r['key'],'centre':r['centre'],**r['payload'],'rev':r['rev']} for r in p14groups['visit']]),
     ('IMPLANTACION_MENSUAL_V14',[{'record_key':r['key'],'centre':r['centre'],**r['payload'],'rev':r['rev']} for r in p14groups['implementation']]),
     ('INDICADORES_IMPL_V14',p14metrics['indicators']),
     ('EVENTOS_CLASIF_V14',normalized_events(patients,episodes,contacts)),
     ('COBERTURA_28_V14',v14map),
     ('ANALISIS_LONG_V16',long_rows),('COHORTE_LONGITUD_V16',cohort_rows),('PENDIENTES_V16',pending_rows)]:
        sheets.append(tabular(title,rows,scope))
    # v0.39: analysis-friendly sheets with fixed schemas and clearly separate denominators.
    v39_schema={
      'V39_CENTROS':('centres',['centre','screening','included','baseline_evaluable','baseline_pct','poor_baseline_n','poor_baseline_denominator','poor_baseline_pct','v1_performed','v2_performed','v2_evaluable']),
      'V39_COBERTURA':('stages',['stage','included','visits_recorded','visits_performed','visits_not_performed','radar_evaluable','radar_denominator','radar_coverage_pct','radar_within_performed_pct','cat_evaluable','cat_denominator','mmrc_evaluable','mmrc_denominator','poor_radar_n','poor_radar_denominator','poor_radar_pct']),
      'V39_LONGITUDINAL':('longitudinal',['participant','centre','v0_date','v1_date','v2_date','radar_v0','radar_v1','radar_v2','cat_v0','cat_v1','cat_v2','mmrc_v0','mmrc_v1','mmrc_v2','delta_radar_v2_v0','delta_cat_v2_v0','delta_mmrc_v2_v0','issues_to_review']),
      'V39_REVISION':('quality',['participant','centre','stage','code','severity','message']),
      'V39_METODOS':('methodology',['rule'])
    }
    for sheetname,(dataset,columns) in v39_schema.items():
        rows=[{'rule':rule} for rule in intelligence[dataset]] if dataset=='methodology' else intelligence[dataset]
        sh=Sheet(sheetname,widths={i:(65 if key in ('message','rule') else 21) for i,key in enumerate(columns,1)},freeze=7)
        sh.line(1,[f'RADAR-CORUÑA · {sheetname}'],1);sh.merge(1,2,1,len(columns));sh.heights[1]=32
        sh.line(3,[f'PILOTO SINTÉTICO · {scope} · UTC {stamp}'],3);sh.merge(3,3,1,len(columns))
        sh.line(5,['Porcentajes: denominador explícito. Vacío: no estimable. Registros revisables no equivalen a diagnóstico.'],4);sh.merge(5,5,1,len(columns))
        sh.line(7,columns,2);sh.heights[7]=33
        for ridx,item in enumerate(rows,8):
            for cidx,key in enumerate(columns,1):sh.put(ridx,cidx,item.get(key),7 if ridx%2==0 else 8)
        sh.filter=f'A7:{colname(len(columns))}{max(7,7+len(rows))}'
        sheets.append(sh)
    dictionary=Sheet('DICCIONARIO',widths={1:23,2:27,3:37,4:47,5:27},freeze=6)
    dictionary.line(1,['Diccionario de las variables exportadas'],1);dictionary.merge(1,2,1,5)
    dictionary.line(3,['Los campos clínicos implementados siguen sujetos a la validación del protocolo y el IP.'],3);dictionary.merge(3,3,1,5)
    dictionary.line(6,['Tabla','Campo interno','Etiqueta','Codificación / definición','Procedencia'],2)
    row=7
    for table,fields in SPEC.items():
        if user.get('role')!='admin' and table in ('TRAZABILIDAD','CAMBIOS_CAMPO'):continue
        for k,label,meaning in fields:
            source=('Calculado en Excel' if table=='VISITAS' and k in ('radar_score','radar_class') else
                    'Validación del extracto' if table=='CALIDAD' else 'Base de datos del servidor')
            dictionary.line(row,[table,k,label,meaning,source],7 if row%2==0 else 8)
            dictionary.heights[row]=22;row+=1
    dictionary.filter=f'A6:E{row-1}'
    sheets.append(dictionary)
    if user.get('role')=='admin':
        sheets.append(tabular('TRAZABILIDAD',audit,scope))
        sheets.append(tabular('CAMBIOS_CAMPO',changes,scope))
    return package(sheets)
