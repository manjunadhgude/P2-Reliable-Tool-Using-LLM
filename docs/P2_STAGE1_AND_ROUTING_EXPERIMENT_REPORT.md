# P2 Stage 1 Fixes and Routing Experiment Status

**Date:** 2026-10-11  
**Overall P2 status:** PARTIAL  
**Stage 1 implementation status:** targeted fixes implemented; backend regression suite passes  
**Controlled routing experiment:** NOT RUN

## Summary

This pass added a trace-grounded guard for unsupported business claims, safer multi-step response composition, and an opt-in V8 candidate for singular unidentified-item requests. V2 through V7 controller source files and the deterministic CI backend were left unchanged. V8 is not the default; opt in with `HYBRID_CONTROLLER_VERSION=v8_candidate` when the Ollama hybrid controller is enabled.

The requested fresh-set V7-versus-typed-router experiment is not complete. I ran a paired diagnostic replay on the available 64-core set using identical saved proposals, but that set is exposed development evidence and does not measure the new application-level response guard or workflow composition fixes. No new inference or fresh evaluation dataset was run, so there are no new raw-model scores or latency claims.

## Changes and regression evidence

| Change | Evidence / root cause | Implementation | Verification |
|---|---|---|---|
| Guard unsupported state and capability claims | V7 actual-app outcomes include a false ticket-created statement without a pending action, plus false claims that tracking/order lookup is unavailable even though `lookup_order` is registered. | `backend/app/main.py` now checks completed ticket/refund claims against pending-action and tool-execution state, catches unsupported tracking-capability denials, and sends unrecognized business requests to a clarification. Neutral conversation remains unchanged. | `test_untraced_business_claim_guard_blocks_false_state_and_capability_claims` |
| Preserve successful facts on a later failed workflow step | Multi-step response handling previously failed closed with a generic response even when a prior step had returned valid facts. | `grounded_workflow_response` now renders successful structured results and identifies a later failed tool step. If an estimate was requested and every checked item is ineligible, it says no estimate applies. | Added tests for eligibility without estimate applicability and partial failure after eligibility. |
| Clarify a singular unidentified item | V7 app result for “Estimate a return for one unidentified item on ORD-10022” executed eligibility and estimate across both order items. This is a verified planning/scope defect. | Added opt-in `HybridControllerV8Candidate`, which recognizes singular unidentified-item phrases and asks for the item ID before any estimate. V7 source and default configuration are unchanged. | New V8 tests verify the clarification and distinguish estimate from eligibility intent. |
| Tool-required fields | Existing controller code already reads each tool's JSON schema `required` fields rather than imposing one global order-ID requirement. | No change. Existing validation remains the authority. | Existing controller and schema tests pass in the full backend suite. |
| Ticket grounding / approval / idempotency | Existing application boundary keeps ticket proposals pending and requires supervisor approval; the saved V7 app evidence records duplicate approval returning one ticket identity/row. | No approval or authorization logic changed. | Existing approval and duplicate-approval tests pass. |

### Commands and results

- `\.venv\Scripts\python.exe -m pytest backend\tests -q` — 82 passed, one upstream Starlette/AnyIO deprecation warning (rerun after V8 addition).
- `\.venv\Scripts\ruff.exe check backend\app\main.py backend\app\hybrid_controller_v8_candidate.py backend\tests\test_api_workflows.py backend\tests\test_hybrid_controller_v8_candidate.py` — passed.
- V8-specific tests — 2 passed as part of the full suite.

## V7 actual-application failure evidence

