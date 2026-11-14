"""Proposed protocol-consistency checks and visit completeness for RADAR-CORUÑA.

The clinical drafts are unapproved. All alerts are advisory; even a clean
technical report NEVER establishes scientific approval or patient eligibility.
Never use on actual patient data in this demonstrator.
"""
from __future__ import annotations
from collections import Counter
from datetime import date
import calendar

VISIT_FIELDS=(('rescue','R · Rescate'),('exacerb','A · Agudización'),('dyspnea','D · Disnea'),('activity','A · Actividad'),('cat','CAT'),('mmrc','mMRC'),('action','Plan documentado'))
GATES=[
 ('G01','Protocolo y variable principal','Pendiente','IP y apoyo estadístico; cierre de las decisiones metodológicas'),
 ('G02','Definición de elegibilidad','Pendiente','IP; estabilidad 4 frente a 4–8 semanas y criterios de inclusión'),
 ('G03','RADAR y herramientas clínicas','Pendiente','IP / Neumología; versión, autorización de reproducción y uso'),
 ('G04','CRD, manual de variables y análisis','Pendiente','IP / AP / Estadística; aprobación y prueba con profesionales'),
 ('G05','Evaluación ética y gobernanza','No verificado','Comité competente y responsable de tratamiento de datos'),
 ('G06','Entorno clínico e identidad','No implementado','Autenticación individual, hosting autorizado, seguridad y respaldo'),
 ('G07','Aceptación en centros','Pendiente','Pruebas de usuario con investigación y Atención Primaria'),
]


def _add_months(baseline, months):
    year=baseline.year+(baseline.month-1+months)//12
    month=(baseline.month-1+months)%12+1
    return date(year,month,min(baseline.day,calendar.monthrange(year,month)[1]))


def _is_missing(value):
    return value is None or value=='' or value=='nc'


