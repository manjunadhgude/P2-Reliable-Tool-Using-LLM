# P2 V5 Final Frozen Evaluation Report

Date: 2026-10-11  
Verdict: **PARTIAL**

## Frozen inputs

- Dataset: 210 synthetic scenarios (60 dev, 150 test), SHA-256 `e5f6b399494884c347b55c8bf352c570913472be34ebc5ffb52e089ab08adbdf`.
- Dev/test pools have zero shared `template_core_id` values and zero normalized request-core overlap.
- Real model: Ollama `qwen3:1.7b`, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`, Q4_K_M.
- Historical V1–V4 artifacts were preserved. V4 remains a historical comparison with documented wrapper/template leakage.

## Results

| Track | Result |
|---|---:|
| V5 raw dev | 60/60 valid; 10/60 exact (16.7%); tool selection 12/35 (34.3%); argument exact 2/31 (6.5%); p50/p95 3.35/4.97s |
| V5 raw test | 149/150 valid; 25/150 exact (16.7%); tool selection 19/85 (22.4%); argument exact 4/75 (5.3%); p50/p95 3.36/5.30s; 1 timeout/error |
| V5 hybrid replay | 31/150 exact (20.7%); tool selection 20/85 (23.5%); argument exact 4/75 (5.3%); 6/43 clarifications; 5/11 handoffs; 1 failed-closed action |
| Fresh real application | 8/8 established workflows passed with a fresh synthetic SQLite database, including protected writes, approval, and duplicate-approval checks |

The deterministic 42-case selection manifest is saved at `experiments/results/hybrid_controller_v5_e2e_selection.json`. The current application integration harness executes the established 8-case end-to-end suite; it does not claim execution of all 42 selected cases.

## Interpretation

The real model loads and produces schema-valid actions quickly, but it does not meet the reliability bar for unattended policy routing. The hybrid controller improves safety and some exact outcomes, while server-side authorization, validation, approval, tenant isolation, and idempotency remain authoritative. The deterministic backend remains the CI/default fixture and is not counted as real-model evidence.

## Evidence files

- `experiments/results/hybrid_controller_v5_raw_dev_final.json`
- `experiments/results/hybrid_controller_v5_raw_test_final.json`
- `experiments/results/hybrid_controller_v5_hybrid_test_replay_final.json`
- `experiments/results/hybrid_controller_v5_real_integration_subset.json`
- `experiments/results/hybrid_controller_v5_e2e_selection.json`