Primary artifact: `experiments/results/p2_recovery_v7_dev_application.json`. It records 42 cases, 28 application checks passed, and 14 failed. This is local Ollama/FastAPI execution with synthetic SQLite and the cached `qwen3:1.7b` Q4_K_M digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`.

Failure examples establish multiple first-failing layers:

- **Intent recognition / unsupported free text:** policy questions without the expected keyword and delivery phrasing fell through to model answers; one answer incorrectly said no tracking tool existed. These are verified outcomes in the saved traces. That lexical miss is a root cause for those examples; broader model weakness is a probable contributing factor.
- **Action selection / unsupported state claim:** an eligibility request returned a claim that a support ticket had been created, with no tool execution or pending action. This is a verified unsupported claim and a verified routing failure.
- **Item scope / workflow planning:** a singular unidentified-item request was expanded to both order items; V8 addresses the demonstrated phrase. Multi-step requests also omitted requested eligibility detail or followed a sequence inconsistent with the prompt. These are verified workflow defects.
- **Estimate sequence / answer completeness:** a saved failed estimate case used `calculate_refund_estimate` directly, without a preceding eligibility check. Another estimate case returned the eligibility result but did not explicitly say why no estimate followed for the ineligible item. These are verified behavior gaps.
- **Ticket intent classification:** one grounded ticket request was denied as an unrequested state change; another ticket request remained pending approval. The first is a verified intent miss; approval safety itself remains intact in the observed duplicate-approval check.
- **Evaluation ambiguity:** application checks are internally authored, family-specific checks. A failed check is evidence of mismatch with that check, not an independently adjudicated human label. The recovery suite is exposed development evidence, not a fresh holdout.

The historical saved 64-core offline replay records V7 39/64 (60.9%) versus V6 37/64 (57.8%), a paired +3.125 percentage points; tool selection 21/32, exact arguments 18/28, and one unexpected write proposal. A new diagnostic replay then fed each of the same 64 saved model proposals through V7 and V8: V7 scored 39/64 (60.9%) and V8 scored 41/64 (64.1%), a paired +3.125 points row-weighted and core-weighted. Both arms had one unexpected write proposal. V8's two additional exact actions were the two singular-item clarification cases. Full rows and hashes are in `experiments/results/p2_stage1_v7_v8_exposed_replay.json`; runner: `experiments/evaluation/compare_v7_v8_saved_proposals.py`. The replay executes no tools, and its corpus was already exposed during V5–V7 development; it is a diagnostic only.

## Frozen-artifact integrity

SHA-256 was captured before edits and checked again afterward. These saved artifacts remained byte-identical:

| Artifact | SHA-256 |
|---|---|
| `experiments/results/p2_recovery_v7_dev_application.json` | `a9e57bdfbf3a46a40cd0807c562a84561cd062012da9ecac039fc5335699d8f4` |
| `experiments/results/p2_recovery_v7_dev_comparison.json` | `0d53eef975d5c6eef332a3b6daff30b2c01618337cd902f019548e4c102fc438` |
| `experiments/results/p2_recovery_v7_dev_freeze.json` | `e7c1793b080983db9bfe31c124a93084f19ae640b8341eb1712d197fd39d2ef1` |
| `experiments/datasets/p2_recovery_v2/scenarios.jsonl` | `78c81c272919396a0f56f1f1830fd6f29c683de579277c0c43aae9743dcb2f4f` |

No historical run result or dataset was edited. The repository has no Git commits (`git log -1` reports that `master` has no commits), so a trustworthy baseline tree diff cannot be produced. Integrity evidence is limited to the captured hashes above and the explicit files changed in this pass.

## Routing experiment decision and next action

The fresh routing experiment remains open. Before it can be called the planned controlled comparison, create and hash a new 64-core, 16-family development set, check overlap with existing corpora, record label provenance, freeze V7-plus-fixes and the separately versioned router, then run one raw proposal pass and replay identical proposals through both arms. Run a separate bounded FastAPI slice on fresh synthetic data. Keep those scores separate from historical V5/V7 evidence and do not claim independent review.

The Stage 1 result supports testing a more explicit intent/slot representation, but it does not establish that routing alone is the dominant cause. Verified failures also occur in workflow composition and final-answer grounding. The new V8 heuristic is an opt-in targeted fix, not evidence of broad routing improvement. No controller promotion or overall P2 acceptance change is justified.