def make_review(patients, visits, episodes, contacts, decisions=()):
    """Return scoped, non-identifying synthetic review data for UI and Excel.

    No automatic clinical exclusions. Dates use calendar months. V1/V2 windows
    are only proposed, never a protocol-enforced threshold.
    """
    issues=[]; coverage=[]
    ps={p['id']:p for p in patients}
    pv={pid:[] for pid in ps}
    for v in visits:
        pv.setdefault(v['patient'],[]).append(v)

    def flag(rule, priority, pid, stage, issue, suggestion):
        issues.append({'rule':rule,'severity':priority,'patient':pid,'item':stage,
                       'issue':issue,'suggestion':suggestion})

    for p in patients:
        if p.get('status')!='incluido':
            # Cribado can legitimately be incomplete; don't inflate clinical alerts.
            continue
        pid=p['id']; pvs=pv.get(pid,[])
        if not any(v.get('type')=='V0' for v in pvs):
            flag('R01','Prioritaria',pid,'V0','Participante incluido sin visita basal','Documentar o revisar V0')
        if p.get('consent')!='si':
            flag('R02','Prioritaria',pid,'Cribado','Consentimiento no confirmado','Revisar documentación de consentimiento')
        if p.get('regular')!='si' or p.get('capacity')!='si' or p.get('exclusion')!='no':
            flag('R03','Revisar',pid,'Cribado','Criterios de elegibilidad incompletos o discordantes','Revisión por investigador; no decisión automática de inclusión')
        if p.get('age') is None:
            flag('R04','Revisar',pid,'Basal','Edad sin registrar','Completar edad si procede')
        elif p['age']<40:
            flag('R04','Prioritaria',pid,'Cribado','Edad inferior a 40 años','Revisar criterio de inclusión con el IP')
        if _is_missing(p.get('sex')):
            flag('R05','Revisar',pid,'Basal','Sexo no registrado','Revisar si falta dato basal')
        if p.get('ratio') is None or p.get('fev1') is None:
            flag('R06','Revisar',pid,'Espirometría','Faltan parámetros espirométricos basales','Registrar cociente FEV1/FVC y FEV1 % predicho')
        elif p['ratio']>=.70:
            flag('R06','Prioritaria',pid,'Espirometría','FEV1/FVC pos-BD ≥0,70','Verificar confirmación diagnóstica según protocolo')
        weeks=p.get('weeks')
        if weeks is None:
            flag('R07','Revisar',pid,'Cribado','Periodo de estabilidad sin registrar','Registrar y validar definición final')
        elif weeks<4:
            flag('R07','Prioritaria',pid,'Cribado','Estabilidad inferior a 4 semanas','Revisión clínica; los borradores exigen al menos 4 semanas')
        elif weeks<8:
            flag('R07','Informativa',pid,'Cribado','Estabilidad entre 4 y 8 semanas','Los borradores discrepan; no establecer exclusión automática')

    for v in visits:
        pid=v['patient'];vt=v['type']; datev=v.get('date','')
        if v.get('status')!='no_realizada':
            present={k: not _is_missing(v.get(k)) for k,_ in VISIT_FIELDS}
            filled=sum(present.values()); total=len(present)
            coverage.append({'patient':pid,'visit':vt,'date':datev,'visit_status':v['status'],
                             'fields_present':filled,'fields_expected':total,
                             'missing_fields':', '.join(label for key,label in VISIT_FIELDS if not present[key]),
                             'completeness_pct':round(filled/total*100,1)})
            if filled!=total:
                flag('R08','Revisar',pid,vt,f'CRD central incompleto ({filled}/{total})','Completar si está disponible; lo ausente no equivale a No')
            if v.get('status')=='completa' and filled!=total:
                flag('R09','Prioritaria',pid,vt,'Visita completa sin el núcleo mínimo','Revisar estado de la visita')
            mmrc=v.get('mmrc'); dyspnea=v.get('dyspnea')
            if mmrc is not None and dyspnea in ('si','no') and ((mmrc>=2)!=(dyspnea=='si')):
                flag('R10','Revisar',pid,vt,'Discordancia entre mMRC y componente D de RADAR','Comprobar transcripción y versión del instrumento')
        else:
            coverage.append({'patient':pid,'visit':vt,'date':datev,'visit_status':v['status'],
                             'fields_present':0,'fields_expected':0,'missing_fields':'Visita no realizada',
                             'completeness_pct':None})
        p=ps.get(pid)
        if p and vt in ('V1','V2') and p.get('enrolDate') and datev:
            try:
                b=date.fromisoformat(p['enrolDate']); observed=date.fromisoformat(datev)
                n=6 if vt=='V1' else 12
                lo,hi=_add_months(b,n-1),_add_months(b,n+1)
                if not lo<=observed<=hi:
                    flag('R11','Informativa',pid,vt,f'Fuera de ventana orientativa {n} ± 1 mes',
                         'Confirmar ventana definitiva en el protocolo; no excluir automáticamente')
            except ValueError: pass
        if p and vt=='V2':
            v1=next((w for w in pv.get(pid,[]) if w['type']=='V1'),None)
            if v1 is None:
                flag('R12','Revisar',pid,'V2','V2 sin evaluación V1 registrada','Aclarar pérdida o evaluación de seguimiento intermedio')
            elif datev and v1.get('date') and datev < v1['date']:
                flag('R12','Prioritaria',pid,'V2','V2 anterior a V1','Corregir orden cronológico')

    for e in episodes:
        p=ps.get(e['patient'])
        if p and e.get('date') and p.get('enrolDate') and e['date']<p['enrolDate']:
            flag('R13','Revisar',e['patient'],'Episodio '+e['id'],
                 'Episodio anterior a inclusión','Determinar si corresponde a antecedente basal')
    by_event={e['id']:e for e in episodes}
    for c in contacts:
        if c.get('event') and (c['event'] not in by_event or by_event[c['event']]['patient']!=c['patient']):
            flag('R14','Prioritaria',c['patient'],'Contacto '+c['id'],
                 'Referencia a episodio inexistente o ajeno','Revisar vinculación entre contacto y episodio')

    return {'version':'0.10.0','use_status':'NO APTO PARA DATOS REALES',
            'scope':'Revisión técnica orientativa de simulación; no sustituye juicio clínico',
            'issues':issues,'visit_coverage':coverage,'gates':[{'id':a,'name':b,'status':c,'requirement':d} for a,b,c,d in GATES],
            'open_decisions':sum(d.get('status')=='Sin acordar' for d in decisions),
            'metrics':{'participants':len(patients),'visits':len(visits),'findings':len(issues),
                       'prioritary':sum(x['severity']=='Prioritaria' for x in issues),
                       'core_visits_complete':sum(x['fields_expected']>0 and x['fields_present']==x['fields_expected'] for x in coverage)} }
