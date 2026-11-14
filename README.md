# RADAR-CORUÑA — v0.41.1 synthetic staging candidate

This repository contains the **RADAR-CORUÑA** longitudinal respiratory research application (FastAPI + static clinical UI) and the optional PostgreSQL staging adapter.

> **Synthetic staging only.** Not approved for real clinical/patient data. Not a live/validated production system. CEIC/institutional/data-protection approvals are separate.

## Architecture

- `server.py`: clinical API, server-side validation, authentication and centre authorization.
- `static/index.html`: clinical UI; the original design is retained.
- `postgres_adapter_v41.py`: experimental PostgreSQL compatibility layer (private `radar` schema).
- `tests/`: local application and browser regression.
- `Dockerfile` / `requirements-staging.txt`: single-worker staging runtime.
- `V41_1_RAILWAY_STAGING_HANDOVER.md`: actual project IDs and deployment steps.

## Connected infrastructure (not yet deployed)

- Supabase: `radar-coruna-staging`, Paris, `vqdpkzlrzwchjumpbqta` (13 private tables, empty).
- Railway: `RADAR-CORUNA-Staging`, `radar-api`, staging environment.
- Hosting URL: reserved, not live: `https://radar-api-staging-27a8b78c.up.railway.app`.

## Before deployment

1. **Private repository only**; keep credentials in Railway environment variables, not here.
2. In Supabase **Connect**, obtain the session-pooler PostgreSQL URI and CA cert; configure the backend URL with verified TLS and correct RADAR project reference.
3. Set `RADAR_DATABASE_URL` and `RADAR_BOOTSTRAP_ADMIN_PASSWORD` in the RADAR Railway service; nonsecret variables are already configured.
4. Connect this repository to the existing `radar-api` Railway service and deploy a **single instance**. Inspect readiness and logs before any user access.
5. Validate end-to-end with synthetic patients and accounts, including centre isolation, audit, invitations, V0/V1/V2 and exports.

See `GITHUB_SETUP.md` and `V41_1_RAILWAY_STAGING_HANDOVER.md` for the detailed setup and known gaps. The PostgreSQL adapter is experimental and has not passed a real remote end-to-end connection test.
