# P2 V4 Controller Reliability Experiment

**Status: PARTIAL.** The opt-in controller candidate improves action routing on the new synthetic sets and passes the established eight-workflow real-application smoke. It does not meet the 90% development target on the final held-out set, does not establish independently reviewed generalization, and does not change P2's original acceptance verdict.

## Executive summary

The V5 evidence still shows weak action selection: raw Qwen3-1.7B exact actions were 25/150 (16.7%); the historical V2 hybrid replay was 31/150 (20.7%); required-slot clarification was 6/43 (14.0%). The hybrid replay was offline and executed no tools. V5 also contains 15 prompt/gold order-ID disagreements (11 test, 4 dev), so its official labels were not repaired or used as if they were correct.

The root cause is mixed: small-model action selection is poor, deterministic routing was brittle to paraphrases and word precedence, ticket arguments were trusted too far, and evaluation labels/metrics obscured some semantic and safety failures. A new opt-in V4 controller addresses the code-backed issues while keeping the default V2 controller and deterministic CI backend unchanged.

On 28 exploratory, distinct-core development prompts with saved local Qwen proposals, the final V4 candidate replay was 27/28 (96.4%) versus V2 baseline replay at 11/28 (39.3%) and raw Qwen at 7/28 (25.0%). It selected the expected tool on 17/18 rows with a tool and matched arguments on 15/16 labeled tool rows. On the separately authored final 18-core holdout, V4 replay was 16/18 (88.9%) versus V2 at 7/18 (38.9%) and raw Qwen at 3/18 (16.7%). V4 selected the expected tool on 10/12 rows with a tool and matched arguments on 9/11 labeled tool rows. The final set is small and its labels are AI-authored, so these are internal engineering measurements, not independent benchmark claims.

The real Ollama model also completed 8/8 established FastAPI workflows using V4: registered order and policy reads, multi-step eligibility, missing-slot clarification, prompt-injection handoff, tenant-scoped denial, and ticket proposal, supervisor approval, and duplicate-approval replay. These eight workflows are executed-task evidence; the 18-case replay is not.

### Backend distinctions

- **Original pinned Transformers Qwen3-1.7B:** previously loaded on CPU but did not produce a complete valid tool-call response within the 90-second limit. This experiment does not change that result.
- **Local Ollama Qwen3-1.7B Q4_K_M:** cached model with digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`; used for every new model-only and actual-app result in this report.
- **`deterministic_test`:** rule-based fixture, still the default for CI. It is not an LLM and is not counted in any real-model score here.

## Failure-to-fix map

| Failure category | Verified cause and evidence | Smallest change and regression evidence | Remaining metric/gap |
|---|---|---|---|
| Missing/conflicting order and item details | V5 dev examples `v5-dev-0001` and `v5-dev-0015` use conflict/missing-order language that V2 did not consistently classify. New prompts `p2-v4-holdout3-007` through `009` cover missing, conflicting, and malformed IDs. | V4 uses parsed request IDs, treats multiple IDs as ambiguous, routes delivery-progress language, and clarifies malformed/missing IDs. Focused controller tests cover these paths. | Final holdout clarification: 4/4. Labels are AI-authored; no broad user-traffic evidence. |
| Eligibility, estimate, policy, and item-listing tool choice | Precedence and lexical overlap in `_intent` caused policy wording to beat eligibility/calculation and allowed `ITEM-####` to match the plain word `item`. A real holdout error (`p2-v4-holdout-001` from the prior exploratory holdout) exposed the identifier-token false positive. | V4 removes order/item IDs before semantic matching, applies calculation/eligibility/policy/listing precedence, and has tests for overlap and ID token parsing. | The first diagnostic holdout had 7/12 tool selections and 4/10 exact arguments; the final holdout is 10/12 and 9/11. |
| Ticket intent and missing details | V5 dev examples `v5-dev-0028` and `v5-dev-0056` proposed descriptions derived from `Reference N.`. A later exploratory case “customer-service case” produced a generic write proposal because the issue extractor treated `customer service` as issue content. | V4 derives summary/description/type from the user's text, strips the synthetic suffix, and clarifies generic ticket requests. Unit regressions cover both synthetic suffix and “customer-service case.” | Final holdout: 1/1 intended proposal grounded; 0 unexpected proposals. Real approval workflow passed; labels remain AI-authored. |
| Routing precedence | V2 routes overlapped phrases by small keyword lists; policy, estimate, eligibility, and list-before-eligibility requests could collide. | Ordered V4 intent rules and multi-step-first patterns; targeted unit tests for policy-vs-calculation and list-before-eligibility. | The final holdout still missed one direct lookup and one invalid model result. No claim of complete semantic parsing. |
| Prompt injection and tenant boundary | The shared security boundary intercepts known bypass/disclosure language before operation routing; authorization remains server-side in domain/tool execution. V5 and prior integration evidence separately show that action replay is not an authorization test. | V4 keeps the existing boundary and server authorization unchanged. New final app run handed off injection and denied the cross-tenant synthetic order; no unauthorized disclosure/write was observed in these cases. | One injection and one tenant case in final smoke; universal safety is not established. |
| Incorrect/invented arguments | Controller V3 accepted model ticket free text even when it was not grounded. General order/item IDs must be request-linked, not supplied by the model alone. | V4 schema-validates ticket arguments, derives free-text fields from request content, and uses user-linked IDs. Final holdout reported 18/18 entity-ID-grounded actions and 1/1 grounded ticket proposal; the executor revalidates as before. | Exact arguments are 9/11; human review and broader adversarial coverage remain needed. |
| Direct answers where tools are needed | Qwen often returns `final_answer` for a clear business operation. On the 18-case final holdout, raw model was 3/18 exact; V2 replay was 7/18. | V4 resolves recognized requests using registered tool contracts. On the 28-case dev replay, V4 was 27/28; on final holdout, 16/18. | Holdout remains below 90%; raw model performance is not repaired by the controller. |
| Evaluator over-credit | Existing action scoring can count an action when expected arguments are null; this does not establish ticket-content validity or task execution. | Historical evaluator/results are unchanged. V4 evaluator reports action-only correctness separately, exact argument metrics where labels exist, schema validity, entity-ID grounding, ticket grounding, unexpected writes, clarifications, handoffs, and explicitly marks execution as unmeasured in offline replay. | Internal labels are AI-authored and not independently reviewed. |
| Misleading labels | V5 generation copied source labels while altering prompt text; forensic audit identified 15 prompt/gold order mismatches. | Official V5 labels and metrics were preserved. New custom sets have separate versioned IDs, explicit cores, and separate manifests. | V5 label disagreements remain; they were not silently fixed. |
| Generalization | V5's development candidate reached 55/60 but proposed two unexpected writes; its overlay was AI-assisted. Final V4 scored 96.4% on its development set and 88.9% on a disjoint 18-core holdout. | Added distinct-core holdouts and stopped tuning after final holdout v3. | Small set, AI-authored labels, 2/18 misses; independent review and a larger untouched task set are needed. |

