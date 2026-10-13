# P2 Definition of Done — Evidence Checklist

## Interview stopping point (2026-10-12)

The project is frozen for interview presentation at the V4 controller result: **27/28 (96.4%)** exact actions on an exploratory 28-core development replay, zero unexpected write proposals, followed by **16/18 (88.9%)** on a separate small AI-labeled set. The 96.4% result is offline and executes no tools. V4 real-app smoke was 8/8 fixed workflows. These results support a portfolio demonstration, not completion of the original acceptance gates. Overall status remains **PARTIAL**. See [final interview endpoint](P2_FINAL_INTERVIEW_ENDPOINT.md).

## Structured intent workflow candidate (2026-10-12)

- [x] Added an opt-in JSON-schema-constrained intent/slot adapter for local Ollama; deterministic CI backend and V2 defaults are unchanged.
- [x] Added a deterministic workflow planner that grounds relevant identifiers, clarifies missing or ambiguous item scope, selects only registered tools, and derives policy/eligibility categories in trusted code. Explicit all-items scope comes from user text; irrelevant model `"*"` spans are not used.
- [x] Ticket proposals continue through the existing pending-approval endpoint and idempotent approval execution.
- [x] Added a separate smoke configuration and implementation notes in `docs/STRUCTURED_INTENT_WORKFLOW.md`.
- [x] Focused structured-intent tests — 16 passed; full backend tests — 98 passed (one existing Starlette/AnyIO deprecation warning).
- [x] Real local Ollama FastAPI smoke, process-supervised with 25-second HTTP and 45-second hard process limits: order lookup 5/5 checks, multi-step USD 90.28 estimate 5/5, pending ticket/supervisor approval/duplicate replay 7/7. Frozen result/source/model artifacts are under `experiments/results/p2_structured_intent_*_20261012T0041*.json`.
- [x] Ruff, frontend production build, isolated Playwright approval flow (1/1), V1–V5 validators, and clean SQLite migration to `0002_turn_budgets (head)` passed.
- [ ] Current Docker Compose readiness is not verified; this host could not connect to the Docker Desktop Linux engine during this pass. An earlier phase's successful Compose run remains historical evidence only.
- [ ] Broad fresh distinct-core real-model evaluation, independent label review, and original model-quality thresholds are still unmet. These curated smoke outcomes do not qualify the candidate for promotion; overall P2 remains **PARTIAL**.

Checked items include evidence. Remaining items are explicitly incomplete or blocked; test-backend metrics are not real-model results.

## Product functionality

- [x] Local install/launch documented and exercised: Python editable install, Alembic migration, Vite build, live API/UI HTTP smoke.
- [x] Chat order lookup returns database/tool result: `backend/tests/test_api_workflows.py`; live smoke returned ORD-10021 transit status.
- [x] Item listing and source-of-truth policy implemented: `backend/app/tools/domain.py`; policy and item domain tests.
- [x] Eligibility is deterministic: `backend/app/tools/domain.py`; eligibility/window/damage tests.
- [x] Refund estimate uses `Decimal`: estimate test returns expected `90.28` for seeded items.
- [x] Ticket appears pending before write: API approval workflow test checks no ticket row before approval.
- [x] Authenticated approve/reject routes: agent denial, supervisor approval, rejection integration tests.
- [x] Model text alone cannot write: only server approval route inserts ticket; integration test verifies pending state.
- [x] Approval replay is idempotent: integration test confirms same ticket ID on repeated approval and one ticket row.
- [x] Conversation history and trace routes/UI implemented: trace endpoint API test and UI trace drawer.
- [x] Experiment history screen displays persisted benchmark runs and saved JSON result artifacts through an evaluator/admin API; records show source, backend, split, status and measured provenance.
- [x] Visible controls are wired to API or role-gated; benchmark outputs explicitly label fixture results.

## Model and orchestration

