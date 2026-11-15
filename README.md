# RADAR-CORUÑA — v0.45 synthetic staging

RADAR-CORUÑA is a longitudinal respiratory research application (FastAPI + clinical frontend + private PostgreSQL). It supports study governance, participant screening, visits V0/V1/V2, episodes, data-quality review, research outputs and role-scoped collaboration.

> **Synthetic staging only.** Do not enter real clinical or identifying data. Use for real patients remains conditional on ethics, institutional and data-protection approvals.

## Authoritative data sources

- `radar.centres`: **registered participating centres**, managed by the study administrator. A new environment starts with **zero** centres and no fabricated participants.
- `radar.users`, `radar.invitations`: persistent user accounts, centre associations and one-use invitation links. Roles are enforced by the server.
- `radar.patients`, `radar.visits`, `radar.episodes`, `radar.contacts`: user-entered research records.
- `radar.study_observations`, `radar.phase14_records`, `radar.missing_data`: complementary CRD entries and data-quality states.
- `radar.audit`, `radar.audit_field_changes`: traceable writes and subsequent field corrections.

**Static clinical dictionaries** (e.g. V0/V1/V2, scored RADAR questions, allowed categories) are not fake observations. Test fixtures are restricted to isolated local/CI databases; remote staging rejects automatic demo seeding. Unknown or inactive centre codes are rejected by the API.

## Staging infrastructure

- **GitHub**: `Baraka124/radar-coruna`
- **Supabase**: `radar-coruna-staging`, `vqdpkzlrzwchjumpbqta`, private `radar` schema
- **Railway**: `RADAR-CORUNA-Staging`, service `radar-api`, `staging`
- **URL**: `https://radar-api-staging-27a8b78c.up.railway.app`

The existing v0.44 Railway deployment remains the known-good baseline during review of PR #5. The additive database migration `migrations/20261115_v045_centres_registry.sql` was applied to staging on 15 November 2026; validation confirmed zero centre rows and preservation of the three pre-existing invitation rows. The new table has RLS enabled and no direct grants to the `anon`/`authenticated` API roles. Do not assume other tables have completed a production security audit.

## Administrator workflow

1. Sign in as the existing authorised administrator.
2. Open **Red de centros** and use **Centros participantes** to register a genuine centre identifier and display name. Nothing is auto-created.
3. Invite a collaborator from the registered centre and select investigator or read-only reviewer permissions.
4. The collaborator accepts the single-use invitation and creates an individual account.
5. Enter **synthetic** participant records, save visits and CRD responses, verify longitudinal views and exports.
6. Deactivation is blocked while a centre retains accounts, patients, complementary records or unexpired pending invitations.
7. Legacy invitations for a centre that has not been registered are shown as **Centro no registrado**, cannot be accepted and may be revoked. The administrator cannot accidentally activate them by registering the same centre code.

## Verification and limitations

- `tests/test_centres_v45.py`: empty state, registry CRUD, invitation lifecycle, two-centre isolation, legacy links and archival guards.
- `tests/conftest.py`: historical test-centre fixtures are injected only in pytest, not into staging.
- `.github/workflows/centre-registry.yml`: Python syntax, JavaScript syntax, full Python regression suite.
- `AUDITORIA_DATOS_REALES_V45.md`: evidence matrix and remaining sources of synthetic or fixed content.

The browser remains a static frontend backed by persistent API requests; this is not a standalone simulation. Remaining work includes explicit loading/empty/error states for auxiliary research modules and live authenticated PostgreSQL end-to-end acceptance before clinical use.
