# P2 Root-Cause Forensic Audit

**Audit date:** 2026-10-11
**Scope:** Evidence-only audit of the P2 evaluation and improvement history. No model inference, tests, tuning, package installation, source edits, or frozen-data changes were performed.
**Overall quality verdict:** **PARTIAL**. The application has successful bounded local-model integrations, while frozen action-quality targets remain unmet and the broader real-application denominator was not executed.

## Executive findings

The evidence does not support one isolated root cause. The low V5 score has at least three independently evidenced contributors: (1) the model and controller do not reliably map paraphrases to the required action/slots; (2) a V5 generator defect produced 15 prompt/gold order-ID disagreements; and (3) V5 contains only 28 distinct test prompt cores repeated across 150 rows, limiting how much independent evidence that denominator represents. The measured real-application subset is a separate eight fixed workflows, not a V5 test execution. Metric labels in historical summaries also need care: offline replay and action exactness are not end-to-end task success.

The strongest supported next move is a small, development-only experiment that first checks prompt-to-label integrity and then isolates controller routing from saved raw-model proposals. It should precede any new model, prompt, or broad implementation cycle. Frozen V5 files and scores must remain untouched.

| Evidence track | Verified result | What it establishes |
|---|---:|---|
| Original pinned Transformers Qwen3-1.7B | Loaded on CPU; timed out at 90 s with truncated action JSON | Model is loadable on CPU but did not complete a usable tool action in that run |
| Ollama Qwen3-1.7B Q4_K_M, V5 raw test | 149/150 valid; 25/150 exact (16.7%); tool selection 19/85 (22.4%); exact arguments 4/75 (5.3%); p50/p95 3.355/5.301 s | Real model proposal quality, scored action-only |
| V5 hybrid-controller replay | 31/150 exact (20.7%); tool selection 20/85 (23.5%); exact arguments 4/75 (5.3%); clarification 6/43 (14.0%); handoff 5/11 (45.5%) | Controller applied to saved proposals; no tools or database writes |
| V5-named real-app artifact | 8/8 fixed workflows passed, actual local Ollama/FastAPI/tool path | Genuine bounded integration evidence, but artifact identifies the dataset as V2 (`3c53d39f…`), not V5 |
| Deterministic backend | Used for CI/test fixtures and regression workflows | Software/test evidence only; never a real-model result |

V5's raw-to-hybrid exact-action transition is 114 wrong in both, 11 raw-wrong/hybrid-right, 5 raw-right/hybrid-wrong, and 20 right in both. The net increase is six examples. That modest gain does not explain away the dominant routing/slot failures.

## Verified root causes and confidence

“Verified” below means the mechanism is directly visible in saved source/artifacts. A mechanism's contribution to a score is causal only where a controlled comparison exists; otherwise it remains a strong or probable explanation.

| Rank | Finding | Confidence | Evidence and interpretation |
|---|---|---|---|
| 1 | Controller intent recognition and precedence are brittle on novel wording | High for code behavior; medium-high as score contributor | `backend/app/hybrid_controller.py` uses literal phrase lists. V5 paraphrases often miss ticket/order/eligibility/boundary intent. “Policy” is checked before eligibility, causing six observed misroutes. Offline replay shows 73 of 88 accepted decisions are wrong; all 22 overrides are wrong, while 17/22 handoffs are wrong. This is not merely a lack of controller activation: some rules actively route the wrong way. |
| 2 | V5 contains prompt-to-gold order-ID mismatches | High | 11 test and 4 dev `multi_step_read` prompts name `ORD-10022`, while gold arguments name `ORD-10021`. V5 generation overwrites prompt text but copies source-row labels. The validator checks normalized prompt overlap, not semantic slot/label agreement. These 11 test examples depress both raw and hybrid exact/argument scores. Counterfactual scores (raw 30/150, hybrid 42/150 if only those 11 test gold IDs were corrected) are diagnostics, not official results. |
| 3 | V5 repeats a small number of test prompt cores | High for dataset structure; medium as score-precision limitation | `generate_v5_suite.py` cycles 14 families and indexes four family templates with the same global index; family recurrence is 14 and `gcd(14,4)=2`, so only two of four strings are selected per family. Test has 28 prompt cores repeated 5–6 times each. A varying “Reference N.” suffix makes full strings unique but not independent language examples. This weakens effective sample diversity; it does not by itself prove score bias. |
| 4 | Evaluation metrics overstate semantic task quality when read as “accuracy” | High | Raw exact scoring checks action type/tool/expected argument fields when present; it does not check final-answer truth, and ticket examples with null expected arguments can score exact without checking ticket contents. Hybrid replay scores saved action projections only. Its source explicitly says no registered tools execute. |
| 5 | V5 actual-app evidence and benchmark evidence are not the same run | High | `hybrid_controller_v5_real_integration_subset.json` says dataset V2 and V2 SHA. The runner hardcodes eight fixed workflows and V2 metadata. The V5 42-case file is a selection manifest only. Therefore 8/8 cannot be represented as 8 V5 cases or 42-case acceptance. |
| 6 | Repeated model calls and one ungrounded response path limit end-to-end latency | High for observed path; medium as general cause | V5 fixed integration traces show 3.18–7.49 s requests for model-dependent workflows and ~22 ms direct paths. Multi-step work invokes successive calls; the policy grounding helper expects `return_window_days`, while the policy tool returns `policy_text`, `version`, `as_of`, leaving that shortcut unreachable. This is an observed design mismatch; the eight-case sample is too small for a general latency claim. |
| 7 | V5 invalid output may have been influenced by synthetic ordinal text | Low / hypothesis | The one invalid case supplied `order_id="74"`; its prompt ended with `Reference 74.`. The artifact does not retain enough raw generation detail to establish causality. Do not treat this as confirmed. |

