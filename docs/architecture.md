# Architecture

P2 is a modular monolith. React communicates with FastAPI over `/api/v1`; SQLAlchemy persists users, synthetic orders, conversations, messages, turns, tool traces, pending actions, tickets, audit events, and benchmark runs.

```text
React UI → FastAPI and signed demo session → normalized action → strict Pydantic schemas
                                               ├── allowlisted read tool → tenant-scoped queries
                                               └── pending ticket → supervisor approval → idempotent insert
```

The model adapter returns a versioned JSON action envelope. The deterministic backend is for demo and tests only. `TransformersModelBackend` loads the pinned Qwen3 revision and emits the same envelope. The UI shows the active backend. Model output does not decide permissions, policy, arithmetic, or approval. For multi-step eligibility and refund estimates, the application constructs the final response from successful registered-tool results; it does not ask the model to restate those outcomes.

SQLite supports local use. PostgreSQL is the Compose database. Alembic contains the initial revision. Startup also uses SQLAlchemy `create_all` as a development fallback for direct test imports; deployments should apply Alembic first.

Only six named tools exist. No shell, generated SQL, arbitrary network action, or chain-of-thought storage is exposed.
