# Implementation Plan — P2

This sequence turns the locked specification into working software. Keep the main branch/worktree runnable. Complete each phase's gate before building dependent features, but do not wait for user confirmation between phases. Record progress in `docs/PROGRESS.md`.

## Phase 0 — Repository and environment discovery

**Actions**
- Inspect the full repository, existing code, operating system, CPU/RAM/disk, Python and Node versions, Docker availability, and GPU/VRAM availability if exposed.
- Confirm which files already exist before edits; preserve existing user work.
- Check model cards, exact licenses, revisions, chat templates/tool-use conventions, and current compatibility for candidate compact open-weight models.
- Test model loading and a single normalized tool action on the feasible hardware/runtime. Attempt a small LoRA/QLoRA feasibility run only when dependency/hardware conditions support it and without using paid resources unless explicitly authorized.
- Write `docs/feasibility_report.md` with commands, exact versions, outcomes and a chosen model/runtime plan.

**Gate**: an honest model/compute plan is documented. If training is blocked, continue the application and mark the training experiment as blocked, not completed.

## Phase 1 — Backend foundation and deterministic business domain

**Actions**
- Establish a clean backend package, settings, logging, database connection, migrations and deterministic synthetic seed data.
- Implement typed domain models and the six approved tools: `lookup_order`, `list_order_items`, `get_return_policy`, `check_refund_eligibility`, `calculate_refund_estimate`, `create_support_ticket`.
- Implement deterministic policy logic, decimal-safe calculations, role/tenant/order scoping, server-side approval workflow and write idempotency.
- Add tool registry metadata, strict Pydantic input/output schemas and bounded execution.
- Add unit tests for normal cases, missing/nonexistent records, denied access, invalid arguments, edge policy conditions, approval and idempotency.

**Gate**: core business/security tests pass without loading an LLM.

## Phase 2 — Model adapter and orchestrator

**Actions**
- Define a model-independent action schema aligned with `config/action_envelope.schema.json`.
- Implement a real open-weight model backend and a separate deterministic test backend. Label the latter visibly in config/UI/docs.
- Implement strict parsing/normalization, one bounded repair attempt, max step/tool/time budgets, policy/auth gates, result handback to the model, and safe termination paths.
- Persist conversation, model-run, tool-execution and pending-action traces.
- Redact logs, handle timeouts, and expose honest backend status.

**Gate**: read-only and multi-step scenarios pass with the test backend; the real model backend has a recorded smoke-test result or a documented environment blocker.

## Phase 3 — API and full-stack UI

**Actions**
- Implement versioned REST routes for health/readiness, system info, authentication/demo session, conversations/messages, approvals/rejections, execution traces and benchmark runs/results.
- Implement the chat/support UI, pending-action review screen, trace timeline, benchmark/experiment dashboard and backend status/settings view.
- Include loading/empty/error/validation/pending states and useful error messages. No dead buttons or hardcoded fake results.
- Add API integration tests and UI end-to-end tests for core journeys.

**Gate**: a clean local setup supports order lookup, eligibility/estimate, ticket proposal, approval/rejection and trace review from the UI.

## Phase 4 — Dataset and baseline evaluation

**Actions**
- Build seeded synthetic scenario generation for every required family in the build spec.
- Write schema validation, duplicate detection, split leakage checks, dataset version/checksum metadata and train/validation/held-out split manifests.
- Implement benchmark runner and result export (JSON and CSV) with explicit run IDs, versions, denominators and error categories.
- Run Baseline A (pretrained model) and Baseline B (prompt-engineered same model) on the locked test suite when real-model access is available. If blocked, keep the runner functional and report that actual model results remain unmeasured.

**Gate**: benchmark is reproducible; held-out data is not used to select prompts/configurations; report is based on actual run artifacts.

## Phase 5 — Fine-tuning experiment

**Actions**
- Build dataset export into the training format and a small training smoke test.
- Train LoRA/QLoRA on one compact model only when the Phase 0 feasibility test succeeds and compute is available.
- Record seeds, dataset/version/checksum, model revision/license, dependencies, hyperparameters, runtime, hardware, memory and any costs.
- Save/reload the adapter and evaluate it with the exact same executor, schemas, safety gates, and held-out test cases used for A/B.
- Analyze success and regressions. Do not assume fine-tuning improves results.

**Gate**: adapter and result artifacts exist before describing the experiment as complete. If not feasible, preserve training scripts/configuration and clearly document the blocker.

## Phase 6 — Optional inference optimization

**Actions**
- Explore quantization or an alternate serving runtime only where supported and justified.
- Compare accuracy/task success, memory, latency and throughput under documented hardware/load settings.
- Skip unsupported variants safely and document why.

**Gate**: only measured, reproducible results are reported.

## Phase 7 — Hardening and handoff

**Actions**
- Finish auth/tenant, prompt-injection, approval bypass, replay/idempotency, unsafe tool, malformed schema, timeout and failure-recovery tests.
- Add Docker/Compose, CI that runs without large model downloads/GPU, lint/type checks, `.env.example`, dependency and license notes.
- Write README, architecture, API, security/threat model, dataset card, model card, training/evaluation protocol, experiment report, deployment guide, troubleshooting guide and demo script.
- Verify quick-start from a clean state where possible; update checklist and progress log.
- Provide an honest final handoff with commands, tests and limitations.

**Gate**: see `docs/ACCEPTANCE_CHECKLIST.md`. Unverified or blocked requirements must stay marked as such.

## Cross-phase priorities

1. Correctness and authorization before model sophistication.
2. Working end-to-end workflow before cosmetic polish.
3. Real model backend separated from the deterministic testing backend.
4. Reproducible evaluation before claims.
5. Secure approval and idempotency before state changes.
6. Keep P2 distinct from P1; do not expand into another general RAG project.