### Specific V5 behavior

Raw test exact matches are 11/11 `no_tool`, 10/10 `ticket_proposal`, and 4/11 `item_listing`; all other families score zero. The 10/10 ticket figure is especially weak because proposal arguments are not scored (`expected_arguments: null`). Raw expected read-tool selection is only 9/75; adding the 10 expected ticket proposals yields the headline 19/85 tool-selection count. Per read tool: lookup order 0/22, refund eligibility 0/11, list items 9/32 (arguments 4/32), return policy 0/10. The one invalid result is a schema validation error (`order_id="74"`), not a 90-second timeout. The evaluator's `timeouts_or_errors` counter counts all invalid actions.

In hybrid replay, `list_order_items` is 15/32 with 4/32 exact arguments, while lookup, eligibility and policy are 0 in the tool-name grouping; ticket proposals are 5/10. Correct tool-name numerator includes expected read tools and proposals. The expected-clarification group (43) becomes 27 final answers, 6 clarifications, 10 handoffs; expected tool calls (75) become 46 final answers, 26 tool calls, one invalid action and two handoffs. Expected handoffs (11) become six clarifications and five handoffs. These distributions directly support routing and action-type confusion as major failures.

The hybrid's family exact counts are: `no_tool` 11/11, `item_listing` 4/11, `missing_item` 6/11, `prompt_injection` 5/11, `ticket_proposal` 5/10, and zero for the remaining eight families. Five raw and eleven hybrid “misses” in `multi_step_read` have the verified order-ID gold mismatch described above.

## How the attempt history evolved

This timeline is bounded by files currently present in the repository. The workspace has no commits, reflog, or retained archive of every user-provided instruction, so it cannot verify every claimed iteration or reconstruct deleted/overwritten versions.

| Phase | What was tried and measured | Why it did not establish satisfactory completion |
|---|---|---|
| Initial model and A/B/C | Transformers Qwen3-1.7B; A/B/C validation exact 0/48 each. Locked old test exact 23/60, 24/60, 24/60. C used a saved/reloaded 20-step NF4 QLoRA adapter (adapter SHA recorded). | C improved some valid-output/latency measures but not exact score over B; small feasibility-scale training and action-only metrics do not show task completion. No tool execution was part of those benchmark scores. |
| CPU fallback and quantized-runtime exploration | CPU import/load repaired; generation exceeded 90 s and returned truncated JSON. 64-token cap truncated; 256-token smoke produced a valid action. GGUF Q4 candidate was inspected, but no compatible Windows CPython 3.12 binary/runtime was available; it was not run. | Fixing model loading did not provide practical CPU generation. Candidate compatibility was not evidence of candidate performance. |
| Local Ollama integration | User-installed Ollama served cached `qwen3:1.7b` Q4_K_M. Native structured tool call smoke selected `lookup_order(ORD-10021)` in ~3.31 s. Actual API lookup and ticket proposal/approval/idempotency succeeded; one multi-step eligibility attempt safely failed on invalid item arguments. | A bounded happy-path integration demonstrated the application path, not general quality. V2 frozen raw scores were 40/140 exact, tool 32/80, arguments 24/70; offline hybrid 96/140 exact, clarification 28/40. |
| Prompt probe and evaluation correction | One short prompt variant did not improve an 8-case smoke; 48 validation actions were valid but 0/48 exact in an earlier diagnostic. Evaluator was corrected to score non-tool action types. | No meaningful quality gain. Historical numbers from different evaluator versions cannot be compared without accounting for changed rules. |
| Hybrid controller v1 | Literal deterministic routing/clarification over model proposals; validation replay 48/48 exact; locked test 43/60 exact, tool/args 31/36, but ticket-missing-order clarification 0/12. Actual fixed integration 8/8. | Strongly demonstrates that fixed dev validation can overstate generalization. Held-out clarification missed every required case; replay is not tool execution. |
| V2 controller iterations | Added missing/ambiguous ticket order checks, estimate routing and safety phrase coverage. Frozen raw test 40/140 exact; hybrid 96/140, clarification 28/40, handoff 10/10. A final synthesis runtime patch fixed an extra-tool/fictitious-failure trace issue; supplemental estimate returned `$50.27` after 27,993 ms. | Iterations fixed concrete safety/runtime paths but did not reach quality targets. A successful patched estimate is not broad latency acceptance. |
| V3 suite/controller | Raw 46/150; hybrid 100/150; clarifications 25/43; handoff 11/11. Fixed real-app subset 8/8. | Stronger action performance than V2, but target metrics remained unmet and the 40–60 real-task run was not attempted. Dev/test were wrappers around repeated source prompts; evidence of generalization is limited. |
| V4 | New frozen dataset; no held-out raw/hybrid or end-to-end score. Audit found 41 shared template IDs and one shared core ID across splits. | Dataset preparation alone did not close evaluation; evidence cannot establish model quality. |
| V5 initial and corrected freeze | First V5 SHA was `1cde0a…`; current data/artifacts use corrected SHA `e5f6b3…`. Current raw 25/150; replay 31/150. Fixed integration artifact reports 8/8 but its underlying dataset identity is V2. | New paraphrase wording exposed poor transfer of both model and literal controller; copied labels include 15 entity mismatches; template generator emits only 28 distinct cores per split. The 42-case file is selection-only, not executed. |

