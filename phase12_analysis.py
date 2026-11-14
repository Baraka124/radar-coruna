"""RADAR-CORUÑA Phase 12: evidence-to-capture mapping and cautious analysis.

All counts are descriptive synthetic-pilot checks, NEVER verified research
results. Definitions are proposed and require PI/statistical sign-off.
"""
from __future__ import annotations
from collections import Counter
from statistics import mean
from study_module import STUDY,ALLOWED_EXTRA
from phase14_completion import FIELD_LOCATION,DERIVED14

# Grounded mappings to fields that can actually be entered in the v0.11 forms,
# recorded by the server, or explicitly calculated from persisted records.
MAP = {

 # CRD v0.27: individual screening, baseline and assessment fields in main workflow.
 'alternative_diagnosis':('Cribado R017','Patient.alternativeDiagnosis'),
 'serious_decompensation':('Cribado R019','Patient.seriousDecompensation'),
 'interfering_trial':('Cribado R020','Patient.interferingTrial'),
 'consent_date':('Cribado R022','Patient.consentDate'),
 'other_comorb':('Basal R043','Patient.otherComorbidities'),
 'charlson_index':('Basal R044','Patient.charlson'),
 'flu_vax_up_to_date':('Basal R051','Patient.fluVaccination (V0; V1/V2 documental pendiente)'),
 'pneumo_vax_up_to_date':('Basal R052','Patient.pneumococcalVaccination (V0; V1/V2 documental pendiente)'),
 'assessor_code':('Visita R065','Visit.assessorCode'),
 'center_code':('Registro de participante','Patient.center'),
 'center_name':('Catálogo estático','CENTRES.name'),
 'participant_code':('Registro de participante','Patient.id'),
 'enrolment_date':('Registro de participante','Patient.enrolDate'),
 'age_years':('Registro de participante','Patient.age'),
 'sex_recorded':('Registro de participante','Patient.sex'),
 'smoking_status':('Registro de participante','Patient.smoking'),
 'pack_years':('Registro de participante','Patient.packs'),
 'spiro_date':('Registro de participante','Patient.spiroDate'),
 'fev1_fvc_postbd':('Registro de participante','Patient.ratio'),
 'fev1_pct_pred':('Registro de participante','Patient.fev1'),
 'prior_exacerb_12m':('Registro de participante','Patient.priorEx'),
 'prior_hosp_12m':('Registro de participante','Patient.priorHosp'),
 'comorb_htn':('Registro de participante','Patient.comorbHtn'),
 'comorb_hf':('Registro de participante','Patient.comorbHf'),
 'comorb_diabetes':('Registro de participante','Patient.comorbDm'),
 'comorb_osa':('Registro de participante','Patient.comorbOsa'),
 'confirmed_copd':('Cribado','Patient.copd'),
 'regular_ap_followup':('Cribado','Patient.regular'),
 'stable_weeks':('Cribado','Patient.weeks'),
 'can_answer':('Cribado','Patient.capacity'),
 'consent_status':('Cribado','Patient.consent'),
 'visit_code':('Formulario de visita','Visit.type'),
 'visit_date':('Formulario de visita','Visit.date'),
 'visit_status':('Formulario de visita','Visit.status'),
 'visit_missing_reason':('Formulario de visita','Visit.reason'),
 'cat_score':('Formulario de visita','Visit.cat'),
 'mmrc_grade':('Formulario de visita','Visit.mmrc'),
 'adherence_method':('IANUS R055, revisión de definición','Visit.ianusVerified; legacy study_observations:adherence_method (otro significado)'),
 'adherence_level':('IANUS R056, revisión de definición','Visit.ianusCollected; legacy study_observations:adherence_level (otro significado)'),
 'radar_rescue':('Formulario de visita','Visit.rescue'),
 'radar_exacerb':('Formulario de visita','Visit.exacerb'),
 'radar_dyspnea':('Formulario de visita','Visit.dyspnea'),
 'radar_activity':('Formulario de visita','Visit.activity'),
 'rescue_med_current':('Tratamiento R048','Visit.rescuePrescription; legacy study_observations:rescue_med_current'),
 'inhaler_lama':('Formulario de visita','Visit.lama'),
 'inhaler_laba':('Formulario de visita','Visit.laba'),
 'inhaler_ics':('Formulario de visita','Visit.ics'),
 'event_code':('Episodios','Episode.episodeNo (R074); ID técnico: Episode.id'),
 'event_date':('Episodios','Episode.date'),
 'exacerbation_severity':('Episodios','Episode.severity'),
 'exacerb_treat_steroid':('Episodios','Episode.steroids'),
 'exacerb_treat_antibiotic':('Episodios','Episode.antibiotics'),
 'event_source':('Episodios','Episode.source'),
 'emergency_attendance':('Episodios','Episode.emergencyStatus (R081) y emergencyDate; contactos separados'),
 'hospital_admission':('Episodios','Episode.admissionStatus (R082) y admissionDate; contactos separados'),
 'event_copd_related':('Episodios','Episode.copd'),
 'active_exacerbation':('Cribado v0.13','Patient.activeExacerb'),
 'data_missing_reason':('Motivos v0.13','missing_data:participant/visit_type/field_code/reason'),
 'eligible_final':('Cribado v0.13','Patient.eligibilityDecision (decisión del investigador)'),
 'screen_failure_reason':('Cribado v0.13','Patient.screenFailureReason'),
 'vital_status':('Estado final v0.13','Patient.vitalStatus'),
 'death_date':('Estado final v0.13','Patient.deathDate'),
 'death_cause_class':('Estado final v0.13','Patient.deathCause'),
}
DERIVED = {
 'radar_total':('Cálculo','Score(3,2,2,1), solo cuatro respuestas completas'),
 'radar_class':('Cálculo','0–1 / 2–3 / >=4, solo RADAR completo'),
 'change_radar_v0_v2':('Cálculo v0.12','Diferencia V2-V0 en pareja completa'),
 'change_cat_v0_v2':('Cálculo v0.12','Diferencia CAT V2-V0 en pareja con ambos CAT'),
 'age_eligible':('Cálculo v0.13','Patient.age >= 40; no decisión automática'),
 'gold_airflow_grade':('Cálculo v0.13','FEV1 % predicho y cociente pos-BD <0.70, GOLD 1-4; revisión clínica'),
 'interval_exacerbations':('Cálculo v0.13','Episodios EPOC por intervalos observados entre visitas'),
 'interval_admissions':('Cálculo v0.13','Contactos de ingreso EPOC por intervalos observados'),
}

