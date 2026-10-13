# P2 Claude Research Source Report

**Evidence snapshot:** 2026-10-11  
**Project:** P2 — Reliable Tool-Using LLM for Business Operations  
**Repository:** `C:\Users\manju\OneDrive\DOCUMENTS\ChatGPT\p2`  
**Verdict:** **PARTIAL** — the synthetic application and selected guarded workflows operate, but the original model-quality thresholds and broad end-to-end acceptance are not met.  
**Purpose:** Factual handoff for Claude's external research. This report does not propose an implemented solution and does not claim independent research.

## 1. Executive summary

P2 is a synthetic e-commerce support assistant with six allowlisted business tools. Its default CI backend is a deterministic test fixture, and its default controller version is V2. The real local model path is opt-in. Experimental controller candidates V4–V8 are selected only by explicit configuration; none is the default.

The strongest direct evidence points to several interacting failure classes, not one root cause:

1. **The local Qwen3-1.7B Q4_K_M model often proposes the wrong action or arguments.** On the frozen V5 test, raw exact actions were 25/150 (16.7%), expected tool selection 19/85 (22.4%), exact expected arguments 4/75 (5.3%), and required clarifications 6/43 (14.0%).
2. **Controller routing is sensitive to wording, intent precedence, and missing/ambiguous entities.** V4 and later candidates improved replay substantially on some internally authored sets, but the gains did not reliably translate into real-app task completion. V7 passed 28/42 real-app checks; V8 only added two exact actions on an already exposed replay set and has no fresh end-to-end evaluation.
3. **Evaluation evidence is constrained by label defects and exposure.** V5 has 15 documented prompt/order-ID versus gold-label disagreements (4 dev, 11 test), and many V5 rows repeat only 28 normalized prompt cores per split. Some action metrics award credit without checking ticket content or final-answer truth. Multiple “holdouts” were examined and later used for development.

Other confirmed contributors include incomplete workflow composition and answer grounding, conflation of action-level replay with execution, small internally authored test sets, and ineffective timeout enforcement in one benchmark run. The most recent 130-core V7/V8 evaluation froze its inputs but failed to produce a complete raw-model result: one request recorded 3,102,971.7 ms despite a configured 30-second timeout. No V7/V8 fresh score or actual-app comparison exists.

The repository registry identifies **16 distinct saved trial/evaluation records**. This is not a count of 16 source edits, and it does not validate the user's reported “more than 50 attempts.” The available checkout cannot reconstruct that many distinct attempts. It has no Git commits or reflog; all files appear untracked. Some historical score files, prompts, controller revisions, and logs are missing. The report therefore does not fabricate a 50-row history.

## 2. Project objective and original acceptance requirements

P2's authoritative build scope is `docs/P2_BUILD_SPEC.md`: a modular monolith for **synthetic** e-commerce customer support and order operations, with six tools: order lookup, item listing, return-policy lookup, refund-eligibility check, refund estimate, and support-ticket proposal. The model cannot execute arbitrary code, SQL, shell, or unrestricted HTTP requests.

The repository instructions and acceptance records require strict typed action validation; registered tools only; server-authoritative business logic and tenant authorization; state changes pending until explicit supervisor approval; idempotent ticket execution; bounded model/tool steps and fail-closed behavior; trace redaction; synthetic data only; and clear separation between fixture and real-model evidence. Historical model-quality gates repeatedly use 90% exact action, 90% tool-selection, and 90% exact-argument targets, with higher clarification targets in earlier phases. Exact gate definitions differ by evaluation protocol, so do not treat all historical scores as one metric series. The most recent V7/V8 evaluation prompt explicitly targets 90% action/tool/argument performance and zero unexpected writes/safety regressions.

Passing unit tests or a fixed integration smoke is not sufficient for acceptance. The current acceptance checklist and reports explicitly leave model-quality and broad task-completion gates unmet. The supported current conclusion is **PARTIAL**, not “100% complete.”

## 3. Current verified project status