- [x] Open-weight Transformers adapter and setup documented: `backend/app/llm/backends.py`, README, model card.
- [x] Versioned action shape aligned with `config/action_envelope.schema.json`; Pydantic validates action and claims.
- [x] Server-side registered-tool allowlist and strict argument schemas are implemented.
- [x] Tool/business authorization, enum, required-field and unknown-field checks are implemented.
- [x] Configurable model-step, wall-clock, output-token, retry and tool-call limits are enforced; tool budget also covers state-change proposals. API regression tests cover exhausted proposal budget. Model generation uses Transformers `max_time` and a post-generation deadline check; an individual GPU kernel cannot be interrupted mid-operation.
- [x] Transformer adapter allows one correction attempt; malformed actions fail closed. Strict parser tests cover unknown tools and extra fields.
- [x] Test backend is visibly labeled “Deterministic test backend — not an LLM” and reports are labeled as fixture behavior.
- [x] Model revision, Apache-2.0 license, chat format and compatibility source checked and documented in `docs/model_card.md`.
- [x] Pinned real-model load and one GPU inference smoke succeeded with PyTorch 2.7.0+cu128, Transformers 4.51.3 and Qwen3-1.7B revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`; prompt returned a schema-valid lookup action. GTX 1650 required CPU offload. First 64-token action truncated and was rejected; normal 256-token cap succeeded.
- [x] Final real-LLM application verification executed. Final verdict is **PARTIAL**, not a quality PASS: actual Ollama+hybrid integration passed 8/8 checked workflows; held-out hybrid action score is 43/60 and missing-ticket-order clarification is 0/12. See the latest section in `docs/FINAL_REAL_LLM_VERIFICATION.md`.
- [x] Low-resource real-model route evaluated using the already-installed local Ollama `qwen3:1.7b` Q4_K_M model; no second model download or paid service was used. Opt-in settings are in `.env.hybrid-real-llm-smoke.example`.
- [x] GGUF/llama.cpp was investigated but not installed or used; Ollama supplied the actual local GGUF runtime. The original Transformers model-only result remains preserved as a separate historical experiment.
- [x] Ollama installation blocker resolved later by the user. The official local API is now serving `qwen3:1.7b`; see the real-model smoke evidence below.
- [x] Ollama real-model application integration: local `qwen3:1.7b` (Q4_K_M, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`) passed 8/8 recorded synthetic workflows, including eligibility. Ticket proposal stayed pending, supervisor approval created one ticket, and replay returned the same ticket. Artifact: `experiments/results/hybrid_controller_v1_real_integration_frozen_20261010.json`.
- [x] Frozen Ollama action-only evaluation completed once on the locked 60-case test split. Raw output: `experiments/results/ollama_qwen3_1.7b_test_frozen_v2.json`; valid 50/60, exact action 12/60, tool-selection match 24/60, exact arguments 12/60, p50/p95 3,400/4,109 ms. Task completion is not measured by this action-only harness; quality targets are documented as unmet/not measurable.
- [x] Historical full 48-case validation remains in its original artifact (old metric: 0/48 exact); corrected bounded raw model result is 12/48 exact. Frozen validation hybrid action replay is 48/48. The two hybrid metrics are application-plus-model actions, not raw LLM scores or task completion.
- [x] Frozen corrected bounded Ollama raw test completed once after source/config freeze: valid 55/60, exact 12/60, tool selection 12/36, exact arguments 12/36, p50/p95 3,104/3,524 ms. Hybrid offline action replay: 43/60 exact; tool selection 31/36; exact arguments 31/36; clarification 0/12; handoff 12/12. Five invalid model actions were handled as fail-closed; one deterministic argument repair occurred with zero extra model retries. The offline evaluator executed no tools, so unsafe/duplicate write execution counts are not measured there. Raw and hybrid evidence paths are recorded in the final verification and test report.

## Data and security

- [x] Only deterministic synthetic demo fixtures and generated synthetic prompts are included.
- [x] Alembic initial migration applied from clean SQLite state; fixed seeding is tested.
- [x] Server-side tenant/order scoping verified for nonexistent and other-tenant records.
- [x] No unregistered tool, arbitrary code, generated SQL or unrestricted HTTP tool is available.
- [x] Prompt injection and policy-bypass examples are in the dataset; direct injection test safely hands off. Read-tool results are marked and serialized as untrusted data before final-answer generation; unit test covers instruction-like tool content.
- [x] `.env.example` contains placeholders; `.env`, databases, adapters and local build artifacts are ignored.
- [x] Dedicated recursive trace redaction covers sensitive keys, email addresses and phone numbers; tests verify a pending reviewer retains original proposal text while the trace is redacted. Audit event details are allowlisted server-generated metadata; hidden reasoning/prompts are not persisted.

## Evaluation and research integrity

- [x] Deterministic generator, validator, checksum manifest and family leakage checks run successfully.
- [x] Train/validation/test family-separated split: 96/48/60 examples; locked test labels are only scored after configuration freeze.
- [x] Benchmark reports denominator, per-family counts, dataset checksum/version, backend/model revision when applicable, and environment.
- [x] Baseline A and B completed on the same 48 validation examples; both exact action matches 0/48. A: valid 48/48, p50 24.77s, p95 27.01s. B: valid 29/48, p50 33.97s, p95 44.39s. Analysis and raw prediction artifacts saved in `experiments/results/`; the locked test split was scored only after configurations were frozen. These are action-selection metrics, not end-to-end task success.
- [x] One-step QLoRA smoke trained, adapter saved, reloaded in a fresh process and generated a response; artifact checksum and training metadata saved to `experiments/results/lora_smoke_report.json`. This is feasibility evidence only, not a quality benchmark or improvement claim.
- [x] Frozen A/B/C action-selection comparison completed on the same isolated 60-case test split after configuration freeze. Exact actions: A 23/60, B 24/60, C 24/60. Valid actions: A 38/60, B 27/60, C 55/60. Validation exact actions were 0/48 for all three; split discrepancy is documented and no generalization or improvement claim is made. Raw predictions and metrics saved in `experiments/results/`.
- [x] 20-step NF4 QLoRA feasibility-scale experiment trained on train-only data, saved/reloaded in a fresh process and evaluated; adapter SHA-256, mean loss, versions and split are recorded in `experiments/results/p2-lora-20step/training_run.json`. This is not a production-length fine-tune and did not improve exact actions over B on test.
- [x] C was evaluated with NF4 QLoRA training and NF4 inference; A/B used unquantized FP16. The analysis explicitly treats latency as confounded and makes no attribution to LoRA alone. No separate paired quantized-vs-unquantized experiment or alternate serving backend was run.
- [x] No fabricated model scores, latency, costs, training outcomes or gains. Fixture validation run (`experiments/results/latest_fixture_run.json`) is labeled and reports a 48-example denominator.

## Engineering and documentation

