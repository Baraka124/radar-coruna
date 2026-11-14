# RADAR-CORUÑA v0.41.1 — connected infrastructure / pending end-to-end deploy

## Verified resources (2026-11-14)

- **Supabase project:** `radar-coruna-staging`, Big-B-LAB, Paris (`eu-west-3`), ref `vqdpkzlrzwchjumpbqta`.
- **Database:** PostgreSQL 17, private `radar` schema with 13 tables, no study data; `anon` and `authenticated` have no `USAGE` privilege on the schema. RLS is not enabled; **NEVER** expose this schema through the client Data API without an approved policy review.
- **Railway project:** `RADAR-CORUNA-Staging`, project ID `9a68f8c2-b571-44fd-8603-ba8f2234664a`.
- **Railway staging environment:** `19b4ef31-3e2b-4e6a-83ca-0773410c386d`.
- **Railway service:** `radar-api`, ID `fb6b96f4-541b-4381-a4f1-cc743ca17df7`, **empty service — not deployed**.
- **Reserved domain:** `https://radar-api-staging-27a8b78c.up.railway.app` (NOT live until deployed).
- Seven non-secret staging variables were set on the service: `RADAR_MODE=synthetic_staging`, `RADAR_STORAGE=postgres`, `RADAR_PUBLIC_ORIGIN`, `RADAR_EXPECTED_PROJECT_REF`, `RADAR_BOOTSTRAP_ADMIN_USER`, `RADAR_SEED_DEMO=0`, `RADAR_WORKERS=1`.
- Railway build uses Dockerfile and readiness `/api/ready`.

## Two remaining connection requirements

1. **Source repository.** Create/select a **new private** GitHub repository dedicated to RADAR-CORUÑA, e.g. `neumACt/radar-coruna`, and push this candidate source. Do not reuse or modify neumDESK/neumuacFQ repositories. Connect this repo to the empty `radar-api` service. GitHub does not currently expose repository creation through the available connector, and the repo was not supplied.
2. **Backend secrets.** In Supabase dashboard > the RADAR project > **Connect**, select direct/session-pooler connection. Provision the DB secret using **Railway Variables**, never chat or GitHub. Set `RADAR_DATABASE_URL` with URL-encoded password and `sslmode=verify-full`; install/point to the project's CA certificate in the backend container. Set `RADAR_BOOTSTRAP_ADMIN_PASSWORD` as a unique strong secret >=16 characters (uppercase/lowercase/digit). Do not log or share these values. PostgreSQL URL must match RADAR project ref, not any other Supabase project.

## Connection and acceptance order

1. Prepare the new private GitHub repository and attach it to `radar-api`.
2. Set backend secrets directly in Railway and configure trusted certificate for TLS `verify-full`. Ensure that host, port, PostgreSQL username and RADAR project ref agree. Check environment variables without printing secret values.
3. Deploy a single synthetic staging replica. Check `/api/health` and `/api/ready`. An unavailable database or missing admin bootstrap must fail closed.
4. Through the new staging URL: sign in as the bootstrap admin, invite two synthetic centre investigators, create synthetic records, save V0/V1, test centre isolation, audit, Excel/CSV export, and concurrent conflict response.
5. Confirm the cross-process PostgreSQL transaction semantics; replace staging-wide advisory serialization before scaling and prohibit all real patient data.
6. Complete a PostgreSQL provider backup + restore drill, review Supabase DB/RLS advisors, and add authorized event updates only after cross-centre isolation passes.

## Security boundaries

- No clinical/identifiable data are authorized. CEIC/institutional approvals are separate prerequisites.
- The `radar` schema is private. The existing FastAPI layer is the only planned API; do not add Supabase anon-key direct access.
- `RADAR_DATABASE_URL` and administrator password must remain backend-only secrets. They are NOT included in this ZIP.
- Current use of PostgreSQL `pg_advisory_xact_lock` serializes all staging DB requests and is a short-term compatibility tactic, not production-grade multiuser concurrency.
- The existing SQLite backup script does **not** back up PostgreSQL.

## Adapter changes in this revision

- Added `RADAR_EXPECTED_PROJECT_REF` verification, rejects wrong direct/pooler projects.
- Requires TLS `sslmode=verify-full`; the application fails closed without suitable CA trust.
- Corrected `/api/state` version to reflect the running application.
- 77/77 selected local clinical/security/adapter regression tests passed. No live FastAPI-to-PostgreSQL test has passed yet.

## Project links

Supabase: https://supabase.com/dashboard/project/vqdpkzlrzwchjumpbqta
Railway: https://railway.com/project/9a68f8c2-b571-44fd-8603-ba8f2234664a