| Area | Verified state | Evidence boundary |
|---|---|---|
| Application | FastAPI/SQLAlchemy modular monolith, React/TypeScript UI, synthetic SQLite/PostgreSQL options, migrations and seed data. | Build and test results are historical records; not rerun for this read-only audit. |
| Tools | Six registered operations, strict Pydantic schemas, tenant-scoped reads, deterministic eligibility/refund logic. | Code evidence in `backend/app/tools/domain.py` and `backend/app/tools/registry.py`. |
| State changes | Ticket proposal is pending; supervisor/admin approval executes it; stored arguments are revalidated; idempotency key returns existing ticket. | Code in `backend/app/main.py` and `backend/app/tools/domain.py`; bounded replay evidence below. |
| Default runtime | `MODEL_BACKEND=deterministic_test`, `HYBRID_CONTROLLER_ENABLED=false`, `HYBRID_CONTROLLER_VERSION=v2`. | `backend/app/core/config.py`; deterministic backend explicitly says it is not an LLM. |
| Active real app selection | When Ollama and hybrid mode are enabled, main application selects V2 or an explicitly configured V4/V5/V6/V7/V8 candidate. V1 is not in the current selector. | `backend/app/main.py:368-384`. |
| Original pinned Transformers model | Loaded on CPU in an earlier attempt, but no complete valid tool-call response within 90 seconds. | Historical reports; distinct from the later Ollama model result. |
| Local Ollama model | Cached `qwen3:1.7b`, Q4_K_M, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`. | Real inference and app artifacts. No paid API/cloud GPU. |
| Overall quality | Frozen V5, Fresh60, V4 final holdout and latest app checks remain below at least some quality/task thresholds. | See sections 5–6. |
| Fresh V7 vs V8 | BLOCKED/incomplete. No raw result artifact, paired fresh replay, or app comparison. | `docs/P2_FRESH_V7_V8_EVALUATION_REPORT.md`. |

The CI deterministic backend's success is software fixture evidence only. It is not included as real-model accuracy or a real-LLM workflow result.

## 4. Evidence and historical reconstruction methodology

Primary evidence was prioritized in this order: saved JSON/JSONL/CSV artifacts and freeze manifests; current source; test files and saved command records; then reports and progress summaries. Historical summaries are treated as secondary where their referenced artifacts are absent or contradictory.

An existing registry, `experiments/results/p2_trial_registry_v1.json`, describes **16 distinguishable saved evaluation/attempt records** and itself states that this is not a verified total of engineering iterations. It references some missing V5 score files and uses report-only evidence for early experiments. Consequently, the register below consolidates those 16 evidence records into 13 chronological phases; raw/model, replay, and app rows within a single phase are separate endpoints of the same experiment where they used the same frozen inputs. It does **not** imply 13 source changes or 16 independent controller changes. The unique count is a lower bound on retained identifiable records; all other reported iterations are untraceable, not assumed nonexistent.

All retained Ollama results name the same local Qwen digest unless otherwise specified. Most custom labels were internally authored or AI-assisted, not independently adjudicated. A “holdout” examined during development is exposed evidence thereafter. Repeated copies, reports, and derived comparisons are not counted as additional attempts.

## 5. Chronological register of identifiable attempts

Dates are given only when supported by artifacts/reports; early phases have unknown dates. Exact prompt/model hashes for some old runs are absent. “Generalization” means credible previously unseen, independently reviewed evaluation, not merely a dataset called holdout.

| ID / approximate date | Target, hypothesis, actual change | Model/config and input | Before → after; method and what changed | Regressions, generalization, disposition |
|---|---|---|---|---|
| T01 Initial A/B/C (date unknown) | Improve initial action selection via prompt variants A/B/C; exact per-attempt prompt changes partly unrecoverable. | Historical Qwen experiments; 48 validation and 60 locked test rows. Some model/runtime identities unavailable. | Validation exact 0/48 for A/B/C. Test exact A 23/60, B 24/60, C 24/60. C failed its stated +5pp gate. Action-only. | Validity differed markedly (A38/60, B27/60, C55/60); C's validity gain did not improve exact action over B. Test had no task execution. No source-hash chronology. **No satisfactory gain.** |
| T02 QLoRA feasibility (date unknown) | Test whether small-scale fine-tuning improved valid actions. | 1-step smoke then 20-step NF4 QLoRA on train-only data; adapter saved/reloaded; artifact in `experiments/results/p2-lora-20step/`. | Training feasibility demonstrated. Test C remained 24/60 vs B24/60; validation exact remained 0/48. | C used NF4 QLoRA/inference while A/B unquantized FP16, so latency attribution is confounded. Feasibility is not a quality improvement. **Did not meet gate.** |
| T03 CPU Transformers attempt (date unknown) | Make the pinned model usable on the current host. | Pinned Qwen3-1.7B Transformers, CPU. 90-second limit; later token-limit probes. | Loaded on CPU but timed out without a complete valid action at 90 s. A 64-token output truncated; a 256-token smoke once produced valid action. | No practical full workflow benchmark; no generalization. **Runtime blocker remained.** |
| T04 Ollama local runtime integration (2026-10-10) | Use cached quantized GGUF on host instead of CPU Transformers. | Ollama `qwen3:1.7b`, Q4_K_M, digest above; native structured tool calls. | Smoke selected `lookup_order(ORD-10021)` in ~3.31s. FastAPI lookup and ticket proposal/approval/replay succeeded. | A multi-step eligibility attempt safely failed due invalid model item arguments. Small happy-path integration only. **Runtime path established, quality unresolved.** |
| T05 Prompt/metric correction probes (date around 2026-10-10) | Improve prompt response and repair evaluator omission of non-tool actions. | Same local Ollama model; one prompt variant and small 8-case smoke; 48-case diagnostic. | One 8-case prompt probe did not improve. Corrected full validation: 48/48 valid but 0/48 exact in one reported run. | Prior metric version was incomparable because non-tool actions were not properly scored. **No demonstrated gain.** |
| T06 V1 hybrid controller (2026-10-10) | Use deterministic intent/slot/controller rules to correct model proposals and clarify. | V1; 48 validation, 60 locked test; separate 8-case real FastAPI integration. | Offline validation replay 48/48; test replay 43/60, tool and args 31/36, handoffs 12/12. Actual integration 8/8. | Required missing-ticket-order clarification was 0/12 (some ticket proposals lacked order ID). Replay did not execute tools. Fixed 8-workflow smoke is not the 60-row test. **Safety/workflow gap; failed original clarification gate.** |
| T07 V2 controller/runtime iterations (2026-10-10) | Add ticket context, estimate routing and safety/runtime checks. | Qwen3 Ollama; V2 test 140 rows; separate actual app smoke. | Raw 40/140 (28.6%), tools 32/80, args 24/70. V2 replay 96/140 (68.6%), tools 50/80, args 44/70, clarification 28/40. A patched supplemental estimate completed list→eligibility→estimate, `$50.27`, in 27,993ms. | Replay is action-only. 90-second app run 8/8 but 30-second version 7/8 due final synthesis exceeding whole-turn bound. Fixes did not meet 90% thresholds. **Partial, runtime and quality remain.** |
| T08 V3 raw/hybrid and subset (2026-10-10) | Broaden prompts and improve reliability; evaluate same proposals through hybrid. | V3 150 rows; same Qwen digest; 8-case app subset. | Raw 46/150 (30.7%), tools 41/85 (48.2%), args 33/75 (44.0%); V3 replay 100/150 (66.7%), tools 55/85, args 51/75, clarifications 25/43, handoff 11/11. App subset 8/8. | Replay did not execute tools; 40–60-case broad app suite not run. Dataset evolution and repeated templates limit generalization. **Improved action replay, not acceptance.** |
| T09 V4 dataset/holdout rounds (2026-10-10 to 11) | Improve paraphrase routing through ordered intent rules, identifier stripping, clarification, ticket grounding. | V4 internal sets; Ollama Qwen; AI-authored labels. Initial and successive 18-core rounds; one later final 18-core holdout. | Earlier V4 report records 11/18, then 12/18; a generic ticket write in an exploratory set prompted ticket grounding. Final dev: raw 7/28, V2 11/28, V4 27/28. Final holdout v3: raw 3/18, V2 7/18, V4 16/18 (88.9%); tool 10/12, args 9/11. | The rounds were examined and candidate fixes followed their errors; therefore “holdout” is no longer untouched. Small AI-authored sets; final V4 still below 90%, with misses. **Useful diagnostics, weak generalization evidence.** |
| T10 V4 8-case real app (2026-10-11) | Confirm V4 against real app orchestration and approval. | Qwen Ollama, V4 opt-in, fresh synthetic DB; separate from action holdout. | 8/8 fixed workflows; six tool events, five model calls; approval replay and tenant denial exercised. | Does not mean 18 holdout rows or 42 workflows completed. Small, fixed smoke. **Bounded integration success.** |
| T11 Official V5 freeze (2026-10-11) | New paraphrase suite and frozen model/controller evaluation. | 210 rows, 60 dev/150 test; Qwen digest; suite SHA `e5f6b399494884c347b55c8bf352c570913472be34ebc5ffb52e089ab08adbdf`. | Raw dev 10/60; test 25/150, 149/150 valid, tools 19/85, args 4/75, p50/p95 3.36/5.30s. V2 replay 31/150; tools 20/85, args 4/75, clarifications 6/43. | 15 prompt/gold order-ID conflicts; only 28 normalized cores per split; evaluator can credit null ticket arguments without checking content. **Official result remains low/frozen; label defect is not permission to alter it.** |
| T12 V5-named app selection and 42-case run (2026-10-11) | Execute selected support workflows in app; compare V4 actual behavior. | 42 selected V5 test rows / 14 families, but only 22 normalized cores; real Ollama/V4/FastAPI synthetic DB. | 26/42 application checks pass, 16 fail; 32 model calls, 19 tool events (15 success, 2 not-found, 2 pending). Duplicate approval returned same ticket and one row. | This run used the V5 selection but app outcomes are not action score. Three selected multi-step labels have order-ID conflicts. Multiple family failures (0/3 policy, eligibility, estimate). **Actual task evidence, below target and exposed.** |
| T13 Recovery V1/V2, V5/V6/V7, Stage1/V8 (2026-10-11) | Recover on distinct-core internal sets; successive preflight/controller changes and response guard. | Recovery V1 and V2 each 64 cores; same Qwen digest; later actual app slices 42. Stage1 V8 uses saved proposals. | V1 raw 17/64, V2 replay 25/64, V5-candidate 53/64 (+43.75pp); app 34/42. Recovery V2 raw 10/64, baseline V2 18/64, V6 37/64 (+29.69pp); app 28/42; one unexpected write proposal. V7 same V2 recovery set 39/64 (+2 over V6; +3.125pp); app 28/42. Exposed V7/V8 replay 39/64→41/64 (+3.125pp), two singular-item gains, one unexpected write each. | Sets were internally authored and inspected; V1/V2 suites differ, so not direct cross-suite comparisons. Better replay did not improve app V6→V7. No fresh V8 inference/app. **Diagnostic; no promotion.** |
| T14 Fresh60 evaluation (2026-10-11) | Create 60 distinct cores across 15 families and pair raw/V2/V4. | Dataset SHA `cf813327e533e8eb8389a6ddfc5a12846e637abd69689d24c2e9802cd6ab3fa4`; 60 cores, 15 families, internal labels; same model digest. | Raw 16/60, tools 16/36, args 12/32; V2 replay 31/60; V4 replay 42/60 (+18.3pp), tools 27/36, args 23/32, zero unexpected writes. | 90% targets unmet. No independent label review. Separately ran V5 app 42 set (T12); it is not Fresh60 app success. **Development diagnostic.** |
| T15 New V7/V8 fresh evaluation freeze and raw run (2026-10-11) | Test V8 on 130 new cores, 13 families, then paired proposals and actual app. | Dataset SHA `c1f24ba55e7b25f2b97d4997eaeb8089b20d8f8faa3d6c98d174672cd8480ab9`; Qwen digest; V7 SHA `78aad9ad43dcef6e95bcc5c2db7c9356df0027dd31a3074ad5df125ed24696c7`; V8 SHA `6733944f0d95ea9dcaf0995af40a8ef57b6d323e7ceae595f098dd04b2ba16a3`. | Frozen 130 prompts, 26-case app slice, source/config hashes matched after attempt. Raw pass did not complete; no complete artifact, no score, no app run. A call logged 3,102,971.7ms under configured 30s. | Internal labels; lexical overlap screen cannot prove semantic novelty. Report says process stopped; no process-level timeout/checkpoint. **Blocked/incomplete, no fresh V7/V8 conclusion.** |
| T16 Latest application response hardening / Stage1 checks (2026-10-11) | Prevent unsupported completion/capability claims; preserve successful facts after partial workflow failure; clarify singular unidentified item. | `main.py` guard/workflow rendering plus opt-in V8; Stage1 app/test changes, 82 backend test report. | Regression suite reported 82 passed, Ruff passed. V7 app traces motivated fixes; exposed replay V7 39/64 vs V8 41/64. | Tests validate code behavior, not model competence; exposed replay does not exercise new response guard. Fresh integration for these changes not run. **Targeted mitigation, efficacy unproven on unseen app workflows.** |

**Register count:** 16 identifiable records as counted by the retained trial registry. T01–T16 are stable consolidated identifiers for the records/phases above; some are component endpoints and the last stage split is based on saved report boundaries. They must not be read as 16 uniquely hashed source revisions. **Reported attempts beyond these are untraceable** from the current repository. No credible number of distinct source edits can be recovered.

### Chronological lesson

The initial hypothesis was that prompt/model formatting could fix tool calls. A/B/C and QLoRA improved validity or feasibility, but exact test action selection barely changed. Local Ollama then removed the runtime obstacle and enabled genuine integration. V1/V2/V3 hybrid routing improved replay while fixing concrete authorization and workflow gaps; however the controller's literal phrases and intent precedence still missed paraphrases, and replay scores were much higher than raw model scores. V4 addressed ID-token collisions and ticket grounding. Its development score rose sharply, but successive “holdouts” informed more fixes, final small-set performance remained under target, and actual application testing uncovered policy/eligibility/estimate and multi-step misses.

V5 tried broader paraphrased prompts and exposed low transfer. Its generator also preserved some source labels while replacing prompt IDs and repeated a small set of prompt cores. Recovery candidates then obtained large replay gains on internally authored, exposed 64-core suites, but the real app remained 34/42 or 28/42; V7 did not improve its app denominator over V6. V8's two gains address a concrete singular-item scope issue only. Finally the fresh 130-core study froze inputs correctly but was defeated by an unbounded inference call. The cycle gradually repaired examples and runtime paths without a stable, unseen, independently reviewed end-to-end gate. This supports a combined-cause account; it does not prove one intervention would solve the system.

## 6. Numerical history and comparability analysis

### Key scores, kept separate by meaning

| Dataset / split | Model/raw | Controller replay | Real application | Diversity / label status |
|---|---:|---:|---:|---|
| Initial validation/test | A/B/C validation exact 0/48 each; test 23/60, 24/60, 24/60 | — | — | Historical split; exact configs partly absent. |
| V1 locked test | Corrected raw 12/60 exact; 55/60 valid | 43/60; tools 31/36; args 31/36; clarification 0/12 | Separate V1 integration 8/8 | Replay/test artifacts; no tool execution in score. |
| V2 frozen test | 40/140 exact; tools 32/80; args 24/70 | 96/140; tools 50/80; args 44/70; clarification 28/40 | Separate 8-case smoke; one timeout variant 7/8 | Different suite/evaluator history than V1/V3. |
| V3 test | 46/150; tools 41/85; args 33/75 | 100/150; tools 55/85; args 51/75; clarify 25/43; handoff 11/11 | Separate subset 8/8 | Same saved proposals for raw/replay; no execution in replay. |
| V4 dev | 7/28 | V2 11/28; V4 27/28 | — | 28 cores/16 families, internal labels, exposed. |
| V4 final holdout v3 | 3/18 | V2 7/18; V4 16/18; tool 10/12; args 9/11 | Separate V4 app smoke 8/8 | 18 cores/17 families; AI-authored; prior rounds informed tuning. |
| V5 official frozen test | 25/150 (16.7%); tools 19/85; args 4/75; clarifications raw 6/43; valid 149/150 | V2 31/150 (20.7%); tools 20/85; args 4/75; correct clarify 6/43 | V5 named integration artifact 8/8 is actually V2 dataset identity; separate 42-case selection app passed 26/42 | 28 unique normalized cores in test; internal labels; 11 prompt/gold ID mismatches. |
| Fresh60 | 16/60; tools 16/36; args 12/32; valid 57/60 | V2 31/60; V4 42/60; V4 tools 27/36, args 23/32 | V5 selected app 26/42 is separate | 60 distinct cores/15 families, internally authored. |
| Recovery V1 | 17/64 | V2 25/64 → V5 candidate 53/64 (+43.75pp) | 34/42 | 64 cores/16 families; internal/exposed. |
| Recovery V2 | 10/64 | V2 18/64 → V6 37/64 (+29.69pp) → V7 39/64 (V6 +3.125pp) | V6 28/42; V7 28/42 | Same 64 cores for V6/V7; internal/exposed; one unexpected write proposal persisted. |
| V7/V8 exposed replay | Same saved proposals, no raw inference | V7 39/64 vs V8 41/64 (+3.125pp); one unexpected write each | None in this replay | Previously exposed set; two gains are singular-item clarifications. |
| Fresh V7/V8 attempt | No complete raw denominator | Not run | Not run | 130 cores/13 families frozen; internal labels; no complete raw artifact. |

V5 official raw-to-V2 replay exact-action transition has 20 correct in both, 11 raw-wrong/replay-right, 5 raw-right/replay-wrong, and 114 wrong in both: net +6 rows. This is replay's impact on action labels, not proof of task completion. V5 raw exact family outcomes were concentrated in no-tool 11/11, ticket proposal 10/10, item listing 4/11; the apparent ticket 10/10 does not score ticket content when expected arguments are null. In V5 replay, item listing was 15/32 but exact args 4/32; expected read-tool family counts for lookup, eligibility and policy were zero. Metrics have different denominators and must not be collapsed.

### Valid same-input comparisons

| Comparison | What is paired | Valid conclusion |
|---|---|---|
| V3 raw vs V3 hybrid | Same 150 saved proposal IDs | Controller replay changed action-label score 46/150→100/150; no tool execution or final factuality. |
| V4 raw vs V2 vs V4 | Same saved proposals within each V4 dev and holdout dataset | Candidate replay improves exact action/tool/argument counts on those internal sets; sets were small and iteratively exposed. |
| Fresh60 raw vs V2/V4 | Same 60 raw proposals and IDs | V4 replay +18.3pp over V2 on this internal 60-core development set; misses 90% targets. |
| Recovery V1 raw/V2/V5 candidate | Same 64 V1 raw proposals | Candidate gains +43.75pp vs V2 in offline replay; app result is a separate 42-case suite. |
| Recovery V2 V2/V6/V7 | Same 64 raw proposals / same set for V6 and V7 | Replay V7 adds two exact rows vs V6, but V6 and V7 app runs both pass 28/42. |
| Exposed V7/V8 | Same 64 saved proposals | V8 adds two singular-item clarifications; not fresh and does not test V8's new application response guard. |

### Invalid or non-comparable comparisons

| Tempting comparison | Why invalid or limited |
|---|---|
| V1 43/60 vs V2 96/140 vs V3 100/150 | Different datasets, denominators, label sets and controller versions; not a paired progression. |
| V4 27/28 vs V5 31/150 | Different data construction and evaluation; V5 tests paraphrase transfer and includes label defects. |
| 8/8 fixed application smoke vs 42/42 or action-score benchmark | Different selected workflows and success checks; integration smoke is not benchmark coverage. |
| V5 “8/8 integration” vs V5 150 test rows | The V5-named integration artifact carries V2 dataset SHA/metadata and a fixed 8-workflow harness. |
| Offline V4/V5/V6/V7/V8 replay vs app pass rate | Replay invokes no registered tool or database; app tests use a separate case set and execution criteria. |
| Recovery V1 53/64 vs Recovery V2 37/64 | Different 64-core suites; no paired comparison. |
| V7 39/64 vs V8 41/64 as unseen performance | Same already exposed proposals; only diagnostic. |
| Latest fresh V7/V8 as a score | No complete raw artifact; no metric exists. Partial console lines are not a denominator. |

The app evidence shows action improvement does not reliably survive execution: V7 replay improved V6 by 2/64 while V7 app remained 28/42; Fresh60 V4 replay was 42/60 yet the separate selected V5 app run was 26/42 (not paired, so it is a warning, not a causal conversion rate). V5 app family checks were eligibility 0/3, refund estimate 0/3, return policy 0/3, multi-step 1/3. Do not subtract these from replay scores or imply same-case comparison.

## 7. Incident and mishap register

Confidence refers to whether the incident occurred in the named evidence, not whether it is the only cause of broader low performance.

| Incident | Evidence and consequence | Confidence / unresolved status |
|---|---|---|
| V5 prompt/gold order ID mismatch | 4 dev and 11 test multi-step rows ask about `ORD-10022` but gold arguments say `ORD-10021`; generator overwrote prompt text while retaining source labels. The official V5 suite/results were not silently corrected. A counterfactual correcting only the 11 test labels is raw 30/150 and replay 42/150, diagnostic only. | **Verified high.** Official labels remain unresolved; independent review overlay is separate. |
| V5 repeated prompt cores | Removing terminal synthetic `Reference N.` leaves 28 test cores repeated 5–6 times. Generator cycles 14 families and indexes four templates such that only two of four per family are selected. | **Verified high.** Limits diversity/effective evidence; does not prove directional score bias. |
| Disputed tickets `v5-dev-0028`, `v5-dev-0056` | V5 dev overlay/analysis flags ticket labels as disputed; original labels and AI-assisted review overlay differ. The two prompts and `Reference N.` wrapper contribute ambiguity about whether extracted issue text is actual content. | **Verified discrepancy, unresolved label intent.** Never substitute overlay silently for official result. |
| Null expected ticket args / action-only credit | Several ticket-proposal rows have `expected_arguments: null`; exact action can score without verifying summary/description grounding. | **Verified evaluator limitation.** Old result not re-scored here. |
| V4 routing regressions | Earlier V4 rounds missed missing-item clarification and routed to `list_order_items`; ticket without required order context could be handed off instead of clarified; return-policy words such as “returns” / “time limit” were missed; synthetic `Reference N.` could become issue detail. Subsequent fixes were prompted by these examples. | **Verified in V4 report and successive artifacts.** Repeated phrase-list patch pattern remains; round-specific exact counts in the reports. |
| V4 identifier false positive and precedence | `ITEM-####` was matched as ordinary “item”; policy/calculation/eligibility/listing phrases collided. V4 strips IDs before matching and orders estimate/eligibility/policy/list intents. | **Verified source and observed case.** Residual semantic coverage unknown. |
| False ticket-created statement in V7 app | Eligibility prompt returned “A support ticket has been created for supervisor approval”; trace had no tool executions and no pending action. | **Verified direct trace.** Stage1 `guard_untraced_business_claim` added; fresh real-app retest of guard absent. No actual ticket was created in this case. |
| False tracking-capability denial | V7 answer claimed tracking/order status could not be checked despite registered `lookup_order`; no tool execution in the failed row. | **Verified direct trace.** Guard added; broad coverage unresolved. |
| Singular item expanded to all order items | “Estimate a return for one unidentified item…” led to listing and eligibility/estimate operations over both items. | **Verified app trace.** V8 asks for item ID in targeted phrase; fresh inference and app comparison unavailable. |
| Incomplete/wrong multi-step execution | Some app answers stopped after item listing, skipped estimate, skipped eligibility, or omitted ineligible/no-estimate explanation. V7 estimate example directly invoked estimate without eligibility first; another returned eligibility result without explaining no estimate. | **Verified examples.** Stage1 grounded workflow response improves partial-result handling; no broad fresh app evidence. |
| Missing/invalid identifiers and ambiguous requests | Historical V1 0/12 missing ticket-order clarifications; V4 and recovery candidates added missing/conflict/malformed ID checks. Invalid raw action examples and tenant-missing records appear in app data. | **Verified across artifacts.** Rate varies by set; broad robustness not demonstrated. |
| Incorrect policy/eligibility/estimate routing | V5 42-app: 0/3 policy, 0/3 eligibility, 0/3 estimate; V7 app includes policy miss and estimate sequence errors. | **Verified samples.** Rules/routing errors and model choice can both contribute; not isolated. |
| Ticket text incomplete or placeholder-derived | V5 dev tickets include descriptions inferred from synthetic `Reference N.`; V4 issue extractor once treated generic “customer-service case” phrase as issue; V4 now strips synthetic suffix and grounds fields from user text. | **Verified prior examples.** No current broad independent adjudication of ticket content. |
| Unexpected state-changing proposals | Recovery V2 V6 and V7 offline replay each recorded one unexpected write proposal. Offline replay did not execute it. | **Verified proposal-level, not actual write.** Investigate candidate-level behavior; do not report as unauthorized write execution. |
| Actual unauthorized write/data disclosure | Covered app runs report no unauthorized ticket write, duplicate row, or cross-tenant disclosure in covered cases; V7 duplicate approval passed. A V5 cross-tenant failed check involved no tool call and no data disclosure. | **No incident evidenced in these samples.** This is not universal assurance. |
| Holdout reuse / exposure | V4 successive “holdout” rounds were scored, then motivated controller changes; recovery and V7/V8 sets were repeatedly inspected. | **Verified by chronology/report.** They are development diagnostics, not unseen final evidence. |
| AI/internal labels called independent | Fresh60, V4 sets, recovery, and V7/V8 prompts are internally/AI-authored; no independent human review recorded. | **Verified provenance limitation.** Label uncertainty remains. |
| V5 V5-app identity mismatch | `hybrid_controller_v5_real_integration_subset.json` reports V2 dataset identity/SHA and a fixed workflow harness. A different V5 selection run is 42 cases/26 pass. | **Verified.** The 8/8 cannot be represented as V5 test or 42-case success. |
| Overlay hash field wrong | Historical V5 comparison `overlay.sha256` contains dataset SHA `e5f6…` rather than overlay actual SHA `f61a90ac676eb8f703d41c3499ec292e514f4ff9c402b207856ec42881f312f1`. | **Verified in V4 report/artifact inspection.** Pre-existing provenance defect; not edited. |
| Source changes after freezes | Some historical `main.py` and evaluation harness changes occurred after earlier freeze artifacts, as reports explicitly note; fresh V7/V8 freeze rechecked all declared hashes after its attempt. | **Verified for named freeze sequences, but no full old before/after repository tree.** This affects provenance. |
| Early V3/V5 hash conflicts | Older reports cite V3 `2b599e…` and initial V5 `1cde0a…`; current retained manifests use V3 `5b636b…` and corrected V5 `e5f6…`. Older byte versions absent. | **Verified discrepancy; cause not recoverable.** Do not harmonize by assumption. |
| Timeout failure | Fresh V7/V8 request logged 3,102,971.7ms although configured 30 sec; no final `p2_fresh_v7_v8_raw.json`. The run was stopped per report, and partial console rows were not scored. | **Verified from run report.** OS/process kill evidence is not retained, so safe termination mechanics cannot be independently audited. Requires process-level deadline/checkpointing in any future separately approved run. |
| Test/build status count drift | Progress/checklist contains historical backend counts of 17, 44, 46, 65, 68, 79, 82 as development stages advanced; not contradictory when dated, but old summaries sometimes state counts without matching artifact/current tree. Docker Compose was successful in one historical phase and unavailable/unverified later. | **Historical outcomes, not current reruns.** No single “current all checks pass” claim from this audit. |
| No Git history | `git log -1` reports current branch has no commits; `git status --short` lists project content as untracked. | **Verified.** Cannot prove full project ancestry, reconstruct overwritten versions, or independently diff a baseline. |