- [x] Unit/domain tests cover tools, policy, calculations, strict schema, authorization, approval/rejection and idempotency.
- [x] API integration tests cover lookup/trace, benchmark persistence, approval and expected failures.
- [x] Playwright browser E2E covers order lookup, ticket proposal and supervisor approval; `npm run test:e2e` passed locally. CI installs Chromium and runs the flow.
- [x] `ruff check app tests`, `pytest` (17 passed), `npm run build`, `npm audit` (0 vulnerabilities), Playwright E2E (1 passed), and dataset validator (204 valid) pass. Model benchmark CLI completed A/B/C validation and locked-test runs; see saved artifacts.
- [x] Docker Compose runtime validated after the user's restart: `docker compose up --build -d`; PostgreSQL 17.4 healthy, API `/health/ready` returned `ready` with database `ready` and `deterministic_test`, web root returned HTTP 200. Fresh PostgreSQL migrations reached `0002_turn_budgets`; a duplicate-column issue in that migration was fixed by checking existing columns before adding them.
- [x] Live Compose workflow: seeded ORD-10021 lookup completed via `lookup_order`; agent ticket proposal remained `pending_approval`; supervisor approval created `TKT-261010-82292350`; repeating approval returned the same ticket ID and “already completed.”
- [x] CI workflow runs backend tests/lint, dataset generation/validation, frontend build and Playwright E2E.
- [x] README, architecture, API, security, deployment, model/dataset cards, experiment protocol, report template and demo script are present.
- [x] `docs/PROGRESS.md` records commands, results, blockers and next work.
- [x] Final handoff includes install/run/test and real-model commands plus current limitations.

## Final bounded hybrid-controller phase — 2026-10-10

- [x] Frozen deterministic hybrid controller implemented and opt-in; default CI backend remains deterministic_test.
- [x] Validation-only development recorded. Corrected bounded raw Qwen validation result: 12/48 exact actions; frozen hybrid action replay: 48/48. These are action-level scores; hybrid replay did not execute tools.
- [x] Actual Ollama/FastAPI integration against fresh synthetic SQLite data: 8/8 checked outcomes passed, including lookup, eligibility, missing-slot clarifications, policy, injection handoff, cross-tenant denial, ticket proposal/approval/replay.
- [x] Frozen source/configuration identified by SHA-256 and one new locked-test inference run completed; historical results and dataset were preserved.
- [x] Locked raw model-only test: 55/60 valid, 12/60 exact, tool selection 12/36, exact arguments 12/36; p50/p95 3,105/3,524 ms.
- [x] Locked hybrid action replay: 43/60 exact, tool selection 31/36, exact arguments 31/36, unsafe-policy handoff 12/12, one repair, zero extra model retries. Offline replay executed no tools, so its unsafe/duplicate write execution fields are not measured.
- [ ] Missing-ticket-order clarification quality target: NOT MET, 0/12. The offline hybrid replay retained 12 ticket-proposal actions, some with a null order ID. This is a material workflow limitation; source was frozen after the one test run and not tuned against test labels.
- [ ] Raw model-only quality goals: NOT MET, tool selection target 85% vs 33.3%; exact-argument target 80% vs 33.3%.
- [x] In the separate real application integration suite, ticket proposal remained pending until supervisor approval; repeated approval returned the same ticket and one row existed. No unapproved ticket write or duplicate was observed in those tested workflows. This does not prove universal safety.
- [x] Final artifacts and distinctions are documented in docs/FINAL_REAL_LLM_VERIFICATION.md, docs/PROGRESS.md, experiments/results/hybrid_controller_validation_v1.md, and experiments/results/hybrid_controller_test_v1.md.

## Final interview-ready pass — hybrid controller v2

- [x] Ticket contract follows the actual schema: generic tickets may be unlinked; order-related tickets require one user-grounded valid order ID before proposal. Controller and API enforce it; approval revalidates the stored schema and tenant-scopes a linked order.
- [x] Clarification regressions cover missing, malformed, ambiguous/conflicting, and later-supplied order IDs, missing item IDs, no tool/write before clarification, and preserved context.
- [x] Seven injection variants are tested at controller and actual API boundary. Unknown tools, malformed action arguments, runtime failures, cross-tenant access, pending approval, approval replay, and duplicate prevention have regression tests.
- [x] Refund-estimate wording is routed through the existing registered item/eligibility/estimate workflow; business calculations remain deterministic.
- [x] Frontend trace shows active backend/model identity, redacted structured proposal, controller decision, registered tool arguments/result, authorization/validation, and trace ID without chain-of-thought.
- [x] Added `docs/DEMO_RUNBOOK.md`, `docs/INTERVIEW_DEFENSE_GUIDE.md`, `docs/PROJECT_CLAIM_EVIDENCE_MATRIX.md`, `docs/FINAL_PROJECT_ACCEPTANCE_REPORT.md`, and README architecture/evaluation instructions.
- [x] Generated v2 internal synthetic suite with separate dev/test template pools (28 dev, 140 test) and 30 separately declared deterministic fault controls. Manifest checksums and validator pass. This is not an external benchmark.
- [x] Regression gate after implementation: backend 44 passed (one upstream Starlette/AnyIO deprecation warning), Ruff passed, frontend build passed, Playwright approval journey 1/1 passed, fresh SQLite migrations reached `0002_turn_budgets (head)`, v2 data validator passed, and whitespace check passed.
- [x] Frozen v2 raw model and paired offline hybrid replay completed once. Raw: valid 134/140, exact 40/140 (28.6%), tool selection 32/80 (40.0%), exact args 24/70 (34.3%). Hybrid: exact 96/140 (68.6%), tool selection 50/80 (62.5%), exact args 44/70 (62.9%), clarification 28/40 (70%). These are action metrics; replay executes no tools. Artifacts and thresholds are in `docs/FINAL_PROJECT_ACCEPTANCE_REPORT.md`.
- [x] Actual local Ollama/FastAPI v2 integration: 90-second run passed 8/8 explicitly checked synthetic workflows; 30-second run passed 7/8 because final synthesis exceeded its whole-turn bound. A supplemental post-patch real estimate workflow passed through list → eligibility → estimate and model final answer. No unapproved ticket write, duplicate ticket row, or successful cross-tenant disclosure was observed in the eight-workflow run; this is bounded evidence only.
- [x] The frozen model-only and hybrid runs retain their pre-answer-phase-patch provenance. The later Ollama final-answer hardening and supplemental estimate smoke are recorded separately in `experiments/results/hybrid_controller_v2_runtime_patch.json`; benchmark scores were not rewritten.
- [x] Final regression gate for this pass: `pytest backend/tests -q` — 46 passed; Ruff passed; frontend production build passed; latest Playwright E2E passed 1/1; v1/v2 dataset validators passed; fresh SQLite migration reached `0002_turn_budgets (head)`; `git diff --check` passed.
- [ ] Raw model/action quality thresholds: NOT MET (tool selection target 85% vs 40.0%, exact arguments target 80% vs 34.3%).
- [ ] Hybrid action thresholds: NOT MET (exact action 68.6% vs 90%; tool selection 62.5% vs 90%; exact args 62.9% vs 90%).
- [ ] Required-slot clarification target: NOT MET (28/40, 70%, target 95%).
- [ ] Docker Compose readiness: NOT VERIFIED in this pass because Docker Desktop's Linux engine pipe was unavailable; earlier successful Compose run is historical evidence only.
- [ ] Overall verdict: **PARTIAL**. Application workflows and bounded real-model integration work, but unmet evaluation targets prevent a full acceptance PASS. Do not report 100% or production ready.

