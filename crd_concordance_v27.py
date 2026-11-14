"""RADAR-CORUÑA: documented concordance between printed CRD and application fields.
Scientific approvals are not inferred; this is an implementation crosswalk.
"""
from __future__ import annotations
from collections import Counter
from study_module import STUDY,ALLOWED_EXTRA
from phase12_analysis import MAP,DERIVED
from phase14_completion import FIELD_LOCATION,DERIVED14

PRINTED_CODES={1,5,10,11,12,13,14,15,16,17,18,19,20,21,22,23,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,62,63,64,65,66,67,68,69,70,71,74,75,76,77,78,79,80,81,82,83,84,85,86,90,91,92,93,94,95,96,97,98,99,103,107}
# Printed identifiers deliberately do NOT include R024 (removed non-inclusion reason), or derived recount R087-089.
REVIEW={
 'R016':'Ayuda se registra como opción distinta de Sí/No.',
 'R024':'Campo heredado en Patient.screenFailureReason: eliminado del CRD en papel por indicación clínica; no recapturar.',
 'R043':'Texto libre de otras comorbilidades; si el catálogo controlado se aprueba, definir codificación antes de análisis.',
 'R045':'LAMA/LABA/ICS se derivan de la pauta inhalada de V0/V1/V2; en monoterapia se selecciona la clase.',
 'R046':'Véase R045: régimen combinado y bandera individual compatibles.',
 'R047':'Véase R045: régimen combinado y bandera individual compatibles.',
 'R048':'Entrada principal en Visit.rescuePrescription; medición complementaria heredada no debe duplicarse.',
 'R049':'El CRD impreso lo solicita en basal; el catálogo histórico admite seguimiento. Confirmar capturas posteriores.',
 'R050':'El CRD impreso lo solicita en basal; el catálogo histórico admite seguimiento. Confirmar capturas posteriores.',
 'R051':'Captura integrada en V0; el catálogo anterior también menciona V1/V2, pendiente de ratificar.',
 'R052':'Captura integrada en V0; el catálogo anterior también menciona V1/V2, pendiente de ratificar.',
 'R053':'Las agudizaciones moderadas y graves se registran por separado; Patient.priorEx se deriva de ambos cuando se informan.',
 'R055':'En el CRD vigente significa consulta IANUS verificada/no verificable. La variable antigua adherence_method NO es equivalente.',
 'R056':'En el CRD vigente significa últimas recetas recogidas Sí/No/NV; período exacto pendiente. La variable antigua adherence_level NO es equivalente.',
 'R065':'Código del evaluador de cada visita registrado en Visit.assessorCode. Revisar conexión con catálogo profesional R005.',
 'R076':'El tipo de episodio se registra en Episode.kind; el catálogo original puede describirlo como derivado.',
 'R083':'Fuente por episodio; lista validada de valores.',
 'R090':'Actuación por visita en el CRD complementario. No se sustituye automáticamente por el campo histórico de Visit.',
 'R099':'La actuación plan documentado (Sí/No/NA/NC) es distinta del texto Visit.action.',
 'R103':'Duración en segundos, opcional y vinculada a visita.',
 'R107':'Motivo de ausencia conservado en tabla missing_data; el CRD impreso usa NR/ND/NP/NA y las categorías digitales requieren conciliación.'
}

def rows():
 out=[]
 for v in STUDY['variables']:
  code,id=v['code'],int(v['id'][1:]);printed=id in PRINTED_CODES
  if code in MAP: typ='Campo principal';source=MAP[code][1]
  elif code in ALLOWED_EXTRA: typ='CRD complementario';source='study_observations.'+code
  elif code in DERIVED: typ='Cálculo';source=DERIVED[code][1]
  elif code in FIELD_LOCATION: typ='Registro auxiliar';source=FIELD_LOCATION[code][1]
  elif code in DERIVED14: typ='Cálculo';source=DERIVED14[code][1]
  else: typ='No implementado';source='—'
  if id in (51,52): typ='Campo principal · solo V0'
  if id in (55,56): typ='Campo principal · significado actualizado'
  if id==24: typ='Conservado por compatibilidad · fuera del CRD'
  if id==107:typ='Captura parcial · conciliación pendiente'
  if id in (45,46,47,53,65,76):typ='Campo principal · verificar mapeo'
  out.append({'id':id,'variable':code,'label':v['label'],'printed_crd':printed,
   'implementation':typ,'technical_source':source,'review':REVIEW.get(f'R{id:03d}',''),
   'moment':v.get('moment',''),'priority':v.get('priority_proposed','')})
 return out

def report():
 r=rows()
 return {'version':'0.27','total_catalogue':len(r),'printed_code_count':sum(x['printed_crd'] for x in r),
  'counts':dict(Counter(x['implementation'] for x in r)),
  'pending_corrections':[x for x in r if x['review']],'variables':r}