## 8. Current architecture and controller-selection behavior

### Actual request lifecycle

1. **Authenticate and scope the conversation.** `backend/app/main.py:358-365` verifies conversation tenant and user, writes user message/turn. User identity and tenant come from server auth dependencies.
2. **Select backend/controller.** `backend/app/core/config.py` defaults to deterministic fixture, hybrid disabled, V2. In hybrid mode the dispatcher at `main.py:368-384` allows V2 and opt-in V4–V8. `hybrid_controller_v1` described in old docs is not an active branch in current selection.
3. **Preflight then model proposal.** `main.py:399-415`: controller preflight can decide without model call; otherwise `backend().act(...)`, strict `validate_action`, then controller `apply`. Without hybrid, model action is validated directly (`main.py:418-427`).
4. **Validate tool and arguments.** Action envelope goes through `validate_action`; selected tool arguments are checked against `ARGUMENT_SCHEMAS` (`main.py:463-467`). `StrictArgs` and tool-specific Pydantic models forbid extra fields (`backend/app/tools/domain.py:15-36`). Unknown tool/action fails closed.
5. **Authorize and execute registered tool.** `execute_for_turn` (main.py around 326 onward) checks registry/role/tenant context, records validation, authorization, status and redacted result. `TOOL_REGISTRY` defines six names, required roles, risk, side effects, and ticket approval/idempotency metadata (`backend/app/tools/registry.py:20-27`). Domain rules/database are authoritative (`domain.py:72-122`).
6. **Compose multi-step operation.** `main.py:470-492` starts from a successful item listing, then uses controller follow-up tool lists or hard-coded phrase checks to run eligibility and potentially estimate. This layer makes a separate intent/workflow decision, and the V5 follow-up list differs from non-V5 keyword handling. Estimate is only called for items returned eligible by the prior tool. This protects calculations but creates duplicate orchestration/routing logic.
7. **Generate final answer.** `grounded_tool_response` (`main.py:66-88`) renders direct reads from results. `grounded_workflow_response` (`91-165`) renders successful steps and partial failure. If no safe renderer applies, the app can ask the model to synthesize from explicitly marked untrusted tool JSON; `guard_untraced_business_claim` (`168-190`) blocks unsupported completion claims and false tracking denial. The model's prose is not authoritative proof of execution.
8. **Approval.** Ticket action produces pending state; supervisor/admin endpoint at `main.py:622-636` tenant-scopes pending action and returns prior completed result on replay. `create_ticket_after_approval` (`domain.py:125-139`) revalidates arguments and checks idempotency before inserting a ticket.
9. **Trace/evaluation.** Controller decisions, tool executions and audit events are saved without hidden reasoning. Offline evaluator replay evaluates action projections only. App runners inspect actual traces and state. Deterministic tests are separate fixture evidence.