### Why repeated improvements did not close the gap

The recurring pattern is that work often improved a local capability or a bounded demonstration—model loadability, schema validity, one read path, approval safety, explicit phrase rules, or final-answer runtime—without validating robust behavior over a diverse and correctly labeled held-out set. Controller validation results were sometimes excellent, but the V1 test's 0/12 clarification and V3/V5 paraphrase failures show narrow phrase coverage. Later generator changes increased apparent case count faster than independent prompt-core diversity. Evaluation tracks were also repeatedly easy to conflate: action-only proposals, offline replay, fixed actual-app workflows, and full test-set task completion are different evidence.

There is no controlled ablation proving that one prompt/controller change caused the V3→V5 decline. V3 and V5 hold model digest, prompt version, schema and broad generation settings constant, while V5 replaces wrapped source prompts with new paraphrases and copies labels. Raw exact moved 46/150 → 25/150; replay 100/150 → 31/150. This is consistent with brittle paraphrase handling and label/generator defects, but the data and prompt construction differences prevent a single-cause attribution. The V5 label counterfactual improves scores, but still leaves most failures unresolved.

## Data, scoring, safety, and provenance audit

### Frozen identities and historical conflicts

V5 current suite, manifest, freeze, raw dev/test, and hybrid replay agree on SHA-256 `e5f6b399494884c347b55c8bf352c570913472be34ebc5ffb52e089ab08adbdf`. The frozen config's source-file hashes match current V5 scoring source. Earlier progress/docs refer to initial V5 SHA `1cde0a85123c696a331d5af5328ecfa935d9f570b66089a7b5a512f6bd975acd`; that byte sequence is absent, so the initial suite cannot be independently reconstructed. Older V3 references use SHA `2b599e…`, while current V3 manifest/artifacts use `5b636b…`; old V3 bytes are also absent. These appear to be historical pre-correction/generated identities, but without prior bytes/history that interpretation is not fully verifiable. Do not overwrite old reports to make them look consistent.

V5 claims zero normalized split overlap, but its validator retains `Reference N.` in normalized text, and the generator uses only two of four pool strings per family. After removing the ordinal suffix, there are 28 distinct prompt cores in each split. V5 dev/test do have zero core-ID overlap and zero normalized text overlap across splits; this is compatible with repeated cores *within* each split.

### Metric boundaries

