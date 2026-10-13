# P2 Final Project Acceptance Report

**Assessment date:** 2026-10-12
**Scope:** Local synthetic e-commerce support application; no production or external business integrations.
**Overall verdict:** **PARTIAL** — the application and bounded real-model workflows run, but held-out action quality and required-slot clarification targets are not met.

> **Interview endpoint update (2026-10-12):** The best presentation result is V4's 27/28 (96.4%) exact-action development replay with zero unexpected write proposals. It used 28 distinct cores and internally AI-authored labels; replay did not execute tools. Its separate 18-core result was 16/18 (88.9%), below the 90% target. V4's separate actual-app smoke passed 8/8 fixed workflows. Later structured-intent smokes passed three selected FastAPI flows but did not form a broad comparison. This is the chosen stopping point for the interview, not a PASS: original acceptance remains **PARTIAL**. See [P2 final interview endpoint](P2_FINAL_INTERVIEW_ENDPOINT.md), [V4 report](P2_CONTROLLER_V4_EXPERIMENT_REPORT.md), and [current checklist](ACCEPTANCE_CHECKLIST.md). Earlier dated status notes below are historical snapshots.

> **Current verification update (2026-10-11):** The latest checkout has 67 passing backend tests, Ruff and frontend builds passing, an isolated Playwright approval flow passing 1/1, clean SQLite migration, and running Docker Compose services. The latest local Ollama/FastAPI integration passed 8/8 fixed synthetic workflows; it is a smoke, not V5 test coverage. The exploratory V5 dev candidate comparison is **not accepted**: its AI-assisted overlay lacked a separate independent human reviewer and the candidate had two unexpected write proposals. The candidate remains unactivated, and frozen quality acceptance remains PARTIAL. Details: [current checklist](ACCEPTANCE_CHECKLIST.md), [current Ollama evidence](FINAL_REAL_LLM_VERIFICATION.md), and [progress log](PROGRESS.md).

> **Latest final-mission update (2026-10-11):** Fixed a verified orchestration defect so multi-step eligibility/refund responses are rendered from successful tool results instead of model-authored outcome prose; malformed multi-step results now fail closed; ISO-date trace redaction is fixed. The final regression suite passed **68 tests**; Ruff, frontend build, isolated Playwright approval flow (1/1), fresh SQLite migration, V1–V5 validators and current Docker Compose process check passed. A new actual local Ollama/FastAPI V4 smoke passed **9/9** on synthetic data, including grounded eligibility and refund estimates, tenant denial, and ticket approval/replay: `experiments/results/p2_final_mission_v4_integration_final_v2_20261011.json`. This smoke is not a broad benchmark. No fresh ≥60-core final suite or independent label review was completed, and locked V5 quality metrics remain below threshold; verdict remains **PARTIAL**.

## Acceptance summary

