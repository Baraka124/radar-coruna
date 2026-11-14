"""RADAR-CORUÑA v0.39 · deterministic read-only research intelligence.

No imputation; results are scoped by the API before entry. Every percentage includes
its actual denominator, and incomplete follow-up is not labelled overdue.
"""
from __future__ import annotations
from collections import Counter
from datetime import date
from phase18_reporting import pct, valid_cat, valid_mmrc
from phase12_analysis import radar_score, radar_category

STAGES = ('V0', 'V1', 'V2')
RADAR_FIELDS = ('rescue', 'exacerb', 'dyspnea', 'activity')


def iso(value):
    try: return date.fromisoformat(value) if value else None
    except (ValueError, TypeError): return None


def add_months(value, months):
    """Calendar months, day clamped to the target month; not 30-day approximations."""
    from calendar import monthrange
    n=value.year*12+(value.month-1)+months
    year, month=divmod(n, 12); month+=1
    return date(year, month, min(value.day, monthrange(year,month)[1]))


def collected(value):
    return value is not None and value != ''


def valid_visit(v):
    return v is not None and v.get('status') != 'no_realizada'


def make_intelligence(patients, visits, episodes=(), contacts=(), missing=(), observations=(), centres=()):
    """Return independent clinical-research indicators from an already-authorised snapshot.

    Centre-specific permissions MUST be checked upstream, not inferred from a browser filter.
    """
    people={p['id']:p for p in patients}
    enrolled={pid:p for pid,p in people.items() if p.get('status')=='incluido'}
    by_stage={(v['patient'],v['type']):v for v in visits if v.get('patient') in people and v.get('type') in STAGES}
    centre_codes=sorted({c.get('code') for c in centres if c.get('code')} | {p.get('center') for p in people.values() if p.get('center')})
    missing_by_key={(r['participant'],r['visit_type'],r['field_code']):r for r in missing if r.get('participant') in people}

    def stage_rows(pids, stage):
        current=[by_stage[(pid,stage)] for pid in pids if (pid,stage) in by_stage]
        performed=[v for v in current if valid_visit(v)]
        radar=[radar_score(v) for v in performed]
        radar=[s for s in radar if s is not None]
        cat=[v['cat'] for v in performed if valid_cat(v.get('cat'))]
        mmrc=[v['mmrc'] for v in performed if valid_mmrc(v.get('mmrc'))]
        return {'stage':stage,'included':len(pids),'visits_recorded':len(current),
                'visits_performed':len(performed),'visits_not_performed':len(current)-len(performed),
                'radar_evaluable':len(radar),'radar_denominator':len(performed),
                'radar_coverage_pct':pct(len(radar),len(pids)),
                'radar_within_performed_pct':pct(len(radar),len(performed)),
                'cat_evaluable':len(cat),'cat_denominator':len(performed),
                'mmrc_evaluable':len(mmrc),'mmrc_denominator':len(performed),
                'poor_radar_n':sum(s>=4 for s in radar), 'poor_radar_denominator':len(radar),
                'poor_radar_pct':pct(sum(s>=4 for s in radar),len(radar))}

    stages=[stage_rows(enrolled,stage) for stage in STAGES]
    centres_rows=[]
    for code in centre_codes:
        cpids={pid for pid,p in people.items() if p.get('center')==code}
        cids={pid for pid in cpids if pid in enrolled}
        s0=stage_rows(cids,'V0');s1=stage_rows(cids,'V1');s2=stage_rows(cids,'V2')
        centres_rows.append({'centre':code,'screening':len(cpids)-len(cids),'included':len(cids),
          'baseline_evaluable':s0['radar_evaluable'],'baseline_pct':s0['radar_coverage_pct'],
          'poor_baseline_n':s0['poor_radar_n'],'poor_baseline_denominator':s0['poor_radar_denominator'],
          'poor_baseline_pct':s0['poor_radar_pct'],'v1_performed':s1['visits_performed'],
          'v2_performed':s2['visits_performed'],'v2_evaluable':s2['radar_evaluable']})

    quality=[]
    def issue(pid,stage,code,level,message):
        p=people.get(pid)
        if p is None:return
        quality.append({'participant':pid,'centre':p.get('center'), 'stage':stage or '',
                        'code':code,'severity':level,'message':message})

    for pid,p in sorted(people.items()):
        if p.get('status')=='incluido':
            if not iso(p.get('birthDate')):issue(pid,'V0','BASE_BIRTH','revisar','Falta la fecha de nacimiento que permite verificar edad basal.')
            if not iso(p.get('enrolDate')):issue(pid,'V0','BASE_DATE','revisar','Falta la fecha de inclusión / V0.')
            if not collected(p.get('ratio')):issue(pid,'V0','BASE_SPIRO','revisar','Sin cociente espirométrico posbroncodilatador documentado.')
            if (pid,'V0') not in by_stage:issue(pid,'V0','V0_MISSING','informar','Participante incluido sin visita V0 registrada.')
        base=by_stage.get((pid,'V0'))
        base_date=iso(base.get('date')) if base and valid_visit(base) else None
        for stage in STAGES:
            v=by_stage.get((pid,stage))
            if v is None:continue
            if not valid_visit(v):
                if not v.get('reason'):issue(pid,stage,'VISIT_NONPERFORMED','revisar','Visita no realizada sin motivo registrado.')
                continue
            if not iso(v.get('date')):issue(pid,stage,'VISIT_DATE','revisar','Visita registrada sin fecha válida.')
            if v.get('status')=='completa':
                absent=[k for k in RADAR_FIELDS if v.get(k) not in ('si','no')]
                if absent:issue(pid,stage,'RADAR_INCOMPLETE','revisar','Visita completa con componentes RADAR ausentes: '+', '.join(absent))
            if stage in ('V1','V2') and base_date and iso(v.get('date')):
                m=6 if stage=='V1' else 12
                start,end=add_months(base_date,m-1),add_months(base_date,m+1)
                current=iso(v['date'])
                if not start<=current<=end:
                    issue(pid,stage,'VISIT_WINDOW','informar',f'Fecha fuera de la ventana prevista ({start.isoformat()} a {end.isoformat()}); conservar fecha real.')
            if stage=='V2' and by_stage.get((pid,'V1')) and valid_visit(by_stage[(pid,'V1')]):
                v1date=iso(by_stage[(pid,'V1')].get('date'));v2date=iso(v.get('date'))
                if v1date and v2date and v2date<v1date:issue(pid,stage,'VISIT_ORDER','revisar','V2 tiene una fecha anterior a V1.')

    for (pid,stage,field),row in sorted(missing_by_key.items()):
        v=by_stage.get((pid,stage));p=people.get(pid)
        if v is None or p is None:continue
        field_value=(v.get(field) if field in v else p.get(field) if field in p else None)
        if collected(field_value):issue(pid,stage,'MISSING_CONFLICT','revisar',f'El campo {field} tiene valor y también motivo de ausencia ({row.get("reason","")}).')
    for e in episodes:
        if e.get('patient') not in people:continue
        pid=e['patient']
        if not iso(e.get('date')):issue(pid,'','EPISODE_DATE','revisar','Episodio sin fecha válida.')
    event_index={e.get('id'):e for e in episodes if e.get('patient') in people}
    for c in contacts:
        if c.get('patient') not in people:continue
        eid=c.get('event')
        if eid and eid in event_index and event_index[eid].get('patient')!=c['patient']:
            issue(c['patient'],'','CONTACT_LINK','revisar','Contacto vinculado a un episodio de otro participante.')
    quality.sort(key=lambda x:(0 if x['severity']=='revisar' else 1,x['centre'] or '',x['participant'],x['stage'],x['code']))
    participant_rows=[]; paired_radar=paired_cat=paired_mmrc=0
    for pid,p in sorted(enrolled.items()):
        v={stage:by_stage.get((pid,stage)) for stage in STAGES}
        score={stage:radar_score(v[stage]) if valid_visit(v[stage]) else None for stage in STAGES}
        cat={stage:v[stage].get('cat') if valid_visit(v[stage]) and valid_cat(v[stage].get('cat')) else None for stage in STAGES}
        mmrc={stage:v[stage].get('mmrc') if valid_visit(v[stage]) and valid_mmrc(v[stage].get('mmrc')) else None for stage in STAGES}
        dr=score['V2']-score['V0'] if score['V0'] is not None and score['V2'] is not None else None
        dc=cat['V2']-cat['V0'] if cat['V0'] is not None and cat['V2'] is not None else None
        dm=mmrc['V2']-mmrc['V0'] if mmrc['V0'] is not None and mmrc['V2'] is not None else None
        paired_radar+=dr is not None;paired_cat+=dc is not None;paired_mmrc+=dm is not None
        participant_rows.append({'participant':pid,'centre':p.get('center'),
             'v0_date':v['V0'].get('date') if v['V0'] else None,
             'v1_date':v['V1'].get('date') if v['V1'] else None,
             'v2_date':v['V2'].get('date') if v['V2'] else None,
             **{f'radar_{s.lower()}':score[s] for s in STAGES},
             **{f'cat_{s.lower()}':cat[s] for s in STAGES},
             **{f'mmrc_{s.lower()}':mmrc[s] for s in STAGES},
             'delta_radar_v2_v0':dr,'delta_cat_v2_v0':dc,'delta_mmrc_v2_v0':dm,
             'issues_to_review':sum(x['participant']==pid and x['severity']=='revisar' for x in quality)})

    return {'version':'0.39','scope':'Centros autorizados por sesión',
      'counts':{'screening':len(people)-len(enrolled),'included':len(enrolled),
                'baseline_evaluable':stages[0]['radar_evaluable'],'poor_baseline_n':stages[0]['poor_radar_n'],
                'poor_baseline_denominator':stages[0]['poor_radar_denominator'],
                'poor_baseline_pct':stages[0]['poor_radar_pct'],
                'paired_radar':paired_radar,'paired_cat':paired_cat,'paired_mmrc':paired_mmrc,
                'quality_to_review':sum(x['severity']=='revisar' for x in quality),'quality_information':sum(x['severity']=='informar' for x in quality),
                'episode_records':sum(e.get('patient') in enrolled and e.get('kind','agudizacion')=='agudizacion' and e.get('copd')=='si' for e in episodes),
                'contact_records':sum(c.get('patient') in enrolled and c.get('copd')=='si' for c in contacts)},
      'stages':stages,'centres':centres_rows,'longitudinal':participant_rows,'quality':quality,
      'methodology':[
        'Población incluida: R023 incluido; cribados y no incluidos quedan fuera de los denominadores de seguimiento.',
        'Mal control basal: RADAR ≥4 / V0 con los cuatro ítems válidos; sin imputar los faltantes.',
        'Cobertura de cada escala: denominadores separados; CAT y mMRC no dependen de RADAR.',
        'Parejas V0–V2 calculadas sólo cuando ambas medidas son válidas; datos ausentes no equivalen a cero.',
        'Ventanas V1 6±1 y V2 12±1 meses son referencias de revisión: no se declaran visitas vencidas.',
        'Incidencias son comprobaciones automáticas de integridad, no dictámenes médicos.',
        'Episodios EPOC y contactos asistenciales son registros distintos; no se suman como nuevas exacerbaciones.',
        'La proporción de uso de RADAR en consultas EPOC no es estimable sin el denominador de consultas elegibles.',
        'Resultados descriptivos del entorno sintético; ninguna inferencia causal ni de eficacia.'
       ]}