- Raw V5 evaluates one normalized model action per case. It does not run the controller or tools.
- Hybrid V5 is replay over the saved raw proposal. It checks controller action outputs; it does not invoke DB/business tools.
- The eight fixed Ollama/FastAPI integration flows execute real local model calls and registered tools against fresh synthetic SQLite data. The artifact is mislabeled as V2 dataset identity, so it cannot be joined to V5 test cases.
- The deterministic backend is explicitly a fixture/testing backend. Its results are software regression evidence, not LLM evidence.
- `exact_action` for no-tool replies does not compare factual response content; ticket cases without expected arguments do not score ticket fields. Tool-selection and argument denominators are different and should not be collapsed into a single “accuracy” claim.
- In the replay evaluator, argument exactness is compared across all 75 expected-argument rows; it is not conditional on a correct selected tool. Conditional on selecting the expected read tool, raw was 4/9 and replay was 4/15 under the official labels. Correcting the 11 mismatched test gold IDs makes those conditional counts 9/9 and 15/15 respectively; this is solely the label counterfactual.
- V5 p50/p95 are action-call latency (raw) or saved-proposal/controller replay timing, not full end-to-end task latency. In the fixed integration trace, model inference dominates DB/controller work; two-stage workflows add calls.

The application's authorization boundaries are not implicated as a root cause by these score artifacts. Existing API/domain code scopes reads by tenant, validates typed tool arguments, and persists ticket proposals pending server-side approval with idempotency. The bounded integration run reports zero observed unauthorized writes, cross-tenant disclosures, and duplicate rows for its covered workflows. V5 offline replay fields for executed unauthorized writes/duplicate approvals are null/not measured; do not interpret null as zero. None of this proves universal safety beyond the reviewed code/tests and executed samples.

### Evidence gaps and history limits

The repo has no Git commit or reflog; every existing project file was untracked at audit start. Consequently there is no trustworthy commit chronology/diff for every historical iteration. The available `PROGRESS.md`, docs, code, frozen artifacts and user-supplied task titles support the timeline above, but the full set of prior prompts is not archived. The exact “25+ improvement attempts” claim cannot be enumerated or verified; only the retained attempts above can be audited. Some old outcomes lack raw model text or per-row traces. The V5 fixed-app harness did not execute the selected 42-case V5 manifest. No general benchmark for resource use or post-optimization latency exists in the current evidence.

## Recommended next experiment (not implemented here)

Do not start with another model download, a test-set retune, or broad prompt edits. The best-supported next step is a bounded dev-only discrimination experiment that separates label defects, model proposal failure, and controller routing.

1. Preserve V5 bytes and all scores. Generate a temporary audit overlay from V5 dev rows only; do not edit the frozen scenario file. Independently review each prompt/gold slot for entity agreement and count unique prompt cores after removing `Reference N.`. Mark disagreements explicitly; do not silently repair labels.
2. Using the already-saved V5 dev proposals (no inference), replay the unchanged controller and tabulate by family: raw action type/tool/arguments, controller decision/reason, final action, and gold validity. This is a reproducible baseline, not a new score on test.
3. Before implementation, present a reviewable one-page plan and decision table. The smallest candidate is a deterministic intent/slot routing prototype evaluated on the audited dev overlay, with explicit intent precedence and mandatory entity/required-slot checks. It must keep all authorization and business rules server-side. Compare against unchanged replay on the same reviewed dev examples.
4. Acceptance for the experiment: all V5 dev examples are paired by exact ID; every label mismatch is flagged before scoring; every repeated prompt core is counted once for diversity reporting; controller decision reasons are emitted for all examples; no unregistered tool or state-changing action can execute; regression suite stays green; and the candidate must improve exact action by at least 10 percentage points over the unchanged **label-audited dev** baseline without reducing correct clarification or handoff counts. This is a decision gate, not a promise of test-set performance.
5. Stop if the overlay cannot be reviewed independently, examples cannot be paired, candidate logic would require weakening controls, improvements depend on duplicated cores or mislabeled examples, or the candidate fails the 10-point dev gate. If it passes, freeze a new version and predeclare a genuinely diverse untouched test set before any inference. Never use V5 test for tuning.

This audit did not implement the experiment. The tailored implementation prompt is in [`P2_NEXT_IMPLEMENTATION_PROMPT.md`](P2_NEXT_IMPLEMENTATION_PROMPT.md); the row-level V5 catalog is in [`p2_root_cause_failure_catalog.json`](../experiments/results/p2_root_cause_failure_catalog.json).

## Audit integrity

The catalog JSON parses and includes all V5 test failures/mismatch cases and V5 dev raw failures, with exact IDs, prompt/gold slots, model/controller outputs, and source file SHA-256 references. Its official metric values are copied from the source artifacts and validated against their case IDs. The only counterfactual values are explicitly labeled and never replace official scores.

At audit start, 233 existing files (excluding virtual environments, VCS/cache folders) had aggregate per-path SHA-256 inventory digest `4457e13a48e19df783cc75f09cde0a863ebd8da8ffbb12f779635a986fb31a6a`. Final verification must compare the same inventory excluding the three approved new files. Git cannot independently prove unchanged status because the workspace has no committed baseline. The audit creates exactly the three approved deliverables; no existing project file is to be changed.
