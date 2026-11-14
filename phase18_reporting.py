"""Phase 18: reproducible *descriptive* reporting from the recorded synthetic cohort.

No imputation, no undocumented denominators, no causal effect claims.
RADAR and CAT paired samples are independent, a crucial distinction.
Clinical/methodological definitions in this report remain proposed pending investigator sign-off.
"""
from __future__ import annotations

from collections import Counter
from math import sqrt
from statistics import mean, median

from phase16_usability import radar, category
from phase14_completion import make_indicators

STAGES = ('V0', 'V1', 'V2')
CATEGORIES = ('Buen control', 'Control parcial', 'Mal control')


def valid_cat(value):
    return type(value) in (int, float) and 0 <= value <= 40


def valid_mmrc(value):
    return type(value) is int and 0 <= value <= 4


def pct(num, den):
    return round(100 * num / den, 1) if den else None


def wilson_95(success, total):
    """Binomial Wilson score interval; descriptive precision, not study validation."""
    if not total:
        return (None, None)
    z=1.959963984540054
    p=success/total
    d=1+z*z/total
    mid=(p+z*z/(2*total))/d
    half=z*sqrt((p*(1-p)+z*z/(4*total))/total)/d
    return (round(100*max(0,mid-half),1), round(100*min(1,mid+half),1))


def complete(v):
    return v is not None and v.get('status')!='no_realizada'