### Responsibilities and ambiguity

The LLM proposes one typed action and may synthesize an answer. Deterministic controllers classify intent, resolve grounded IDs, clarify, and sometimes override model proposals. Tool schemas validate structure; registry authorizes tool availability/role; domain and database enforce business/tenant rules; workflow orchestration sequences list→eligibility→estimate; response templates/guards ground or reject unsupported prose. These layers overlap: base V2 intent matching, controller candidate overrides, main.py keyword triggers, controller follow-up tools and answer guard can each make a decision about the same workflow. A correct tool action can still be incomplete at workflow level; a final answer can be factually unsupported if a guard pattern misses it.

The base controller `backend/app/hybrid_controller.py:27-55,254-300` uses phrase matching and schema-derived required fields. V4 (`hybrid_controller_v4_candidate.py:18-90`) strips order/item IDs before matching and gives estimate/eligibility/policy/listing precedence, but remains a phrase/regex router. V5 derives multi-step follow-up tools. V6/V7 add intent/workflow preflight. V8 adds a narrow singular unidentified-item intent. Candidates inherit earlier logic, so behavior and precedence accumulate rather than reside in one declarative workflow model.

### Tool and backend specifics

`backend/app/llm/backends.py:23-58` marks deterministic fixture as non-LLM and selects Transformers/Ollama by config. Transformers adapter uses `max_time` but that is not a guaranteed OS-level process kill (`75-143`). Ollama adapter uses local HTTP and structured tool calls elsewhere in the file. Tool result wrapper (`8-11`) explicitly marks returned values untrusted. No paid API or external financial action was used in cited evidence.

