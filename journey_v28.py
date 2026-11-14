"""Read-only, per-participant RADAR longitudinal record review.

Uses persisted records, never changes them. No implicit 'No' responses are inferred
from absent events, contacts, visits or observations.
"""
from __future__ import annotations

STAGES = ('V0', 'V1', 'V2')
WEIGHTS = {'rescue': 3, 'exacerb': 2, 'dyspnea': 2, 'activity': 1}


def summarize(patient: dict, visits: list[dict], episodes: list[dict],
              contacts: list[dict], observations: list[dict], missing: list[dict]) -> dict:
    pid = patient['id']
    visits = [v for v in visits if v.get('patient') == pid]
    episodes = [e for e in episodes if e.get('patient') == pid]
    contacts = [c for c in contacts if c.get('patient') == pid]
    observations = [o for o in observations if o.get('participant') == pid]
    missing = [m for m in missing if m.get('participant') == pid]
    by_visit = {v.get('type'): v for v in visits if v.get('type') in STAGES}
    observation_counts = {stage: sum(o.get('visit_type') == stage for o in observations) for stage in STAGES}
    missing_counts = {stage: sum(m.get('visit_type') == stage for m in missing) for stage in STAGES}
    stages = []
    alerts = []
    for stage in STAGES:
        v = by_visit.get(stage)
        if not v:
            stages.append({'stage': stage, 'recorded': False, 'status': 'sin_registrar', 'date': '',
                           'radar_total': None, 'radar_class': '', 'cat': None, 'mmrc': None,
                           'ianus_verified': '', 'ianus_collected': '',
                           'complementary_count': observation_counts[stage], 'missing_count': missing_counts[stage]})
            continue
        complete = v.get('status') != 'no_realizada' and all(v.get(k) in ('si', 'no') for k in WEIGHTS)
        total = sum(weight for key, weight in WEIGHTS.items() if v.get(key) == 'si') if complete else None
        category = ('buen_control' if total <= 1 else 'control_parcial' if total <= 3 else 'mal_control') if total is not None else ''
        if v.get('status') == 'completa' and (total is None or v.get('cat') is None or v.get('mmrc') is None):
            alerts.append({'code': 'VISITA_INCOMPLETA', 'stage': stage,
                           'message': f'{stage}: registrada como completa con datos esenciales ausentes; revisar ficha histórica'})
        if v.get('ianusVerified') == 'no' and v.get('ianusCollected') in ('si', 'no'):
            alerts.append({'code': 'IANUS_INCONSISTENTE', 'stage': stage,
                           'message': f'{stage}: IANUS no verificable con respuesta Sí/No de recogida'})
        stages.append({'stage': stage, 'recorded': True, 'status': v.get('status', 'parcial'),
                       'date': v.get('date', ''), 'radar_total': total, 'radar_class': category,
                       'cat': v.get('cat'), 'mmrc': v.get('mmrc'),
                       'ianus_verified': v.get('ianusVerified', ''), 'ianus_collected': v.get('ianusCollected', ''),
                       'complementary_count': observation_counts[stage], 'missing_count': missing_counts[stage]})
    d0 = by_visit.get('V0', {}).get('date', '')
    d1 = by_visit.get('V1', {}).get('date', '')
    d2 = by_visit.get('V2', {}).get('date', '')
    if d0 and d1 and d1 <= d0:
        alerts.append({'code': 'ORDEN_VISITAS', 'stage': 'V1', 'message': 'V1: fecha no posterior a V0'})
    if d1 and d2 and d2 <= d1:
        alerts.append({'code': 'ORDEN_VISITAS', 'stage': 'V2', 'message': 'V2: fecha no posterior a V1'})
    if d0 and d2 and d2 <= d0:
        alerts.append({'code': 'ORDEN_VISITAS', 'stage': 'V2', 'message': 'V2: fecha no posterior a V0'})
    episode_lookup = {e.get('id'): e for e in episodes}
    unrelated_links = [c for c in contacts if c.get('event') and c.get('event') not in episode_lookup]
    for c in unrelated_links:
        alerts.append({'code': 'CONTACTO_SIN_EPISODIO', 'stage': 'episodios',
                       'message': f"Contacto {c.get('id', 'sin ID')}: episodio asociado no disponible"})
    for e in episodes:
        linked = [c for c in contacts if c.get('event') == e.get('id') and c.get('copd') == 'si']
        for kind, field in (('urgencias', 'emergencyStatus'), ('ingreso', 'admissionStatus')):
            if e.get('copd') == 'si' and any(c.get('type') == kind for c in linked) and e.get(field) != 'si':
                alerts.append({'code': 'CONTACTO_EVIDENCIA', 'stage': 'episodios',
                               'message': f"Episodio {str(e.get('episodeNo') or '?').zfill(2)}: {kind} documentado sin respuesta Sí"})
    sums = {v['stage']: v['radar_total'] for v in stages}
    delta = sums['V2'] - sums['V0'] if sums['V0'] is not None and sums['V2'] is not None else None
    return {
        'participant': pid, 'centre': patient.get('center', ''),
        'enrolment_status': patient.get('status', 'cribado'),
        'stages': stages, 'recorded_visits': sum(s['recorded'] for s in stages),
        'complete_radar': sum(s['radar_total'] is not None for s in stages),
        'radar_delta_v0_v2': delta,
        'events': {'all': len(episodes),
                   'copd_exacerbations': sum(e.get('kind', 'agudizacion') == 'agudizacion' and e.get('copd') == 'si' for e in episodes),
                   'other': sum(e.get('kind') == 'otro' for e in episodes),
                   'contact_count': len(contacts),
                   'linked_contact_count': sum(bool(c.get('event')) for c in contacts),
                   'unlinked_contact_count': sum(not c.get('event') for c in contacts),
                   'emergency_copd': sum(c.get('type') == 'urgencias' and c.get('copd') == 'si' for c in contacts),
                   'admission_copd': sum(c.get('type') == 'ingreso' and c.get('copd') == 'si' for c in contacts)},
        'outcomes': {'vital_status': patient.get('vitalStatus', ''),
                     'last_information_date': patient.get('lastInformationDate', ''),
                     'death_date': patient.get('deathDate', '')},
        'missing_total': len(missing), 'observations_total': len(observations),
        'alerts': alerts,
    }
