"""Explicit synthetic test-data adapter for the stricter v0.32 inclusion contract.

Used ONLY by historical tests, never imported by the production API. Fields already
present in a test case are preserved, including invalid values in negative tests.
"""
from __future__ import annotations
from datetime import date, timedelta
from functools import wraps

def valid_record(payload:dict)->dict:
    record=dict(payload)
    if record.get('status') != 'incluido':
        return record
    base=date.fromisoformat(record.get('enrolDate') or '2026-01-10')
    record.setdefault('enrolDate',base.isoformat())
    age=record.get('age')
    age=65 if age is None else int(age)
    born=date(base.year-age,1,1)
    defaults={
        'birthDate':born.isoformat(),
        'copd':'si','regular':'si',
        'lastCopdReviewDate':(base-timedelta(days=150)).isoformat(),
        'weeks':5,'capacity':'si',
        'activeExacerb':'no','exclusion':'no',
        'alternativeDiagnosis':'no','seriousDecompensation':'no',
        'interferingTrial':'no','eligibilityDecision':'elegible',
        'consent':'si','consentDate':(base-timedelta(days=5)).isoformat(),
        'spiroDate':(base-timedelta(days=30)).isoformat(),
        'ratio':0.60,
    }
    for key,value in defaults.items():record.setdefault(key,value)
    return record

def valid_patient_factory(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):return valid_record(fn(*args,**kwargs))
    return wrapper
