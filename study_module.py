"""Versioned scientific CRD catalogue and strict validation for the synthetic RADAR study.

The catalogue is a proposed study specification, not an ethics-approved CRD.
This extension records only fields not already represented by v0.8's specialised forms.
"""
from __future__ import annotations
import json
import re
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parent
STUDY=json.loads((ROOT/'study_spec_v09.json').read_text(encoding='utf-8'))
CATALOGUE={v['code']:v for v in STUDY['variables']}
# Fields already stored in Patient, Visit, Episode or Contact; do not duplicate them.
EXISTING={
 'center_code','center_name','participant_code','enrolment_date',
 'age_years','sex_recorded','smoking_status','pack_years','spiro_date','fev1_fvc_postbd','fev1_pct_pred',
 'prior_exacerb_12m','prior_hosp_12m','comorb_htn','comorb_hf','comorb_diabetes','comorb_osa',
 'inhaler_lama','inhaler_laba','inhaler_ics','cat_score','mmrc_grade',
 'visit_code','visit_date','visit_status','visit_missing_reason',
 'radar_rescue','radar_exacerb','radar_dyspnea','radar_activity','radar_total','radar_class',
 'event_code','event_date','event_source','exacerbation_severity','exacerb_treat_steroid',
 'exacerb_treat_antibiotic',
 # R090/R098 use the CRD-expanded visit-specific capture; historic Visit fields remain readable.
}
# All fields with a visit-specific meaning that can be captured in the expanded CRD.
ALLOWED_EXTRA={
 'comorb_ihd','comorb_depression','comorb_anxiety','comorb_cachexia',
 'rescue_med_current','longterm_oxygen','pulm_rehab','adherence_method','adherence_level',
 'action_adherence_counsel','action_smoking_counsel','action_activity_counsel',
 'action_vaccine_review','action_comorb_review','action_pulm_rehab_offer',
 'action_inhaled_change','action_plan_documented','action_inhaler_tech',
 'action_specialty_referral','assessment_seconds'
}
# Additional less urgent fields remain in the research catalogue, but are disabled pending approval.
VALUE_OPTIONS={
 'comorb_ihd':['si','no','no_consta'],
 'comorb_depression':['si','no','no_consta'],
 'comorb_anxiety':['si','no','no_consta'],
 'comorb_cachexia':['si','no','no_consta'],
 'rescue_med_current':['SABA','SAMA','ambos','otro','ninguno','no_consta'],
 'longterm_oxygen':['si','no','no_consta'],
 'pulm_rehab':['en_curso','realizada','no','no_consta'],
 'adherence_method':['cualitativo','instrumento_validado','pendiente'],
 'adherence_level':['buena','regular','mala','no_evaluada'],
 'action_inhaler_tech':['si','no','no_aplica','no_consta'],
 'action_specialty_referral':['si','no','no_aplica','no_consta'],
 'action_adherence_counsel':['si','no','no_aplica','no_consta'],
 'action_smoking_counsel':['si','no','no_aplica','no_consta'],
 'action_activity_counsel':['si','no','no_aplica','no_consta'],
 'action_vaccine_review':['si','no','no_aplica','no_consta'],
 'action_comorb_review':['si','no','no_aplica','no_consta'],
 'action_pulm_rehab_offer':['si','no','no_aplica','no_consta'],
 'action_inhaled_change':['si','no','no_aplica','no_consta'],
 'action_plan_documented':['si','no','no_aplica','no_consta']
}
VISIT_SCOPE={'V0','V1','V2'}


def available(code,visit):
    if code not in ALLOWED_EXTRA or visit not in VISIT_SCOPE:
        return False
    if code in ('comorb_ihd','comorb_depression','comorb_anxiety','comorb_cachexia'):
        return visit=='V0'
    return True


def validate(code,visit,value):
    if not available(code,visit):
        raise ValueError('Variable no habilitada en esta visita')
    if value is None or value=='':
        return None # Empty means do not record a measurement, not 'No'.
    if code=='assessment_seconds':
        if type(value) is not int or not (0 <= value <= 7200):
            raise ValueError('Duración: número entero entre 0 y 7200 segundos')
        return value
    if not isinstance(value,str) or value not in VALUE_OPTIONS[code]:
        raise ValueError('El valor no pertenece al catálogo de la variable')
    return value


def public_catalogue():
    # Map the actual persisted fields, not merely conceptual candidate names.
    from phase12_analysis import catalogue_coverage
    trace={x['code']:x for x in catalogue_coverage()}
    rows=[]
    for row in STUDY['variables']:
        r=dict(row)
        mapping=trace[r['code']]
        r['implementation']=mapping['status']
        r['technical_source']=mapping['location']
        scope=[v for v in ('V0','V1','V2') if available(r['code'],v)]
        # Do not present old non-equivalent R055/R056 or duplicate R048 as new CRD entries.
        # Their stored historical values remain available for explicit reconciliation.
        legacy_view_only={'adherence_method','adherence_level','rescue_med_current'}
        if r['code'] in legacy_view_only:scope=[]
        # R049/R050 are on the printed basal page; preserve historical follow-up values.
        if r['code'] in ('longterm_oxygen','pulm_rehab'):scope=['V0']
        r['visit_scope']=scope
        r['legacy_input_hidden']=r['code'] in legacy_view_only
        r['choices']=VALUE_OPTIONS.get(r['code'],[])
        r['approved']=False
        rows.append(r)
    return {'version':STUDY['version'],'status':STUDY['status'],'variables':rows,'decisions':STUDY['decisions']}
