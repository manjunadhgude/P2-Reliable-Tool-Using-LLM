# API

FastAPI OpenAPI UI is at `/docs`. Application routes use `/api/v1` except health and metrics.

| Method and path | Access | Purpose |
|---|---|---|
| `GET /health/live` | public | Process liveness |
| `GET /health/ready` | public | Database/backend status |
| `GET /api/v1/system/info` | public | Safe backend/model labels |
| `POST /api/v1/auth/demo-session` | public | Signed seeded demo session |
| `GET /api/v1/auth/me` | bearer | Current role/tenant |
| `POST /api/v1/conversations` | bearer | Create conversation |
| `GET /api/v1/conversations` | bearer | User's own conversations |
| `GET /api/v1/conversations/{id}` | bearer | User-scoped history |
| `POST /api/v1/conversations/{id}/messages` | bearer | Orchestrate a turn |
| `GET /api/v1/pending-actions` | supervisor/admin | Review queue |
| `POST /api/v1/pending-actions/{id}/approve` | supervisor/admin | Approve/create ticket once |
| `POST /api/v1/pending-actions/{id}/reject` | supervisor/admin | Reject pending action |
| `GET /api/v1/turns/{id}/trace` | owner | Tool trace |
| `GET /api/v1/benchmarks` | bearer | Saved runs |
| `GET /api/v1/experiments` | evaluator/admin | Saved database runs and sanitized result-artifact history |
| `POST /api/v1/benchmarks` | evaluator/admin | Run validation benchmark |
| `GET /api/v1/benchmarks/{id}/export?format=json\|csv` | bearer | Export saved result |
| `GET /metrics` | local demo | Aggregate counts |

Login body: `{"username":"agent"}`, `supervisor`, or `evaluator`; use returned token as `Authorization: Bearer …`. Approval checks role and tenant server-side.
