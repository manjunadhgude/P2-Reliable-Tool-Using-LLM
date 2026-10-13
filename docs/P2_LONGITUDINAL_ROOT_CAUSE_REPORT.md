# P2 Longitudinal Root-Cause and Failed-Attempt Report

**Evidence snapshot:** 2026-10-11. **Overall status: PARTIAL.** This report consolidates preserved project history with the V5–V7 bounded recovery work. “Verified” below means supported by code or a saved execution artifact; it does not mean independently adjudicated by an external reviewer.

## Executive finding

P2 has a functioning synthetic-data application with strict tool schemas, server-side business rules, tenant-scoped access, traces, pending ticket proposals, supervisor approval, and duplicate-approval protection. The limiting factor is not one isolated software bug. It is the combined reliability of a small local model's intent/action proposals, brittle or ambiguous natural-language routing, and weaknesses in the evaluation evidence. Hybrid controllers improve action replay on some internally authored suites, but the gains do not consistently carry into the real application checks. The official frozen V5 metric remains low and unchanged. No candidate has earned a generalization or overall acceptance claim.

## Root-cause evidence

### Verified causes

1. **Model actions are often incomplete or wrong.** On the official frozen V5 test, raw Qwen exact action was 25/150 (16.7%); tool choice was 19/85 (22.4%), exact arguments 4/75 (5.3%), and correct clarifications 6/43 (14.0%). The smaller recovery V1/V2 real-model runs likewise generated only 17/64 and 10/64 exact actions. These are measured failures, not inferences.
2. **Intent-to-workflow precedence and entity resolution are fragile.** Earlier code audits found lexical token matches that confuse item identifiers with intent, direct answers that bypass a required tool, eligibility/estimate/policy precedence collisions, and order/item ambiguity. Recovery application traces still show absent or incorrect calls for eligibility, estimates, policy, and lookup. V5/V6/V7 candidates did not eliminate these families.
3. **Action replay is not task completion.** Official V5 V2 replay is 31/150 (20.7%), but it executes no registered business tool. Real-app checks are separately measured: historical 42-case V5/V4 run 26/42; recovery V1/V5-controller run 34/42; recovery V2/V6 run 28/42; recovery V2/V7 run 28/42. The distinct scopes must not be merged or treated as paired scores.
4. **The target labels and test provenance limit conclusions.** Historical audits found V5 prompt/gold entity disagreements and repeated prompt cores in selected subsets. New recovery suites are internally authored, were exposed through iterative development, and have not received independent human adjudication. Their scores are development diagnostics.
5. **Safety controls work in covered examples, but do not imply quality acceptance.** The recovery V7 actual-app artifact records a repeated supervisor approval returning the same ticket ID and exactly one ticket row. This supports idempotency for that run, not universal security certification.

### Probable explanations

- A compact 1.7B Q4_K_M model may be under-capable for the varied tool-selection, argument-grounding, ambiguity, and multi-step tasks in this project. The repeated raw action weakness and low-latency no-call/wrong-call behavior support this, but no controlled model-size experiment isolates model capacity from prompts, controller behavior, or labels.
- The controller’s growing set of intent heuristics may improve known phrases while leaving uncovered paraphrases and can also route borderline cases incorrectly. The V6/V7 gains are modest and remain below workflow thresholds; this explanation is plausible but needs a frozen, independently reviewed experiment.
- Some apparent action errors may be evaluation-label noise, especially where prompt/order identifiers conflict. The conflicts are verified in historical audits, but their contribution to each newly recorded failure count is not established here.

### Untested hypotheses

- A stronger locally runnable model or a tool-native constrained decoding mode would improve end-to-end task success enough to meet acceptance thresholds.
- A more explicit, typed workflow planner would reduce misses without increasing false-positive state-changing proposals.
- The current dataset’s failure distribution predicts performance on real support requests. No real customer data or external benchmark was used, so this remains untested.

## Attempt history and why scores did not settle the question

The available written records and experiment artifacts describe the following progression. The trial registry at `experiments/results/p2_trial_registry_v1.json` points to the exact saved evidence. The repository contains no Git commits, so earlier file ancestry and some intermediate prompt/config iterations cannot be reconstructed reliably; counts such as “25+” or “40+” attempts cannot be independently verified from this checkout.

