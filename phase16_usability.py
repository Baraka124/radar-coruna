"""Phase 16 · participant worklist and reproducible research extracts.

Pure transformations on already authorised synthetic dataset. No visit is
considered overdue from its stage alone; protocol timing requires agreement.
"""
from collections import Counter

STAGES=('V0','V1','V2')
RADAR=('rescue','exacerb','dyspnea','activity')
WEIGHTS=(3,2,2,1)


def radar(v):
    if v is None or v.get('status')=='no_realizada' or any(v.get(k) not in ('si','no') for k in RADAR):
        return None
    return sum(w for k,w in zip(RADAR,WEIGHTS) if v[k]=='si')


def category(value):
    return None if value is None else 'Buen control' if value<=1 else 'Control parcial' if value<=3 else 'Mal control'


def pending_work(patients,visits):
    """Return one next useful action per participant, plus any recorded visit gaps.

    Later stages are not called late simply because they are unrecorded.
    """
    by_patient={}
    for v in visits:
        by_patient.setdefault(v['patient'],{})[v['type']]=v
    work=[]
    for p in sorted(patients,key=lambda x:x['id']):
        pv=by_patient.get(p['id'],{})
        task={'participant':p['id'],'centre':p['center'],'visit':'', 'priority':'Pendiente',
              'step':'','detail':'','action':'participant','status':p.get('status','cribado')}
        if p.get('status')!='incluido':
            if p.get('eligibilityDecision')=='no_elegible':
                task.update(priority='Sin pendientes de núcleo',step='Cribado cerrado',detail='No elegible; sin tareas de inclusión automáticas',action='detail')
            else:
                task.update(step='Completar cribado',detail='Confirmar elegibilidad e inclusión según el protocolo',action='screen')
        elif not pv.get('V0'):
            task.update(visit='V0',step='Registrar V0',detail='Evaluación basal aún no registrada',action='visit')
        else:
            for stage in STAGES:
                v=pv.get(stage)
                if v and v.get('status')=='no_realizada':
                    task.update(visit=stage,priority='Revisión',step='Visita no realizada',detail='Revisar seguimiento sin crear una visita duplicada',action='visit');break
                if v and v.get('status')!='no_realizada':
                    incomplete=[k for k in RADAR if v.get(k) not in ('si','no')]
                    if incomplete:
                        task.update(visit=stage,step='Completar RADAR',detail=', '.join(incomplete),action='visit');break
                    missing=[k for k in ('cat','mmrc') if v.get(k) is None]
                    if not v.get('action'):missing.append('action')
                    if missing:
                        task.update(visit=stage,step='Completar núcleo de visita',detail=', '.join(missing),action='visit');break
                elif not v:
                    prev='V0' if stage=='V1' else 'V1'
                    if stage!='V0' and pv.get(prev) and pv[prev].get('status')=='completa':
                        task.update(visit=stage,priority='Próxima etapa',step='Preparar '+stage,
                                    detail='Seguimiento previsto; fecha de cita no establecida por esta comprobación',action='visit')
                    break
            else:
                task.update(priority='Sin pendientes de núcleo',step='Revisar resultados',detail='V0, V1 y V2 tienen los campos básicos registrados',action='detail')
        work.append(task)
    return work


def analysis_long(patients,visits):
    pmap={p['id']:p for p in patients}
    rows=[]
    for v in sorted(visits,key=lambda z:(z['patient'],STAGES.index(z['type']))):
        p=pmap.get(v['patient'])
        if not p:continue
        s=radar(v)
        performed=v.get('status')!='no_realizada'
        rows.append({'participant':v['patient'],'centre':p['center'],'visit':v['type'],'date':v['date'],
         'visit_status':v.get('status',''), 'radar_complete':'si' if s is not None else 'no',
         'rescue':v.get('rescue',''),'exacerb':v.get('exacerb',''),'dyspnea':v.get('dyspnea',''),
         'activity':v.get('activity',''),'radar_score':s,'radar_class':category(s),
         'cat':v.get('cat') if performed else None,'mmrc':v.get('mmrc') if performed else None,
         'action':v.get('action','') if performed else '',
         'age_v0':p.get('age'),'sex':p.get('sex',''),'fev1_pct':p.get('fev1'),
         'fev1_fvc':p.get('ratio'), 'smoking_baseline':p.get('smoking','')})
    return rows


def cohort_wide(patients,visits,episodes,contacts):
    by_patient={}
    for v in visits:by_patient.setdefault(v['patient'],{})[v['type']]=v
    ep=Counter(e['patient'] for e in episodes if e.get('copd')=='si')
    er=Counter(c['patient'] for c in contacts if c.get('copd')=='si' and c.get('type')=='urgencias')
    admits=Counter(c['patient'] for c in contacts if c.get('copd')=='si' and c.get('type')=='ingreso')
    out=[]
    for p in sorted(patients,key=lambda x:x['id']):
        x=by_patient.get(p['id'],{});a=x.get('V0');b=x.get('V1');c=x.get('V2')
        s0=radar(a);s1=radar(b);s2=radar(c)
        cat0=a.get('cat') if a and a.get('status')!='no_realizada' else None
        cat2=c.get('cat') if c and c.get('status')!='no_realizada' else None
        out.append({'participant':p['id'],'centre':p['center'],'status':p.get('status',''),
           'age_v0':p.get('age'),'sex':p.get('sex',''),'v0_date':a.get('date','') if a else '',
           'v1_date':b.get('date','') if b else '', 'v2_date':c.get('date','') if c else '',
           'radar_v0':s0,'radar_v1':s1,'radar_v2':s2,
           'radar_delta_v2_v0':s2-s0 if s0 is not None and s2 is not None else None,
           'cat_v0':cat0,'cat_v2':cat2,
           'cat_delta_v2_v0':cat2-cat0 if cat0 is not None and cat2 is not None else None,
           'ep_copd_recorded':ep[p['id']],'emergency_copd_recorded':er[p['id']],
           'admissions_copd_recorded':admits[p['id']],
           'paired_radar':'si' if s0 is not None and s2 is not None else 'no'})
    return out
