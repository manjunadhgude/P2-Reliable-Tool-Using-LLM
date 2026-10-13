# Hybrid Controller v1 — Locked Test Report

## Freeze and protocol

The controller/source/configuration was frozen before the single new test inference run. No Git commit exists in this workspace; the source/config SHA-256 is recorded in `hybrid_controller_frozen_config_v1.json` as `57473c7008957e9221601caeb81c6c50278ac007fc9d1339d579a164f509745b`. Dataset SHA-256 is `a4c83c7dc28ffba20a4c08c6bd318a6dcf7ece14688806340fea531897ff42a2`. The Ollama model was `qwen3:1.7b`, Q4_K_M, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`; prompt `ollama-native-v1`, action schema `1.0.0`, `think=false`, temperature 0, streaming disabled, 256-token cap, 90-second timeout.

The model-only run used `HYBRID_CONTROLLER_ENABLED=false`. It called the real local Ollama model for all 60 examples. Then the frozen hybrid controller replayed saved action projections. That replay did not execute registered tools or write to a database. No controller changes or test reruns were made after observing these outcomes.

## Results

| Measure | Qwen model-only | Hybrid action replay |
|---|---:|---:|
| Exact actions | 12/60 (20.0%) | 43/60 (71.7%) |
| Valid model actions | 55/60 (91.7%) | 5 invalid model actions handled as fail-closed |
| Tool selection | 12/36 (33.3%) | 31/36 (86.1%) |
| Exact arguments | 12/36 (33.3%) | 31/36 (86.1%) |
| Correct missing-ticket clarifications | Model proposed ticket actions | 0/12 (0%) |
| Correct unsafe-policy handoffs | 0/12 | 12/12 (100%) |
| Incorrect model tool/state proposals | 22 | 22 model proposals audited; other invalid cases failed closed |
| Model-proposed prohibited writes | 21 | 12 final state-change proposal actions remained in the offline action replay |
| Deterministic controller repairs / extra model retries | — | 1 repair / 0 extra retries |
| Estimated hybrid-path model calls | — | 48/60; offline estimate, not live count |
| Proposal latency p50/p95 | 3,104 / 3,524 ms | same saved proposals for the cases used |
| Controller overhead p50/p95 | — | 0.052 / 0.112 ms, offline replay only |

Hybrid exact action matches by test family: nonexistent order 12/12, cross-tenant order 12/12, refund estimate 7/12, missing ticket order 0/12, unsafe policy bypass 12/12. The exact-action result increased by 51.7 percentage points over the corrected raw-model score. This is an application-plus-model result, not an increase in Qwen's own accuracy. The validation split had 48/48 hybrid exact actions, so the lower and uneven held-out result is visible rather than tuned away.

## Material limitation

For all 12 missing-ticket-order examples, the model proposed `create_support_ticket`; the hybrid action replay retained a `propose_state_change` action, in several cases with `order_id: null`. This missed the expected clarification and is a workflow correctness gap. The offline evaluator executed no proposals, so it cannot establish whether those proposals would be accepted or whether a write would occur. The test is not evidence that those particular pending proposals are safe to approve. The controller was frozen and not revised from this test result, as required by the split protocol.

The 5 invalid model actions failed closed; 1 schema-grounded deterministic repair occurred; no extra model retry occurred. The offline artifact reports unsafe/duplicate state changes as `null` because it executes no tools. Safety execution and duplicate protection are measured separately in the actual application integration suite, where the only ticket was held pending, explicitly approved once by a supervisor, and replay returned the same ticket without a second row.

## Interpretation

The controller improves the measured test action selection substantially over raw Qwen, but the overall target is **PARTIAL**. Model-only targets of 85% tool selection and 80% exact arguments were not met (both are 33.3%). Hybrid action exact match is 71.7%; missing-ticket clarification is 0/12; refund-family action match is 7/12. These scores measure only this synthetic locked split and do not imply generalization to real support traffic.

## Artifacts and reproduction

- Raw model-only JSON: `ollama_qwen3_1.7b_test_modelonly_corrected_bounded_v1.json`
- Hybrid JSON/CSV: `hybrid_controller_v1_test_bounded_final.json` and `.csv`
- Freeze record: `hybrid_controller_frozen_config_v1.json`
- Validation report: `hybrid_controller_validation_v1.md`

The model-only run can be reproduced with a fresh output path using the command in `README.md`. If rescored, pass that saved raw artifact to `evaluate_hybrid_controller.py`. Do not tune from or rerun the locked result as a score-improvement loop.
