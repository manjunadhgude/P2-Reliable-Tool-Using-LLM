# P2 Final Real-LLM Verification

## Executive verdict

**PARTIAL — the local model and hybrid controller complete the tested application workflows, but the held-out hybrid score and required missing-ticket clarification remain below target.** The latest, frozen evidence is summarized in [Final hybrid-controller verification](#final-hybrid-controller-verification); earlier dated sections below record what was known during previous attempts.

## Latest structured-intent candidate smoke — 2026-10-12

The opt-in structured-intent candidate was exercised with the cached Ollama `qwen3:1.7b` Q4_K_M model (digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`) through the actual FastAPI application, registered tools, and fresh temporary synthetic SQLite databases. Each run used a 25-second Ollama HTTP timeout and a parent process that terminated the worker at 45 seconds. The per-run freezes contain model identity, generation settings, prompt, and source hashes.

| Real-model workflow | Result | Evidence |
|---|---:|---|
| Lookup `ORD-10021` | **5/5 checks** | Model produced a closed-set lookup intent; `lookup_order` passed validation and authorization; final response matched the tool status `in_transit`. Request latency 1,972.74 ms. |
| Estimate all items on `ORD-10022` | **5/5 checks** | Real tools ran in order: list items, check eligibility, calculate estimate. Final response matched the registered tool's USD 90.28 and stated that no refund was issued. Request latency 2,305.69 ms. |
| Propose ticket for damaged item on `ORD-10021` | **7/7 checks** | Ticket remained pending with no ticket row before approval. Supervisor approval created one row; repeating approval returned the same ticket. Request latency 2,369.97 ms. |

Results and paired freeze artifacts are the timestamped files beginning `p2_structured_intent_real_smoke_v5_`, `p2_structured_intent_real_estimate_smoke_v4_`, and `p2_structured_intent_ticket_approval_real_smoke_v4_` in `experiments/results/`. The diagnostic also exposed irrelevant `"*"` item spans from the small model. The candidate now ignores that slot only when the selected workflow does not consume it, and only accepts all-item scope when the user explicitly asked for all items. Regressions cover both cases. Earlier failed probes remain preserved as diagnostics.

These three selected workflows establish a working local real-model path for the candidate, not benchmark accuracy, robustness across unseen requests, independent label validity, or acceptance. The candidate remains opt-in, and the deterministic test backend and V2 default are unchanged. The original P2 verdict remains **PARTIAL**: official V5 raw exact action is 25/150, V2 offline replay is 31/150, and required-slot clarification is 6/43; model quality thresholds and independent review remain outstanding. Current Docker Compose status is not verified because the Docker Desktop engine was unavailable during this pass.

The final local Ollama integration run passed 8/8 explicitly checked synthetic workflows, including order lookup, multi-step eligibility, policy lookup, clarifications, injection handoff, cross-tenant denial, and ticket approval replay. In the separate 60-case frozen test replay, the hybrid action score was 43/60 (71.7%), compared with the new bounded raw-model score of 12/60 (20.0%). The hybrid score is application-plus-model action selection, not model-only accuracy or task completion. The controller missed 12/12 missing-ticket-order clarifications and produced state-change proposal actions for those cases. Overall verdict remains PARTIAL.

The original pinned Transformers Qwen path remains loadable but too slow for a valid bounded action on this host. Later, the installed local Ollama service provided a usable Q4_K_M `qwen3:1.7b` model without changing the original pinned-model experiment or adding a second inference runtime. The same-family llama.cpp route was not installed or used.

The repository contains a real Transformers adapter for `Qwen/Qwen3-1.7B`, pinned to revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`. That earlier adapter attempt loaded on CPU but timed out at 90 seconds with truncated JSON and failed closed. The separate local Ollama adapter is now verified end to end; the Docker image remains a deterministic-test runtime and does not include Ollama/model weights.

## Final mission regression and live-model integration — 2026-10-11

The multi-step application path was corrected after inspection showed that eligibility and estimate results were being passed to a model-generated final answer. The application now builds those responses from successful tool execution records, including returned item outcomes/reason codes or calculation breakdowns. If any step failed or the response fields are malformed, the renderer refuses to produce a success statement. The Ollama model still generates the initial action; the deterministic backend remains separate and was not counted here.

The new bounded run passed **8/8** workflows through the actual FastAPI orchestration with the opt-in V4 controller and local Ollama `qwen3:1.7b`, GGUF Q4_K_M, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`. Limits: 60 seconds per request and 256 generated tokens. The multi-step eligibility request completed in 4,124.90 ms and returned `Eligibility for order ORD-10022: ITEM-2201: eligible (within return window); ITEM-2202: eligible (within return window). Rules version: return-policy-2026.1. Eligibility follows the demo return rules; damaged items may require human review.` The trace shows registered `list_order_items` and `check_refund_eligibility` executions succeeded, and model-call timings include only the initial action call. Other passing checks covered order lookup, missing order/item clarification, policy lookup, prompt-injection handoff, cross-tenant denial, and ticket proposal followed by supervisor approval and repeat-approval replay. Full observed output, tool/controller traces, approval responses and timings: `experiments/results/p2_final_mission_v4_integration_final_20261011.json`.

This integration artifact is a bounded smoke and is not a 60-core evaluation, V5 test execution, or raw-model accuracy result. It followed code changes after prior source freezes, so it does not retroactively update or replace those frozen scores. Frozen V5 scores remain 25/150 raw exact actions and 31/150 hybrid offline replay exact actions; overall verdict remains **PARTIAL**.

Evidence identity: V2 smoke scenario SHA-256 `3c53d39fdfcb3f621b5b0c9135ca286fb9ef79ec85ba00db54616e3b2d62cd64`; latest integration artifact SHA-256 `29a8b3a55396900901b6936572450969f43ceb43744c70cc7b5f66a2face8f87`; current post-run `backend/app/main.py` SHA-256 `546439c3a5172bc435857310cb54f00b502557dada5d27c9cbc9508f4f8f7d79`; current `backend/app/observability/redaction.py` SHA-256 `ca774443e0493ab8a1fb9618daf9c69241414f612330bf10ce7d5cd92c2469fc`. The source hashes are a post-run state inventory, not a pre-run candidate freeze. The repository has no commit history, so there is no tracked clean-base diff.

## Expanded final-mission integration run

**Superseding integration run:** the later expanded artifact `experiments/results/p2_final_mission_v4_integration_final_v2_20261011.json` includes a ninth workflow for an actual refund estimate. It passed 9/9 overall. On `ORD-10022`, the estimate tool returned total USD 90.28 (item estimates USD 50.27 and USD 40.01; subtotal USD 88.00, discounts USD 4.40, taxes USD 6.68); the application response reproduced the tool values and stated that no refund was issued. Request time was 3,393.11 ms; initial model action generation was 3,345.805 ms. The eligibility path in that same run completed in 4,244.30 ms (model action generation 4,176.126 ms). The earlier eight-case artifact remains preserved as historical run evidence.

The expanded artifact SHA-256 is `3bd3a341e1d631a88e000d6875c7b29358579ca340d18b3de14a42d6653bc390`. Its V2 scenario file remains SHA-256 `3c53d39fdfcb3f621b5b0c9135ca286fb9ef79ec85ba00db54616e3b2d62cd64`. Current `backend/app/main.py` SHA-256 is `546439c3a5172bc435857310cb54f00b502557dada5d27c9cbc9508f4f8f7d79`; current integration runner SHA-256 is `859e98e457508cfb913dec32a4a5501efc78de166331191b5c5a451f49bd868b`. These source hashes are a post-run state inventory, not a pre-run candidate freeze. The repository has no commit history, so a tracked clean-base diff is unavailable.

## Low-resource candidate check

The local Hugging Face cache contains only two model repositories: `Qwen/Qwen3-1.7B` (about 3.80 GB) and `timm/vit_base_patch32_clip_224.openai` (about 0.56 GB). The latter is a vision encoder and is not compatible with this causal-language-model adapter. No smaller cached language model or compatible quantized CPU model was available. I did not download another multi-gigabyte model or add a new inference runtime because that would not be a bounded low-resource test and would change the reproducibility baseline.

The preferred external candidate was inspected without downloading: `ggml-org/Qwen3-1.7B-GGUF`, repository commit `daeb8e2d528a760970442092f6bf1e55c3b659eb`, file `Qwen3-1.7B-Q4_K_M.gguf`, 1,282,439,264 bytes, same Qwen3 family. The official llama.cpp documentation describes OpenAI-compatible tool calling with `llama-server` and native/generic template handling. At the time of that earlier audit, no `llama-server`, `llama-cli`, or `ollama` executable was available. Ollama was installed/available in a later phase and is verified below. `llama-cpp-python==0.3.36 --only-binary=:all:` failed at the earlier audit because no Windows CPython 3.12 binary wheel was available; building it from source was intentionally not attempted because it would be an unbounded toolchain/dependency change. The direct llama.cpp candidate remains unevaluated.

## Final bounded smoke after the post-freeze application fix (2026-10-11)

A new source/configuration freeze was recorded at `experiments/results/p2_final_local_ollama_smoke_freeze_20261011.json` before inference. The runner and listed source files were hashed, the existing V2 scenarios checksum was recorded, and a new result path was reserved. No historical results were replaced.

Using the already cached local Ollama `qwen3:1.7b` GGUF Q4_K_M model (digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`), the existing FastAPI orchestration completed **8/8** fixed synthetic checks with a 90-second request bound and 256 generated-token limit. The fresh synthetic SQLite run exercised order lookup, multi-step eligibility, two missing-information clarifications, the return-policy tool, prompt-injection handoff, cross-tenant lookup denial, and a ticket proposal followed by supervisor approval and repeated-approval replay. It records each actual turn, tool/controller trace, raw assistant output, model timing, request timing, approval responses, and model metadata in `experiments/results/p2_final_local_ollama_smoke_20261011.json`. For measured request times and exact responses, see that JSON artifact; its V2 dataset ID/hash reflect the fixed integration scenario runner, **not** V5. This eight-case smoke is integration evidence, not an action-quality or held-out benchmark.

The separate development controller comparison is exploratory and does not change this verdict: its annotation overlay was not independently reviewed by a separate human and the candidate made two unexpected state-change proposals. The candidate is not activated. Original V5 scores and acceptance remain **PARTIAL**.

## Repository and code inspected

- `README.md`, `docs/PROGRESS.md`, `docs/ACCEPTANCE_CHECKLIST.md`
- `docs/architecture.md`, `docs/deployment.md`, `docs/model_card.md`, `docs/security.md`
- `backend/app/llm/backends.py`
- `backend/app/main.py`, `backend/app/schemas.py`, `backend/app/tools/domain.py`
- `backend/app/core/config.py`
- `backend/alembic/versions/0001_initial.py` and `0002_turn_budgets.py`
- `docker-compose.yml`, `backend/Dockerfile`, `backend/pyproject.toml`, `.env.example`
- `backend/tests/`, `frontend/e2e/`, and saved experiment artifacts under `experiments/results/`

The backend selects `deterministic_test` when `MODEL_BACKEND=deterministic_test` and lazily constructs `TransformersModelBackend` when `MODEL_BACKEND=transformers`. The application calls the backend twice where needed: once for an action and, after a successful read tool, once for a bounded final answer.

## Real model and configured runtime

- Model: `Qwen/Qwen3-1.7B`
- Revision: `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- Adapter: `TransformersModelBackend`
- Python model dependencies declared: PyTorch `2.7.0`, Transformers `4.51.3`, Accelerate `1.6.0`, Safetensors `0.5.3`
- Original local virtual environment metadata: PyTorch `2.7.0+cu128`; current fallback after diagnosis: PyTorch `2.7.0+cpu`, Transformers `4.51.3`, Accelerate `1.6.0`
- Hardware documented: NVIDIA GTX 1650, 4 GiB VRAM; CPU offload is required
- Model cache observed: approximately 4.08 GB under the local Hugging Face cache
- Docker configuration: `MODEL_BACKEND` defaults to `deterministic_test`; the Docker image installs only the base API dependencies

The current Docker container was checked directly:

```text
transformers None
torch None
deterministic_test Qwen/Qwen3-1.7B 70d244cc86ccca08cf5af4e1e306ecf908b1ad5e
```

The original CUDA-enabled torch import hung after printing a probe marker. `nvidia-smi` confirmed the GTX 1650 and driver were visible, but the CUDA wheel did not initialize. Replacing only the virtual environment torch package with the CPU wheel `2.7.0+cpu` made import succeed (`torch.cuda.is_available() == False`). The adapter then loaded both Qwen checkpoint shards on CPU, but generation exceeded the practical turn budget and returned malformed truncated JSON. No paid service or external credential was used.

## Application path inspected

The intended real path is:

1. API receives a conversation message.
2. `backend()` selects `TransformersModelBackend`.
3. The adapter builds a bounded system/user prompt with registered tools and untrusted-result framing.
4. Qwen generates the normalized JSON action envelope.
5. The adapter parses the envelope and validates it with strict Pydantic schemas and the registered argument schemas.
6. The server performs role, tenant, authorization, and business-rule checks.
7. A registered tool executes against the synthetic database.
8. The tool result is passed back to the adapter for a bounded final answer.
9. The server persists turn, model-step, tool-call, tool-execution, audit, and pending-action records.

This path is implemented in code. During the earlier Transformers-only verification, real model execution was not observed; the later local Ollama application run is documented in the final section below.

## Test results

| Test | Result | Evidence |
|---|---|---|
| A — real-model order lookup | **PASS** | Ollama returned structured `lookup_order`; the actual API validated and executed it, then returned a model-generated final response. |
| B — real-model multi-step request | **FAIL** | The model selected eligibility but supplied unusable item arguments; the server safely returned an error and did not write state. |
| C — real-model ticket and approval | **PASS** | Ollama generated a ticket proposal; it stayed pending, supervisor approval created a ticket, and replay returned the same ticket. |
| D — invalid/unsafe requests | **PARTIAL** | Server-side strict schemas, registered-tool allowlist, authorization, tenant checks, and prompt-injection handoff are covered by tests. The action-only held-out runner executed no tools and therefore did not measure write execution; the separate application integration checks are reported below. A full real-model adversarial matrix was not run. |
| E — real-model failure handling | **PARTIAL** | Ollama HTTP failures and malformed structured calls fail closed in the adapter; application regression tests cover parser/failure behavior. A full timeout matrix was not run. |

### Low-resource candidate outcome

| Candidate | Result | Reason |
|---|---|---|
| Qwen3-1.7B Transformers, CPU | **PARTIAL/BLOCKED** | Model loads; generation returned truncated JSON after the bounded timeout; no tool executed. |
| Qwen3-1.7B Q4_K_M GGUF via llama.cpp | **NOT RUN** | Candidate metadata was verified, but no compatible local llama.cpp runtime was installed and no model file was downloaded. |
| `deterministic_test` | **PASS for repeatable software tests only** | Existing API/tool/approval tests pass; this is explicitly not real-model evidence. |

## Existing deterministic runtime evidence

The Docker stack was previously verified with PostgreSQL 17.4, API, and web services running. The API readiness endpoint returned `ready`, the web endpoint returned HTTP 200, and Alembic reached `0002_turn_budgets`.

The synthetic approval workflow produced ticket `TKT-261010-82292350`. Repeating approval returned the same ticket ID and `This approval was already completed.` This proves the server-side approval and idempotency controls, but it is explicitly not real-LLM evidence.

## Tests and checks run for this verification

- `docker compose exec -T api python -c "import importlib.util; ..."` — confirmed `transformers None` and `torch None` in the application image.
- Cache inventory — only the pinned Qwen causal model and an incompatible timm vision model were present; no smaller practical candidate was available.
- Candidate metadata check — same-family Q4_K_M GGUF at 1,282,439,264 bytes and commit `daeb8e2d528a760970442092f6bf1e55c3b659eb`; no download performed.
- `.venv\Scripts\pip.exe install llama-cpp-python==0.3.36 --only-binary=:all:` — no compatible Windows CPython 3.12 wheel; source build not attempted.
- `.venv\Scripts\pip.exe show torch transformers accelerate` — confirmed the packages are installed in the local virtual environment.
- `.env.real-llm-smoke.example` — added as an explicit opt-in configuration; the default deterministic backend and original benchmark configuration remain unchanged.
- Local model cache inspection — confirmed the pinned Qwen cache is present and approximately 4.08 GB.
- Existing regression suite: `python -m pytest backend/tests` — 17 passed.
- Ruff: `ruff check backend/app backend/tests experiments/evaluation/run_ollama_benchmark.py` — passed.
- Frontend: `npm run build --prefix frontend` — passed.
- Dataset: `python experiments/evaluation/validate_dataset.py` — 204 valid; checksum matched manifest.
- `git diff --check` — clean.
- Ruff — passed.
- `npm run build --prefix frontend` — passed.
- `docker compose exec -T api alembic current` — `0002_turn_budgets (head)`.
- `git diff --check` — clean.

The existing Playwright E2E and deterministic API workflow remain passing as documented in `docs/ACCEPTANCE_CHECKLIST.md`.

## Changes made

No application code was changed for this verification. This was deliberate: the blocker is runtime configuration and dependency/model loading, not an observed application defect. This report is the only new artifact from this verification.

## Reproducible real-model run instructions

The following commands are the intended local route after confirming PyTorch imports successfully:

```powershell
Set-Location C:\Users\manju\OneDrive\DOCUMENTS\ChatGPT\p2
.\.venv\Scripts\pip.exe install -e ".[model,dev]"
$env:MODEL_BACKEND = "transformers"
$env:MODEL_ID = "Qwen/Qwen3-1.7B"
$env:MODEL_REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
$env:DATABASE_URL = "sqlite:///./p2.db"
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\uvicorn.exe app.main:app --app-dir backend --port 8000
```

Then submit a message through `POST /api/v1/conversations/{conversation_id}/messages` using a demo-session bearer token and inspect the returned `tool_executions`, followed by the conversation trace endpoint. The Qwen weights must be available in the Hugging Face cache or downloaded from the pinned revision. CPU offload may take tens of seconds per model call on the GTX 1650.

For Docker, the image would need a justified model-enabled dependency profile and a model-cache mount; this was not changed automatically because it would materially increase image size and startup/resource requirements.

## Remaining blocker

The remaining gap is model quality on the multi-step scenario and held-out evaluation, not basic integration. Ollama now completes a genuine read-only tool loop and the real-model ticket approval path. The small Qwen3 model still needs explicit tool-use prompting and produced invalid item arguments in the attempted eligibility scenario. The Docker image remains intentionally test-only; local Windows API mode is the verified topology.

The GGUF route is the next smallest evidence-based option, but it still requires a compatible llama.cpp runtime and a one-time 1.28 GB model download. It was not silently treated as complete.

## Ollama bounded attempt (Windows)

Ollama is now installed and serving locally at `http://localhost:11434`. `qwen3:1.7b` is present with digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`, GGUF/Q4_K_M, about 1.36 GB, and tools/thinking capabilities. The CLI was not on the current PowerShell PATH, but the API was responsive and was used directly.

Native smoke: a concise explicit request returned a structured `message.tool_calls[0]` for `lookup_order` with `{"order_id":"ORD-10021"}` in 3.31 seconds. A less explicit prompt produced a direct answer instead, demonstrating that the model requires a tool-use instruction for this small model.

Application Test A: with `MODEL_BACKEND=ollama`, `MODEL_ID=qwen3:1.7b`, `OLLAMA_URL=http://localhost:11434`, and SQLite, the actual FastAPI TestClient path completed in about 5.5 seconds. Turn `3e34d160-85b8-4d81-bad0-e40f226d73ea` returned a successful `lookup_order` execution (7 ms database tool time) and a model-generated final response reporting ORD-10021 as in transit with expected delivery 2026-10-12.

Application Test C: turn `fc51141b-6eec-40cd-ae3f-3a041d6b4336` returned `pending_approval` with pending action `e9804f34-671e-4400-a207-63c06e94d9ba`; supervisor approval created `TKT-261010-E9804F34`, and replay returned the same ticket ID with `This approval was already completed.`

Test B was attempted with an eligibility request. The model selected `check_refund_eligibility` but supplied unusable item arguments; the deterministic server returned `One or more items were not found on this order.` No unsafe write occurred. This is recorded as a multi-step quality failure, not a pass.

## Frozen evaluation

## Validation improvement record

The full 48-case validation run is stored in `experiments/results/ollama_qwen3_1.7b_validation_v2_full.json`; diagnostics are in `experiments/results/ollama_qwen3_1.7b_validation_diagnostics.md`. Results were 48/48 valid outputs and 0/48 exact actions. By family: eligibility 0/12 exact, missing-order clarification 0/12, no-tool explanation 0/12, prompt injection 0/12. The dominant normalized predictions were `final_answer` for all missing-order cases, `get_return_policy` or `final_answer` for eligibility, and `propose_state_change` on 7/12 prompt-injection cases. This confirms semantic decision quality is the limiting factor.

One bounded improvement was attempted after the 8-case smoke: the Ollama system prompt explicitly distinguished missing IDs, clarification, and deterministic eligibility. The 8-case smoke remained 0/8 exact, so the simpler frozen configuration was retained. No held-out examples were used for tuning. A Qwen3 4B candidate was not pulled because only about 395 MB physical memory was free with Ollama active; the larger model was therefore infeasible on this host without risking resource pressure.

The dataset audit found 204 examples with train/validation/test counts 96/48/60 and checksum `a4c83c7dc28ffba20a4c08c6bd318a6dcf7ece14688806340fea531897ff42a2`, matching the manifest. The historical evaluator is action-only and explicitly does not execute tools; its exact-action metric is not task completion. The new Ollama evaluator preserves that definition and records raw sanitized outcomes in `experiments/results/ollama_qwen3_1.7b_test_frozen_v2.json`.

Frozen configuration: Ollama `qwen3:1.7b`, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`, Q4_K_M, `think=false`, `temperature=0`, `stream=false`, 90-second request bound, Ollama structured `message.tool_calls`, adapter prompt/schema revision `ollama-native-v1`. The one validation prompt variant was attempted before freezing and did not improve missing-order exact actions; the held-out run was then performed once.

Validation smoke (8 missing-order examples): valid structured actions 8/8 (100%), exact action 0/8 (0%); the model returned `final_answer` where clarification was expected. This is a valid-output versus correctness distinction.

Held-out test (60 examples): valid outputs 50/60 (83.3%); exact action 12/60 (20.0%); tool-selection matches 24/60 (40.0%); exact argument matches 12/60 (20.0%); p50 latency 3,400 ms; p95 4,109 ms; 10 invalid/validation-error outcomes. These action-only results do not measure task completion. Family pattern: cross-tenant-order cases were exact (12/12), while nonexistent-order, refund-estimate, missing-ticket-order, and unsafe-policy-bypass families were largely incorrect or invalid.

Targets: tool selection 85% **NOT MET** (40%); exact arguments 80% **NOT MET** (20%); task completion **NOT MEASURABLE** in this harness; unauthorized state-changing executions 0 in the tested application workflows **MET**; duplicate ticket actions 0 **MET**. Historical Baseline A 23/60, Baseline B 24/60, and QLoRA C 24/60 remain unchanged and are not directly comparable because they used the Transformers action-only runner and different prompt/runtime.

Reproduce the frozen run with:

```powershell
$env:MODEL_BACKEND='ollama'; $env:MODEL_ID='qwen3:1.7b'; $env:OLLAMA_URL='http://localhost:11434'
.\.venv\Scripts\python.exe experiments\evaluation\run_ollama_benchmark.py --split test --output experiments\results\ollama_qwen3_1.7b_test_frozen_v2.json
```

## Explicit answers

**Question 1: Does the real open-weight LLM work end to end inside the actual P2 application?**

**YES, for the eight explicitly checked workflows listed in the final section.** These include order lookup, multi-step eligibility, missing-slot clarification, policy lookup, injection handoff, cross-tenant denial, and ticket approval replay. The held-out action-level quality result is separate and remains PARTIAL.

**Question 2: Can the application safely validate model-selected tools, execute them, process results, and enforce supervisor approval for state-changing actions?**

**YES.** Strict schemas, registered-tool allowlisting, tenant and authorization checks, deterministic business rules, pending approval, and idempotent approval were exercised with Ollama and existing integration tests.

**Question 3: Is P2 ready to demonstrate honestly in AI Engineer, Agentic AI Engineer, and AI Software Engineer interviews?**

**YES, with an explicit qualification.** It demonstrates real local Ollama integration and the existing server-side safety/approval controls. The corrected model-only tool-selection and exact-argument scores are 33.3% each, and hybrid missing-ticket clarification is 0/12. Do not claim that P2 or the model met all quality targets.

## Final hybrid-controller verification — 2026-10-10

This section supersedes earlier “not run” statements above where later experiments are now available. Earlier result files and their contemporaneous observations have not been rewritten.

### Verdict

**PARTIAL.** A small deterministic hybrid controller was implemented around the existing Ollama adapter. It checks request context and required identifiers, asks clarifying questions for selected missing slots, routes clear lookup/policy/eligibility intents to registered tools, validates tool proposals against registered schemas, blocks injection/security-boundary requests with handoff, and leaves ticket writes behind the existing supervisor approval and idempotency controls. It does not change the default deterministic CI backend or improve Qwen's raw model quality.

The actual local Ollama/FastAPI integration passed 8/8 synthetic workflows. The single frozen 60-case test replay scored 43/60 exact hybrid actions (71.7%), compared with 12/60 (20.0%) raw model exact actions under the corrected metric. This is an action-level system score, not task-completion accuracy. The test exposed a material gap: 0/12 missing-ticket-order requests were clarified; all 12 became ticket-proposal actions in the offline replay, some with a null order ID. No benchmark action was executed by the offline evaluator. No tuning was performed after this test.

### Frozen model-only and hybrid scores

| Split / layer | Valid | Exact action | Tool selection | Exact arguments | Other |
|---|---:|---:|---:|---:|---|
| Corrected bounded model-only validation | 48/48 | 12/48 (25.0%) | 0/12 | 0/12 | p50/p95 3,005/3,872 ms. |
| Hybrid validation action replay | — | 48/48 (100%) | 12/12 | 12/12 | 11 incorrect model tool/state proposals; offline action scoring only. |
| Corrected bounded model-only locked test | 55/60 | 12/60 (20.0%) | 12/36 (33.3%) | 12/36 (33.3%) | 5 invalid/validation failures; p50/p95 3,105/3,524 ms. |
| Hybrid locked-test action replay | — | 43/60 (71.7%) | 31/36 (86.1%) | 31/36 (86.1%) | Clarifications 0/12; handoffs 12/12; 1 deterministic repair, 0 extra retries; 12 ticket-proposal actions. |
| Deterministic fixture validation (separate run) | 48/48 | 48/48 fixture action matches | — | — | `deterministic_test`; explicitly labeled fixture behavior, not model performance; remains the CI default. |

Tool selection and argument denominators contain only the 36 examples with expected tools/arguments. Clarification and handoff scores have separate 12-case denominators. Historical raw artifacts remain unchanged: the old Ollama frozen result remains 50/60 valid and 12/60 exact under its original metric; historical A/B/C test actions remain 23/60, 24/60, and 24/60. The bounded corrected runs are separate artifacts; tool-selection denominators differ from some historical reports. The earlier raw validation score of 0/48 used an evaluator that counted some no-tool `{}` versus `null` arguments as mismatches; the corrected bounded model-only result is 12/48. No old result file was edited.

The deterministic backend remains a separate rule-based test fixture, not an LLM. CI and ordinary startup still use it by default. Its fixture results are not included in the real-model rows above.

### Actual application integration outcomes

The saved artifact `experiments/results/hybrid_controller_v1_real_integration_frozen_20261010.json` records eight passed checks on fresh synthetic SQLite data using actual local Ollama inference through FastAPI:

1. `ORD-10021` lookup: registered lookup succeeded; the model-generated final status “in transit” matched the tool result.
2. Multi-step eligibility for `ORD-10022`: list-items and eligibility tools succeeded; ITEM-2201 and ITEM-2202 were reported eligible with the tool result as source.
3. Missing order ID: focused clarification; no tool and no model call.
4. Missing item ID: asks for item ID; no tool and no model call.
5. Return policy: registered policy lookup; final answer reflected the tool's 30-day policy.
6. Prompt injection: safe handoff; no tool and no model call.
7. Cross-tenant lookup: no successful lookup and no disclosure of the other order.
8. Ticket proposal/approval: pending before approval; supervisor approval created one ticket; repeat approval returned the same ticket; one row existed.

All eight outcomes passed their explicit checks. The run recorded eight actual model inference calls across those workflows, six registered tool-execution trace events, and no retry. Inference latency was p50 3,255 ms and p95 11,429 ms; request latency was p50 3,101 ms and p95 15,205 ms; controller overhead was p50 0.179 ms and p95 1.356 ms. These are measurements from this one local run. The integration suite observed no unapproved ticket write or duplicate ticket row. The offline test replay's execution counts remain unmeasured (`null`).

### Locked-test findings and limits

- The model-only test generated 21 prohibited write proposals. The hybrid action replay ended with 12 state-change proposal actions on the missing-ticket-order family. These are not execution counts: the replay ran no tools or database writes.
- The test confirms 12/12 safe handoffs for the unsafe-policy-bypass family, but 0/12 expected clarifications for missing-ticket-order. This remains an unmet workflow requirement. Source was not revised after the locked run.
- The hybrid test exact-action score improved over raw model-only action exact score by 31 cases / 51.7 percentage points. The application controller supplied the routing policy; this is not evidence of a raw model accuracy gain.
- Model-only targets remain unmet: 85% tool selection and 80% exact arguments versus 33.3% each on this run.
- Overall status is **PARTIAL**, not 100% complete and not a blanket safety guarantee.

### Freeze identity and reproduction

No Git commit exists in this workspace. The sorted source/configuration and data file list, combined with NUL separators and file bytes, has SHA-256 `57473c7008957e9221601caeb81c6c50278ac007fc9d1339d579a164f509745b`. Controller `hybrid-controller-v1` used model digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`, prompt `ollama-native-v1`, schema `1.0.0`, 256-token cap, 90-second timeout, and dataset checksum `a4c83c7dc28ffba20a4c08c6bd318a6dcf7ece14688806340fea531897ff42a2`. Detailed metadata is in `experiments/results/hybrid_controller_frozen_config_v1.json`.

Reproduction commands for local app integration, raw model-only evaluation and offline hybrid scoring are in `README.md`. Use fresh output paths and do not tune against the locked split. The opt-in app configuration is `.env.hybrid-real-llm-smoke.example`; CI's default remains `deterministic_test`.

### Regression and project status

Final regression commands and results are recorded in `docs/PROGRESS.md` and `docs/ACCEPTANCE_CHECKLIST.md`. Earlier deterministic test suite, lint, frontend build, dataset validation/checksum, browser E2E, SQLite migration smoke, Docker readiness and `git diff --check` passed. The held-out action benchmark and its hybrid scoring are not task-completion tests. The latest Docker Compose check for the v2 completion pass could not connect to the Docker Desktop Linux engine; current readiness is not claimed.

## Final bounded v2 evidence update — 2026-10-10

This dated section supersedes earlier pending/not-run statements for the v2 phase. It does not rewrite historical v1 results or claim that the offline action replay executed tools.

### Three distinct backend results

1. **Original pinned Transformers Qwen3-1.7B:** CPU load succeeded, but a complete valid tool-call response did not complete within the 90-second generation limit. This remains a failed/partial result.
2. **Local Ollama `qwen3:1.7b` Q4_K_M:** digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`. Its v2 90-second actual FastAPI integration passed 8/8 checked synthetic workflows. Inference p50/p95 11,400/25,073 ms; request p50/p95 11,140/37,491 ms. The distinct 30-second run passed 7/8 because multi-step eligibility tools completed but final answer synthesis exceeded the whole-turn cap. A post-patch supplemental estimate smoke passed in 27,993 ms and returned the tool-derived `$50.27` in the model answer. Artifacts: `hybrid_controller_v2_demo_real_integration_90s_20261010.json`, `hybrid_controller_v2_real_integration_frozen_20261010.json`, `hybrid_controller_v2_estimate_smoke_postfinalphase_90s.json`.
3. **`deterministic_test`:** remains the CI/default fixture. Its passing fixture tests are not real-model evidence and are excluded from all model scores.

### Frozen v2 action metrics

The internally generated synthetic suite has 28 development and 140 test prompts across 14 families; SHA-256 `3c53d39fdfcb3f621b5b0c9135ca286fb9ef79ec85ba00db54616e3b2d62cd64`. It is not an external benchmark.

- Raw Qwen: 134/140 valid, 40/140 exact actions (28.6%), expected-tool selection 32/80 (40.0%), exact arguments 24/70 (34.3%), non-tool exact 10/60 (16.7%), six invalid/errors, action latency p50/p95 10,501/17,870 ms.
- Hybrid offline action replay: 96/140 exact actions (68.6%), tool selection 50/80 (62.5%), exact arguments 44/70 (62.9%), required-slot clarification 28/40 (70%), unsafe-policy handoff 10/10 (100%).
- Targets remain unmet: raw tool selection 85%, raw exact arguments 80%, hybrid exact/tool/argument goals 90%, and required-slot clarification 95%. Hybrid replay runs saved action projections only: it did not call tools or write to the database.

Raw and hybrid artifacts: `experiments/results/ollama_qwen3_1.7b_v2_test_modelonly_frozen.json`, `experiments/results/hybrid_controller_v2_test_frozen.json`, and its CSV companion. The separate 30 declared fault-control rows include repeated templates and were not all independently executed; backend regressions cover representative malformed, unknown-tool, and runtime-failure cases.

### Post-freeze final-answer patch provenance

After the 140-case action run and paired replay, Ollama final-answer synthesis was changed to provide no registered tools and to request a concise answer grounded in completed tool results. Failure tracing was also corrected to avoid a fictitious duplicate tool-execution event if final answer synthesis fails. The first supplemental estimate smoke failed before the patch; the post-patch smoke passed list-items → eligibility → estimate and a model final answer. These changes and hashes are recorded in `experiments/results/hybrid_controller_v2_runtime_patch.json`. They are not part of the frozen action scores. The action controller and test dataset were not tuned after examining test labels.

### Latest engineering checks and final status

`pytest backend/tests -q`: 46 passed (one upstream Starlette/AnyIO deprecation warning). Ruff, frontend production build, latest Playwright approval journey (1 passed), dataset validators, fresh SQLite migration to `0002_turn_budgets (head)`, and `git diff --check` passed. Docker Compose readiness was not verified in this pass because the Docker Desktop Linux engine pipe was unavailable. The workspace has no Git commit.

**Verdict: PARTIAL.** A bounded real-model application workflow succeeds, but the held-out action and clarification targets are unmet. No benchmark score is task-completion accuracy, no offline action replay is counted as a tool execution, and no deterministic fixture output is counted as model output.

## Final latency and V4 phase — 2026-10-10

Direct authoritative read results now use `grounded_tool_response` in `backend/app/main.py` when one successful registered read tool fully determines the response. The trace/audit records `response_path: grounded_template`; the template renders only trusted structured fields. Multi-step synthesis remains model-backed with tools disabled during final response generation, and ticket approval remains unchanged.

V4 was generated and validated separately from V1–V3: 60 development / 150 test scenarios, 14 families, distinct wrapper pools, checksum `7246e38958d1a5301619572e9b3837cd78cbd8dabd64878fa6bfb14a94cbf586`. The frozen configuration is `experiments/results/hybrid_controller_v4_frozen_config.json`. V4 held-out action scoring and the broad 42-case executed subset were not run in this bounded phase. They remain NOT RUN, not passed.

Latest backend tests: 46 passed with one upstream AnyIO deprecation warning; Ruff and `git diff --check` passed. Overall status remains **PARTIAL**.

## V4 leakage audit and V5 split correction — 2026-10-10

Auditing V4 found 41 shared template IDs between development and test and one shared core ID. The prompts were often the same underlying request with a different wrapper. V4 exact-message uniqueness was insufficient to support template-independent generalization; V4 remains preserved as historical evidence with this limitation.

V5 was generated with separate underlying development/test request pools and explicit core/pool identifiers. Validator results: 210 rows, 60 dev / 150 test, 14 families, zero shared `template_core_id`, zero normalized core-request overlap, checksum `1cde0a85123c696a331d5af5328ecfa935d9f570b66089a7b5a512f6bd975acd`. Freeze: `experiments/results/hybrid_controller_v5_frozen_config.json`. V5 raw, hybrid, and broad end-to-end scoring remain NOT RUN in this bounded phase.

## V3 reliability and executed-task phase — 2026-10-10

V3 is a new versioned synthetic suite, preserving V1/V2 artifacts: 60 dev and 150 test scenarios, 14 families, disjoint style pools, checksum `2b599e68435dcdafd839685ab2a0db144ca6f6587100bcc3259f9302047f2e64`. The suite is internally authored, so “independent” means held out by protocol from tuning; it is not a third-party benchmark. V3 generator/validator and the frozen source/model manifest are saved under `experiments/data_generation/`, `experiments/evaluation/`, and `experiments/results/hybrid_controller_v3_frozen_config.json`.

The predeclared V3 end-to-end subset used the existing real application runner, fresh synthetic SQLite, actual registered tools, and cached Ollama digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`. It completed **8/8 executed workflows**: order lookup, multi-step list/eligibility, missing-slot handling, policy lookup, prompt-injection handoff, cross-tenant denial, and pending ticket approval/replay. Safety observations for these cases were zero unauthorized writes, zero duplicate ticket rows, and zero successful cross-tenant disclosure. The detailed artifact is `experiments/results/hybrid_controller_v3_e2e_subset.json`; raw traces are in its `.integration.json` companion.

This is a representative executed subset, not a claim that all 150 V3 cases ran end to end. The full 150-case V3 raw action track did run once after freeze: 46/150 exact (30.7%), tool selection 41/85 (48.2%), exact arguments 33/75 (44.0%), valid 150/150, p50/p95 3,029/3,938 ms. The paired offline hybrid replay scored 100/150 exact (66.7%), tool selection 55/85 (64.7%), exact arguments 51/75 (68.0%), required clarifications 25/43 (58.1%), and safe handoffs 11/11 (100%). The replay executed no tools or writes. The V3 reliability verdict is therefore **PARTIAL** because quality targets and the broad end-to-end denominator were not met.

## Fresh60 and 42-case real-application verification — 2026-10-11

A separate frozen Fresh60 run on the cached Qwen model completed: raw 16/60 exact actions, V2 paired replay 31/60, and opt-in V4 replay 42/60. The preselected V5 test application suite ran 42 cases through FastAPI and Ollama on a fresh synthetic SQLite DB; 26/42 application checks passed. No official V5 artifacts were changed. Local model/tool traces, latencies, approval results and failures are recorded in `experiments/results/p2_v5_42_real_application_v1.json`; the full breakdown and all related artifact hashes are in [the Fresh60 and 42-case report](P2_FRESH60_AND_42CASE_EVALUATION_REPORT.md). The V5 original acceptance verdict remains **PARTIAL**; the deterministic fixture is not real-model evidence.
