"""V0/V1/V2 CRD workflow specification for the synthetic RADAR-CORUÑA pilot.

Version 0.11: candidate definitions, never a medically approved instrument.
Only observations already represented by patient, visit, and CRD-extra storage
are evaluated. Missing != 'no' and score=0 is a legitimate full assessment.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date

VERSION='0.11-draft'

# Unique field codes in exportable clinical capture. A source is attached to each
# field so future CRD revisions cannot silently reinterpret existing values.
BASELINE = [
    ('copd','EPOC confirmada','paciente','cribado'),
    ('consent','Consentimiento documentado','paciente','cribado'),
    ('regular','Seguimiento habitual en AP','paciente','cribado'),
    ('capacity','Capacidad para participar','paciente','cribado'),
    ('exclusion','Ausencia de criterios de exclusión','paciente','cribado'),
    ('weeks','Semanas desde última agudización','paciente','cribado'),
    ('enrolDate','Fecha basal','paciente','cribado'),
    ('age','Edad (años)','paciente','caracterizacion'),
    ('sex','Sexo registrado','paciente','caracterizacion'),
    ('smoking','Tabaquismo basal','paciente','caracterizacion'),
    ('packs','Paquetes-año (si procede)','paciente','condicional'),
    ('spiroDate','Fecha de espirometría','paciente','caracterizacion'),
    ('ratio','FEV1/FVC posbroncodilatador','paciente','caracterizacion'),
    ('fev1','FEV1 (% predicho)','paciente','caracterizacion'),
    ('priorEx','Agudizaciones previas 12 meses','paciente','caracterizacion'),
    ('priorHosp','Ingresos previos 12 meses','paciente','caracterizacion'),
]
VISIT = [
    ('rescue','RADAR · Medicación de rescate','visita','nucleo'),
    ('exacerb','RADAR · Agudizaciones 3 meses','visita','nucleo'),
    ('dyspnea','RADAR · Disnea','visita','nucleo'),
    ('activity','RADAR · Actividad física','visita','nucleo'),
    ('cat','CAT (0–40)','visita','nucleo'),
    ('mmrc','mMRC (0–4)','visita','nucleo'),
    ('action','Actuación clínica documentada','visita','nucleo'),
    ('smoking','Tabaquismo en seguimiento','visita','seguimiento'),
    ('inhaler','Técnica inhalatoria revisada','visita','actuaciones'),
    ('education','Educación / autocuidado','visita','actuaciones'),
    ('referral','Derivación a Neumología','visita','actuaciones'),
    ('lama','LAMA','visita','tratamiento'),
    ('laba','LABA','visita','tratamiento'),
    ('ics','Corticoide inhalado','visita','tratamiento'),
]
EXTRAS = [
    ('adherence_method','Método de adherencia (pendiente de consenso)','crd','condicional'),
    ('adherence_level','Adherencia (pendiente de consenso)','crd','condicional'),
    ('assessment_seconds','Duración de la evaluación','crd','operativa'),
    ('action_adherence_counsel','Intervención en adherencia','crd','actuaciones'),
    ('action_smoking_counsel','Consejo antitabaco','crd','actuaciones'),
    ('action_activity_counsel','Consejo sobre actividad','crd','actuaciones'),
    ('action_vaccine_review','Revisión vacunal','crd','actuaciones'),
    ('action_comorb_review','Revisión de comorbilidades','crd','actuaciones'),
    ('action_pulm_rehab_offer','Oferta de rehabilitación','crd','actuaciones'),
    ('action_inhaled_change','Cambio en tratamiento inhalado','crd','actuaciones'),
    ('longterm_oxygen','Oxigenoterapia domiciliaria','crd','condicional'),
    ('pulm_rehab','Rehabilitación respiratoria','crd','condicional'),
]
YES_NO={'si','no'}

def observed(x):
    # Numeric 0 must count as observed. "no consta" is *known missing*, not negative.
    return x is not None and x not in ('','nc','no_consta','pendiente','ne','no_evaluada')

def has_core_value(code,value):
    if code in ('rescue','exacerb','dyspnea','activity'):
        return value in YES_NO
    return observed(value)

def manifest():
    rows=[]
    for code,label,source,category in BASELINE:
        rows.append({'stage':'V0','code':code,'label':label,'source':source,
                     'section':category,'priority':'Propuesta de registro' if category!='condicional' else 'Si procede',
                     'approval':'Pendiente de aprobación clínica'})
    for code,label,source,category in VISIT+EXTRAS:
        rows.append({'stage':'V0/V1/V2','code':code,'label':label,'source':source,
                     'section':category,'priority':'Núcleo propuesto' if category=='nucleo' else 'Condicional / complementaria',
                     'approval':'Pendiente de aprobación clínica'})
    return rows

def build_workflow(patients,visits,observations=(),episodes=(),contacts=()):
    """Return centre-scoped CRD status and unresolved research-data review signals."""
    by_visit={(v['patient'],v['type']):v for v in visits}
    by_obs={(x['participant'],x['visit_type'],x['variable_code']):x.get('value') for x in observations}
    events=defaultdict(list); encounters=defaultdict(list)
    for x in episodes:events[x['patient']].append(x)
    for x in contacts:encounters[x['patient']].append(x)
    result=[]
    for p in sorted(patients,key=lambda x:x['id']):
        pid=p['id']
        for stage in ('V0','V1','V2'):
            v=by_visit.get((pid,stage))
            status='No registrada' if v is None else ('No realizada' if v['status']=='no_realizada' else 'Registrada')
            missing=[]; alerts=[]; core_count=0
            if v and v['status']!='no_realizada':
                for key,label,*_ in VISIT[:7]:
                    if has_core_value(key,v.get(key)):core_count+=1
                    else:missing.append(label)
                if core_count==7 and v.get('status')=='parcial':
                    alerts.append('Núcleo cumplimentado; estado de visita pendiente de confirmar')
                if v.get('status')=='completa' and core_count<7:
                    alerts.append('Declarada completa con información insuficiente')
                mmrc=v.get('mmrc')
                if mmrc is not None and v.get('dyspnea') in YES_NO and ((mmrc>=2)!=(v['dyspnea']=='si')):
                    alerts.append('Revisar discordancia entre mMRC y RADAR-D')
                adherence_method=by_obs.get((pid,stage,'adherence_method'))
                adherence_level=by_obs.get((pid,stage,'adherence_level'))
                if observed(adherence_level) and not observed(adherence_method):
                    alerts.append('Adherencia consignada sin método documentado')
            baseline_count=None;baseline_expected=None;baseline_missing=[]
            if stage=='V0':
                basal=BASELINE
                # Pack-years are conditional; missing in a never-smoker is not an alert.
                relevant=[x for x in basal if x[0]!='packs' or p.get('smoking') in ('actual','ex')]
                baseline_expected=len(relevant)
                baseline_count=sum(has_core_value(key,p.get(key)) for key,*_ in relevant)
                baseline_missing=[label for key,label,*_ in relevant if not has_core_value(key,p.get(key))]
                if p.get('status')=='incluido' and baseline_missing:
                    alerts.append('Caracterización basal pendiente de revisión (no equivale a inelegibilidad)')
            # These are study event *counts*, not inferred follow-up windows or outcomes.
            result.append({
                'patient':pid,'centre':p['center'],'stage':stage,'visit_status':status,
                'visit_date':v.get('date') if v else '',
                'core_present':core_count if v and v['status']!='no_realizada' else None,
                'core_expected':7 if v and v['status']!='no_realizada' else None,
                'core_missing':missing,'core_pct':round(core_count/7*100,1) if v and v['status']!='no_realizada' else None,
                'baseline_present':baseline_count,'baseline_expected':baseline_expected,
                'baseline_missing':baseline_missing,'alerts':alerts,
                'episode_count':len(events[pid]),'contact_count':len(encounters[pid]),
                'status_note':'Propuesta técnica · No constituye elegibilidad, aprobación ni cierre clínico'
            })
    return {'version':VERSION,'use_status':'SOLO SIMULACIÓN',
            'definition_status':'BORRADOR · requiere revisión del IP y equipo investigador',
            'manifest':manifest(),'rows':result,
            'summary':{'patients':len(patients),'visits':len(visits),
                       'core_complete':sum(r['core_pct']==100 for r in result),
                       'pending_baseline':sum(r['stage']=='V0' and bool(r['baseline_missing']) and r['visit_status']!='No realizada' for r in result),
                       'no_records':len(patients)==0}}
