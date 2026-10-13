# Hybrid Controller v1 — Validation Report

## Scope and evidence layers

This report evaluates the frozen `hybrid-controller-v1` against the 48-example validation split. The raw-model result and controller replay are separate: model-only measures Qwen's normalized proposal; hybrid action-level measures the action selected by deterministic application logic after applying request context and policy. The hybrid replay does not execute tools or score generated answer wording. Actual task outcomes are reported in the separate FastAPI/Ollama integration artifact.

Dataset: `experiments/datasets/scenarios.jsonl`, SHA-256 `a4c83c7dc28ffba20a4c08c6bd318a6dcf7ece14688806340fea531897ff42a2`; split 96/48/60. Model: local Ollama `qwen3:1.7b`, Q4_K_M, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`; prompt `ollama-native-v1`; action schema `1.0.0`; `think=false`, temperature 0, streaming off, 256 generated-token cap, 90-second timeout.

## Results

| Measure | Result | Definition |
|---|---:|---|
| Model-only valid actions | 48/48 (100%) | Parsed and schema-valid; validity is not correctness. |
| Model-only exact actions | 12/48 (25%) | Correct action type/tool and exact expected arguments where applicable. |
| Model-only tool selection | 0/12 (0%) | Only examples with an expected tool are in the denominator. |
| Model-only exact arguments | 0/12 (0%) | Only expected-tool examples with arguments are in the denominator. |
| Hybrid action exact match | 48/48 (100%) | Final offline controller action compared to expected action labels. Not task completion. |
| Hybrid tool selection | 12/12 (100%) | Tool-expected subset; deterministic routing contributes to this result. |
| Hybrid exact arguments | 12/12 (100%) | Expected-tool subset; grounded identifiers and tool schema/context contribute. |
| Correct clarification / handoff | 12/12 / 12/12 | Missing-order clarification and prohibited/injection handoff subsets. |
| Incorrect model tool/state proposals | 11 | Four wrong eligibility tool choices plus seven unrequested state-change proposals. |
| Prohibited model write proposals | 7 | These were not accepted by the live controller; validation preflight intercepted the requests. |
| Hybrid state-change proposals / retries | 0 / 0 | The 7 unrequested write proposals were preempted; no extra model retry was used. One schema-grounded argument repair is permitted by design, but none occurred here. |
| Estimated model calls | 24/48 | Validation controller replay predicts that 24 requests would be answered by preflight without Ollama; this is not a live call count. |
| Model call latency on used proposals | p50 3,103.76 ms; p95 4,412.99 ms | Latencies from the saved model-only proposal artifact for cases where the controller uses a proposal. |
| Controller overhead | p50 0.0227 ms; p95 0.0407 ms | Offline replay timing only. |

Per-family hybrid action exact match was 12/12 for each of missing-order, eligibility, no-tool explanation, and prompt-injection families. This score reflects the application controller; it does not mean Qwen achieved those scores.

## Validation replay history

The saved replay artifacts document one controller version and no versioned controller-source change: each reports controller source SHA-256 9245e5a85b6a73ec748314cca4911c065d4364b7a5a1b2bbce5602030c4ccd54. The current controller has the same SHA. This workspace has no Git commit or source history to reconstruct edits that were not recorded.

- `hybrid_controller_v1_validation.json` is an early replay and reports 24/48 exact actions; the 12 eligibility and 12 no-tool cases were marked `failed_closed`.
- `hybrid_controller_v1_validation_replay_corrected.json` is a later replay over the same named unbounded model-only input and reports 48/48; it selects deterministic eligibility actions and accepts the no-tool responses.
- `hybrid_controller_v1_validation_final.json` reports 48/48 using that earlier raw model-only input.
- `hybrid_controller_v1_validation_bounded_final.json` and the selected `hybrid_controller_v1_validation_frozen.json` report 48/48 using the corrected bounded raw-model artifact. The frozen JSON also records prompt/schema versions.

The early and later replay artifacts are both retained. Their differing outputs are not attributed to improved Qwen behavior or to a measurable controller-source change; the run artifacts do not record a cause for the replay delta. The final selected validation result is the frozen replay paired with the bounded raw artifact, and the held-out score remains separately reported.


## Metric correction and limitations

The historical evaluator compared `{}` against `null` for some non-tool expected actions, undercounting those matches. Historical raw JSON and historical reported scores were left unchanged. The new bounded model-only evaluator treats arguments as not applicable when no tool arguments are expected. Under that corrected definition, the bounded 48-case Qwen result is 12/48 exact, rather than the historical 0/48 figure. The saved old metric is retained as historical evidence and must not be silently rewritten.

This validation report is action-level. The model-only runner does not execute business tools; the hybrid replay consumes sanitized saved action projections, omits generated free text, and does not execute tools. Do not interpret 48/48 as a raw-model gain or as end-to-end task success. The small validation set is also not broad evidence of production reliability.

## Artifacts

- Raw model-only: `ollama_qwen3_1.7b_validation_modelonly_corrected_bounded_v1.json`
- Hybrid action replay JSON/CSV: `hybrid_controller_v1_validation_frozen.json` and `.csv`
- Actual application outcomes: `hybrid_controller_v1_real_integration_frozen_20261010.json`
- Frozen source/config record: `hybrid_controller_frozen_config_v1.json`
- Design: `docs/HYBRID_CONTROLLER_DESIGN.md`

The source/configuration SHA-256 in the freeze record identifies the controller, adapters, test code, evaluation code, schemas, runtime example configuration and dataset inputs used for the locked test. No controller tuning will be performed against the held-out result.