## Paired action results

These action metrics replay the same saved Qwen proposals through raw, V2, and V4 paths. Replay does not execute tools, authorize access, create tickets, or measure final-answer truth.

| Set | Rows / distinct cores / families | Raw Qwen exact | V2 replay exact | V4 replay exact | V4 tool choice | V4 exact arguments | V4 correct clarification / handoff | V4 unexpected writes | V4 grounded ticket proposals |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Exploratory development | 28 / 28 / 16 | 7/28 (25.0%) | 11/28 (39.3%) | 27/28 (96.4%) | 17/18 (94.4%) | 15/16 (93.8%) | 6/6; 2/2 | 0 | 2/2 |
| Final holdout v3 | 18 / 18 / 17 | 3/18 (16.7%) | 7/18 (38.9%) | 16/18 (88.9%) | 10/12 (83.3%) | 9/11 (81.8%) | 4/4; 1/1 | 0 | 1/1 |

All examples in each V4 set have unique normalized cores, so row-weighted and core-weighted exact-action accuracy are equal: development 96.4% and final holdout 88.9%. There are no repeated cores to inflate either result.

For the same paired proposals, V2 → V4 tool selection was 6/18 → 17/18 on development and 4/12 → 10/12 on the final holdout. Exact labeled arguments were 4/16 → 15/16 on development and 3/11 → 9/11 on the final holdout. These gains describe deterministic controller replay over the same model proposals, not a raw-model improvement.

Per-family counts and paired outcomes are in `experiments/results/p2_v4_real_model_dev_replay_final.json` and `experiments/results/p2_v4_real_model_holdout_final_v2.json`. Additional earlier experiments are retained separately: the first V4 diagnostic holdout was 11/18; the next exploratory holdout was 12/18 but had one generic ticket proposal. That safety miss triggered the ticket-grounding correction; it is not concealed or replaced by the later score.

Final holdout raw Qwen latency was p50 3.09 seconds / p95 3.78 seconds. These values measure one local generation per prompt, not end-to-end application latency.

## Real application-path execution

Artifact: `experiments/results/p2_v4_real_app_integration_final_v3.json`.

