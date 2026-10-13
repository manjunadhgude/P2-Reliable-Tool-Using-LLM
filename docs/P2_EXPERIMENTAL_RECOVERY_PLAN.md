# P2 Experimental Recovery Plan and Outcomes

**Status:** bounded recovery completed; no candidate accepted. **Overall P2 verdict remains PARTIAL.** All recovery sets below are internal development diagnostics, not independent human-reviewed evaluation.

## Questions and hypotheses

1. **H1 — Explicit workflow plan improves action selection:** direct-controller mapping of clear policy, eligibility, estimate, lookup, and ticket intents should reduce model direct-answer/no-tool failures. V5 recovery replay supports this on its own set, but its actual app slice and lack of independent adjudication limit the claim.
2. **H2 — Ambiguity handling improves missing/conflicting entity behavior:** V6 adds intent/entity checks. The V2 recovery replay gained versus its V2 controller baseline, but 14/42 real-app checks still failed.
3. **H3 — Preflight action selection adds value beyond V6:** V7 routes recognized requests through an explicit action before model generation. On the already exposed V2 recovery set, it improved action replay by only 2/64 cases (+3.125 pp) and did not improve the 42-case application pass count over V6 (28/42 each). H3 is not supported as an acceptance-level fix.

## Experiment design and immutable evidence

- **Recovery V1:** 64 rows, 64 unique normalized cores, 16 families, SHA-256 `998587e78c934ff48a50a6b422d613dacb37db68fa6dde1b50940f828522e098`. Frozen source/config and application selection recorded in `p2_recovery_freeze_v1.json` before model inference.
- **Recovery V2:** 64 rows, 64 unique cores, 16 families, SHA-256 `78c81c272919396a0f56f1f1830fd6f29c683de579277c0c43aae9743dcb2f4f`. Frozen with V6 in `p2_recovery_v2_freeze.json`; V7 has a separate development diagnostic freeze `p2_recovery_v7_dev_freeze.json`.
- Model: cached local Ollama `qwen3:1.7b`, Q4_K_M, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`. No download was needed during these runs.
- Raw inference was captured once per suite. Controller numbers are paired offline replays over those saved model proposals; they do **not** execute tools. Application checks use separate fresh synthetic databases and actual FastAPI/Ollama traces.
- Each recovery dataset has 64 unique cores; therefore row-weighted and core-weighted scores coincide. This removes repeated-core weighting as an explanation for these particular gains, but does not address independent labels or leakage from iterative inspection.

## Results

| Run | Raw exact | Baseline exact | Candidate exact | Paired gain | Unexpected writes | Actual app |
|---|---:|---:|---:|---:|---:|---:|
| Recovery V1, V2→V5 | 17/64 (26.6%) | 25/64 (39.1%) | 53/64 (82.8%) | +28/64 = +43.75 pp | 0 candidate | 34/42 |
| Recovery V2, V2→V6 | 10/64 (15.6%) | 18/64 (28.1%) | 37/64 (57.8%) | +19/64 = +29.69 pp | 1 candidate | 28/42 |
| Recovery V2, V2→V7 | 10/64 (15.6%) | 18/64 (28.1%) | 39/64 (60.9%) | +21/64 = +32.81 pp over V2; +2/64 = +3.13 pp over V6 | 1 candidate | 28/42 |

V5/V6/V7 labels and application checks were authored inside this project. V7’s V2 set had already been used by the V6 experiment and inspected. Treat the results as diagnostic only. V1 and V2 are different datasets: do not interpret 53/64 versus 37/64 or the app counts as a paired controller comparison.

## Real application-path evidence

The app runner recorded each case’s real assistant output, request duration, tool trace, and family-specific checks. Runs used only seeded synthetic SQLite. The V7 run completed 42/42 requests; 28 passed the defined family checks and 14 failed. It also attempted duplicate supervisor approval: both responses referenced the same ticket ID, and exactly one ticket row existed. This is a positive safety regression signal for that path, not broad workflow acceptance.

The runner initially had an indentation error in its final artifact-writing block, which prevented the V7 run from starting. The indentation was corrected, the script compiled, and the subsequent complete run is the saved `p2_recovery_v7_dev_application.json`. This repair changed only the evaluation runner; it did not change model/controller source after the V7 diagnostic freeze. The error and correction are part of the audit trail.

## Decision and stopping conditions

- Stop this implementation cycle. Do not promote V5, V6, or V7 to default.
- Do not tune on the recovery sets again; they are now exposed development evidence.
- Before another score-directed change, independently adjudicate a fresh set of at least 60 distinct normalized cores across at least 12 meaningful families, resolve all prompt/gold entity conflicts without changing official labels, freeze source/model/evaluator, and pre-register the gate.
- Require both row-weighted and core-weighted paired exact-action gains of at least 10 percentage points on the same adjudicated examples, no unexpected state-changing proposals, and no regression in authorization/safety checks. Then require a separately frozen application run with real tool traces and approval/idempotency checks before acceptance.
- If a minimum of 20 independently reviewed cores across 10 families is unavailable, call the comparison inconclusive. A development pass only authorizes proposing a separately frozen follow-up; it does not establish generalization or change P2 acceptance.

## Exact evidence artifacts

- Recovery V1 raw: `experiments/results/p2_recovery_raw_v1.json`; paired scores: `experiments/results/p2_recovery_comparison_v1.json`; actual app: `experiments/results/p2_recovery_application_v1.json`.
- Recovery V2 raw: `experiments/results/p2_recovery_v2_raw.json`; V6 scores: `experiments/results/p2_recovery_v2_comparison.json`; V6 actual app: `experiments/results/p2_recovery_v2_application.json`.
- V7 scores and actual app: `experiments/results/p2_recovery_v7_dev_comparison.json`, `experiments/results/p2_recovery_v7_dev_application.json`.
- Versioned dataset manifests, annotation policies, freezes, and exact hashes are retained alongside those outputs; see `experiments/results/p2_trial_registry_v1.json` for evidence hashes and reconstructed attempt entries.
