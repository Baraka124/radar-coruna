# RADAR-CORUÑA v0.41 — PostgreSQL staging handover

**Stage:** server-side PostgreSQL adapter candidate. **NOT** approved for clinical data, and not yet a remote working app.

## Applied in Supabase (confirmed 2026-11-14)

- Primary connected account, organization `Big-B-LAB`, dedicated project `radar-coruna-staging` (`vqdpkzlrzwchjumpbqta`), Paris `eu-west-3`.
- Migration `radar_v041_initial_private_schema` created 13 tables under private `radar` schema.
- All tables were verified empty. `anon` and `authenticated` do **not** have `USAGE` on `radar` schema. No patient records imported.
- Project URL: https://supabase.com/dashboard/project/vqdpkzlrzwchjumpbqta
- Security check: database inspection flags **RLS disabled on the 13 private tables**. Their private schema and revoked grants prevent anonymous/direct authenticated access under the current model. **Before ANY Data API exposure, design and test RLS centre membership policies; don't enable the schema for browser API use.** The current server adapter uses a backend DB connection, not a browser Supabase client.

## Application-side changes in this candidate

- `RADAR_STORAGE=postgres` enables `postgres_adapter_v41.py`; absent/`sqlite` keeps v0.40's existing local behavior.
- FastAPI endpoints, study validation, frontend HTML, V0–V2, RBAC, centre scoping and exports are retained; no clinical UI redesign.
- Adapter maps SQLite placeholders and controlled SQL expressions, maps JSONB and timestamps to legacy response shapes, and supports audit identity keys and batch field changes.
- Uses transaction-scoped PostgreSQL advisory locking to serialize staging DB requests across application replicas while preserving existing read/check/write semantics. This is a **temporary staging measure**; it limits throughput, and a proper row-level concurrency design and load tests are required.
- Runtime refuses experimental PostgreSQL mode outside `RADAR_MODE=synthetic_staging`; no bootstrap demo account allowed. Bootstrap credentials must be set in server environment secrets.
- Existing SQLite backup scripts are **not valid PostgreSQL backup procedures**. Use provider backups and verified Postgres restore drills.

## Current tests and limitations

- Offline adapter SQL compatibility tests passed; focused historical regression passed on SQLite local mode.
- The PostgreSQL driver was **not available in the isolated artifact runtime**, and installation failed due to no package-network access; a real FastAPI↔Supabase database connection and end-to-end PostgreSQL parity tests were NOT performed.
- `psycopg[binary]` has been added to `requirements-staging.txt` (pin to verify with deployment environment). Connect using **server-side** `RADAR_DATABASE_URL` only. Obtain actual credentials from Supabase > Connect; never publish them in chat, ZIP or JS.
- No live application deployed; no websocket/SSE push or Supabase Realtime implemented. Multiuser centralized storage does not imply real-time browser refresh.

## Next engineering acceptance steps (mandatory)

1. Configure a separate backend service and private env secrets for the exact RADAR staging project. Obtain database URL from Supabase Connect (direct or session pooler; TLS certificate verification).
2. Install driver and launch synthetic staging, run `/api/ready`, verify the initial admin and no demo credentials.
3. Execute **the entire** clinical/API/browser suite against PostgreSQL, and repair any remaining SQL typing/transaction differences. Include JSONB, datetime, audit, 409 conflicts, invitation redemption, exports and center-isolation attacks.
4. Verify concurrent writes using two genuinely independent FastAPI processes. Replace staging-wide advisory serialization with granular row-level conflict handling once parity is proven.
5. Enable patient-safe security controls, role grants, connection pooling, monitoring and tested restore. Keep application service private until authorization and acceptance.
6. Introduce real-time event delivery with per-centre authorization after backend storage is validated.
7. Obtain CEIC and institutional approvals before considering any real data.

## Verification examples

```bash
python -m pytest -q tests/test_phase41_postgres_adapter.py tests/test_phase40_operations.py tests/test_phase38_multicentre.py tests/test_phase39_intelligence.py tests/test_phase32_intelligent_capture.py
```

An environment template is in `.env.postgres-staging.example`. It contains dummy placeholders, not passwords.