### Material excerpt: business logic is not model authority

`domain.py:93-107` computes eligibility from seeded delivery state/date and refuses refund estimates for ineligible items; `domain.py:125-139` revalidates ticket arguments and checks the idempotency key before insertion. That separation worked in covered examples. The recurring problem is reaching the correct, complete sequence and accurately describing its result.

## 9. Detailed latest application failure analysis

The latest detailed V7 app artifact is `experiments/results/p2_recovery_v7_dev_application.json`: 42 cases, 28 pass/14 fail, local Qwen3-1.7B Q4_K_M, FastAPI, fresh synthetic SQLite, V7 opt-in. It records model metadata and per-row request text, action/controller decisions, calls, tool executions, final answer and check outcomes. The data is internally authored and already exposed.

Verified examples include:

- `p2-recovery-v2-eligibility-01`: request asks whether `ITEM-2201` on `ORD-10022` is returnable. Model answered with details and said a support ticket was created for approval. Trace has no tool events and `pending_action: null`. This is an unsupported statement, not an actual write.
- Missing/specific-item requests could list and operate on all items rather than ask which one. V8's exposed replay gain is limited to two such clarification examples.
- Some estimate traces call estimate without eligibility first; some multi-step answers omit eligibility or estimate result. Orchestration tries to impose the sequence, but phrase detection and requested item scope still matter.
- Policy wording absent from the heuristic vocabulary can yield unsupported free-text or a false “no tracking” capability statement, despite `lookup_order` being registered.
- One ticket request was wrongly denied; a separate proposal case remained correctly pending approval.
- Malformed order IDs and conflicting IDs are clarified in some candidate paths; that does not imply all paraphrases or follow-ups work.

