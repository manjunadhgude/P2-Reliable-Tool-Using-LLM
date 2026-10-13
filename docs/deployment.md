# Deployment and troubleshooting

## Local

Follow [README quick start](../README.md). SQLite is the low-friction local database; PostgreSQL is supported with SQLAlchemy. API port is 8000; Vite UI port is 5173.

## Compose

Compose provisions PostgreSQL, API and static frontend. `docker compose up --build` applies Alembic then runs Uvicorn. The fixture backend is default. Do not expose demo identities or the default Compose signing secret.

## Real model

Install optional Transformers dependencies and set `MODEL_BACKEND=transformers`, retaining the pinned revision. First load downloads weights. CPU inference may be slow; GPU runtime needs compatible PyTorch/CUDA. This laptop has a 4 GiB GPU and initially lacked PyTorch/Transformers, so real inference and LoRA were not verified. No cloud GPU was provisioned.

## Troubleshooting

- `503` readiness: check `DATABASE_URL` and apply `alembic upgrade head`.
- UI cannot reach API: check port 8000 and `CORS_ORIGINS`.
- Demo sign-in: API seeds role accounts at startup.
- Model load fails: use `MODEL_BACKEND=deterministic_test` or install compatible extras; the UI labels the backend.
- Dataset unavailable: run the generator from repository root; benchmark reads validation only.