| Area | Verdict | Evidence and limits |
|---|---|---|
| Real Ollama application path | PASS for bounded workflows | Ollama `qwen3:1.7b` Q4_K_M completed 8/8 explicit synthetic checks through FastAPI with a 90-second turn bound. A post-runtime-patch refund-estimate workflow also passed. A separate 30-second run passed 7/8; its multi-step eligibility final response exceeded the whole-turn budget. |
| Original pinned Transformers model | PARTIAL | Pinned Qwen3-1.7B loaded on CPU but did not produce a complete valid tool-call response within the 90-second generation limit. Historical result preserved. |
| Raw model action quality | NOT MET | Frozen v2 raw run: valid 134/140 (95.7%); exact 40/140 (28.6%); expected-tool selection 32/80 (40.0%); exact tool arguments 24/70 (34.3%); non-tool exact 10/60 (16.7%); six invalid/errors. Targets for tool and argument accuracy were 85% and 80%. |
| Hybrid action quality | NOT MET | Frozen offline v2 action replay: exact 96/140 (68.6%); tool selection 50/80 (62.5%); exact arguments 44/70 (62.9%); required-slot clarification 28/40 (70%). Targets were 90% exact/tool/arguments and 95% clarification (with minimum floors also unmet for action metrics). This replay executed no tools. |
| Ticket clarification contract | PARTIAL | Code and API enforce a grounded order ID for order-related tickets; generic unlinked tickets remain valid per the schema. Seven injection variants and ticket clarification cases have regressions. Held-out hybrid clarification score is 28/40, below target. |
| State-change approval and idempotency | PASS for tested flows | In bounded actual-app runs and regressions, ticket stayed pending before supervisor approval; replay returned the same ticket and one row existed. No unapproved ticket write, duplicate ticket row, or successful cross-tenant disclosure was observed in the eight-check 90-second integration run. These counts are bounded evidence, not a universal guarantee. |
| Deterministic backend | PASS as test fixture | CI/default `deterministic_test` remains explicitly labeled; its separate 48/48 fixture validation is not model performance and is not included in real-model metrics. |
| UI and regression gate | PASS for checks run | Backend: 46 passed; Ruff passed; frontend production build passed; latest Playwright approval journey passed 1/1. Fresh SQLite migration reached `0002_turn_budgets (head)`; v1 and v2 dataset validators passed. Docker Compose was unavailable in the latest check. |
| Evaluation integrity | PARTIAL | V2 suite is internally generated synthetic data, 28 dev / 140 test cases across 14 families. One frozen raw run and paired offline replay are preserved. The 30 fault-control rows are declared templates; they were not all independently executed. This is not an external benchmark. |

## Model identities and separate results

### Original pinned Transformers model

The pinned Transformers Qwen3-1.7B revision loaded on CPU, but did not produce a complete valid tool-call response within the 90-second generation limit. This result is separate from Ollama and remains unchanged.

### Smaller local Ollama model

