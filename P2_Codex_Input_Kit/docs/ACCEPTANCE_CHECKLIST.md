# P2 Definition of Done — Acceptance Checklist

Do not check a box unless code, a test, a command output, or a saved experiment artifact provides evidence. Add file paths/commands beside completed items. Use `BLOCKED` with an explanation where external compute/access prevents verification.

## Product functionality
- [ ] Clean setup instructions install and launch the application.
- [ ] Chat workflow performs an order lookup using database/tool results.
- [ ] Chat workflow lists order items and returns the source-of-truth policy.
- [ ] Refund/return eligibility comes from deterministic business rules.
- [ ] Refund estimate uses application-side decimal arithmetic.
- [ ] Ticket proposal is shown as pending before it can be created.
- [ ] Ticket can be explicitly approved/rejected through an authenticated backend route.
- [ ] A ticket cannot be created from model text alone or before required approval.
- [ ] Repeated/replayed approved requests do not create duplicate tickets.
- [ ] Conversation history and trace details are viewable.
- [ ] Benchmark/experiment views are connected to actual persisted run data.
- [ ] No dead buttons, simulated business results presented as real, or hardcoded fake benchmark charts.

## Model and orchestration
- [ ] Real open-weight model adapter exists and has documented setup/configuration.
- [ ] Model/action output is normalized into the versioned internal action schema.
- [ ] Tool allowlist is enforced server-side.
- [ ] Argument types, required fields, enum values and unknown fields are validated.
- [ ] Model turn/tool-call/time/retry budgets are enforced.
- [ ] Malformed outputs fail safely; repair retries are bounded.
- [ ] The deterministic test backend is clearly labelled and never counted as real model performance.
- [ ] Model license, revision, chat template and compatibility are documented from checked sources.

## Data and security
- [ ] Only synthetic fixtures are included.
- [ ] Database migrations and deterministic seeding work from a clean state.
- [ ] Authorization and tenant/order scope are enforced by the server.
- [ ] Unregistered tools and arbitrary code/raw SQL/HTTP execution cannot be invoked by the model.
- [ ] Prompt-injection/bypass requests are included in tests.
- [ ] Tool outputs/user input are treated as untrusted.
- [ ] Secrets are excluded from source control; `.env.example` contains placeholders only.
- [ ] Trace/audit logs redact sensitive fields and exclude hidden chain-of-thought.

## Evaluation/research integrity
- [ ] Dataset generator and validator run reproducibly.
- [ ] Train/validation/test split manifest and leakage checks exist.
- [ ] Held-out test examples are not used for prompt/training selection.
- [ ] Benchmark runner reports denominator, task family, model revision, dataset version and environment.
- [ ] Baseline A and B actual results are saved, or the precise blocker is documented.
- [ ] Fine-tuning is only claimed complete if training, adapter reload and held-out evaluation actually ran.
- [ ] Optional quantization/serving results are backed by real runs; otherwise marked not run.
- [ ] No fabricated accuracy, speed, cost or improvement metrics.

## Engineering quality and documentation
- [ ] Unit tests cover tools, policies, schema validation, permissions, approvals and idempotency.
- [ ] API integration tests cover primary flows and expected failures.
- [ ] UI end-to-end tests cover at least order lookup and approval workflow.
- [ ] Lint/type checks and the available test suite pass, with exact commands recorded.
- [ ] Docker/Compose local run is documented and tested where available.
- [ ] CI runs core tests without requiring a GPU or downloading a large model.
- [ ] README, architecture, API, security, deployment and troubleshooting docs exist.
- [ ] Dataset card, model card, experiment protocol/report and demo script exist or clearly explain blocked experiments.
- [ ] `docs/PROGRESS.md` accurately reports completed work, failed commands, limitations and next action.
- [ ] Final handoff contains exact setup/run/test commands, verified results and unresolved limitations.