def catalogue_coverage():
    result=[]
    for v in STUDY['variables']:
        code=v['code']
        if code in MAP: status,location='Capturable',MAP[code][1]
        elif code in ALLOWED_EXTRA: status,location='CRD ampliado',f'study_observations:{code}'
        elif code in DERIVED: status,location='Derivada / provisional',DERIVED[code][1]
        elif code in FIELD_LOCATION: status,location='Capturable',FIELD_LOCATION[code][1]
        elif code in DERIVED14: status,location='Derivada / provisional',DERIVED14[code][1]
        else: status,location='No implementada','—' 
        result.append({'id':v['id'],'code':code,'label':v['label'],
                       'entity':v.get('entity',''),'priority':v.get('priority_proposed',''),
                       'status':status,'location':location,'evidence':v.get('evidence',''),
                       'pending':v.get('pending',''),'approver':v.get('validator','')})
    return result

def radar_score(v):
    keys=('rescue','exacerb','dyspnea','activity')
    if v.get('status')=='no_realizada' or not all(v.get(k) in ('si','no') for k in keys): return None
    return sum(w for k,w in zip(keys,(3,2,2,1)) if v[k]=='si')

def radar_category(n):
    if n is None:return None
    return 'Buen control' if n<=1 else 'Control parcial' if n<=3 else 'Mal control'

