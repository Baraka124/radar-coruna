"""RADAR-CORUÑA phase 14: remaining 28 candidate variables and implementation metrics.

The schema follows the two supplied protocol drafts and the 107-field catalogue;
provisional definitions remain visible in the field dictionary.
"""
from __future__ import annotations
from datetime import date
from collections import Counter
import re

# Registry is the only source for validation, the investigator UI, and export headings.
# Kinds: centre, professional, screening, baseline, visit, implementation.
DEFINITIONS={
 'centre':{
  'center_start_date':('Fecha de activación', 'date', None),
  'center_end_use':('Uso de RADAR al cierre', 'choice', ['si','no','no_evaluable']),
 },
 'professional':{
  'clinician_role':('Función del profesional','choice',['medicina','enfermeria','coordinacion','otro']),
  'training_date':('Fecha de formación RADAR','date',None),
  'survey_utilidad':('Utilidad percibida (escala provisional 1–5)','integer_1_5',None),
  'survey_factibilidad':('Factibilidad (escala provisional 1–5)','integer_1_5',None),
 },
 'screening':{
  'screen_code':('Código único de cribado','screen_code',None),
  'screen_date':('Fecha de cribado','date',None),
  'alternative_diagnosis':('Diagnóstico alternativo excluyente','yesno',['si','no','no_consta']),
  'serious_decompensation':('Comorbilidad grave descompensada','yesno',['si','no','no_consta']),
  'interfering_trial':('Ensayo interferente','yesno',['si','no','no_consta']),
  'consent_date':('Fecha consentimiento','date',None),
 },
 'baseline':{
  'other_comorb':('Otra comorbilidad relevante (categoría provisional)','choice',['respiratoria','cardiovascular','metabolica','otra','ninguna','no_consta']),
  'charlson_index':('Índice Charlson (0–37)','integer_0_37',None),
  'flu_vax_up_to_date':('Vacunación antigripal al día','yesno',['si','no','no_consta']),
  'pneumo_vax_up_to_date':('Vacunación neumocócica al día','yesno',['si','no','no_consta']),
  'ccq_score':('Cuestionario CCQ (0–6; opcional)','decimal_0_6',None),
  'bode_score':('Índice BODE (0–10; opcional)','integer_0_10',None),
 },
 'visit':{
  'assessor_code':('Profesional evaluador','professional_code',None),
  'flu_vax_up_to_date':('Vacunación antigripal al día','yesno',['si','no','no_consta']),
  'pneumo_vax_up_to_date':('Vacunación neumocócica al día','yesno',['si','no','no_consta']),
  'ccq_score':('Cuestionario CCQ (0–6, si procede)','decimal_0_6',None),
  'clinical_notes_structured':('Actuación estandarizada (provisional)','choice',['sin_cambios','revision_tratamiento','refuerzo_adherencia','educacion','derivacion','otros','no_consta']),
 },
 'implementation':{
  'eligible_copd_visits':('Consultas EPOC candidatas a RADAR (denominador)','count',None),
  'visits_with_radar':('Consultas con RADAR completo (numerador)','count',None),
 },
}
# Clinician code is the canonical key of the professional record; it is not repeated
# as mutable data. Five of the 28 gaps are computed rather than new user inputs.
KEY_FIELD={'professional':'clinician_code'}
DERIVED14={
 'event_type':('Eventos normalizados','Tipo obtenido de episodio, urgencias, ingreso o estado vital'),
 'interval_urgent':('Resultados por intervalo','Urgencias EPOC entre visitas documentadas'),
 'centers_activated':('Indicadores implantación','Centros con fecha de activación documentada'),
 'professionals_trained':('Indicadores implantación','Profesionales con fecha de formación documentada'),
 'retention_v2':('Indicadores seguimiento','V2 registradas / participantes con V2 vencida según fecha de corte'),
}
FIELD_LOCATION={field:(kind,f'phase14_records.{kind}.{field}') for kind,defs in DEFINITIONS.items() for field in defs}
FIELD_LOCATION['clinician_code']=('professional','phase14_records.professional.key')


def describe():
 return {kind:[{'code':k,'label':v[0],'type':v[1],'choices':v[2] or []} for k,v in fields.items()] for kind,fields in DEFINITIONS.items()}