- Model: local Ollama `qwen3:1.7b`, Q4_K_M, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`.
- Controller: `hybrid-controller-v4-grounded-ticket-candidate`, explicitly opt-in.
- Result: 8/8 checks passed on fresh synthetic SQLite data; six registered tool events; five model calls recorded by the harness.
- Observed cases: lookup, multi-step items/eligibility, missing order and item clarification, policy result, injection handoff, cross-tenant denial, ticket pending approval and duplicate-approval replay.
- Request latency p50/p95: 2.80 / 5.77 seconds. No ticket existed before approval; repeating approval returned the same ticket; one row was present. This is a bounded fixed workflow subset, not the final 18-case action set executed end to end.

## Changes and reproducibility

- Added `backend/app/hybrid_controller_v4_candidate.py`. It is not the default. `HYBRID_CONTROLLER_VERSION` defaults to `v2`; only `v4_candidate` selects this implementation when Ollama plus hybrid mode is explicitly enabled.
- Added `.env.v4-candidate-real-llm-smoke.example` as the separate opt-in configuration.
- Added controller regressions in `backend/tests/test_hybrid_controller_v3_candidate.py`.
- Added paired metrics in `experiments/evaluation/compare_controller_v4_real_model.py` and an explicit controller-version option to `experiments/evaluation/run_hybrid_real_integration.py`.
- Added internal synthetic datasets under `experiments/datasets/p2_controller_v4_eval`, `p2_controller_v4_holdout_v1`, `p2_controller_v4_holdout_v2`, and `p2_controller_v4_holdout_v3`. Each is distinct-core, with manifests; all annotations are AI-authored, not human-adjudicated.
- Final holdout freeze: `experiments/results/p2_v4_holdout_v3_freeze.json`. Dataset SHA-256: `01d824839a8d0b49726745eb7b2c7ef1858268343301f591ad1b10290380a352`. Model-only output SHA-256: `df628102bfd96c48894643b860d1ee7aa4fb7e2d922f95d6e36ef296f151033d`.
- The V5 scenario SHA remains `e5f6b399494884c347b55c8bf352c570913472be34ebc5ffb52e089ab08adbdf`, matching the V5 manifest. Current hashes of historical V5 raw test, hybrid replay, and review overlay are respectively `d5d5e2471de4d15d0c51d15899dbfe37652e810ada4777a560185d5e608690e3`, `b85f987a1c30261cc7da7d365fe6eef3d2213854a577f9d085542504031b223b`, and `f61a90ac676eb8f703d41c3499ec292e514f4ff9c402b207856ec42881f312f1`. The historical comparison artifact's `overlay.sha256` field contains the dataset SHA (`e5f6…`) rather than the overlay's actual SHA (`f61a…`); this is a pre-existing provenance bug and was not silently edited. No Git commit/history exists in this checkout, so repository-wide before/after proof is unavailable.

## Verification commands and outcomes

- `.\.venv\Scripts\python.exe -m pytest backend/tests -q` — 65 passed, one upstream Starlette/AnyIO deprecation warning.
- `.\.venv\Scripts\python.exe -m ruff check backend/app backend/tests experiments/evaluation/compare_controller_v4_real_model.py experiments/evaluation/run_hybrid_real_integration.py` — passed.
- `npm run build --prefix frontend` — passed.
- V1 dataset, V2, V3, V4, and V5 validators — passed; V5 remains 60 dev / 150 test with zero normalized prompt-core overlap.
- New V4 suite integrity checks — all manifests and SHA-256 values match; 28/28 and 18/18/18 distinct cores; no prompt overlap with V5.
- Fresh SQLite Alembic migration — passed from a temporary database to `0002_turn_budgets (head)`. An initial command from the repository root failed because the Alembic config expects the backend working directory; the corrected command passed.
- Final V4 actual FastAPI/Ollama integration — 8/8 passed. Deterministic CI backend remains the default.

## Remaining work and verdict

1. Obtain independent human review of the custom expected actions and unresolved V5 label disagreements; AI-authored labels cannot substantiate a definitive quality claim.
2. Expand the untouched evaluation denominator and execute broad, predeclared end-to-end cases through FastAPI; current real-app evidence is 8 workflows.
3. Improve the two remaining final-holdout action misses without tuning against that holdout, then freeze another disjoint evaluation before judging the next iteration.
4. Run the original P2 acceptance gates using adjudicated data. Keep V4 opt-in until those gates pass.

**The project remains PARTIAL, not 100% complete.** The final candidate is promising and safer on the measured action set, but its separate holdout exact-action score is 88.9%, its argument score is 81.8%, and independent labels/generalization evidence are absent. The original V5 result remains 25/150 raw and 31/150 hybrid; the new V4 result does not overwrite or replace it.