Model: `qwen3:1.7b`, GGUF Q4_K_M, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`.

- The 90-second v2 actual application integration passed 8/8 checked synthetic workflows. It exercised lookup, multi-step eligibility, missing-slot clarification, policy lookup, injection handoff, cross-tenant denial, and ticket proposal/supervisor approval/replay. Eight model inference calls; inference p50/p95 11,400/25,073 ms; request p50/p95 11,140/37,491 ms. Artifact: `experiments/results/hybrid_controller_v2_demo_real_integration_90s_20261010.json`.
- The separate 30-second v2 integration passed 7/8. Registered list-items and eligibility tools succeeded, but model final synthesis failed within the whole-turn request bound; the request took 37,491 ms. Artifact: `experiments/results/hybrid_controller_v2_real_integration_frozen_20261010.json`.
- After the frozen action suite, final-answer synthesis was hardened to call Ollama without registered tools and request a concise answer grounded in tool results. The supplemental estimate smoke then passed through the actual app: `list_order_items` → `check_refund_eligibility` → `calculate_refund_estimate`; tool-derived amount `$50.27`; model answer included the amount; no ticket write. Request time 27,993 ms. Artifact: `experiments/results/hybrid_controller_v2_estimate_smoke_postfinalphase_90s.json`.
- Before the patch, the same estimate path executed its tools but final answer generation failed. That failure artifact is preserved. The trace was corrected so failed final synthesis does not create a fictitious duplicate failed-tool event.

The post-freeze answer-phase patch does not alter the frozen raw action run or offline hybrid action scores. It is documented in `experiments/results/hybrid_controller_v2_runtime_patch.json`; current source is therefore not byte-for-byte identical to the frozen source bundle. The post-patch estimate smoke is supplemental, not a benchmark score.

### Frozen v2 action suite

Dataset: `experiments/datasets/hybrid_controller_v2/scenarios.jsonl`; 28 dev / 140 test cases; 14 behavior families. Dataset SHA-256: `3c53d39fdfcb3f621b5b0c9135ca286fb9ef79ec85ba00db54616e3b2d62cd64`. The test prompts are internally authored synthetic cases, not an independently sourced benchmark.

| Layer | Result | What it measures |
|---|---:|---|
| Raw Ollama model | 134/140 valid; 40/140 exact (28.6%) | Single model-generated action proposals; no tools executed. |
| Raw expected-tool choice | 32/80 (40.0%) | Cases whose expected action selects a tool. |
| Raw exact tool args | 24/70 (34.3%) | Cases with expected tool arguments. |
| Hybrid controller action replay | 96/140 exact (68.6%) | Final action after controller policy applied to saved raw proposals; no tools or database writes executed. |
| Hybrid expected-tool choice | 50/80 (62.5%) | Controller-plus-proposal tool selection. |
| Hybrid exact tool args | 44/70 (62.9%) | Controller-plus-proposal tool arguments. |
| Required-slot clarification | 28/40 (70%) | Clarification cases; target was 95%. |
| Unsafe-policy handoff | 10/10 (100%) | The held-out family’s expected handoff cases. |

Artifacts: `experiments/results/ollama_qwen3_1.7b_v2_test_modelonly_frozen.json`, `experiments/results/hybrid_controller_v2_test_frozen.json`, and CSV companion. The model-only p50/p95 action latency was 10,501/17,870 ms. Do not describe action replay as task completion or infer execution safety counts from it; those fields are not measured by the offline evaluator.

## Safety contract and tested outcomes

Only registered tools execute. Strict schemas reject unknown tools/properties and malformed arguments. Authorization, tenant scope, eligibility, arithmetic, and approval are server-side. State-changing ticket proposals remain pending until an authenticated supervisor approves; stored arguments are revalidated, and idempotency prevents duplicate tickets on replay. Prompts and tool output are treated as untrusted; hidden reasoning is not recorded. The included records are synthetic only.

The actual-app integration observed no successful cross-tenant disclosure, unapproved ticket insertion, or duplicate ticket row across its eight checked workflows. Automated tests additionally cover API boundaries, authorization, invalid actions, injection strings, pending approval and replay. This evidence only applies to the tested cases.

## Runtime and resource limits

The available Ollama model was already cached; no paid service or new model download was used. The host has an i5-1240P, 7.7 GiB visible RAM, and a 4 GiB GTX 1650; one inventory observed about 0.5 GiB free RAM while the model used about 1.7 GiB VRAM. The 30-second end-to-end cap was insufficient for some two-stage calls; the documented local demo uses a 90-second request bound. Docker Desktop's Linux engine pipe was unavailable during the latest check, so current Compose readiness is not claimed (prior successful Compose evidence remains historical).

## Commands and evidence

Latest checks for this completion pass:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q  # 46 passed
.\.venv\Scripts\ruff.exe check backend/app backend/tests experiments/evaluation experiments/data_generation
npm run build --prefix frontend
npm run test:e2e --prefix frontend                 # 1 passed
.\.venv\Scripts\python.exe experiments/evaluation/validate_dataset.py
.\.venv\Scripts\python.exe experiments/evaluation/validate_v2_suite.py
git diff --check
```

Fresh SQLite migration smoke reached `0002_turn_budgets (head)`. The latest Docker check could not connect to Docker Desktop's Linux engine; do not represent Docker as currently verified.

## Overall conclusion

P2 is an interview/demo-ready local portfolio application for bounded synthetic workflows, with a real local model path, server-side safety controls, traceability, approval and idempotency. It is **not 100% complete against the stated model-quality acceptance targets** and is **not production-ready**. The raw and hybrid held-out scores and the clarification rate are below target. The deterministic backend is only a test fixture. No real customer, payment, email, or production integration exists.

## V3 reliability phase

V3 adds a new internally generated suite at `experiments/datasets/hybrid_controller_v3/`: 60 development and 150 held-out scenarios across 14 families, with disjoint style pools and checksum `2b599e68435dcdafd839685ab2a0db144ca6f6587100bcc3259f9302047f2e64`. It is an internal synthetic benchmark, not an external independent benchmark. Generator, validator, and freeze manifest are `generate_v3_suite.py`, `validate_v3_suite.py`, and `experiments/results/hybrid_controller_v3_frozen_config.json`.