## V3 reliability phase — 2026-10-10

- [x] New V3 internal synthetic suite generated and validated: 60 dev / 150 test, 14 behavior families, disjoint style pools, checksum `2b599e68435dcdafd839685ab2a0db144ca6f6587100bcc3259f9302047f2e64`.
- [x] V3 model/source freeze manifest created with cached Ollama digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`.
- [x] Predeclared actual-app V3 subset executed 8/8 workflows on fresh synthetic SQLite, with registered tool traces, final answers, clarifications, injection handoff, cross-tenant denial, approval and replay. Artifacts: `experiments/results/hybrid_controller_v3_e2e_subset.json` and `.integration.json`.
- [x] V3 executed subset observed zero unauthorized writes, zero duplicate ticket rows, and zero successful cross-tenant disclosure. These counts apply only to the eight executed cases.
- [x] V3 raw-model 150-case action score completed once after freeze: 150/150 valid, 46/150 exact (30.7%), tool selection 41/85 (48.2%), exact arguments 33/75 (44.0%), p50/p95 3,029/3,938 ms, zero timeouts/errors. Artifact: `experiments/results/hybrid_controller_v3_raw_test_final.json`.
- [x] V3 hybrid offline 150-case replay completed against the same 150 raw IDs: 100/150 exact (66.7%), tool selection 55/85 (64.7%), exact arguments 51/75 (68.0%), required-slot clarification 25/43 (58.1%), safe handoff 11/11 (100%). Artifact: `experiments/results/hybrid_controller_v3_hybrid_test_replay_final.json`. No tools or writes execute in this track.
- [ ] V3 end-to-end target on 40–60 workflows: NOT MET/NOT RUN as a broad sample; only the declared 8-workflow representative subset executed and all 8 passed.
- [ ] V3 phase verdict: **PARTIAL**. The real application path is demonstrated on the executed subset, but full V3 acceptance requires a separately resourced final action and end-to-end evaluation.

## Final latency and V4 phase

- [x] Added a general grounded response path for direct successful read-tool results. It renders only trusted result fields, records `grounded_template`, and preserves authorization, validation, approval, and deterministic business rules.
- [x] Regression suite after latency change: 46 backend tests passed; Ruff passed; `git diff --check` passed.
- [x] Generated and validated V4 internal synthetic suite: 60 dev / 150 test, 14 families, checksum `7246e38958d1a5301619572e9b3837cd78cbd8dabd64878fa6bfb14a94cbf586`; V4 freeze manifest created with model digest and source hashes.
- [ ] V4 raw action track: NOT RUN in this bounded phase.
- [ ] V4 hybrid action replay: NOT RUN in this bounded phase.
- [ ] V4 broad executed end-to-end subset: NOT RUN; existing V3 executed subset remains 8/8 and is not relabeled as V4.
- [ ] Latency target PASS: NOT VERIFIED after the optimization on a fresh broad workload; prior V3 p95 was approximately 59.9 seconds overall.

## V4 audit and V5 split integrity

- [x] V4 audit completed without modifying V4: 41 shared template IDs and one shared core ID across dev/test; wrapper-only variation means V4 is not clean unseen-template evidence.
- [x] V5 generated and validated with separate underlying template pools, explicit core/pool IDs, 60 dev / 150 test, 14 families, zero core overlap and zero normalized core-request overlap. SHA-256: `1cde0a85123c696a331d5af5328ecfa935d9f570b66089a7b5a512f6bd975acd`.
- [x] V5 freeze manifest created with cached Ollama digest, controller/schema/prompt versions, settings, source hashes and dataset checksum.
- [ ] V5 raw action evaluation: NOT RUN.
- [ ] V5 hybrid replay: NOT RUN.
- [ ] V5 42-case actual end-to-end suite: NOT RUN.
## V5 frozen evaluation evidence (2026-10-11)

- [x] V5 dataset regenerated, validated, and frozen with disjoint core pools (`e5f6b399494884c347b55c8bf352c570913472be34ebc5ffb52e089ab08adbdf`).
- [x] Real Ollama V5 dev/test inference and hybrid replay artifacts saved.
- [x] Fresh real application integration subset passed 8/8, including approval and duplicate-approval protection.
- [x] Deterministic 42-case manifest created before execution.
- [ ] Full 42-case real-application execution: unmet; the existing integration harness supports the established 8-case suite only.
- [ ] Overall real-model reliability acceptance: unmet; V5 hybrid exact action rate is 20.7%.

## Completion re-audit and bounded engineering fix — 2026-10-11

## Final mission verification — 2026-10-11

### Engineering verification

- [x] Current backend regression suite: `python -m pytest backend/tests -q` — **51 passed**, one upstream Starlette/AnyIO deprecation warning.
- [x] Current Ruff check: `ruff check backend/app backend/tests` — passed.
- [x] Frontend production build: `npm run build --prefix frontend` — passed.
- [x] Browser approval journey: Playwright — **1 passed** on isolated API/web ports and a new SQLite database. A first default-port attempt reused the already-running Compose API/web at the default ports and its persistent PostgreSQL state; two old pending-ticket cards made the test heading ambiguous. Isolated execution passed without changing the test or deleting stored data.
- [x] Fresh SQLite migration: upgrade/current — `0002_turn_budgets (head)`.
- [x] V1, V2, V3, V4, and V5 validators — passed; V5 remains 60 dev / 150 test, zero normalized cross-split overlap, SHA `e5f6b399…`.
- [x] Docker Compose config/build/start and live health: API, Postgres 17.4 and web all running. API `/health/ready` returned `ready`, database `ready`, backend `deterministic_test`; web returned HTTP 200. A live synthetic `ORD-10021` lookup returned the seeded transit status. Existing `p2_p2-postgres` volume was reused and retained.
- [x] New actual local model smoke after a fresh source/config freeze: `experiments/results/p2_final_local_ollama_smoke_20261011.json`, using cached local Ollama `qwen3:1.7b` Q4_K_M digest `8f68893c…`, 90-second request limit and 256-token cap. **8/8** fixed synthetic application workflows passed, including real tool traces, cross-tenant denial and ticket approval/replay. It is separately labeled against V2 (`3c53d39f…`), not a V5 benchmark.
- [x] New smoke freeze: `experiments/results/p2_final_local_ollama_smoke_freeze_20261011.json`. The seven listed source files and V2 dataset hash were captured before inference; the output file did not exist before the run.
- [x] Deterministic backend remains the Compose/CI default and is not counted as real-model success. No paid/cloud API, new model download, or real customer/payment integration was used.

### One-shot V5 development comparison and decision

- [x] One paired saved-proposal comparison was run on the same 60 V5 dev row IDs, preserving the official V5 labels and frozen data. Its artifact is `experiments/results/p2_v5_dev_controller_candidate_comparison_v1.json`.
- [x] Reported exploratory scores: baseline 28/60 (46.67%) row-weighted and 45.83% core-weighted; candidate 55/60 (91.67%) row-weighted and 91.07% core-weighted; paired gains +45.00 and +45.24 percentage points. There are 28 distinct normalized cores, all repeated: 24 occur twice and 4 occur three times, across 14 families; hence all 60 rows contribute to repeated-core results and there are no singleton-core contributions. Per-family and paired details are in the JSON artifact.
- [x] Candidate safety result: baseline unexpected write proposals 0, candidate 2; clarification 3/19 → 17/19; handoff 4/4 → 4/4. Candidate gate is **FAILED** due to a safety regression. Candidate is an unactivated experiment module, not runtime behavior.
- [ ] V5 candidate acceptance: **INCONCLUSIVE / NOT ACCEPTED**. The overlay was prompt-first and retained official labels but was prepared by a Codex AI reviewer, not a separate independent human reviewer; audit history also means it was not blind. Therefore it does not satisfy independent-adjudication criteria even though 60 rows / 28 cores / 14 families were annotated. The gate must not be described as a valid model/controller quality win. No second candidate cycle and no V5 test tuning occurred.

### Current two-part verdict

- **Engineering completion:** functional, reproducible and demonstrable for the bounded synthetic local workflows above; safe controls are covered by tests and selected end-to-end runs. Limitations: no independent human label review, candidate safety regression, broad 42-case V5 application execution not run, and model-quality thresholds remain unmet. Not production-ready.
- **Original project acceptance:** **PARTIAL**. Frozen V5 raw exact action remains 25/150 (16.7%); V5 hybrid offline replay remains 31/150 (20.7%), with 6/43 (14.0%) required-slot clarifications. These thresholds are not changed by the exploratory dev comparison or the separate 8-workflow integration smoke.

### Original requirement completion matrix

| Requirement area | Status | Evidence and remaining gap |
|---|---|---|
| Core application functionality | **PASS (bounded synthetic scope)** | Six registered tools, persisted conversations/traces, and React chat are implemented. Backend workflow tests and the Playwright order lookup → pending ticket → supervisor approval journey pass. No real customer/external financial action exists. |
| Tool-calling and workflow reliability | **FAIL / INCOMPLETE** | Real Ollama/FastAPI executed 8/8 fixed V2 workflows, but V5 is not that app run and its selected 42-case run was not executed. V5 raw exact 25/150, hybrid replay 31/150; replay executes no tools. The 85% tool, 80% argument and 80% task-completion gates are unmet or not measured broadly. |
| Security and human approval | **PASS for covered tests/workflows; universal behavior NOT VERIFIED** | API/domain and controller tests cover validation, allowlisting, tenant-scoped reads, injection, pending approval, approval-time revalidation and idempotency. Historical actual-app subset observed no unauthorized write, duplicate ticket, or successful cross-tenant disclosure for its covered cases. |
| Backend, database, API, frontend quality | **PASS locally, Docker NOT VERIFIED currently** | Current backend tests, Ruff, production frontend build, browser approval flow and clean SQLite Alembic migration pass. The current Docker Linux engine was not checked successfully in this pass; historical Compose success is not current readiness. |
| Testing and reproducibility | **INCOMPLETE** | Automated checks and V1–V5 manifests/artifacts exist, but there is no Git commit/reflog; V5 has 15 prompt/gold entity disagreements and only 28 underlying prompt cores per split; an independent-label review artifact and V5 42-case E2E run are absent. |
| Model quality and evaluation | **FAIL** | V5 raw tool selection 19/85 (22.4%), exact arguments 4/75 (5.3%), hybrid action exactness 31/150 (20.7%), clarification 6/43 (14.0%). Original A/B/C test exact actions 23/60, 24/60, 24/60; C did not reach the specified +5-point improvement over B. Original pinned Transformers run timed out with incomplete JSON. |
| Documentation and portfolio demonstration | **PASS for local demo; deployment claims limited** | README, runbook, architecture, security, evaluation and claim/evidence docs are present and README status is current. Local browser E2E passes. Production readiness and current Docker deployment are not claimed. |

**Overall original acceptance: PARTIAL.** Core software and safety behavior have meaningful bounded evidence. Model-quality gates remain failed, broad task completion is not measured, and current Compose readiness is unverified. The matrix does not redefine or lower the original thresholds.

### Latest commands actually run

- Targeted policy-path test: `python -m pytest backend/tests/test_hybrid_controller.py -q` — **25 passed**, one upstream Starlette/AnyIO deprecation warning.
- Full backend suite: `python -m pytest backend/tests -q` — **47 passed**, same warning.
- Backend lint: `ruff check app tests` — passed.
- Frontend production build: `npm run build --prefix frontend` — passed.
- Browser end-to-end: `npm run test:e2e --prefix frontend` on isolated ports with a fresh synthetic SQLite DB — **1 passed** (order lookup, pending ticket, supervisor approval).
- Dataset checks: `validate_dataset.py` — 204 rows, SHA `a4c83c7d…`; `validate_v2_suite.py` — 168 scenarios + 30 controls; V3/V4 validators — 210 rows each; `validate_v5_suite.py` — 210 rows, 60 dev/150 test, SHA `e5f6b399…`. All passed with manifest hashes.
- Clean SQLite migration: `alembic upgrade head` and `alembic current` against a new temporary DB — `0002_turn_budgets (head)`.
- Current Docker check: `docker compose ps` could not connect to `dockerDesktopLinuxEngine`; current Compose readiness remains **NOT VERIFIED**.
- At the time of this Phase 13 snapshot, the first migration invocation used an incorrect relative Python path and did not execute; a corrected fresh-database migration then succeeded. No inference or held-out tuning was run in that phase. The later bounded local Ollama smoke is recorded in Phase 14; no V5 held-out inference/tuning was run.

### Bounded policy-response fix

- [x] Successful `get_return_policy` result now renders its authoritative `policy_text`, category, version and date in the grounded response path. This fixes a mismatch: the prior helper expected `return_window_days`, while the actual registered tool returns `policy_text`.
- [x] Regression verifies real FastAPI orchestration returns the seeded policy and makes one model call, without a second model synthesis call.
- [x] Frozen datasets, manifests, raw model outputs, hybrid test replays and historical reports were preserved; no model score was recomputed or changed.
- [ ] V5's source freeze is historical for `backend/app/main.py` after this post-freeze policy-response fix. V5 dataset and score artifacts remain hash-identical. Any future model inference must first create a new versioned source/config freeze and new output files.
- [x] Phase 13's V5 comparison status was **NOT RUN** at that historical point. One later paired comparison is now recorded in `experiments/results/p2_v5_dev_controller_candidate_comparison_v1.json`; exploratory gains were +45.00 pp row-weighted and +45.24 pp core-weighted, but it is not accepted because the AI-assisted overlay lacks separate independent human review and the candidate made two unexpected state-change proposals.
- [x] The user-specified minimum of 20 independently reviewed prompt cores across 10 families remains the rule. Although the overlay annotates 28 cores / 14 families, independently human-reviewed count is not established, so this comparison is inconclusive. No follow-up candidate iteration or V5 test tuning was done.
- [ ] Locked-test model/action/task quality remains failed. **Current Docker Compose readiness is verified** in the later Phase 14 entry above (API/database healthy, web HTTP 200, synthetic lookup complete); the earlier Docker-unverified line was a historical status.

### Final checklist state (supersedes earlier snapshot rows above)

- Engineering: core synthetic workflows, tests, docs, local real-model smoke and current Compose demo are functional and reproducible within the stated bounded checks; **not production-ready**.
- Original acceptance: **PARTIAL**. Current locked V5 raw/hybrid/clarification metrics remain 25/150, 31/150, and 6/43 respectively; broad 42-case V5 application execution, independent label review, and model-quality thresholds remain outstanding.
- The eight-case real Ollama smoke is V2-scoped integration evidence, not a V5 metric. The deterministic backend is only a test fixture.

## V4 controller improvement experiment — 2026-10-11

- [x] Verified code/evidence root causes: brittle intent precedence; direct-answer substitution for tools; item-ID tokens triggering lexical routing; ticket text accepted without request grounding; evaluator action-only credit when expected args are null; and 15 V5 prompt/gold order-ID disagreements.
- [x] Added the opt-in `hybrid-controller-v4-grounded-ticket-candidate`; the default controller version remains V2 and the deterministic CI backend remains default.
- [x] Added regressions for missing/conflicting IDs, policy/eligibility/estimate precedence, item-ID token handling, ticket issue grounding, generic ticket clarification, prompt injection and grounding.
- [x] Added separately versioned distinct-core synthetic evaluation sets, manifests, a paired evaluator, and real-model outputs. All added labels are explicitly AI-authored, not independent human review.
- [x] Exploratory V4 development replay: V2 11/28 (39.3%) → final V4 27/28 (96.4%); tool choice 17/18; exact arguments 15/16; unexpected writes 0; grounded ticket proposals 2/2. This is not independent acceptance evidence.
- [x] Final V4 holdout v3: raw Qwen 3/18 (16.7%), V2 replay 7/18 (38.9%), V4 replay 16/18 (88.9%); exact arguments 9/11 (81.8%); tool selection 10/12 (83.3%); correct clarifications 4/4; handoff 1/1; unexpected write proposals 0; grounded ticket proposals 1/1. Offline only; no tool execution.
- [x] Paired tool/argument metrics: development V2→V4 tool selection 6/18→17/18 and exact arguments 4/16→15/16; final holdout 4/12→10/12 and 3/11→9/11. These are controller replay metrics, not raw model improvements.
- [x] Final actual local Ollama/FastAPI V4 smoke passed 8/8 on synthetic data, including approval/idempotency and tenant-denial checks. This does not represent the 18-case holdout run end-to-end.
- [x] Final checks: backend `pytest` 65 passed; Ruff passed; frontend build passed; all V1–V5 suite validators passed; fresh SQLite migration reached `0002_turn_budgets (head)`.
- [ ] V4 acceptance target: **NOT MET**. Final holdout action score is 88.9%; labels are not independently adjudicated; the holdout is only 18 rows. Although final V4 development replay exceeded 90%, independent-label and broader task-completion evidence are missing.
- [ ] Original P2 acceptance: **PARTIAL**. Official V5 raw/hybrid scores remain 25/150 (16.7%) and 31/150 (20.7%); V5 clarification remains 6/43 (14.0%). Historical scores and labels were not changed.
- [ ] Next: independently review labels, improve remaining action/argument misses without retuning against final holdout v3, freeze a new distinct-core evaluation, and broaden actual FastAPI end-to-end execution. Keep V4 opt-in.

Detailed findings, metrics, hashes, commands and remaining gaps: [P2 V4 Controller Reliability Experiment](P2_CONTROLLER_V4_EXPERIMENT_REPORT.md).

## Final mission implementation update — 2026-10-11

- [x] Multi-step eligibility/estimate final responses use only successful, schema-shaped registered-tool results. Actual Ollama/FastAPI eligibility workflow was exercised; output identifies the item, returned eligibility/reason, and no model-generated final answer was used.
- [x] Tool-failure/malformed-result response path fails closed. Regression tests cover failed workflow evidence and missing required result fields.
- [x] ISO dates such as `2026-10-12` remain readable in traces; actual phone strings remain redacted.
- [x] Latest full backend suite: **68 passed** (one upstream Starlette/AnyIO deprecation); Ruff, frontend production build, all V1–V5 validators, isolated Playwright approval journey (1/1), fresh SQLite migration to `0002_turn_budgets (head)`, and current Compose process check passed.
- [x] New real local Ollama/FastAPI smoke: 9/9 bounded workflows with cached Qwen3-1.7B Q4_K_M and opt-in V4 controller, including both eligibility and refund-estimate multi-step paths. Evidence with raw outputs/traces/timings: `experiments/results/p2_final_mission_v4_integration_final_v2_20261011.json`. This is not a broad action benchmark or V5 app run.
- [ ] Fresh development/final evaluation with at least 60 distinct prompt cores and at least 12 families: **NOT CREATED/RUN** in this implementation pass. Existing 18-row final V4 set and V5 evidence do not satisfy this new target.
- [ ] Independent human label review and broad 42-case V5 application execution remain outstanding. Frozen V5 quality results remain unchanged: raw 25/150, hybrid offline replay 31/150, clarification 6/43. Overall original acceptance stays **PARTIAL**.

## Fresh60 and V5 42-case evaluation — 2026-10-11

- [x] Created and validated a separate 60-row evaluation with 60 distinct normalized prompt cores across 15 families; 0 exact and 0 high-similarity flags in comparison with 1,084 prompts from 9 JSONL/CSV corpora. Labels are internal, not independently human-reviewed. Dataset SHA-256: `cf813327e533e8eb8389a6ddfc5a12846e637abd69689d24c2e9802cd6ab3fa4`.
- [x] Froze V4 candidate/source/config, model digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`, generation settings, tool schema and evaluator before inference. V2 remains default; deterministic CI backend is unchanged.
- [x] One actual local Ollama action run completed 60/60: raw 16/60 exact (26.7%); V2 paired replay 31/60 (51.7%); V4 paired replay 42/60 (70.0%). Unique-core scores equal row scores. V4 improvements are +18.3 pp, but exact args 23/32 (71.9%) and tool choice 27/36 (75.0%) miss 90% targets; raw unexpected write proposals 2, V4 0.
- [x] Ran all 42 preselected V5 cases through FastAPI/Ollama with a fresh seeded synthetic SQLite DB. Actual-app checks: 26/42 pass, 16 fail; 32 model calls and 19 tool events. Detailed per-case answers, traces, timings and failure reasons are in `experiments/results/p2_v5_42_real_application_v1.json`.
- [x] Duplicate approval replay passed: same ticket ID returned on repeat, exactly one ticket row. Prompt-injection cases passed 3/3; two cross-tenant attempts returned not-found, while one safely avoided tool disclosure but failed the stricter required-denial trace check.
- [x] V5 selected cases contain 22 prompt cores (14 repeated: six x3, eight x2; eight singletons) and three prompt/label order-ID conflicts. Official V5 labels/results were not edited.
- [x] Regression checks: 68 backend tests passed; Ruff passed; frontend build passed; V1–V5 data validators passed; clean SQLite migration reached `0002_turn_budgets (head)`.
- [ ] Acceptance targets: unmet. V4 candidate is 70.0% exact action, 75.0% tool choice, and 71.9% exact arguments; real application checks passed 26/42. Policy, eligibility, refund estimate and multi-step workflows remain unreliable.
- [ ] Original P2 acceptance remains **PARTIAL**. Historical V5 scores remain 25/150 raw, 31/150 offline V2 replay and 6/43 clarifications; no held-out generalization claim is supported.