def make_report(patients,visits,episodes=(),contacts=(),implementation=(),centres=(),cutoff=None):
    """Input data must be filtered to the requesting user's study-centre scope."""
    enrolled={p['id']:p for p in patients if p.get('status')=='incluido'}
    byvisit={}
    for v in visits:
        key=(v.get('patient'),v.get('type'))
        if v.get('patient') in enrolled and v.get('type') in STAGES and complete(v):
            byvisit[key]=v
    # Denominators: enrolled participants, observed visits, complete instruments.
    distributions=[]
    stage_summary={}
    for stage in STAGES:
        observed=[v for (pid,st),v in byvisit.items() if st==stage]
        classified=[radar(v) for v in observed]
        classified=[s for s in classified if s is not None]
        classes=Counter(category(s) for s in classified)
        cat_values=[float(v['cat']) for v in observed if valid_cat(v.get('cat'))]
        mmrc_values=[v['mmrc'] for v in observed if valid_mmrc(v.get('mmrc'))]
        for cat in CATEGORIES:
            distributions.append({'visit':stage,'category':cat,'n':classes[cat],
                'denominator':len(classified),'percent':pct(classes[cat],len(classified))})
        stage_summary[stage]={
            'visit':stage,'enrolled':len(enrolled),'visits_recorded':len(observed),
            'radar_complete':len(classified),'radar_incomplete_recorded':len(observed)-len(classified),
            'radar_coverage_pct':pct(len(classified),len(enrolled)),
            'cat_recorded':len(cat_values),'cat_median':round(median(cat_values),2) if cat_values else None,
            'cat_mean':round(mean(cat_values),2) if cat_values else None,
            'mmrc_recorded':len(mmrc_values),'radar_mean':round(mean(classified),2) if classified else None,
            'poor_n':classes['Mal control'],'poor_pct':pct(classes['Mal control'],len(classified))
        }
    pairs=[]
    radar_deltas=[]; cat_deltas=[]; mmrc_deltas=[]
    transitions=Counter()
    for pid in sorted(enrolled):
        a,b=byvisit.get((pid,'V0')),byvisit.get((pid,'V2'))
        s0=radar(a) if a else None
        s2=radar(b) if b else None
        c0=a.get('cat') if a else None
        c2=b.get('cat') if b else None
        m0=a.get('mmrc') if a else None
        m2=b.get('mmrc') if b else None
        has_radar=s0 is not None and s2 is not None
        has_cat=valid_cat(c0) and valid_cat(c2)
        has_mmrc=valid_mmrc(m0) and valid_mmrc(m2)
        dr=s2-s0 if has_radar else None
        dc=round(c2-c0,2) if has_cat else None
        dm=m2-m0 if has_mmrc else None
        if has_radar:
            radar_deltas.append(dr)
            transitions[(category(s0),category(s2))]+=1
        if has_cat:cat_deltas.append(dc)
        if has_mmrc:mmrc_deltas.append(dm)
        pairs.append({'participant':pid,'centre':enrolled[pid].get('center'),
            'v0_date':a.get('date') if a else None,'v2_date':b.get('date') if b else None,
            'radar_v0':s0,'radar_v2':s2,'paired_radar':'si' if has_radar else 'no',
            'delta_radar':dr,'control_v0':category(s0),'control_v2':category(s2),
            'cat_v0':c0 if valid_cat(c0) else None,'cat_v2':c2 if valid_cat(c2) else None,
            'paired_cat':'si' if has_cat else 'no','delta_cat':dc,
            'mmrc_v0':m0 if valid_mmrc(m0) else None,'mmrc_v2':m2 if valid_mmrc(m2) else None,
            'paired_mmrc':'si' if has_mmrc else 'no','delta_mmrc':dm})
    n_transitions=sum(transitions.values())
    transition_rows=[{'control_v0':before,'control_v2':after,'n':transitions[(before,after)],
                     'denominator':n_transitions or None,'percent':pct(transitions[(before,after)],n_transitions)}
                     for before in CATEGORIES for after in CATEGORIES]
    poor=stage_summary['V0']['poor_n']
    base_n=stage_summary['V0']['radar_complete']
    ci=wilson_95(poor,base_n)
    # Episodes and contacts are *registered records*, not independently verified incidence.
    raw_eps=sum(e.get('patient') in enrolled and e.get('copd')=='si' and e.get('kind','agudizacion')=='agudizacion' for e in episodes)
    raw_er=sum(c.get('patient') in enrolled and c.get('copd')=='si' and c.get('type')=='urgencias' for c in contacts)
    raw_adm=sum(c.get('patient') in enrolled and c.get('copd')=='si' and c.get('type')=='ingreso' for c in contacts)
    indicator_rows=[]
    def add(group,label,n,d,val,unit,scope,notes):
        indicator_rows.append({'group':group,'indicator':label,'numerator':n,'denominator':d,
            'value':val,'unit':unit,'population':scope,'interpretation':notes})
    add('COHORTE','Participantes incluidos',len(enrolled),None,len(enrolled),'n','Todos los incluidos','Recuento registrado')
    add('RADAR V0','RADAR basal completo',base_n,len(enrolled),pct(base_n,len(enrolled)),'%','Participantes incluidos','Cobertura de medida; no sustituye el CRD completo')
    add('RADAR V0','Mal control basal RADAR ≥4',poor,base_n,pct(poor,base_n),'%', 'RADAR V0 clasificable','Prevalencia descriptiva de registros completos')
    add('RADAR V0','IC 95% Wilson · límite inferior',None,base_n,ci[0],'%', 'RADAR V0 clasificable','Intervalo orientativo; método sujeto a plan estadístico')
    add('RADAR V0','IC 95% Wilson · límite superior',None,base_n,ci[1],'%', 'RADAR V0 clasificable','Intervalo orientativo; método sujeto a plan estadístico')
    add('SEGUIMIENTO','RADAR V1 completo',stage_summary['V1']['radar_complete'],len(enrolled),stage_summary['V1']['radar_coverage_pct'],'%','Participantes incluidos','No inferir que la visita es vencida')
    add('SEGUIMIENTO','RADAR V2 completo',stage_summary['V2']['radar_complete'],len(enrolled),stage_summary['V2']['radar_coverage_pct'],'%','Participantes incluidos','No inferir que la visita es vencida')
    add('PAREJAS','RADAR V0–V2 pareado',len(radar_deltas),len(enrolled),pct(len(radar_deltas),len(enrolled)),'%','Participantes incluidos','Solo registros RADAR completos en ambos tiempos')
    add('PAREJAS','Cambio medio RADAR V2−V0',None,len(radar_deltas),round(mean(radar_deltas),2) if radar_deltas else None,'puntos','Parejas RADAR válidas','Cambio descriptivo; ninguna atribución causal')
    add('PAREJAS','CAT V0–V2 pareado',len(cat_deltas),len(enrolled),pct(len(cat_deltas),len(enrolled)),'%','Participantes incluidos','Independiente de la completitud de RADAR')
    add('PAREJAS','Cambio medio CAT V2−V0',None,len(cat_deltas),round(mean(cat_deltas),2) if cat_deltas else None,'puntos','Parejas CAT válidas','Cambio descriptivo; ninguna atribución causal')
    add('PAREJAS','mMRC V0–V2 pareado',len(mmrc_deltas),len(enrolled),pct(len(mmrc_deltas),len(enrolled)),'%','Participantes incluidos','Independiente de RADAR y CAT')
    add('PAREJAS','Cambio medio mMRC V2−V0',None,len(mmrc_deltas),round(mean(mmrc_deltas),2) if mmrc_deltas else None,'puntos','Parejas mMRC válidas','Escala ordinal: interpretación descriptiva provisional')
    add('EVENTOS','Agudizaciones EPOC registradas',raw_eps,None,raw_eps,'n','Eventos en base de datos','Recuento bruto; NO tasa de incidencia')
    add('EVENTOS','Urgencias EPOC registradas',raw_er,None,raw_er,'n','Contactos en base de datos','No sumar a agudizaciones')
    add('EVENTOS','Ingresos EPOC registrados',raw_adm,None,raw_adm,'n','Contactos en base de datos','No sumar a agudizaciones')
    # Only calculate implementation adoption using explicitly reported monthly denominators.
    adoption=make_indicators(implementation,patients,visits,centres,cutoff=cutoff)['indicators'] if centres else []
    for m in adoption:
        add('IMPLANTACIÓN',m['indicator'],m['numerator'],m['denominator'],m['value'],m['unit'],
            'Registros de implantación',' '+m['note'])
    center_rows=[]
    for centre in sorted(set(p['center'] for p in enrolled.values())):
        ids={pid for pid,p in enrolled.items() if p['center']==centre}
        scores=[radar(byvisit[(pid,'V0')]) for pid in ids if (pid,'V0') in byvisit]
        complete_scores=[x for x in scores if x is not None]
        center_rows.append({'centre':centre,'included':len(ids),'radar_v0_complete':len(complete_scores),
          'poor_v0':sum(x>=4 for x in complete_scores),'poor_pct':pct(sum(x>=4 for x in complete_scores),len(complete_scores)),
          'radar_v2_complete':sum(radar(byvisit[(pid,'V2')]) is not None for pid in ids if (pid,'V2') in byvisit)})
    return {'version':'0.18-scientific-report-draft','counts':{'included':len(enrolled),'recorded_patients':len(patients),
       'baseline_complete':base_n,'radar_pairs':len(radar_deltas),'cat_pairs':len(cat_deltas)},
       'stages':[stage_summary[s] for s in STAGES],'indicators':indicator_rows,'distributions':distributions,
       'pairs':pairs,'transitions':transition_rows,'centres':center_rows,
       'methodology':[
        {'rule':'Cohorte','definition':'Solo participantes con estado incluido; cribados fuera del denominador clínico'},
        {'rule':'RADAR completo','definition':'Cuatro respuestas SI/NO; 0 es una puntuación válida; no_realizada excluida'},
        {'rule':'Prevalencia basal','definition':'RADAR V0 ≥4 / todos los RADAR V0 completos; no / todos los incluidos'},
        {'rule':'IC 95%','definition':'Wilson binomial para proporción basal, solo demostrativo; confirmar plan estadístico'},
        {'rule':'Parejas RADAR','definition':'V0 y V2 clasificables; delta = V2 – V0'},
        {'rule':'Parejas CAT','definition':'CAT V0 y V2 válidos [0,40], independientemente de RADAR'},
        {'rule':'Parejas mMRC','definition':'mMRC V0 y V2 válidos [0,4], independientemente de RADAR'},
        {'rule':'Transiciones','definition':'Nueve combinaciones V0→V2 con denominador de parejas RADAR completas'},
        {'rule':'Visitas futuras','definition':'Una V1 o V2 no registrada no se considera automáticamente pérdida o retraso'},
        {'rule':'Eventos','definition':'Agudización, urgencias e ingreso son registros distintos; no sumar ni presentar como tasas'},
        {'rule':'Implantación','definition':'Consultas RADAR / consultas EPOC elegibles, únicamente meses-centro documentados'},
        {'rule':'Interpretación','definition':'Resultados descriptivos de prueba; cambios no demuestran efecto causal'}
       ],'scientific_status':'Propuesta técnica · requiere conformidad metodológica de los investigadores'}