The predeclared V3 actual-application subset executed 8/8 workflows successfully through fresh synthetic SQLite and local Ollama. It covered order lookup, multi-step eligibility, clarifications, policy, injection handoff, cross-tenant denial, and ticket approval/replay. The artifact is `experiments/results/hybrid_controller_v3_e2e_subset.json` with the underlying execution trace in `hybrid_controller_v3_e2e_subset.integration.json`. This is executed task evidence for the representative subset only; it is not a 150-case end-to-end score. The subset observed zero unauthorized writes, zero duplicate ticket rows, and zero cross-tenant disclosure in the tested cases. Model latency remained resource-constrained: one lookup request was 74,704 ms and its model calls were 58,011 ms and 16,176 ms; the run used the cached Q4_K_M model and a 90-second request bound.

The full V3 action tracks did run once after the corrected V3 freeze. Raw Ollama produced 150/150 valid records, 46/150 exact actions, 41/85 expected-tool selections, and 33/75 exact argument dictionaries. The paired offline replay produced 100/150 exact actions, 55/85 tool selections, 51/75 exact arguments, 25/43 required clarifications, and 11/11 safe handoffs. These are action-level results; replay executed no tools or writes. The broad 40–60 workflow end-to-end target was not attempted because the local runtime is resource-constrained; only the predeclared 8-case application subset was executed. Overall verdict remains **PARTIAL**.

See the complete V3 metrics report at `experiments/results/hybrid_controller_v3_final_metrics.md`.

## Final bounded acceptance phase: latency optimization and V4 freeze

The application now uses a deterministic `grounded_tool_response` path for direct authoritative read results (lookup, policy, item listing, eligibility, and estimate). It renders only fields returned by successful registered tools, records `response_path=grounded_template`, and never bypasses authorization or business rules. Multi-step workflows and ticket approval retain the existing bounded model synthesis path. Backend regression coverage remains 46 passed after this change.

V4 was generated and validated as a new internal synthetic suite: 60 development and 150 test scenarios across 14 families, with checksum `7246e38958d1a5301619572e9b3837cd78cbd8dabd64878fa6bfb14a94cbf586`. The V4 freeze is `experiments/results/hybrid_controller_v4_frozen_config.json`. V4 action and broad 42-case end-to-end scoring were not run in this bounded phase; no V4 score is inferred from V3.

The latest acceptance verdict is **PARTIAL**. The grounded response path addresses unnecessary final-answer latency, but a fresh broad latency benchmark and V4 held-out task run remain required before a PASS claim.

## V4 audit and V5 acceptance preparation

The V4 audit found template-level leakage: **41 shared `template_id` values** between development and test, and one shared `template_core_id`; prompts differed mainly by wrapper wording. V4 exact-message uniqueness therefore does not establish unseen-template generalization. V4 remains historical and its manifest/results are unchanged.

V5 corrects this evaluation design. It has 60 development and 150 test scenarios across 14 families, separate underlying template pools, explicit `template_core_id` and `template_pool_id`, zero shared core IDs, and zero normalized core-request overlap. V5 SHA-256 is `1cde0a85123c696a331d5af5328ecfa935d9f570b66089a7b5a512f6bd975acd`; freeze manifest: `experiments/results/hybrid_controller_v5_frozen_config.json`. V5 is an internally authored synthetic benchmark, not an external benchmark.

V5 action and 42-case end-to-end scoring were not run in this bounded phase. The project remains **PARTIAL**; no V5 score is claimed.

## Final Fresh60 and V5 application verification update — 2026-10-11

A new frozen 60-core Ollama evaluation and the preselected V5 42-case real FastAPI/Ollama application suite have now been run. Fresh60 results were raw 16/60, paired V2 replay 31/60, and opt-in V4 replay 42/60; V4 tool choice was 27/36 and exact arguments 23/32. The 42-case actual application checks passed 26/42, with 16 failures. Duplicate ticket approval was idempotent. These runs use internal evaluation labels and do not meet the 90% engineering targets or establish generalization. Official frozen V5 raw/hybrid/clarification results remain unchanged at 25/150, 31/150 and 6/43. Original P2 acceptance remains **PARTIAL**. Full case-level traces, score definitions, family breakdowns, hashes, and exact failure IDs are in [the Fresh60 and 42-case report](P2_FRESH60_AND_42CASE_EVALUATION_REPORT.md).
