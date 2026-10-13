# START HERE — Codex Input Kit for P2

## Your task
Build the actual working software for **P2 — Reliable Tool-Using LLM for Business Operations**. This folder is the project blueprint and implementation instruction package. It is not the application source code itself.

## Read these files first
1. `AGENTS.md` — permanent coding and safety rules.
2. `docs/P2_BUILD_SPEC.md` — authoritative, complete product and technical specification.
3. `docs/IMPLEMENTATION_PLAN.md` — the required implementation sequence and phase gates.
4. `docs/ACCEPTANCE_CHECKLIST.md` — definition of done.
5. `config/project_manifest.json` and `config/action_envelope.schema.json` — machine-readable project and action contracts.

If a short summary in this file conflicts with the full build specification, follow the full build specification unless it conflicts with a mandatory security rule in `AGENTS.md`. Do not quietly redesign or expand the locked project.

## Instructions to Codex

**Work in the current workspace and build the project, not just a plan.**

1. Inspect the repository, operating system, installed toolchains, available disk/RAM/GPU, and existing files before making changes. Preserve valuable existing work; do not overwrite unrelated user files.
2. Create `docs/feasibility_report.md` with the environment findings, candidate model/license/revision checks, what can run locally, and whether fine-tuning is feasible. Verify current model cards, licenses, model templates and library compatibility from authoritative sources during implementation.
3. Make sensible, low-risk engineering choices consistent with the full specification. Do not ask for approval for routine decisions. Ask only when a genuine external decision, secret, payment, destructive action, or unavailable resource blocks a required step.
4. Start implementing after recording the initial plan. Do not stop at a scaffold, architecture diagram, task list, or Phase 0 report. Proceed through the phases in `docs/IMPLEMENTATION_PLAN.md`, keeping the app runnable and testing each stage.
5. Keep a truthful progress log at `docs/PROGRESS.md`: completed work, commands run, test results, known failures, decisions, and the single next action. Update it as you go so work can resume after a context/session limit.
6. If a model download, GPU, cloud account, API credential, or paid resource is unavailable, do not fabricate it or incur charges. Continue all work that can be done safely; implement the real model integration, give exact setup/run instructions, and clearly mark the blocked experiment. The deterministic test backend is for tests/demo control only and must never be represented as a real LLM or as genuine model benchmark results.
7. Use the approved tool allowlist only. All authorization, tenant scoping, return/refund rules, arithmetic, approval gates and idempotency checks belong in ordinary application code, not in model judgement. The model must never receive shell/code execution, arbitrary HTTP access, raw SQL execution or unrestricted database writes.
8. For every state-changing ticket operation, create a pending action and require explicit server-verified user approval before insertion. Prevent duplicate writes on retries. Fail closed on malformed output, missing permissions or uncertain policy results.
9. Implement and test backend, frontend, database migrations/seeds, model adapter, evaluation harness, documentation, containerized local run and CI. No dead buttons or fake functional screens. Do not mark a feature complete until it works through its real application path or is explicitly labelled as a limitation.
10. Do not invent scores, benchmark charts, training outcomes, model compatibility, screenshots, deployment success or resume claims. Generate all metrics from actual runs and include denominators, data split, versions, hardware, timestamps and limitations.
11. Run tests and linters after meaningful changes. Fix failures. Before finishing, run the available full test suite and the documented end-to-end smoke path. If a test cannot run, state precisely why and do not report it as passing.
12. Keep dependencies coherent and pinned once tested. Separate optional training dependencies from the web API runtime where practical. Never commit secrets; create `.env.example` only.
13. Continue automatically through all phases when safe and resources permit. Do not stop at each phase to ask whether to continue. If you hit a real blocker, document it and complete independent work around it.
14. At the end, provide a concise handoff: what works, exact setup/run/test commands, verified test results, real-model status, benchmark/training status, known limitations, and any user action required.

## Minimum final output
- A working full-stack project in this workspace.
- Reproducible synthetic data and deterministic business tools.
- Real open-weight model integration with model-independent action normalization.
- Explicitly labelled deterministic test backend.
- Human-approved support-ticket creation.
- Traces/audit, evaluation dataset and runner, result exports, tests, Docker/Compose and CI.
- Documentation listed in `docs/ACCEPTANCE_CHECKLIST.md`.

## Start instruction
Begin by inspecting the repository and environment, then implement the project end-to-end according to this kit. Do not return only a plan. Keep `docs/PROGRESS.md` current throughout.
