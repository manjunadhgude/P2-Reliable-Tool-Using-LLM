# Hybrid Controller Design — Version 2 (2026-10-10)

## Goal

Combine the real Ollama proposal with a small deterministic workflow layer. The controller improves application routing and slot handling; it does not improve or relabel raw model accuracy.

## Data sources and boundaries

- Current user message: untrusted request text. Only identifiers matching `ORD-` plus five digits and `ITEM-` plus four digits may be extracted.
- Conversation history: consulted only when the latest assistant response asks for an order ID, item ID, or ticket issue details. The controller follows that clarification chain back to the original user request; it does not reuse IDs from unrelated completed turns. Multiple IDs remain ambiguous.
- Tool results: trusted only when produced by the server in this turn. The existing orchestration uses returned order/item IDs for deterministic workflows.
- Tool schemas: `TOOL_REGISTRY` and `ARGUMENT_SCHEMAS` are the sources of required fields. No parallel field catalog is maintained.
- Dataset labels and example metadata are never read by runtime controller code.

## Decision order

1. Clear security and prohibited financial-write requests receive a safe handoff before inference.
2. Clear order, item, eligibility, and ticket requests resolve slots only from the user message or clarification-linked history. Missing or ambiguous slots produce a focused clarification without inference.
3. The model action envelope and registered tool are validated. With the hybrid flag enabled, the Ollama adapter passes the known tool's argument object to the controller for strict schema validation; the final action is validated before execution.
4. Clear lookup, item-list, policy, eligibility, and refund-estimate requests route through registered actions. Eligibility and estimates first list authorized order items; the server uses database-derived item IDs and deterministic business rules. A specific-item request without an item ID is clarified. Explicit item IDs are checked against the referenced order by the registered tool.
5. A ticket proposal is accepted only for an explicit ticket request with issue context. The domain schema allows generic tickets with no order ID. If the issue refers to an order, delivery/shipment, item/product, return, or refund, the request must contain exactly one valid, user-grounded order ID. Unknown properties and model-invented identifiers are rejected or discarded for a generic unlinked ticket. The API checks this again before creating a pending action. Approval revalidates the stored schema and tenant-scopes the referenced order before writing.
6. Other read-tool proposals are checked against their registered schemas. Required order/item identifiers must be grounded. At most one schema-grounded argument repair is recorded; the controller does not issue a second model request.
7. Unrequested state changes are handed off. Unclear intents or invalid proposals are clarified or fail closed. No fallback tool is selected to match a benchmark label.

## Version 2 changes and regression evidence

- Ticket order requirement follows the source schema: `TicketArgs.order_id` is optional for generic support requests; order-related issues require one request-grounded order ID before a proposal can be staged. The clarification prompt is recognized by the conversation-context linker, so a follow-up ID resumes the original request safely.
- The API boundary repeats the order-ID grounding check even when the hybrid controller is disabled. Ticket arguments are revalidated at approval execution, and an invalid pending row fails with HTTP 422 without creating a ticket.
- Refund estimate phrasing enters the existing registered list → eligibility → estimate workflow. Common return-window/period/deadline wording routes to the policy tool. Broader general-pattern injection/bypass matching hands off before inference.
- `backend/tests/test_hybrid_controller.py` adds missing, malformed, ambiguous/conflicting, follow-up-supplied ticket identifiers; generic unlinked ticket behavior; API boundary checks; estimate routing; and seven injection phrasings through both the controller and API.
- Controller version is `hybrid-controller-v2`. The historical v1 frozen artifacts are unmodified. New v2 suite and freeze hashes are recorded under `experiments/datasets/hybrid_controller_v2/` and `experiments/results/`.

## Trace and budgets

Hybrid turns record backend/model identity, the proposal's action type/tool/arguments (PII-redacted, generated free text omitted), envelope validity, final action type/tool, decision and validation-failure category, repair count, model-call count and per-call elapsed time, and controller elapsed time. Hidden reasoning and prompts are not persisted. Existing model-step and tool-call budgets remain active; Ollama generation uses the configured `MODEL_MAX_NEW_TOKENS` cap (256 in the frozen run) and request timeout. Ollama failures do not fall back to the deterministic test backend.

The feature is opt-in through `HYBRID_CONTROLLER_ENABLED=true` and applies only with `MODEL_BACKEND=ollama`. CI and ordinary local startup remain on `deterministic_test` by default.

## Evaluation layers

- **Model-only:** the adapter proposal before controller intervention. Existing artifacts remain untouched; new reports use corrected definitions for non-tool actions.
- **Hybrid action-level:** the final controller action scored against the same action labels. This measures the application-plus-model action choice, not raw model intelligence or task completion.
- **Integration:** actual application/database workflows, tool results, final response checks, and approval outcomes. Only outcomes executed and explicitly checked are reported as task completion.

The offline hybrid evaluator replays saved action projections containing action type, tool, and arguments. It omits model-generated free text, does not score answer wording, and does not execute business tools. Separate API tests and the real-Ollama integration artifact cover those behaviors.

After the v2 action-suite freeze, Ollama final-answer synthesis was hardened to expose no registered tools and ask for a concise response grounded in the completed tool result. This post-freeze final-phase patch is separately hashed and documented in `experiments/results/hybrid_controller_v2_runtime_patch.json`; it is not included in the frozen raw/hybrid action metrics. A supplemental actual-app refund-estimate smoke passed after the patch.

For non-tool expected actions, argument accuracy is not applicable. Exact action compares action type, expected tool presence/name, and complete arguments only when the expected action includes arguments. Tool-selection accuracy uses only examples with an expected tool; no-tool, clarification, and handoff rates are shown separately.