| Phase | Saved evidence | Outcome and limitation |
|---|---|---|
| Initial A/B/C prompt/model experiments and CPU Transformers attempt | Forensic audit and final verification reports | A/B/C exact test results 23/60, 24/60, 24/60; C did not meet its specified improvement target. Pinned Transformers CPU run did not finish a valid tool call within its limit. |
| V1 hybrid controller | `hybrid_controller_v1_test_bounded_final.json` | 43/60 (71.7%) in offline action evaluation; clarifications 0/12. No tool execution in that score. |
| V2 frozen evaluation | `hybrid_controller_v2_test_frozen.json` | 96/140 (68.6%); tool 50/80, arguments 44/70, clarifications 28/40. Inconsistent with V1 scope and not a direct paired comparison. |
| V3 raw and hybrid | Reports and saved V3 results | Raw 46/150 (30.7%); offline hybrid 100/150 (66.7%). The large gap is controller replay, not a model-quality improvement or end-to-end score. |
| V4 controller experiments | V4 report and Fresh60 report | Replays rose to 27/28 on development and 16/18 on a small “holdout” later exposed as development evidence. AI-authored labels, template leakage concerns, and tiny samples prevent acceptance. Fresh60 V4 replay was 42/60 (70%). |
| Official V5 freeze | V5 report/artifacts | Raw 25/150; V2 replay 31/150; clarifications 6/43. Exact arguments 4/75. The official result remains frozen. |
| V5 broad actual application run | V5/Fresh60 reports | 26/42 application checks passed, with policy, eligibility, refund estimate, and multi-step misses. Duplicate approval passed. |
| Recovery V1 / V5 controller candidate | `p2_recovery_comparison_v1.json`, `p2_recovery_application_v1.json` | On 64 unique cores, V2 replay 25/64 (39.1%) to candidate replay 53/64 (82.8%), +43.75 points; candidate unexpected writes 0. Real-app slice 34/42. Strong development signal, but internally authored labels and exposed iteration; not acceptance evidence. |
| Recovery V2 / V6 candidate | `p2_recovery_v2_comparison.json`, `p2_recovery_v2_application.json` | V2 replay 18/64 (28.1%) → V6 37/64 (57.8%), +29.69 points; one unexpected write proposal. Real-app slice 28/42. Different suite from recovery V1; scores are not a direct paired version comparison. |
| Recovery V2 / V7 preflight candidate | `p2_recovery_v7_dev_comparison.json`, `p2_recovery_v7_dev_application.json` | V6 37/64 → V7 39/64 (60.9%), +3.13 points in replay; one unexpected write proposal remains. Actual app 28/42; duplicate approval passed. This was a diagnostic on an already exposed set. |

Scores did not establish success because (a) impressive replay gains were measured on narrow, internal, repeatedly inspected prompts, (b) action exactness can improve without producing a correct application workflow, (c) app checks expose unresolved tool routing and grounding cases, and (d) the official V5 action score and acceptance thresholds remain unmet. No result justifies replacing the default V2 controller or altering the original acceptance verdict.

## Best-supported next direction

The evidence most strongly supports a **small, controlled intent/workflow-routing experiment**, with no model retraining and no new broad heuristic expansion. Freeze one independently reviewed, distinct-core set before evaluation; identify whether preflight routing fixes specific app failures while preserving no-tool, clarification, tenant, and approval behavior. Recovery V7’s +3.13 point replay change and unchanged 28/42 app result are insufficient to deploy it. Compare candidate changes to V2 and V7 on the *same* adjudicated cases; keep action replay, tool execution, and application completion as separate endpoints.

## Integrity and limitations

- The official V5 datasets, labels, raw outputs, and results were not intentionally edited by this work; recovery artifacts use new names.
- The original deterministic backend remains the default for CI and is not real-model evidence. Real-model runs used local Ollama `qwen3:1.7b`, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`, Q4_K_M, with synthetic SQLite data.
- No paid API, cloud GPU, real customer data, or external financial integration was used.
- With no Git commits/reflog, there is no reliable baseline tree to prove that every historical project file is byte-for-byte unchanged. Evidence hashes in manifests/freezes identify the specific preserved artifacts that were checked, not a full repository diff.
- Independent label adjudication, sufficiently large unseen test data, broad end-to-end success, universal security assurance, and passing original model-quality gates remain unresolved.