def make_analysis(patients, visits, episodes=(),contacts=()):
    """Cross-centre or single-centre scope must be handled before this call."""
    cohort={p['id']:p for p in patients if p.get('status')=='incluido'}
    byvisit={(v['patient'],v['type']):v for v in visits if v['patient'] in cohort and v.get('status')!='no_realizada'}
    v0={pid:byvisit.get((pid,'V0')) for pid in cohort}
    v2={pid:byvisit.get((pid,'V2')) for pid in cohort}
    baseline={pid:radar_score(v) for pid,v in v0.items() if v}
    assessed={pid:n for pid,n in baseline.items() if n is not None}
    poor=sum(n>=4 for n in assessed.values())
    paired=[]
    for pid in sorted(cohort):
        a=v0.get(pid);b=v2.get(pid)
        if not a or not b: continue
        sa=radar_score(a);sb=radar_score(b)
        if sa is None or sb is None: continue
        ca=a.get('cat');cb=b.get('cat')
        paired.append({'participant':pid,'center':cohort[pid]['center'],
         'date_v0':a.get('date'),'date_v2':b.get('date'),
         'radar_v0':sa,'radar_v2':sb,'delta_radar':sb-sa,
         'control_v0':radar_category(sa),'control_v2':radar_category(sb),
         'cat_v0':ca,'cat_v2':cb,'delta_cat':cb-ca if isinstance(ca,int) and isinstance(cb,int) else None,
         'interpretation':'Cambio descriptivo; NO causalidad atribuible a RADAR'})
    assessed_n=len(assessed)
    pct=round(100*poor/assessed_n,1) if assessed_n else None
    # Keep the legacy descriptive CAT indicator aligned with the Phase 18
    # independent CAT-pair rule, even when RADAR is incomplete.
    cat_deltas=[]
    for pid in cohort:
        a=v0.get(pid);b=v2.get(pid)
        if not a or not b:continue
        ca,cb=a.get('cat'),b.get('cat')
        if type(ca) is int and type(cb) is int and 0<=ca<=40 and 0<=cb<=40:
            cat_deltas.append(cb-ca)
    # Counts are NOT incidence rates: without a fully ascertained observation
    # window and complete reporting, zero database rows is not evidence of zero events.
    metrics=[
     ('COHORTE','Participantes incluidos',len(cohort),None,len(cohort),'Recuento administrativo'),
     ('RADAR V0','Basales con RADAR completo',assessed_n,len(cohort),round(100*assessed_n/len(cohort),1) if cohort else None,'Cobertura, no prevalencia'),
     ('RADAR V0','Mal control basal (RADAR ≥4)',poor,assessed_n,pct,'Denominador = basales clasificables; no usar total reclutado'),
     ('SEGUIMIENTO','Parejas V0–V2 con RADAR completo',len(paired),len(cohort),round(100*len(paired)/len(cohort),1) if cohort else None,'No imputar ausencias / pérdidas'),
     ('SEGUIMIENTO','Cambio medio RADAR V2−V0',None,len(paired),round(mean(x['delta_radar'] for x in paired),2) if paired else None,'Descriptivo; sin inferencia de eficacia'),
     ('SEGUIMIENTO','Cambio medio CAT V2−V0',None,len(cat_deltas),round(mean(cat_deltas),2) if cat_deltas else None,'Solo parejas CAT completas; sin causalidad'),
     ('EVENTOS','Episodios EPOC registrados',sum(e.get('copd')=='si' and e.get('kind','agudizacion')=='agudizacion' and e.get('patient') in cohort for e in episodes),None,None,'Conteo de registros; NO tasa de exacerbación'),
     ('EVENTOS','Contactos EPOC registrados',sum(c.get('copd')=='si' and c.get('patient') in cohort for c in contacts),None,None,'Contacto independiente de episodio; NO sumar a exacerbaciones'),
     ('IMPLANTACIÓN','% visitas EPOC con RADAR',None,None,None,'NO CALCULABLE: falta total de consultas elegibles, incluidas sin RADAR'),
     ('IMPLANTACIÓN','% profesionales formados',None,None,None,'NO CALCULABLE: falta registro profesional y denominador'),
    ]
    report=[{'group':g,'indicator':name,'numerator':num,'denominator':den,'value':val,
             'unit':'%' if name.startswith(('Mal control','Basales con','Parejas V0','%')) else ('puntos' if name.startswith('Cambio') else 'n' if name.startswith(('Participantes','Episodios','Contactos')) else ''),
             'interpretation':notes} for g,name,num,den,val,notes in metrics]
    coverage=catalogue_coverage()
    counts=dict(Counter(x['status'] for x in coverage))
    return {'version':'0.12-scientific-draft','status':'PILOTO SINTÉTICO · NO APROBADO',
      'methodology':'Denominadores explícitos, análisis pareado y no estimabilidad documentada',
      'metrics':report,'paired':paired,'coverage':coverage,
      'coverage_counts':counts,'total_variables':len(coverage),
      'decisions':STUDY['decisions'],'unavailable':[m['indicator'] for m in report if m['interpretation'].startswith('NO CALCULABLE')]}
