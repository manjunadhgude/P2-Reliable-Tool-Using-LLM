# P2 Fresh V7 vs V8 Evaluation — Blocked Run Report

**Date:** 2026-10-11  
**Fresh evaluation status:** **BLOCKED — raw model pass did not complete**  
**Overall P2 acceptance:** **PARTIAL**  
**Controller changes during this evaluation:** none

## Executive result

The new evaluation set and all pre-inference inputs were frozen successfully. One local Ollama raw-proposal pass was started, but it did not finish and produced no complete raw-result JSON. The configured 30-second timeout did not bound one inference call in practice: a recorded row duration was **3,102,971.7 ms** (about 51.7 minutes). The process was stopped under the resource limit. No partial console output was promoted to a score.

Therefore this evaluation cannot determine whether V8 improves on previously unseen requests. The earlier exposed-set diagnostic (V7 39/64, V8 41/64) remains diagnostic only. No fresh V7/V8 action metric, paired improvement, uncertainty interval, or actual-application comparison is available. No PASS is claimed.

## Frozen evaluation inputs

- Dataset: `experiments/datasets/p2_fresh_v7_v8_v1/scenarios.jsonl`
- Dataset SHA-256: `c1f24ba55e7b25f2b97d4997eaeb8089b20d8f8faa3d6c98d174672cd8480ab9`
- Size: **130 unique prompt cores**, **13 families**, 10 cases per family.
- Families: order lookup, item listing, return policy, eligibility, refund estimate, multi-step workflows, missing information, ambiguous requests, support tickets, prompt injection, tenant isolation, invalid/unsupported requests, and no-tool conversation.
- Overlap audit: screened **2,220 prompts from 34 saved artifacts**; zero exact-core or >=0.78 character 3-gram Jaccard matches. This lexical check cannot prove semantic novelty.
- Labels: internal, written before inference from P2 tool schemas, seed records, and the annotation policy; not independently human-reviewed.
- App slice: `experiments/results/p2_fresh_v7_v8_app_slice_selection.json`, **26 cases**, two per family, selected before inference for equivalent V7/V8 runs with separate fresh synthetic databases.
- Freeze: `experiments/results/p2_fresh_v7_v8_freeze.json`. All frozen source hashes were rechecked after the attempt; no mismatches were found. Dataset and overlap hashes also match.

## Frozen model and source identity

- Runtime: local Ollama, no cloud or paid API.
- Model: `qwen3:1.7b`, Q4_K_M, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`.
- Generation: temperature 0, thinking off, non-streaming, 256 max new tokens, configured 30-second request timeout, one bounded repair retry.
- V7 SHA-256: `78aad9ad43dcef6e95bcc5c2db7c9356df0027dd31a3074ad5df125ed24696c7`.
- V8 SHA-256: `6733944f0d95ea9dcaf0995af40a8ef57b6d323e7ceae595f098dd04b2ba16a3`.
- The freeze manifest records hashes for application orchestration, tool schemas/registry, model prompt adapter, configuration, dataset, label policy, overlap checker, and scoring/application evaluators.
- V8 remained opt-in; V7 behavior and both controller files were unchanged during this evaluation. Deterministic CI defaults were unchanged.

## Inference attempt and results

Command used:

```powershell
$env:MODEL_BACKEND='ollama'
$env:MODEL_ID='qwen3:1.7b'
$env:OLLAMA_URL='http://localhost:11434'
$env:REQUEST_TIMEOUT_SECONDS='30'
$env:MODEL_MAX_NEW_TOKENS='256'
.\.venv\Scripts\python.exe experiments\evaluation\run_ollama_benchmark.py `
  --dataset experiments\datasets\p2_fresh_v7_v8_v1\scenarios.jsonl `
  --split dev `
  --output experiments\results\p2_fresh_v7_v8_raw.json
```

The run emitted some individual rows to the console, including a first request taking 32,176.66 ms and a later request taking 3,102,971.7 ms. It was stopped before the benchmark wrote its final artifact. `experiments/results/p2_fresh_v7_v8_raw.json` does not exist. Because the full proposal set is unavailable, the evaluator was not run and no raw, V7, or V8 score is reported.

The runner's use of a 30-second `urllib` timeout did not produce a practical end-to-end bound for this call. The long call is the verified resource blocker. Do not rerun the full set unchanged; a future attempt needs an independently enforced process-level wall-clock limit and a newly frozen run configuration.

## Actual application comparison

Not run. The frozen 26-case slice was prepared for both controller arms, with separate SQLite databases and checks for registered-tool execution, final-answer grounding, multi-step completeness, tenant denial, pending ticket state, supervisor approval, and duplicate approval. Since the raw pass did not finish, the application comparison was not started. No deterministic fixture was counted as real-model evidence.

## Decision against P2 gates

| Gate | Result |
|---|---|
| Fresh raw-model exact action, tool choice, and arguments | **Unavailable — inference incomplete** |
| Fresh paired V7 vs V8 improvement and uncertainty | **Unavailable — no complete shared proposals** |
| Unexpected write proposals / safety regression on full set | **Unavailable — incomplete proposal set** |
| Actual FastAPI tool execution and task completion for both arms | **Not run** |
| V8 proven better on previously unseen prompts | **No conclusion** |
| Original P2 acceptance | **PARTIAL; not met by this run** |

The previously observed exposed-set replay was V7 39/64 vs V8 41/64 (+3.125 percentage points), with one unexpected write proposal in each arm. It is not fresh evidence and does not satisfy the requested 90% action/tool/argument targets. Historical V5/V7 artifacts and original acceptance scores remain unchanged.

## Remaining work

1. Diagnose the local inference timeout behavior without changing V7 or V8.
2. Create a separately versioned runner with a process-level hard deadline and partial-progress checkpointing, then freeze its hash and configuration before the next inference attempt.
3. Only if a bounded full raw pass completes, run the frozen V7/V8 identical-proposal replay and score it with the frozen evaluator.
4. Run the same frozen 26 actual-app cases through V7 and V8 with fresh synthetic databases; retain tool traces and approval/idempotency evidence.
5. Reassess the gates. Independent human label review and broader validation would still be needed before generalization or overall acceptance claims.
