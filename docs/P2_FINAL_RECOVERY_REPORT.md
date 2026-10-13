# P2 Final Recovery Report

**Date:** 2026-10-11  
**Verdict:** **PARTIAL — project runs, but original model-quality and broad end-to-end acceptance are not met.**

## What was done

- Completed bounded V5, V6, and V7 opt-in recovery-controller iterations without changing the default deterministic CI backend or the official pinned V5 result.
- Created two separately named 64-case recovery suites, source/config freezes, raw inference outputs, paired offline action replays, application selections, and complete real-app traces.
- Ran real local Qwen through the existing FastAPI orchestration and seeded synthetic SQLite. No paid API/cloud GPU, customer data, or financial integration was used.
- Verified duplicate supervisor approval in the V1 and V2 recovery application runs, including the V7 diagnostic: repeat approval returned the same ticket and left exactly one ticket row.
- Repaired a syntax/indentation defect in the V7 evaluation runner after it prevented execution; compilation and the subsequent 42-case run succeeded.

## Main results

| Evidence | Result | Meaning |
|---|---:|---|
| Original locked V5 raw model action | 25/150 = 16.7% | Frozen historical model score; unchanged. |
| Original locked V5 V2 controller replay | 31/150 = 20.7% | Offline saved-action replay; no registered tools executed. |
| Original V5 correct clarifications | 6/43 = 14.0% | Clarification gate remains failed. |
| Recovery V1 raw / V5 replay | 17/64 / 53/64 | Internal diagnostic; 64 unique cores; offline replay candidate 82.8%. |
| Recovery V1 actual app | 34/42 passed | Real local model and FastAPI checks; still 8 failures. |
| Recovery V2 raw / V6 replay | 10/64 / 37/64 | Internal diagnostic; offline replay candidate 57.8%, with one unexpected write proposal. |
| Recovery V2 V6 actual app | 28/42 passed | Real workflow checks; 14 failures. |
| Recovery V2 V7 replay / actual app | 39/64 / 28/42 | V7 replay is 60.9%; app count unchanged from V6. One unexpected write proposal remains. |
| Deterministic backend | CI fixture | Software regression aid only; not a model result and not counted as real-LLM success. |

The recovery sets contain unique cores, so row/core weighted action scores are equal for those sets. Yet they are internally authored and iteratively exposed. Their results cannot validate generalization. The real-app slices show that better replay does not guarantee successful workflows.

## Direct answers to the completion questions

1. **What was verified to be wrong?** Raw model action/argument quality is low; intent and entity routing have failure cases; historical V5 annotations contain documented entity conflicts; and replay scores do not execute tools. These points are supported by saved results and source audits.
2. **What is the primary root cause?** Multiple interacting factors: limited model action quality, brittle/ambiguous workflow routing and entity grounding, and evaluation-label/provenance limitations. Evidence does not isolate a single cause.
3. **Why did earlier approaches fail to yield reliable acceptance?** Offline controller gains were evaluated on small internal sets; some sets were repeatedly inspected; actual application workflows remained below target; and the official frozen test still misses model-quality thresholds. Scores across different sets are not comparable as paired evidence.
4. **Which approach is best supported?** A narrowly scoped, explicit intent/workflow-routing experiment is the most evidence-aligned next hypothesis. V7 itself is not accepted: its gain over V6 was only 2 cases in 64 replay rows and app success stayed 28/42.
5. **What measurable criteria apply next?** At least 10 percentage-point paired improvement in both row-weighted and core-weighted exact-action accuracy on the same independently reviewed development examples; at least 20 independently reviewed cores across 10 families or mark inconclusive; zero unexpected writes; retain security, tenant, validation, approval and idempotency checks; then a separately frozen real-app run.
6. **What is missing?** Independent human review; fresh, sufficiently sized and unseen evaluation; resolution through a separate review overlay of all gold/prompt conflicts; broad application completion at its acceptance threshold; and original model-quality target attainment.
7. **Were the tests run?** Yes. Backend: 79 passed, 1 upstream AnyIO/Starlette deprecation warning. Ruff: passed. Frontend production build: passed. V5 dataset validator: passed (210 rows; 60 dev/150 test; no normalized-core overlap). Real Qwen/FastAPI V7 diagnostic: 42 cases, 28 pass/14 fail.
8. **Were security controls relaxed?** No. The candidate routing remains opt-in; business authorization and approval stay server-side. Duplicate approval behaved idempotently in the saved run. The deterministic backend remains a test fixture.
9. **Did original artifacts change?** No intentional edits were made to historical score artifacts. New experiments use versioned output paths. A complete proof of unchanged repository state is not possible because there is no Git commit history or baseline tree; saved hashes were used where manifests/freezes provide them.
10. **Is P2 complete and accepted?** No. Core synthetic application functionality and selected safety paths are demonstrated, but quality/acceptance gates remain unmet. Overall status stays **PARTIAL**.

## Current checks

- `python -m pytest backend/tests -q` — **79 passed** (one upstream deprecation warning).
- `ruff check backend/app backend/tests ...` — passed for the checked application/tests and recovery evaluation scripts.
- `npm run build --prefix frontend` — passed.
- `python experiments/evaluation/validate_v5_suite.py` — valid, 210 rows, 60/150 split, zero normalized-core overlap.
- Recovery V7 real application run — 42 cases, 28 passed; duplicate-approval/idempotency subcheck passed.

The current checks do not re-run the official model benchmark, and none changes its score. Docker readiness and broad locked-test task completion were not newly established in this recovery pass.

## Recommended next steps

1. Have an independent human reviewer adjudicate a new 60+ distinct-core set across 12+ families; use a separate overlay and retain official V5 labels unchanged.
2. Freeze one candidate and one baseline source/config/model/evaluator before a single bounded paired run. Do not reuse the exposed recovery sets for acceptance.
3. Require the action gate and safety criteria above. If they pass, create a separately frozen follow-up application test; only then consider any default change.
4. Keep V2 default and deterministic CI backend until acceptance evidence supports a change.

See [longitudinal root-cause report](P2_LONGITUDINAL_ROOT_CAUSE_REPORT.md), [recovery experiment report](P2_EXPERIMENTAL_RECOVERY_PLAN.md), and `experiments/results/p2_trial_registry_v1.json`.
