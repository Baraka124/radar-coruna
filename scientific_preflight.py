"""RADAR-CORUÑA Phase 5: observational scientific UAT preflight.

Read-only checks that FLAG possible mismatches between the 09/11/2026 clinical
protocol and a synthetic pilot database. They neither establish clinical
eligibility nor modify records, endpoints, scores, or exports.
"""
from __future__ import annotations

import calendar
from datetime import date
from typing import Any

CRITERIA_VERSION = 'RADAR-2026-11-09/UAT-v0.32'


def _months_after(day: date, offset: int) -> date:
    m = (day.month - 1) + offset
    year = day.year + m // 12
    month = m % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def evaluate_participant(person: dict[str, Any], visits: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return potential gaps for scientific review; no automatic approval/exclusion."""
    visits = visits or []
    findings: list[dict[str, str]] = []

    def add(level: str, code: str, issue: str):
        findings.append({'level': level, 'code': code, 'issue': issue})

    pid = str(person.get('id', ''))
    if not pid.startswith('SIM-'):
        raise ValueError('El preflight sólo acepta identificadores sintéticos SIM-.')
    if person.get('status') != 'incluido':
        return {'participant': pid, 'stage': 'cribado', 'findings': [],
                'conclusion': 'Cribado: no evaluado como participante incluido'}

    age = person.get('age')
    if age is None:
        add('revisar', 'EDAD', 'No consta edad basal evaluable; contrastar fecha de nacimiento.')
    elif age < 40:
        add('bloqueo', 'EDAD', 'Edad inferior a 40 años frente a criterio del protocolo.')
    if not person.get('birthDate'):
        add('revisar', 'R026', 'No consta fecha completa de nacimiento requerida por CRD.')

    if person.get('copd') != 'si':
        add('bloqueo', 'EPOC', 'EPOC no confirmada como Sí para inclusión.')
    if not person.get('spiroDate'):
        add('revisar', 'ESPIROMETRIA_FECHA', 'No consta fecha de espirometría documentada.')
    ratio = person.get('ratio')
    if ratio is None:
        add('revisar', 'FEV1_FVC', 'No consta cociente FEV1/FVC posbroncodilatador.')
    elif not 0 <= ratio < 0.70:
        add('bloqueo', 'FEV1_FVC', 'FEV1/FVC no es inferior a 0,70, criterio de inclusión.')

    weeks = person.get('weeks')
    if weeks is None:
        add('revisar', 'ESTABILIDAD_4_SEMANAS', 'No consta intervalo de estabilidad documentado.')
    elif weeks < 4:
        add('bloqueo', 'ESTABILIDAD_4_SEMANAS', 'Menos de 4 semanas de estabilidad clínica.')
    if person.get('activeExacerb') == 'si':
        add('bloqueo', 'AGUDIZACION_ACTIVA', 'Se ha indicado agudización activa.')
    elif person.get('activeExacerb') != 'no':
        add('revisar', 'AGUDIZACION_ACTIVA', 'La ausencia de agudización activa no está confirmada.')

    if person.get('regular') == 'no':
        add('bloqueo', 'SEGUIMIENTO_AP', 'Seguimiento habitual previo marcado como No.')
    elif person.get('regular') != 'si':
        add('revisar', 'SEGUIMIENTO_AP', 'Falta confirmar seguimiento habitual en centro.')
    documented = person.get('lastCopdReviewDate')
    baseline_day = person.get('enrolDate')
    if not documented:
        add('revisar', 'VISITA_AP_ANO_PREVIO', 'No consta fecha de control EPOC en el año previo.')
    elif baseline_day:
        try:
            review_date = date.fromisoformat(documented)
            reference = date.fromisoformat(baseline_day)
            try: earliest = reference.replace(year=reference.year-1)
            except ValueError: earliest = reference.replace(year=reference.year-1,day=28)
            if not earliest <= review_date < reference:
                add('bloqueo','VISITA_AP_ANO_PREVIO', 'Control EPOC no fechado en el año anterior a V0.')
        except ValueError:
            add('revisar','VISITA_AP_ANO_PREVIO','Fecha de última consulta AP inválida.')

    if person.get('capacity') not in ('si', 'ayuda'):
        level = 'bloqueo' if person.get('capacity') == 'no' else 'revisar'
        add(level, 'CAPACIDAD', 'Verificar capacidad para responder escalas (con apoyo si procede).')
    for field, code, title in (
        ('alternativeDiagnosis', 'R017', 'diagnóstico alternativo'),
        ('seriousDecompensation', 'R019', 'comorbilidad descompensada'),
        ('interferingTrial', 'R020', 'ensayo interferente'),
    ):
        val = person.get(field)
        if val == 'si':
            add('bloqueo', code, f'Exclusión presente: {title}.')
        elif val != 'no':
            add('revisar', code, f'Exclusión sin respuesta explícita: {title}.')

    if person.get('consent') != 'si':
        add('bloqueo', 'R021', 'Consentimiento firmado no consta como Sí.')
    if not person.get('consentDate'):
        add('revisar', 'R022', 'Falta fecha de consentimiento firmado.')
    if person.get('eligibilityDecision') != 'elegible':
        add('revisar', 'R023', 'Falta confirmación documental de elegibilidad.')
    if not person.get('enrolDate'):
        add('bloqueo', 'INCLUSION', 'Falta fecha de incorporación.')

    baseline = next((v for v in visits if v.get('patient') == pid and v.get('type') == 'V0'), None)
    if baseline:
        try:
            t0 = date.fromisoformat(baseline['date'])
        except (TypeError, ValueError, KeyError):
            add('revisar', 'V0_FECHA', 'Fecha basal no interpretable en revisión temporal.')
        else:
            if person.get('enrolDate') and baseline.get('date') != person['enrolDate']:
                add('bloqueo', 'V0_CONCORDANCIA', 'V0 y fecha de inclusión no coinciden.')
            for stage, left, right in (('V1', 5, 7), ('V2', 11, 13)):
                event = next((v for v in visits if v.get('patient') == pid and v.get('type') == stage), None)
                if event:
                    try:
                        observed = date.fromisoformat(event['date'])
                        if not _months_after(t0, left) <= observed <= _months_after(t0, right):
                            add('revisar', f'{stage}_VENTANA',
                                f'{stage} fuera de ventana nominal; conservar fecha real y acordar tratamiento analítico.')
                    except (TypeError, ValueError, KeyError):
                        add('revisar', f'{stage}_FECHA', f'Fecha de {stage} no interpretable.')

    return {'participant': pid, 'stage': 'incluido', 'findings': findings,
            'conclusion': 'Incidencias de preflight para revisión científica' if findings else
                          'Sin incidencias automáticas; NO equivale a elegibilidad validada'}


def aggregate(patients: list[dict[str, Any]], visits: list[dict[str, Any]]) -> dict[str, Any]:
    results = [evaluate_participant(p, visits) for p in patients]
    return {
        'criteria_version': CRITERIA_VERSION,
        'scope': 'Solo datos sintéticos; comprobación documental y no decisoria',
        'participants': len(results),
        'included': sum(x['stage'] == 'incluido' for x in results),
        'with_blockers': sum(any(f['level'] == 'bloqueo' for f in x['findings']) for x in results),
        'with_review_items': sum(any(f['level'] == 'revisar' for f in x['findings']) for x in results),
        'findings': results,
        'structural_limits': [
            'La aplicación no certifica que el cociente documentado procede de espirometría posbroncodilatadora válida.',
            'La fecha declarada de una consulta EPOC durante el año previo debe contrastarse con la documentación original.',
            'La existencia material de consentimiento firmado requiere comprobación autorizada fuera del programa.',
            'Las ventanas de V1/V2 se señalan; no se imputan ni modifican visitas y su tratamiento es metodológico.',
            'Las pendientes clínicas y éticas se cierran por aprobación del IP/coordinación; un test verde no las resuelve.',
        ],
    }