Full findings, per-family metrics, failed example IDs, hashes, timing and limitations: [Fresh60 and 42-case evaluation report](P2_FRESH60_AND_42CASE_EVALUATION_REPORT.md).

## Stage 1 workflow fixes — 2026-10-11

- [x] Guard unsupported ticket/refund completion and tracking-capability claims using action/trace state and the registered tool list.
- [x] Preserve successful eligibility facts when a later workflow step fails; explicitly distinguish an ineligible result from a refund estimate.
- [x] Add opt-in V8 handling for singular unidentified-item requests; ask for the missing item ID before estimate execution. V8 remains unpromoted.
- [x] Existing required tool slots remain schema-derived; approval, authorization and idempotency controls remain covered by the existing tests.
- [x] Backend regression suite: 82 passed, one upstream Starlette/AnyIO deprecation warning; Ruff passed on changed files.
- [x] Exposed-set paired diagnostic replay: V7 39/64; V8 41/64; +3.125 pp row/core; both have one unexpected write. This uses historical proposals and is not the planned fresh-set experiment or actual tool execution.
- [ ] Planned fresh-set controlled V7-versus-typed-router experiment: NOT COMPLETE. A new development dataset, overlap audit, freeze manifest, post-fix raw proposal pass, replay, and separate actual-app slice remain required.
- [ ] Overall P2 acceptance remains **PARTIAL**. This pass supplies no new model quality or end-to-end score and does not alter historical metrics.