No actual unauthorized write or cross-tenant disclosure is shown in the cited V7 app traces. Duplicate approval returned the same ticket ID and exactly one database row. These statements apply only to the tested sample.

The Stage1 change added a server response guard and safer grounded workflow renderer; it reported 82 backend tests and Ruff pass. The fresh V7/V8 freeze evaluation did not complete and its planned 26-case app comparison never started, so these mitigations lack fresh real-model end-to-end efficacy evidence.

## 10. Root-cause analysis and counterevidence

Confidence: **High** = direct source/artifact evidence for mechanism/outcome; **Medium** = several consistent observations but competing causes; **Low** = plausible, insufficiently isolated.

| Rank / hypothesis | Evidence and failures it explains | Counterevidence / limits | Confidence; what distinguishes it |
|---|---|---|---|
| 1. Intent/workflow/slot routing is brittle | Literal vocabularies and explicit precedence in base/V4 controllers; V5 app 0/3 policy/eligibility/estimate; V7 policy/lookup/ticket/estimate misses; V4 regressions on missing item, `returns`/`time limit`, synthetic references. | V4 reaches 16/18 on one small final set; several failures are raw-model direct-answer or incomplete-synthesis rather than pure router behavior. | **High for observed code/rows, medium-high as broad contributor.** Same saved proposals through a narrowly changed router on a preregistered diverse set plus real app execution can isolate routing. |
| 2. Raw model action quality is poor | V5 25/150, 4/75 args; Fresh60 16/60; V4 final holdout raw 3/18; recovery raw 10–17/64. | Controller overrides sometimes produce high scores; local model completes some workflows quickly. No model-size controlled experiment isolates capability. | **High for observed scores, medium for model capacity as root cause.** Compare models under identical prompt/schema/data/runtime on a frozen suite and actual app. |
| 3. Evaluation/labels hide or distort quality | V5 ID mismatch; repeated cores; null ticket expected args; action-only scoring doesn't test factual answer or execution; V5 app identity mismatch; bad overlay hash field. | Separate app checks and later distinct-core suites reveal genuine failures even aside from label defects. | **High.** Independent adjudication, reviewed overlay, core-weighted metrics and trace-based task completion. |
| 4. Overfitted routing / model-controller conflict | V4 fixes followed exposed errors; V7 preflight can replace a model answer; V8 two gains are exact phrase-targeted; V6/V7 replay one unexpected write proposal. | Deterministic override sometimes improves same-proposal outcomes; no evidence every override harmful. | **Medium.** Record raw decision, controller decision and downstream result; paired ablation of predeclared routing rules. |
| 5. Workflow orchestration and final response overlap | Main.py independently detects list→eligibility→estimate; V5 controller has follow_up_tools; grounded renderers handle partial failures, but legacy synthesis path remains. Observed omitted stages and answers. | Stage1 renderer/guard added; covered regression tests pass. | **High for design overlap, medium for score contribution.** Execute identical workflows with explicit step/result state trace and fault injection; compare final-answer assertions. |
| 6. Small/repeated data and exposure exaggerate gains | V5 150 rows only 28 cores; V4 successive holdouts used for fixes; 64-core recovery repeatedly inspected; V7/V8 set exposed. | Fresh60 and frozen 130-core dataset are more diverse; the latter never completed inference. | **High as evidence limitation; uncertain score inflation direction.** New independently reviewed cores frozen once; exact/core-weighted uncertainty. |
| 7. Runtime/timeout makes evidence incomplete | CPU Transformers 90s timeout; V2 synthesis 30s vs 90s differences; latest 30s call logged ~51.7min; no raw artifact. | Ollama prior runs completed at 3–8s typical p50/p95 in smaller controlled tasks. | **High for specific failures, medium as general system cause.** Enforce OS process deadline, request cancellation, checkpoint rows, test timeout semantics. |
| 8. Ticket argument grounding and unsupported claims | V5 dev ticket placeholders; V7 false ticket-created response with no pending action; V4 change grounds ticket text; Stage1 guard. | Ticket approval/idempotency worked in covered app tests; no real false write happened in cited row. | **High for observed content/control defect.** Human review of ticket fields and trace-conditioned answer validation. |

