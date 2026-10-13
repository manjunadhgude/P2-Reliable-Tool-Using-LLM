# Review of Qwen's Four-Phase Diagnostic Framework for P2

**Review date:** 2026-10-12  
**Purpose:** Check the supplied framework against P2's project rules and independently recount selected saved metrics.  
**Work performed:** Read-only artifact audit and documentation review. No inference, test run, source change, dataset change, or acceptance-verdict change.

## Assessment

This response is materially closer to the P2 question than Qwen's previous response. Its sequence—resource/contract screening, raw metric audit, failure diagnosis, then a paired native end-to-end comparison—is a useful structure. Its key recommendation to compare on reviewed, identical prompt cores against unchanged V2 is aligned with P2.

It is still a proposed framework, not a completed experiment. It reports no P2 results of its own. The sample table showing values such as 75%, 80%, and 90% is hypothetical and must not be mistaken for P2 measurements. Numbered citations are again provided without bibliography or direct links, so source-based claims cannot be checked from the pasted text.

## Independent recount of existing artifacts

I summed row-level fields from the saved JSON and compared them with the artifact-level metric summaries. The listed counts match:

| Artifact | Recalculated from rows | Saved summary | Result |
|---|---:|---:|---|
| `hybrid_controller_v5_raw_test_final.json` | Exact action 25/150; tool name 19/85 expected named-tool cases; exact arguments 4/75 rows with expected arguments | 25/150; 19/85; 4/75 | Matches |
| `hybrid_controller_v5_hybrid_test_replay_final.json` | Exact action 31/150; correct clarification 6/43; correct handoff 5/11 | 31/150; 6/43; 5/11 | Matches |
| `p2_fresh60_raw_ollama_v1.json` | Exact action 16/60; schema-valid 57/60; tool name 16/36; exact arguments 12/32 | 16/60; 57/60; 16/36; 12/32 | Matches |
| `p2_fresh60_controller_comparison_v1.json` | Paired row exact: raw 16/60, V2 baseline 31/60, candidate 42/60; 60 unique cores | 16/60, 31/60, 42/60; 60 cores | Matches |
| `p2_v5_42_real_application_v1.json` | Application checks passed 26/42 | 26/42 | Matches |

This recount verifies stored arithmetic for these specific artifacts only. It does not validate the semantic correctness or independent review of the gold labels, establish that metrics are sufficient for broad reliability, or turn offline replay into real tool execution. Fresh60 labels were internally authored; V5 contains the previously audited prompt/gold ID conflicts and repeated cores. The V5 42-case app suite is a separate execution and is not a fresh untouched generalization result.

## Corrections and boundaries

### 1. Resource and compatibility failures need distinct statuses

A process timeout means the quality result for that case is unavailable; mark the inference comparison **inconclusive/blocked** and preserve the timeout as an operational result. If a candidate cannot produce/consume the required typed contract or exceeds a predeclared deployment ceiling, it is **infeasible for this operating envelope**, not merely a successful candidate with an inconclusive quality score. Do not relax the bounds after observing results.

The 25-second HTTP and 45-second parent-process limits were used by the latest structured-intent smoke runner; they are pilot ceilings, not proven product SLAs. The older V7/V8 event exceeded a 30-second configured request timeout by a large margin. Measure against a hard process deadline.

### 2. Trace content must remain observable and minimal

The supplied text both prohibits hidden chain-of-thought and elsewhere recommends capturing “reasoning steps,” “complete transcripts,” and the agent's full “decision-making narrative.” These statements conflict. Follow P2's rule: never store hidden chain-of-thought or private deliberation. Capture only useful observable fields: case ID, model/runtime/config identity, parsed intent or action, schema-validation outcome, controller decision and reason code, registered tool and validated arguments, authorization result, tool result, final rendered answer, timings and synthetic final state. Redact sensitive values and preserve only what is needed for diagnosis.

P2 uses synthetic examples; do not import production customer logs or call them a necessary source for this experiment.

### 3. Metric recommendations must stay tied to the decision

Keep task success, raw model/intent quality, offline replay and actual-app results separate. Tool selection/arguments have conditional denominators; exact action can omit semantic final-answer accuracy; offline replay does not measure authorization execution or database writes. Report those limitations beside the metric.

Do not make `pass@k`/`pass^k`, repeated inference, dollar cost, reasoning-coherence scores, LLM-as-judge, or an ideal-path efficiency score mandatory for the first bounded experiment. The local model incurs no per-call API charge in these runs, and repeated inference multiplies hardware use. Add a measure only when it answers a predeclared decision question and fits the pilot budget. The sample scores in Qwen's table are illustrative, not evidence.

### 4. Preserve the valid replay distinctions

The repository already contains saved proposal replayers/comparators for compatible controller contracts (including V7/V8 saved-proposal comparison), actual-app runners, and the structured-intent smoke runner with frozen source/model evidence. Inspect and reuse these before proposing a new generic replay platform.

An identical-prompt paired comparison is valid for native end-to-end V2 vs structured candidate runs if each arm uses its own actual contract, frozen code/config/model, comparable fresh seeded state, and a fixed evaluator. It can determine comparative end-to-end performance on those prompts, but does not by itself isolate model versus planner because the proposal contracts differ. Use separate structured-intent-vs-gold labels and candidate-planner-with-gold-intent diagnostics. Directly feeding `IntentEnvelope` into V2 remains invalid absent a separately frozen, reviewed adapter.

### 5. Sampling and decision rules remain predeclared

Use the established unique-core accounting and row- and core-weighted exact-action scores. Pair by prompt core; uncertainty must respect core as the sampling unit. Independent label review occurs before inference. Unresolved labels are not correct; report their count and exclude them from scored denominators, and mark the comparison inconclusive if reviewed coverage is inadequate. Keep the candidate gate of at least +10 percentage points on both row- and core-weighted development exact-action accuracy, the approximately 90% original targets, and zero unexpected writes/no safety regression. Passing development only authorizes a separately frozen follow-up; it does not establish held-out generalization or change overall P2 acceptance.

## Recommended project-specific use of the four phases

1. **Screen:** limit candidates to those fitting the frozen process/memory budget and safely integrable with P2's strict intent/action contract. Screen all four conceptual approaches on evidence, but only pilot a viable one (at most one alternate local runtime/model).
2. **Audit:** independently recount relevant saved JSON metrics and inspect denominators/metric definitions. Preserve distinctions among raw proposal, replay, app execution and fixture results.
3. **Diagnose:** use observable traces and reviewed gold labels to classify the earliest demonstrated failure stage; allow multiple or unknown causes. Score structured model intent separately and test the candidate planner with gold intent separately.
4. **Compare:** run the leading viable candidate and unchanged V2 natively on the same new, independently reviewed distinct cores, fresh equivalent synthetic state, frozen settings and process deadlines. Report end-to-end pairing without claiming identical proposal replay.

## Conclusion

Qwen's four-phase structure is a useful outline, and the selected arithmetic claims recounted here match their saved JSON summaries. The framework itself did not run an evaluation and supplies no new performance result. Its unsupported citations, hypothetical sample scores, conflicting trace guidance and overbroad metric list must not be treated as project evidence. Overall P2 status remains **PARTIAL**.