Evidence and limits: [Stage 1 workflow fixes and routing experiment status](P2_STAGE1_AND_ROUTING_EXPERIMENT_REPORT.md).

## Fresh V7/V8 evaluation — 2026-10-11

- [x] Frozen a new 130-core, 13-family internal development set, overlap audit, scoring/application evaluators, V7/V8 and local model identity before inference. No overlaps found by the documented lexical check.
- [ ] Complete raw model inference: **BLOCKED**. A configured 30-second local inference timeout was exceeded in practice; one recorded call lasted about 52 minutes. Process stopped; no complete raw artifact and no score reported.
- [ ] Fresh paired V7/V8 replay, per-family/uncertainty metrics, and equivalent real FastAPI runs: **NOT RUN** because a complete raw proposal set is unavailable.
- [x] V7/V8 unchanged; V8 opt-in; no historical result changed.
- [ ] V8 improvement on unseen requests: **UNDETERMINED**. Overall P2 acceptance remains **PARTIAL**; original action/tool/argument gates are not newly met.

Evidence: [Fresh V7/V8 evaluation report](P2_FRESH_V7_V8_EVALUATION_REPORT.md), freeze manifest `experiments/results/p2_fresh_v7_v8_freeze.json`.


## Recovery completion addendum — 2026-10-11

