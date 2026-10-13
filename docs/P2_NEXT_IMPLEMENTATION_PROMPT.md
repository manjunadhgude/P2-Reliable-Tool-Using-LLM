# P2 — Small, Evidence-Driven Controller Reliability Experiment

## Mission

Use the findings in `docs/P2_ROOT_CAUSE_FORENSIC_AUDIT.md` and `experiments/results/p2_root_cause_failure_catalog.json` to determine whether a small deterministic intent/slot-routing change can materially improve P2 action reliability on development data. This is a new, versioned experiment. It is not authorization to tune on V5 test, alter historical evidence, or claim production readiness.

## Required review gate before implementation

First inspect the current repository and prepare a concise, reviewable plan containing:

1. Exact files that would be added or edited, and why each is necessary.
2. A frozen-source preservation plan for V5 datasets, raw results, hybrid replay, manifests, reports, and existing defaults.
3. The V5 dev examples affected by the 4 verified prompt/gold order-ID mismatches, the proposed independent label-review method, and how corrected/uncertain annotations will be represented in a temporary overlay without changing V5.
4. The unchanged-controller baseline and candidate comparison fields, paired by `example_id`.
5. A proposed controller precedence/slot-validation decision table, including conflicting orders, cross-tenant requests, item-specific eligibility, general policy, missing order/item fields, ticket proposals, prompt injection, unsupported intent, and multi-step reads.
6. Exact tests, commands, timeouts, model calls, and resource limits.
7. Risks, explicit stop conditions, and a list of all existing files whose hashes will be checked before and after.

Do not implement until this plan is available for review and approved. No user data or paid/cloud resources are needed.

## Smallest decisive experiment

### Phase A — label and diversity audit (no inference)

- Use only the existing V5 dev split (60 rows) and saved V5 dev model proposals.
- Do not modify `experiments/datasets/hybrid_controller_v5/scenarios.jsonl`, any manifest, or any historical result.
- Create a separately named, temporary/versioned review overlay. For each row, record prompt entity IDs, expected argument IDs, label agreement, reviewer disposition, and unique prompt-core key after stripping the synthetic `Reference N.` suffix.
- Independently adjudicate all four known dev `multi_step_read` disagreements and check every other slot for prompt/gold agreement. Preserve original gold fields alongside any reviewer annotation.
- Define one normalization function and apply it unchanged to baseline and candidate examples: remove only a trailing, case-insensitive `Reference N.` suffix (where `N` is an integer), Unicode-normalize to NFC, trim, collapse internal whitespace, and case-fold. Preserve IDs and original prompt text; do not strip order/item identifiers or paraphrase content.
- Report row count, unique normalized cores, number of cores repeated more than once, each repeated core's multiplicity, family coverage, and exact label-disagreement count. If independent review is unavailable, mark affected rows unresolved and exclude them from both systems' scored denominators; never count unresolved labels as correct.
- Require at least **20 distinct, independently reviewed normalized prompt cores spanning at least 10 scenario families** for a meaningful decision. If the adjudicated overlay falls below either threshold, label the result **INCONCLUSIVE** and do not declare the candidate gate passed, even if row-level scores rise.

### Phase B — saved-proposal controller comparison (no model inference)

- Pair the unchanged controller baseline and candidate output by exact example ID over the reviewed V5 dev overlay.
- Candidate should be the smallest deterministic intent/slot gate needed to test the audit's leading explanation. Avoid a generalized parser or architecture rewrite.
- Suggested order: security/boundary classification first; extract and validate all request-linked entity identifiers; resolve ambiguity before routing; then explicit operation precedence (ticket intent with required details, item-specific eligibility, refund estimate, general policy, list items, order lookup); unsupported/uncertain requests clarify or hand off. Preserve tenant checks, registered-tool allowlist, schema validation, business rules, approval gate and idempotency unchanged.
- Record for every row: model proposal; baseline decision/reason/action; candidate decision/reason/action; gold label and annotation status; exact-action result; tool-selection and argument result; clarification/handoff result; whether the prompt core is repeated.
- Score reviewed and unresolved labels separately. Do not use a counterfactual corrected label as the official V5 score. For reviewed rows, calculate exact-action per core first, then average the core-level accuracies with equal weight per unique core.

## Measurable acceptance criteria

This dev experiment passes its decision gate only if all are true:

- Exact one-to-one pairing for every included example; no missing/duplicate IDs.
- Independent label review covers all included examples; known mismatches are explicitly corrected in the overlay or excluded from the adjudicated denominator with counts and reasons.
- Report both row-weighted exact-action accuracy (all adjudicated rows pooled) and core-weighted exact-action accuracy (compute each unique normalized core's exact-action rate, then average cores equally).
- The baseline and candidate use the same adjudicated example IDs and the exact same normalized core function. Candidate gain is at least **10 percentage points in both** row-weighted and core-weighted exact-action accuracy. Report the paired gains in percentage points.
- Report the development row count; unique core count; number of repeated cores and their multiplicities; baseline/candidate row-weighted and core-weighted scores; and per-family row-weighted and core-weighted results. Explain repeated-core contribution by separately reporting the baseline-to-candidate change for singleton cores and repeated cores, with row and core denominators for each group.
- Correct clarification and correct handoff counts do not regress versus that same baseline; report numerators and denominators separately.
- No increase in malformed actions, unauthorized writes, cross-tenant disclosures, or duplicate state changes; all state-changing proposals remain pending until server-side approval.
- Existing backend regression tests, lint, frontend build, dataset validators, and any applicable safety/idempotency checks pass. Clearly identify which commands were actually run.
- No existing benchmark or frozen artifact changes; hash check confirms this.

These criteria authorize only a decision about whether to prepare a separately frozen follow-up. They do not establish locked-test generalization, end-to-end acceptance, or a PASS verdict.

## Explicit stopping conditions

Stop without implementation or report a failed experiment if:

- The review plan cannot isolate the smallest candidate or preserve frozen evidence.
- Gold labels cannot be independently checked; mark uncertain rows unresolved rather than guessing.
- Proposed routing would infer authorization, tenant ownership, refund eligibility, approval, or business calculations from model text.
- Any test requires real customers/payments, external writes, paid APIs, cloud GPUs, or a large dependency/model download.
- The candidate fails the 10-point development gate, regresses correct clarification/handoff, or gains only by exploiting repeated cores or unresolved labels.
- Either weighted metric improves by less than 10 percentage points, or fewer than 20 distinct reviewed cores across 10 families remain. In the latter case report **INCONCLUSIVE**; unresolved labels are never scored as correct.
- Resource use exceeds the predeclared bound, a test hangs, or a safety regression appears. Bound every command and model/runtime operation; no model inference is needed in Phases A/B.

If Phase B passes, stop and present the evidence for review. Do not continue into a held-out test run in the same iteration. A later phase must first freeze candidate source, evaluator, annotation policy, and a diverse untouched evaluation set, then receive a distinct authorization before any test inference.

## Reporting requirements

Update only newly approved/versioned artifacts after the review gate. Report baseline and candidate counts, adjudicated and unresolved denominators, label disagreements, normalization rule, unique prompt cores and multiplicities, both weighted metrics and paired gains, repeated-versus-singleton contribution, per-family results, exact commands, hashes, risks, and deviations. Keep action-level metrics separate from actual tool execution and end-to-end task success. Never call an offline replay a tool run; never count deterministic fixtures as real model evidence. Passing this development gate only permits proposing a separately frozen follow-up; it does not establish held-out generalization or change the overall P2 acceptance verdict. Keep overall P2 status **PARTIAL** unless all pre-existing acceptance requirements are independently satisfied with evidence.