Do not conclude “the model alone is responsible.” The raw model is weak on action selection; controller rules can repair and can misroute; workflow orchestration is a second decision system; data/scoring create uncertainty; and app-level completion has separate failures. The repository does not contain a controlled experiment that apportions percentages of the final miss rate to these causes.

## 11. Why previous approaches did not converge

The recurring engineering pattern was to inspect a failure, add a phrase/slot rule or renderer, and rescore a small or already seen set. Each step could produce local gains, but often changed several interacting behaviors at once. A controller that overrides more model outputs can increase exact action matching while changing clarification, tool sequence, or actual app outcomes. There was not one stable task-success endpoint across all rounds.

Specific mechanisms:

- **Action-match optimization was easier than task success.** A correct action label can have bad arguments, missing steps, a false final answer, or no actual tool execution. V5's null expected ticket fields amplify this mismatch.
- **Known phrasing became controller rules.** Literal and regex rules solve targeted examples but cannot prove semantic coverage. Precedence changes can repair one family and shadow another, as V4 regression rounds show.
- **Sets were small or reused.** V4 “holdout” rounds influenced subsequent fixes, recovery suites were inspected repeatedly, and V7/V8's +2/64 result is explicitly exposed. No 50+ chronological source diff exists to audit overfitting attempt by attempt.
- **Labels and prompt construction were not always aligned.** V5 ID conflicts mean the “correct” answer is wrong for some prompt text; repeated cores overstate independent language variation; AI-written labels may encode author assumptions.
- **Application and benchmark evidence were separate.** Large replay gains did not reliably change 42-case app completion. Fixed 8/8 smoke tested carefully selected workflows rather than broad benchmark distributions.
- **Runtime was not consistently bounded.** A configured timeout did not bound the latest inference call; partial output was correctly excluded from metrics, but the experiment could not answer its question.

This is a supported synthesis of multiple observations, not proof that any one factor caused a specified number of failures. A decisive research design should change one layer at a time on paired, reviewed examples and retain both action and execution-level measures.

## 12. Experiment and evaluation reliability analysis

### Frozen V5 and historical provenance

Current V5 suite and current artifacts agree on SHA `e5f6b399494884c347b55c8bf352c570913472be34ebc5ffb52e089ab08adbdf`. Older text cites an initial V5 SHA `1cde0a…`; bytes are not retained. Older V3 references cite `2b599e…`, whereas current files use `5b636b…`; older bytes are unavailable. The V5 review overlay actual hash is `f61a90ac676eb8f703d41c3499ec292e514f4ff9c402b207856ec42881f312f1`, but the comparison artifact stores dataset SHA in its overlay hash slot. Historical rows/results were to remain unchanged.

The V5 generation/validation logic checks normalized text overlap but does not semantically verify entity references against expected arguments. Its terminal `Reference N.` suffix masked repeated cores in earlier normalization. These are independent evaluator/data-quality defects.

### Exposed holdouts and labels

V4's first/second/final 18-core rounds were used to guide fixes, including a generic ticket proposal. They are chronological diagnostics but not clean untouched holdouts. Recovery and exposed V7/V8 data likewise cannot substantiate generalization. Fresh60 and fresh V7/V8 use internal labels. There is a separate V5 review overlay for adjudicated scoring, but it is AI-assisted and conflicts on ticket cases; it is not independent human review. Do not correct official labels silently or treat unresolved labels as correct.

### Metrics and execution

Raw action evaluation measures parsed model proposal; offline replay applies controller to saved proposals; actual app runs tool validation, authorization, DB/business logic, workflow steps, approval, and final answer. These answer different questions. V5 raw exact-action score does not verify no-tool answer factuality; ticket fields may be absent from label; replay doesn't execute a tool. Fresh60 app failures and V7 trace examples reveal failure categories that action-only metric misses.

### Timeout and partial output

Latest fresh runner configured 30 seconds but recorded a 3,102,971.7ms call, and stopped before writing complete JSON. Partial console output was not promoted to a score; app comparison was not started. The saved report says process was stopped, but shell/process termination evidence is absent. Any follow-on needs an independently enforced process-level wall-clock deadline and incremental, durable row checkpoints, then a new freeze. Do not reuse the old partial output as a result.

### Test and environment provenance

Historical backend test counts vary as the project changed (17, 44, 46, 65, 68, 79, 82). They are dated stage results, not one contradictory measurement. Ruff/frontend/migration/Playwright have historical pass records. Docker Compose passed in one phase and was later not verified because the Docker engine was unavailable; do not claim current Docker readiness. This report did not rerun tests because its scope is read-only forensic source preparation.

### Same-input vs cross-set uncertainty

Paired raw-vs-controller comparisons on exact IDs are interpretable as replay effects for that set. Cross-dataset score progression is not. Most internal custom labels lack independent review and even a paired test can be invalid if labels conflict. There are not enough independent, adjudicated cores to support a definitive generalization claim. No uncertainty interval for a fresh V7/V8 gain exists because that experiment did not produce results.

## 13. Existing safeguards and invariants

- Only six registered tools are available; registry metadata declares state effects, roles, and ticket approval/idempotency requirements.
- Strict Pydantic schemas reject unknown fields and malformed arguments; action validation rejects unsupported action/tool forms.
- Business calculations and return eligibility are deterministic and server-side. The model does not decide tenant access or authorize a ticket.
- Conversation/order access is tenant-scoped in application/domain code; a model-supplied identifier alone does not grant access.
- Ticket proposals remain pending until supervisor/admin approval; stored ticket arguments are revalidated; idempotency prevents duplicate insertion. Multiple app runs show replay returning the same ticket ID and one row.
- Tool results are wrapped as untrusted data for model synthesis; hidden chain-of-thought is not stored. Traces redact sensitive values and record controller/tool outcomes.
- Step/tool/time/token/retry budgets exist. However the latest timeout observation means configured request timeout alone is not an adequate process-level bound.
- Deterministic test backend remains explicitly identified and is not counted as real-model evidence.
- Synthetic data only; no customer/payment integrations or paid/cloud inference in described experiments.

These controls are evidenced for tested cases, not a certification of universal security or production readiness.

## 14. Unresolved evidence gaps

1. No Git commits, reflog, or trusted initial tree: source ancestry, overwritten code, and complete timeline cannot be reconstructed. Current `git status` is all untracked.
2. More than 50 reported attempts cannot be uniquely enumerated. Exact prompts, commands, source diffs, configs, dates and outputs for many alleged attempts are absent. Registry contains 16 distinguishable records only.
3. Early A/B/C and original V1/V2 artifacts lack some exact source, prompt, evaluator, model-revision and dataset hashes. Some headline scores rely on reports because named raw result files are missing.
4. Initial V3/V5 hashes cited in old docs cannot be reconstructed from current bytes.
5. V5 15 prompt/gold ID conflicts and two disputed ticket examples need independent review. The AI-assisted overlay is not independent adjudication.
6. No independent human labels for Fresh60, V4, recovery or fresh V7/V8 sets; semantic novelty is not proven by lexical overlap screening.
7. V5 42-case application checks have 22 unique cores; V7/recovery app checks use selected and exposed cases. They do not establish broad unseen completion.
8. Latest raw V7/V8 run lacks complete output, per-row durable checkpoints, verified process-kill evidence, and actual app execution. No score should be imputed.
9. V5 fixed “8/8” application result has V2 dataset identity, so no V5 row-level join exists.
10. Hash mismatch in overlay field, historical main.py changes after older freeze, and absent old source snapshots make some freezes incomplete as whole-repository provenance.
11. No controlled model-size/runtime comparison isolates small-model capability; no empirical basis for claiming a larger model would meet the targets on this hardware.
12. Generalized security assurance, business-user acceptance and production readiness are not established.

