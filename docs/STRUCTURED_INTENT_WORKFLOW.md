# Structured Intent Workflow Candidate

**Status:** opt-in engineering candidate; not an accepted replacement for V2.  
**Current verdict:** implementation and three bounded real-Ollama synthetic application workflows pass. This is smoke evidence only; quality on broad or unseen requests is not established.

## What changed

The candidate asks the local Ollama backend for a JSON-schema-constrained `IntentEnvelope`: a closed-set intent, candidate order/item IDs, item scope, requested outputs, and optional policy/reason/ticket quote fields. The response is parsed by a strict Pydantic model. It cannot name arbitrary tools or return a business outcome.

`StructuredIntentWorkflowController` then creates a fixed registered-tool action. It checks only the identifier slots relevant to the selected workflow, independently extracts valid identifiers from the request/context, rejects malformed or conflicting order references, and asks for clarification when a specific item is not identified. “All items” is accepted only when the user explicitly says all/every/each; an irrelevant model item span such as `"*"` is ignored for an explicitly all-items request and never becomes a tool argument. Eligibility reason and policy category come from deterministic trusted-code checks, not from the model's corresponding suggestion fields. Ticket issue text must be grounded in the user/context text and is still only proposed for supervisor approval.

The application continues to validate action and tool schemas, authorize tenant/role access, enforce domain rules, and run registered operations. Read-tool outputs are validated against strict typed result models before they enter orchestration or response rendering. The estimate workflow is explicitly listing → eligibility → estimate for eligible items. Safety preflight runs before model interpretation. The model does not write a customer-facing business answer in this candidate; smalltalk receives a fixed capability response, and tool paths use the existing grounded result renderers.

## Configuration

V2 and `deterministic_test` remain the defaults. To opt in with an already-installed local Ollama model, copy `.env.structured-intent-candidate-real-llm-smoke.example` to `.env` and start the backend as documented in the README. Select:

```text
MODEL_BACKEND=ollama
HYBRID_CONTROLLER_ENABLED=true
HYBRID_CONTROLLER_VERSION=structured_intent_candidate
```

The `/api/v1/system/info` response reports the selected controller mode. Do not use the example file as a production configuration.

## Safety and known limits

- The schema constrains output shape, not semantic correctness. The model may still misclassify intent or omit a requested output.
- Model-provided `item_scope`, `reason`, and `policy_category` do not establish bulk scope or business decisions. Trusted code verifies item scope and derives reason/category.
- Tool execution still performs tenant authorization and item/order membership checks. An ID appearing in a message never grants access.
- Ticket writes remain pending and require supervisor approval; approval-time validation and idempotency are unchanged.
- The inherited turn timeout is not an OS process kill. The previous long inference incident means a real-model run must be separately bounded and stopped if the host/runtime exceeds its limit.
- Initial real-model ticket and estimate probes safely clarified because the model emitted the irrelevant `"*"` item span. That trace led to the intent-relevant-slot validation above; focused regressions were added before rerunning. Failed diagnostic artifacts remain preserved separately.
- The V5 test set and all historical benchmark artifacts were untouched. The three successful smokes are not a fresh benchmark, broad quality score, or generalization claim.

## Bounded real-model application evidence (2026-10-12)

All three runs used the already cached local Ollama model `qwen3:1.7b`, Q4_K_M, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`, an opt-in structured-intent controller, a fresh temporary SQLite database, a 25-second HTTP request timeout, and a 45-second parent-process hard deadline. The frozen outputs include parsed model intent, the assistant response, tool outputs/traces, timings, checks, and source hashes.

| Workflow | Result | Observed evidence |
|---|---:|---|
| `ORD-10021` lookup | **5/5 checks passed** | Model intent was `lookup_order`; registered tool authorized and returned `in_transit`; final answer matched. Request 1,972.74 ms. |
| All-item estimate for `ORD-10022` | **5/5 checks passed** | Registered sequence `list_order_items` → `check_refund_eligibility` → `calculate_refund_estimate` succeeded. Final response included tool-derived USD 90.28 and said no refund was issued. Request 2,305.69 ms. |
| Damaged-item ticket for `ORD-10021` | **7/7 checks passed** | Ticket was pending with no row before approval; supervisor approval created it; repeating approval returned the same ticket; exactly one row existed. Request 2,369.97 ms. |

The latest versioned artifacts use timestamp-suffixed names beginning `p2_structured_intent_real_smoke_v5_`, `p2_structured_intent_real_estimate_smoke_v4_`, and `p2_structured_intent_ticket_approval_real_smoke_v4_` in `experiments/results/`; each has a matching `_freeze_` artifact. Re-running the command creates a new timestamped result when the default path already exists. No model download or paid service was used.

## Intended evaluation

The next evidence step is a fresh, independently reviewed, distinct-core comparison against the unchanged V2 behavior, with a predeclared application slice and safe paired uncertainty reporting. Report parse/intent, tool choice, arguments, clarification, real tool execution, final answer, approval safety, and latency separately. Internal labels must be identified as such. These three selected smokes do not authorize promotion to default.