| Requirement | Status | Evidence / remaining gap |
|---|---|---|
| V5–V7 bounded model/controller diagnostics | **COMPLETE (development diagnostics)** | Real local Ollama/FastAPI recovery runs recorded; no cloud/paid resources. New internal data is exposed and not independently human-reviewed. |
| V7 42-case application path | **PARTIAL** | 28/42 checks pass; 14 fail. Duplicate approval returns same ticket and one row. See `experiments/results/p2_recovery_v7_dev_application.json`. |
| Controller action score gate | **NOT MET / NOT ACCEPTANCE-ELIGIBLE** | Recovery V1 candidate 53/64, V2 candidate V6 37/64, V7 39/64; these are offline action replays on internal data. V6/V7 retain one unexpected write proposal. No fresh independent-label gate. |
| Official frozen V5 quality gate | **NOT MET** | Preserved raw 25/150, V2 replay 31/150, clarifications 6/43; no metric was substituted or updated. |
| Regression checks | **PASS for current local scope** | 79 backend tests passed (one upstream deprecation warning), Ruff passed, frontend build passed, V5 dataset validator passed. |
| Overall P2 acceptance | **PARTIAL** | Keep deterministic CI default and V2 controller default; no candidate promotion. Independent review, unseen broad evaluation, quality thresholds, and end-to-end target remain open. |

The detailed evidence and root-cause analysis are in `docs/P2_FINAL_RECOVERY_REPORT.md`, `docs/P2_LONGITUDINAL_ROOT_CAUSE_REPORT.md`, and `docs/P2_EXPERIMENTAL_RECOVERY_PLAN.md`. Reconstructed history is indexed with artifact hashes in `experiments/results/p2_trial_registry_v1.json`. Lack of Git commits/reflog prevents a complete repository-baseline diff.
