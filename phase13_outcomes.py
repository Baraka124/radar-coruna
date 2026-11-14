"""Phase 13 · Structured eligibility and outcome accounting for a SYNTHETIC study.

Clinical definitions remain PROVISIONAL until approval by the investigators.
All event counts are descriptive; contacts do not add to exacerbation counts.
"""
from __future__ import annotations

MISSING_FIELDS={'cat','mmrc','rescue','exacerb','dyspnea','activity','adherence','action',
                'fev1','ratio','spiroDate','priorEx','priorHosp'}
BASE_FIELDS={'fev1','ratio','spiroDate','priorEx','priorHosp'}

def gold_airflow_grade(p):
    """Proposed GOLD airflow obstruction grades; require post-BD COPD confirmation.
    Not the GOLD A/B/E clinical grouping. No inference when measurement unavailable.
    """
    ratio,fev1=p.get('ratio'),p.get('fev1')
    if ratio is None or fev1 is None or ratio>=0.70 or fev1<0:
        return None
    return 4 if fev1<30 else 3 if fev1<50 else 2 if fev1<80 else 1


def screening_rows(patients):
    rows=[]
    for p in sorted(patients,key=lambda x:x['id']):
        age=p.get('age')
        warns=[]
        if p.get('status')=='incluido':
            if p.get('eligibilityDecision','pendiente')!='elegible':
                warns.append('Decisión formal de elegibilidad por confirmar')
            if age is None or age<40:warns.append('Edad no documentada o inferior a 40 años')
            if p.get('regular')!='si':warns.append('Seguimiento habitual AP pendiente')
            if p.get('capacity')!='si':warns.append('Capacidad para responder pendiente')
            if p.get('exclusion')!='no':warns.append('Criterios de exclusión pendientes')
            if p.get('activeExacerb','') not in ('no',):warns.append('Agudización activa no descartada')
            if p.get('ratio') is None or p.get('ratio')>=0.70:warns.append('Obstrucción pos-BD no verificada')
        if p.get('vitalStatus')=='fallecido' and not p.get('deathDate'):
            warns.append('Fecha de fallecimiento no documentada')
        rows.append({
            'participant':p['id'],'center':p['center'],'status':p.get('status','cribado'),
            'eligibility_decision':p.get('eligibilityDecision','pendiente'),
            'active_exacerbation':p.get('activeExacerb',''),
            'screen_failure_reason':p.get('screenFailureReason',''),
            'age_eligible': ('si' if age>=40 else 'no') if age is not None else '',
            'fev1_pct_pred':p.get('fev1'),
            'ratio_postbd':p.get('ratio'),
            'gold_airflow_grade':gold_airflow_grade(p),
            'vital_status':p.get('vitalStatus',''),
            'death_date':p.get('deathDate',''),
            'death_cause':p.get('deathCause',''),
            'review':'; '.join(warns),
        })
    return rows


def visit_value(p, v, field):
    if field in BASE_FIELDS:return p.get(field)
    return v.get(field)


def make_outcomes(patients,visits,episodes=(),contacts=(),missing=()):
    pby={p['id']:p for p in patients}
    vby={(v['patient'],v['type']):v for v in visits}
    stage_pairs=(('V0','V1'),('V1','V2'),('V0','V2'))
    intervals=[]
    for pid,p in sorted(pby.items()):
        if p.get('status')!='incluido':continue
        for first,last in stage_pairs:
            a=vby.get((pid,first));b=vby.get((pid,last))
            if not a or not b or a.get('status')=='no_realizada' or b.get('status')=='no_realizada':continue
            start,end=a['date'],b['date']
            if end<=start:continue
            es={e['id']:e for e in episodes if e.get('patient')==pid and start<e.get('date','')<=end}
            cs={c['id']:c for c in contacts if c.get('patient')==pid and start<c.get('date','')<=end}
            included=[e for e in es.values() if e.get('copd')=='si' and e.get('kind','agudizacion')=='agudizacion']
            intervals.append({
                'participant':pid,'center':p['center'],'interval':first+'→'+last,
                'date_from':start,'date_to':end,
                'exacerbations_copd':len(included),
                'exacerbations_moderate':sum(e.get('severity')=='moderada' for e in included),
                'exacerbations_severe':sum(e.get('severity')=='grave' for e in included),
                'exacerbations_indeterminate':sum(e.get('severity')=='indeterminada' for e in included),
                'er_copd':sum(c.get('type')=='urgencias' and c.get('copd')=='si' for c in cs.values()),
                'admissions_copd':sum(c.get('type')=='ingreso' and c.get('copd')=='si' for c in cs.values()),
                'note':'Contactos y episodios distintos. Incluye fecha final; excluye fecha inicial. Fechas y categorías requieren revisión clínica.',
            })
    reasons=[];conflicts=[]
    for m in missing:
        p=pby.get(m['participant'])
        if not p:continue
        row={k:m[k] for k in ('participant','visit_type','field_code','reason','rev','username','updated_at')}
        row['center']=p['center']
        v=vby.get((m['participant'],m['visit_type']))
        existing=visit_value(p,v,m['field_code']) if v else None
        # 'pendiente', 'nc' and empty are not actual measurements
        valid=existing is not None and existing not in ('','nc','ne','pendiente')
        row['conflict']='Motivo de ausencia coexistente con dato registrado' if valid else ''
        reasons.append(row)
        if valid: conflicts.append(row)
    return {'version':'0.13-draft','scope':'Solo simulación; no inferencia clínica',
            'eligibility':screening_rows(patients),'intervals':intervals,
            'missing':reasons,'missing_conflicts':conflicts,
            'methodological_cautions':[
                'GOLD 1-4 deriva de FEV1 % predicho y ratio pos-BD, no sustituye revisión clínica.',
                'La decisión de elegibilidad corresponde al investigador y el periodo de estabilidad sigue pendiente.',
                'Una agudización y un contacto asistencial pueden pertenecer al mismo episodio.',
                'No se imputan ceros ante datos ausentes; no se infiere el seguimiento de una visita no registrada.',
                'Las ventanas y definiciones de resultados deberán quedar fijadas en el protocolo autorizado.'
            ]}