def validate_payload(kind, payload):
 if kind not in DEFINITIONS:raise ValueError('Sección no reconocida')
 if not isinstance(payload,dict) or set(payload)-set(DEFINITIONS[kind]):raise ValueError('Campos desconocidos en el registro')
 result={}
 for code,(label,typ,choices) in DEFINITIONS[kind].items():
  val=payload.get(code)
  if val is None or val=='':result[code]=None;continue
  if typ in ('choice','yesno'):
   if not isinstance(val,str) or val not in choices:raise ValueError(f'{label}: valor no permitido')
  elif typ=='date':
   if not isinstance(val,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',val):raise ValueError(f'{label}: fecha AAAA-MM-DD requerida')
   try:date.fromisoformat(val)
   except ValueError:raise ValueError(f'{label}: fecha inválida')
  elif typ=='screen_code':
   if not isinstance(val,str) or not re.fullmatch(r'SIM-SCR-[A-Za-z0-9_-]{1,16}',val):raise ValueError('Código de cribado debe comenzar por SIM-SCR-')
  elif typ=='professional_code':
   if not isinstance(val,str) or not re.fullmatch(r'SIM-PRO-[A-Za-z0-9_-]{1,16}',val):raise ValueError('Código del profesional: SIM-PRO-...')
  elif typ.startswith('integer') or typ=='count':
   if type(val) is not int:raise ValueError(f'{label}: entero requerido')
   maxi={'integer_1_5':5,'integer_0_37':37,'integer_0_10':10,'count':10000000}[typ]
   mini=1 if typ=='integer_1_5' else 0
   if not mini<=val<=maxi:raise ValueError(f'{label}: fuera de rango {mini}–{maxi}')
  elif typ=='decimal_0_6':
   if type(val) not in (int,float) or not 0<=val<=6:raise ValueError(f'{label}: valor de 0 a 6')
   val=round(float(val),2)
  else:raise ValueError('Tipo no disponible')
  result[code]=val
 if kind=='implementation':
  den,num=result['eligible_copd_visits'],result['visits_with_radar']
  if num is not None and den is None:raise ValueError('Indique primero el total de consultas candidatas')
  if num is not None and num>den:raise ValueError('Consultas RADAR no puede superar consultas candidatas')
 if kind=='screening' and result['consent_date'] and result['screen_date'] and result['consent_date']<result['screen_date']:
  raise ValueError('Fecha de consentimiento anterior al cribado: revisar')
 return result


def valid_key(kind,key):
 # Syntax validation only; API also checks an active centre in the DB.
 centre=r'[A-Z][A-Z0-9_-]{2,23}'
 if kind=='centre':return bool(re.fullmatch(centre,key))
 if kind=='professional':return bool(re.fullmatch(r'SIM-PRO-[A-Za-z0-9_-]{1,16}',key))
 if kind in ('screening','baseline'):return bool(re.fullmatch(r'SIM-[A-Za-z0-9_-]{1,20}',key))
 if kind=='visit':return bool(re.fullmatch(r'SIM-[A-Za-z0-9_-]{1,20}:(V0|V1|V2)',key))
 if kind=='implementation':return bool(re.fullmatch(centre+r':\d{4}-(0[1-9]|1[0-2])',key))
 return False

def group_records(rows):
 return {k:sorted([r for r in rows if r['kind']==k],key=lambda r:r['key']) for k in DEFINITIONS}


def make_indicators(rows,patients,visits,centres,cutoff=None):
 """Compute only metrics for which we have an explicit denominator.

 Missing monthly counts do not mean zero eligible consultations.
 V2 retention is reported for participants with twelve calendar months elapsed.
 """
 cutoff=cutoff or date.today().isoformat()
 groups=group_records(rows)
 centre_map={r['key']:r for r in groups['centre']}
 active=[c for c in centres if (centre_map.get(c['code'],{}).get('payload',{}).get('center_start_date') or '9999-12-31')<=cutoff]
 professionals=groups['professional']
 trained=[p for p in professionals if p['payload'].get('training_date')]
 month_rows=groups['implementation']
 observed=[x for x in month_rows if x['key'].split(':')[1] <= cutoff[:7] and x['payload'].get('eligible_copd_visits') is not None and x['payload'].get('visits_with_radar') is not None]
 denominator=sum(x['payload']['eligible_copd_visits'] for x in observed)
 numerator=sum(x['payload']['visits_with_radar'] for x in observed)
 # Monthly rows with missing numerator/denominator are omitted and explicitly counted.
 incomplete=len(month_rows)-len(observed)
 qualifying=[]
 for p in patients:
  if p.get('status')!='incluido':continue
  start=p.get('enrolDate')
  if not start:continue
  try:
   d=date.fromisoformat(start)
   try:due=d.replace(year=d.year+1)
   except ValueError:due=d.replace(year=d.year+1,day=28)
  except Exception:continue
  if due.isoformat()<=cutoff:qualifying.append(p['id'])
 v2={v['patient'] for v in visits if v.get('type')=='V2' and v.get('status')=='completa'}
 reten_num=sum(p in v2 for p in qualifying)
 result=[
  {'indicator':'Centros activados','numerator':len(active),'denominator':len(centres),'value':len(active),'unit':'n','note':'Fecha de activación consignada'},
  {'indicator':'Profesionales formados','numerator':len(trained),'denominator':len(professionals),'value':len(trained),'unit':'n','note':'Fecha de formación documentada'},
  {'indicator':'Adopción RADAR en consultas elegibles','numerator':numerator if observed else None,'denominator':denominator if observed else None,'value':round(100*numerator/denominator,1) if denominator else None,'unit':'%','note':f'{len(observed)} meses-centro completos; {incomplete} incompletos. No equiparar con visitas de la cohorte.'},
  {'indicator':'% profesionales registrados con formación','numerator':len(trained) if professionals else None,'denominator':len(professionals) if professionals else None,'value':round(100*len(trained)/len(professionals),1) if professionals else None,'unit':'%','note':'Denominador = profesionales registrados en la aplicación; no es el total de plantilla.'},
  {'indicator':'Seguimiento V2 al cumplirse 12 meses','numerator':reten_num if qualifying else None,'denominator':len(qualifying) if qualifying else None,'value':round(100*reten_num/len(qualifying),1) if qualifying else None,'unit':'%','note':f'Corte {cutoff}. Solo incluidos con 12 meses transcurridos; requiere revisión de ventanas y pérdidas.'},
 ]
 return {'indicators':result,'month_rows':month_rows,'groups':groups,'as_of':cutoff,'incomplete_month_rows':incomplete}


def normalized_events(patients,episodes,contacts):
 out=[]
 for e in episodes:
  out.append({'participant':e['patient'],'date':e['date'],'event_type':e.get('kind','agudizacion'),'source_id':e['id'],'related_episode':'','copd':e.get('copd'),'note':f"Episodio R074 {e.get('episodeNo', '?')} contado por separado"})
 for c in contacts:
  out.append({'participant':c['patient'],'date':c['date'],'event_type':c['type'],'source_id':c['id'],'related_episode':c.get('event',''),'copd':c.get('copd'),'note':'Contacto no añade agudización'})
 for p in patients:
  if p.get('vitalStatus')=='fallecido' and p.get('deathDate'):
   out.append({'participant':p['id'],'date':p['deathDate'],'event_type':'defuncion','source_id':p['id'],'related_episode':'','copd':'','note':'Estado vital del participante'})
 return sorted(out,key=lambda r:(r['participant'],r['date'],r['event_type']))


def reconcile_legacy_analysis(report, metrics):
    """Make previously unestimable v0.12 indicators consistent with v0.14 inputs."""
    replacements={
      '% visitas EPOC con RADAR':'Adopción RADAR en consultas elegibles',
      '% profesionales formados':'% profesionales registrados con formación',
    }
    lookup={m['indicator']:m for m in metrics.get('indicators',[])}
    for r in report['metrics']:
        indicator=replacements.get(r['indicator'])
        if indicator is None:continue
        m=lookup[indicator]
        r.update(numerator=m['numerator'],denominator=m['denominator'],value=m['value'],unit='%',
          interpretation=m['note'] + (' · No estimable hasta disponer del denominador' if m['value'] is None else ''))
    report['unavailable']=[r['indicator'] for r in report['metrics'] if r['value'] is None and r['indicator'] in replacements]
    return report