## 15. Research questions for Claude

Claude should conduct external research and cite primary sources directly. The following questions tie research categories to verified P2 evidence; they are questions, not conclusions.

| Research area / question | P2 connection |
|---|---|
| How do experienced teams handle tool-routing failures in small local models without brittle keywords? | Qwen raw V5 25/150; V4 phrase/precedence regressions; V7 app tool-routing misses. |
| When should routing be deterministic, model-based, or hybrid? How can override policy avoid blocking a correct model action? | V4 replay gains coexist with regressions; V6/V7 unexpected write proposals and app mismatch. |
| What schema-constrained generation and recovery methods improve valid calls while preserving strict fail-closed validation? | Invalid raw actions, five corrected V1 test failures, one V5 invalid action; generation repair is bounded but quality remains low. |
| How do production agents guarantee final answers reflect successful tool results? | V7 false ticket-created claim with no pending action; false tracking denial; multi-step omissions. |
| How should stateful workflows handle partial failure, missing entities, ambiguous IDs and dependencies? | Singular item expanded to all items; eligibility/estimate sequencing and partial-result failures. |
| How should tool-using systems be evaluated when action exactness conflicts with task completion? | V5 action replay 31/150 vs separate 42-case app 26/42; null ticket fields and no final factuality scoring. |
| How to detect benchmark leakage, repeated prompt cores and noisy labels? | V5 28 cores/150 rows; ID mismatch; V4 holdouts exposed; AI-assisted ticket overlay. |
| How should paired studies estimate uncertainty and decide whether +2/64 is meaningful? | Exposed V7/V8 +3.125pp on same 64 proposals, no fresh score or independent labels. |
| What model capability is realistic for P2, and is Qwen3-1.7B sensible under the hardware budget? | Model's low exact-action/argument scores; local runtime works, Transformers CPU timed out; no controlled size comparison. |
| Which established benchmark/task-completion evaluations resemble P2's six-tool, safety-gated workflows? | P2 needs both routing and actual execution/approval/tenant boundaries, not tool-name match alone. |
| What experiment distinguishes model weakness from controller, architecture, labels, and runtime effects? | Existing comparisons bundle layers and datasets; timeout prevented latest fresh comparison. |
| What is the smallest scientifically defensible next experiment? | Must be fresh, independently reviewed, paired, safely bounded and measure both actions and real app traces without touching V5 test. |

Claude should specifically answer:

1. How do experienced teams handle tool-routing failures in small local models without brittle keyword systems?
2. When should routing be deterministic, model-based, or hybrid?
3. How do production agents guarantee final answers reflect actual tool results?
4. How should multi-step workflows handle partial failure, missing entities, and dependencies between tools?
5. How do researchers evaluate agents when action scores conflict with task completion?
6. How can benchmark overfitting be detected and credible generalization established?
7. What model capability is realistically required, and is Qwen3-1.7B sensible given the hardware constraints?
8. What experiment conclusively separates model weakness from controller and architecture weakness?
9. Which established approaches apply to P2 and what evidence supports them?
10. What is the smallest scientifically defensible next experiment?

Research should address practical memory/latency/runtime limits, process-level deadlines, tool-call reliability, typed intent/workflow state, final-answer grounding, evaluation validity, paired confidence intervals, and safety invariants. Do not assume that a model upgrade alone will fix task completion.

## 16. Priority-ordered handoff brief

1. **Treat P2 as PARTIAL.** Keep V2/default fixture behavior and candidate opt-in status; no version has met broad original acceptance.
2. **Preserve and audit labels.** Do not edit official V5 test. Independently review prompt/entity/gold alignment, especially 15 ID mismatches and `v5-dev-0028`/`v5-dev-0056`, with a separate explicit overlay.
3. **Separate layers.** For every failure retain raw model proposal, controller decision/reason, validated action, tool authorization/execution, every workflow step, pending/approved state, and final-answer grounding.
4. **Avoid phrase-list growth as an untested fix.** Research an explicit typed routing/workflow design and compare it to baseline with same proposals and independent labels before implementation is selected.
5. **Make the next evidence credible.** Freeze a distinct-core, independently reviewed set and evaluator; report row/core metrics and per-family results; use paired uncertainty; then run a separately selected fresh synthetic app slice.
6. **Bound runtime before inference.** Enforce process-level hard deadline and checkpoint each result row. Stop if the model cannot reliably complete bounded runs on current hardware.
7. **Keep safety and scope.** Synthetic data only; six registered tools; strict schemas; tenant authorization and business rules server-side; ticket approval/idempotency unchanged; no cloud spend or external integrations.
8. **Do not treat the incomplete fresh V7/V8 run as evidence.** No raw score, paired replay, or app result exists. Exposed +2/64 remains diagnostic only.

### Source map for Claude

The report is designed to be self-contained, but these primary artifacts are the best verification trail if access is available:

- Specs/status: `docs/P2_BUILD_SPEC.md`, `docs/ACCEPTANCE_CHECKLIST.md`, `docs/PROGRESS.md`.
- Historical synthesis: `docs/P2_ROOT_CAUSE_FORENSIC_AUDIT.md`, `docs/P2_LONGITUDINAL_ROOT_CAUSE_REPORT.md`, `docs/P2_FINAL_RECOVERY_REPORT.md`.
- V4/V5/Fresh60: `docs/P2_CONTROLLER_V4_EXPERIMENT_REPORT.md`, `docs/V5_FINAL_EVALUATION_REPORT.md`, `docs/P2_FRESH60_AND_42CASE_EVALUATION_REPORT.md`.
- V7/V8: `docs/P2_STAGE1_AND_ROUTING_EXPERIMENT_REPORT.md`, `docs/P2_FRESH_V7_V8_EVALUATION_REPORT.md`.
- Saved trial registry and detailed rows: `experiments/results/p2_trial_registry_v1.json`, `p2_recovery_v7_dev_application.json`, `p2_v5_42_real_application_v1.json`, `p2_fresh60_raw_ollama_v1.json`, `p2_fresh60_controller_comparison_v1.json`, `p2_stage1_v7_v8_exposed_replay.json`, `p2_fresh_v7_v8_freeze.json`.
- Current code references: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/hybrid_controller.py`, `backend/app/hybrid_controller_v4_candidate.py` through `v8_candidate.py`, `backend/app/tools/domain.py`, `backend/app/tools/registry.py`, `backend/app/llm/backends.py`.

**Report limitation:** This handoff consolidates available artifacts and identifies evidence gaps; it cannot reconstruct absent historical runs or replace independent review. No external citations are included because Claude is being asked to perform that research.
