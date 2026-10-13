# P2 Deep Research Handoff — What Happened and What Remains

**Prepared:** 2026-10-12  
**Current P2 verdict:** **PARTIAL**. This is an evidence handoff, not a new evaluation or a claim that the project is accepted.

## Project summary

P2 is a local-first synthetic e-commerce support agent. It should understand a request, choose a safe registered workflow, use validated tools against synthetic data, ground its answer in tool results, and keep support-ticket creation pending until an authorized supervisor approves it. CI's deterministic test backend is separate from real-model evidence. The application and safety controls work on covered paths, but broad real-model quality and generalization goals remain unmet.

## What happened

1. **Pinned Transformers model:** Qwen3-1.7B loaded on CPU, but a recorded 90-second generation attempt ended with truncated action JSON. This established loadability, not practical completion of a tool action within that run.
2. **Local Ollama inference:** The cached model `qwen3:1.7b`, Q4_K_M, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`, enabled actual local application calls without a paid API or cloud GPU. Broad action-selection and argument scores remained low.
3. **Controller iterations:** Literal phrases, routing precedence and slot checks improved selected replay outcomes, but paraphrases and missing/ambiguous details continued to fail. Excellent scores on some small validation slices did not transfer consistently.
4. **Evaluation defects and limitations:** V5 had 15 prompt/gold order-ID disagreements. Its 150 test rows reduce to 28 normalized prompt cores after removing the synthetic `Reference N.` suffix; those cores repeat five to six times. Labels were not independently reviewed. Raw model proposals, offline controller replay and actual application execution are distinct forms of evidence.
5. **Fresh V7/V8 comparison:** A new set of 130 cores across 13 families and the sources/evaluator/controllers/model were frozen. A local Ollama call lasted a recorded 3,102,971.7 ms despite a configured 30-second request timeout. The run was stopped; no complete proposal artifact, paired score, uncertainty estimate or application comparison exists. The exposed-set V7 39/64 vs V8 41/64 result is diagnostic only.
6. **Opt-in structured-intent candidate:** The real model returns a schema-constrained closed-set intent and candidate slots. Trusted code grounds identifiers, plans fixed workflows, validates registered tools, authorizes access, applies business rules, and renders tool-backed results. The model cannot choose arbitrary tools, decide business outcomes or approve writes. The deterministic CI default and V2 behavior remain unchanged.
7. **Three bounded real-model app smokes passed:** Using cached local Qwen through FastAPI and tools with fresh temporary synthetic SQLite:
   - `ORD-10021` lookup: 5/5 checks, ~1.97 seconds; actual tool result was `in_transit` and the final answer matched.
   - All-item estimate for `ORD-10022`: 5/5, 2.31 seconds; list → eligibility → estimate tools returned USD 90.28, and the final answer correctly said no refund was issued.
   - Damaged-item ticket: 7/7, 2.37 seconds; it stayed pending before approval, supervisor approval created it, repeated approval returned the same ticket, and the database contained one ticket row.

   These are selected integration smokes, not a representative benchmark.
8. **Qwen Deep Research handoff/review cycle:** A project history report and research prompt were prepared. The first submitted research response substituted unrelated mobile-automation products for the four P2 approaches; the next response proposed a more relevant four-phase outline but still had unverified numeric citations, hypothetical example scores, and conflicting guidance about collecting reasoning traces. Both were reviewed; neither executed P2 inference or produced model-performance results. The current prompt explicitly prevents those errors.
9. **Ollama structured-output feasibility review:** The local adapter already sends the `IntentEnvelope` JSON Schema via Ollama `/api/chat`'s `format` field and validates the response. Current official Ollama documentation supports this interface, and three saved real-Qwen app smokes used it successfully. A later study recommended models/quantizations absent from the checked cache and made unlinked stability/low-level claims; it did not run a comparative experiment. See `docs/P2_OLLAMA_STRUCTURED_OUTPUT_FEASIBILITY_REVIEW.md`.

## Evidence and interpretation

| Evidence | Result | What it does and does not establish |
|---|---:|---|
| Pinned Transformers Qwen3-1.7B | CPU load worked; one 90 s generation attempt produced incomplete action JSON | That attempt failed to produce a complete usable action within its bound. |
| V5 raw model test | 25/150 exact actions (16.7%); tool choice 19/85 (22.4%); exact arguments 4/75 (5.3%) | Real proposal quality under action-only scoring; not tool execution. V5 has verified entity-label conflicts. |
| V5 hybrid replay | 31/150 exact (20.7%); tool choice 20/85 (23.5%); arguments 4/75 (5.3%) | Replayed saved proposals; no tools/database actions executed. |
| Fresh60 raw / V2 replay / V4 replay | 16/60 (26.7%) / 31/60 (51.7%) / 42/60 (70.0%) exact actions | Internal labels, not independently reviewed. Replay is offline. V4 still missed ~90% targets. |
| V5-selected 42-case app suite with Qwen and V4 | 26/42 checks passed (61.9%) | Actual synthetic execution, but selected from exposed V5 cases; not fresh generalization. |
| Fresh V7/V8 | No complete score | Blocked by the exceptionally long inference call; no comparison conclusion. |
| Structured-intent smokes | Three workflows passed 17/17 listed checks | Narrow real integration evidence; not broad accuracy or unseen-request reliability. |
| Deterministic backend | Software/regression tests passed; latest recorded full backend suite 98 passed | Fixture/test evidence only, not LLM performance. |

### Independent arithmetic recount (2026-10-12)

The following counts were recalculated by summing row-level values in the saved raw JSON and agree with the artifact summaries:

| Artifact | Recalculated counts |
|---|---|
| `hybrid_controller_v5_raw_test_final.json` | exact action 25/150; tool name 19/85; exact arguments 4/75 |
| `hybrid_controller_v5_hybrid_test_replay_final.json` | exact action 31/150; correct clarification 6/43; correct handoff 5/11 |
| `p2_fresh60_raw_ollama_v1.json` | exact action 16/60; valid action 57/60; tool name 16/36; exact arguments 12/32 |
| `p2_fresh60_controller_comparison_v1.json` | raw 16/60; V2 baseline replay 31/60; V4 candidate replay 42/60; 60 unique cores |
| `p2_v5_42_real_application_v1.json` | actual application checks 26/42 |

This is an arithmetic consistency check only. It does not validate gold-label correctness, independent review, causal interpretation, or generalization. In particular, action-only and offline replay scores do not establish successful real tool execution. Qwen's example table values (such as 75%, 80% and 90%) were illustrative placeholders, not P2 observations.

Hardware reported in the fresh V7/V8 report: Intel Core i5-1240P (12 cores/16 logical processors), NVIDIA GTX 1650 (4 GB), Intel UHD. A prior probe recorded about 0.55 GiB free RAM. These are run-specific observations, not general throughput claims.

### Verified findings

- Broad raw-Qwen action/argument scores and named replay scores are low against P2's goals.
- V5 contains 15 prompt/gold order-ID disagreements and only 28 normalized cores across 150 test rows after suffix removal.
- The fresh V7/V8 raw pass did not finish; the configured request timeout did not practically bound the recorded call.
- The structured-intent candidate completed the three saved real-model FastAPI workflows above.
- Deterministic CI results are not real-model benchmark results.

### Probable explanations, not isolated causal proof

- Both model intent/slot weakness and literal controller routing/precedence likely contribute to paraphrase failures. No complete controlled ablation apportions the score loss between them.
- Repeated cores weaken the independent diversity represented by row counts; repetition alone does not prove score bias direction.
- Local inference constraints require a true process-level bound. A request timeout setting alone did not stop the observed long call.

### Untested or unresolved

- Whether structured intent improves broad, independently reviewed performance over unchanged V2 on fresh distinct cores.
- Whether a different small open-weight model/runtime improves quality on this Windows hardware within practical time and memory limits.
- Which design intervention (structured intent, grounded slots, deterministic routing, different model, or a combination) gives the best paired gain.
- Broad ticket-content grounding and safety beyond selected real-app cases.

## Completion status

**Implemented and evidenced:** synthetic-data application; registered typed tools; tenant authorization; deterministic business rules; pending ticket approval and duplicate-approval protection; traces; deterministic CI backend; opt-in structured-intent workflow; regression coverage; three bounded real-Qwen app smokes; model/history documentation.

**Still open for original acceptance:** independent label review; sufficiently large fresh distinct-core evaluation; broad exact-action/tool/argument quality near the stated 90% targets; a complete bounded fresh V7/V8 comparison; broad actual-app task-success evidence; independent generalization evidence. Overall status remains **PARTIAL**.

## Source artifacts

- `docs/P2_ROOT_CAUSE_FORENSIC_AUDIT.md`
- `docs/P2_LONGITUDINAL_ROOT_CAUSE_REPORT.md`
- `docs/STRUCTURED_INTENT_WORKFLOW.md`
- `docs/PROGRESS.md` and `docs/ACCEPTANCE_CHECKLIST.md`
- `docs/FINAL_REAL_LLM_VERIFICATION.md`
- `docs/P2_FRESH60_AND_42CASE_EVALUATION_REPORT.md`
- `docs/P2_FRESH_V7_V8_EVALUATION_REPORT.md`
- Real smoke output and matching freeze JSONs: `experiments/results/p2_structured_intent_real_smoke_v5_20261012T004107Z.json`, `experiments/results/p2_structured_intent_real_estimate_smoke_v4_20261012T004115Z.json`, `experiments/results/p2_structured_intent_ticket_approval_real_smoke_v4_20261012T004111Z.json` and respective files with `_freeze_` in their names.

Treat project reports/artifacts as the evidence set, not independent peer review. Recalculate artifact metrics before relying on them. No usable Git commit history is available, so a complete iteration chronology or diff cannot be independently reconstructed.

## Research question

Identify the best-supported smallest next experiment to distinguish model proposal weakness from controller/slot-grounding failures, label issues and runtime limitations. Compare structured intent plus trusted deterministic planning, native constrained tool/action calls, deterministic routing with model fallback, and an alternate small local model/runtime only when authoritative compatibility evidence supports it. Recommend a frozen paired development experiment with independent review where practical, unique prompt-core accounting, row- and core-weighted metrics, real application execution, safety/approval checks, appropriate uncertainty, resource limits and explicit stop rules. Make recommendations only; do not change code, data, defaults, historical results or the overall verdict.

The latest Qwen framework's four phases—resource/contract screening, raw-artifact metric audit, failure diagnosis, and native paired end-to-end comparison—are a useful organizing outline, not evidence that any new P2 experiment has run. Reuse existing P2 runners and traces where possible; do not propose a new generic record/replay platform unless you identify a concrete missing capability. Resource timeout means no quality conclusion for affected cases; a candidate that cannot meet the frozen operating envelope or safe contract is infeasible for this pilot. Never store chain-of-thought. Use synthetic data only.
