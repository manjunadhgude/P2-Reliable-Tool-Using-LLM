# Review of Qwen's Experimental Framework for P2

**Review date:** 2026-10-12  
**Scope:** Project-specific methodology review of the supplied “Diagnosing Systemic Failures” framework. No code, data, model settings, evaluation results, or acceptance status were changed.

## Assessment

The framework has useful principles for P2: bound each inference at the process level; freeze inputs and evaluators; adjudicate labels before inference; separate offline, human-reviewed and actual-app outcomes; use fresh synthetic state; and report inconclusive results honestly. These fit the project's constraints.

It should not be followed verbatim. Some proposed methods would create invalid comparisons or overstate what measurements establish.

## Project-specific corrections

### 1. Direct paired replay across current controller interfaces is invalid

The framework proposes taking the structured-intent model output and feeding it into V2 as the same proposal. In P2, the structured candidate consumes a strict `IntentEnvelope` (`intent`, candidate IDs, requested outputs, etc.); its planner then creates a registered-tool action. The existing V2 path consumes the user request through its own action/controller flow. These are different interfaces and semantic stages. Passing an `IntentEnvelope` directly to V2 is not a valid replay, and a hand-written conversion adapter could introduce another source of error.

Valid alternatives:

- **Intent/model quality:** Score the frozen structured-intent output against independently adjudicated intent and slot labels. Report separately from application actions.
- **Candidate planner quality:** Supply the adjudicated gold `IntentEnvelope` to the candidate planner offline. This estimates planner behavior given correct intent; it does not measure model quality or compare V2.
- **V2 vs candidate application comparison:** Run each native system on the same frozen prompt cores and comparable fresh seeded databases. Pair by core ID and compare task outcomes. Proposals need not be identical because the architectures consume different representations; call this an end-to-end comparison, not an isolated controller test.
- **Cross-controller replay, only if needed:** Specify and freeze a shared intermediate contract and a separately tested deterministic adapter for each controller. Report conversion failures separately. Do not call it identical-proposal replay unless the serialized proposal is actually identical and accepted natively by both arms.

### 2. The error-attribution table overclaims causality

“Live run failed / replay succeeded” does not by itself prove a controller-routing failure; differences may come from app state, tool execution, renderer, approval state or replay harness. “Both failed” does not prove a model proposal error; a later stage may have failed despite a correct proposal. Attribute the **first demonstrably incorrect stage** from the saved trace, and allow “unknown/multiple causes.” A counterfactual replay supports a causal claim only when its inputs, environment and contract are controlled.

Classify failures separately as schema/parse; intent/slot mismatch; planner decision mismatch; registered-tool validation/authorization; tool/domain result; final-answer grounding; timeout/resource; and label ambiguity.

### 3. Keep the first experiment small

The supplied proposal adds TTFT, inter-token latency, tokens/second, KV cache estimates, CPU utilization, multiple trials, semantic similarity, LLM-as-judge, weighted scoring and broad quality rubrics. Most are not needed to choose P2's next step. For a first CPU feasibility comparison, record model load time, end-to-end inference latency, memory if reliably available, completion/schema-valid rate and adjudicated task/action quality. Do not install another runtime or model solely to collect secondary metrics.

Use one warm-up and one bounded request per selected core initially; run repeated stochastic trials only if the pilot completes within budget and variance affects the decision. Use a hard parent-process timeout, checkpoint each case, and stop at the predeclared request/time budget. A Python/HTTP timeout alone is insufficient, as the V7/V8 incident showed.

### 4. Lightweight independent review protocol

For every unique development core, one reviewer who did not author its label should review the prompt, expected intent/action, exact identifiers/arguments, clarification requirement and safety outcome **before model output is seen**. Preserve IDs and text; flag ambiguity or prompt/label mismatch rather than silently correcting it. A second reviewer should blindly review a predeclared stratified subset (all families and high-risk cases represented) and all disagreements; adjudicate before freezing the overlay.

Report reviewer count, reviewed-core count, double-review coverage, raw agreement, disagreements and unresolved cases. Cohen's kappa can be supplementary for two reviewers, but a generic threshold should not be the sole quality gate because prevalence and class balance affect interpretation. Unresolved labels are not correct: exclude them from scored denominators and state the denominator, or declare the experiment inconclusive if coverage is inadequate. Do not invent risk weights or replace predeclared row/core metrics with a weighted headline.

### 5. Statistical and decision framing

Keep the predeclared gate: row-weighted and core-weighted exact-action improvements must each be at least 10 percentage points on the same reviewed development examples before proposing a separately frozen follow-up. Show paired per-core differences and uncertainty resampled by core, not repeated row. Also show family results and the original ~90% targets; a development gate is not held-out acceptance. Safety requires zero unexpected writes and no regression in authorization, tenant isolation, pending approval or idempotency on executed cases.

If there are too few independently reviewed cores, unresolved labels, wide uncertainty, incomplete freeze artifacts or a process timeout, report **inconclusive/blocked**. Do not extend the run, drop cases or select a favorable subset after seeing results.

## Recommended smallest decisive sequence

1. **Review and freeze:** Prepare fresh distinct prompt cores and labels; independently review before inference; reconcile disagreements; freeze dataset, review overlay, scoring, candidate/V2 source and model/runtime hashes.
2. **Bounded CPU feasibility pilot (optional arm):** Compare cached Ollama with at most one compatible CPU-only option on a small preselected family-balanced subset, using a fresh worker process per case, hard timeout and fixed total budget. Skip the alternate if it needs a large download/install or does not fit memory.
3. **Attribute quality:** Save candidate raw structured intent and score it against adjudicated intent/slot labels. Separately feed gold intents to the candidate planner to measure conditional planner errors. Do not feed candidate `IntentEnvelope` objects directly into V2.
4. **Native paired comparison:** Run V2 and the structured candidate on the same frozen reviewed cores with fresh equivalent synthetic database state. Keep each system's native adapter/controller path. Report row/core exact action and end-to-end success separately, along with tool execution, grounding, clarification, safety, approval and idempotency.
5. **Decide:** Apply the paired +10 pp row and core development gate, original quality targets and safety gate. Passing only authorizes proposing a separately frozen follow-up; it does not change P2 acceptance.

## Citation limitation

The pasted framework uses numeric citation markers such as `[[10]]` but provides no bibliography or direct links. Its source-dependent claims and thresholds cannot be independently checked from the pasted material. Treat them as unverified until complete citations are supplied and each source is checked against its claim.

## Conclusion

Use the framework's freezing, independent review and evidence separation. Correct its cross-controller replay design and keep the first experiment bounded. The most informative next result is a reviewed fresh-core native V2-versus-structured-candidate application comparison, complemented by separate model-intent and gold-intent-planner diagnostics. Current P2 verdict remains **PARTIAL**.
