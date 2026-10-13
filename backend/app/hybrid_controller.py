"""Deterministic workflow guard for untrusted model action proposals."""

from dataclasses import dataclass
import re

from app.tools.domain import ARGUMENT_SCHEMAS
from app.tools.registry import TOOL_REGISTRY

ORDER_ID_RE = re.compile(r"\bORD-[0-9]{5}\b", re.IGNORECASE)
ITEM_ID_RE = re.compile(r"\bITEM-[0-9]{4}\b", re.IGNORECASE)


@dataclass(frozen=True)
class ControllerDecision:
    action: dict
    decision: str
    reason: str
    retry_count: int = 0
    request_text: str = ""


class HybridController:
    """Resolve clear slots/intents, then enforce registered tool contracts."""

    version = "hybrid-controller-v2"

    def preflight(self, text: str, history: list[dict] | None = None) -> ControllerDecision | None:
        active_text, contextual_ids = self._active_context(text, history or [])
        boundary = self._boundary_action(active_text)
        if boundary:
            return ControllerDecision(boundary, "handoff", "security_or_financial_boundary", request_text=active_text)

        intent = self._intent(active_text)
        if intent not in {"lookup_order", "list_order_items", "eligibility", "refund_estimate", "ticket"}:
            return None

        order_ids = self._ids(ORDER_ID_RE, text) or contextual_ids["order_id"]
        if len(order_ids) > 1:
            return ControllerDecision(self._clarify("order_id", "Which order ID should I use?"),
                                      "clarification", "ambiguous_order_id", request_text=active_text)
        if intent != "ticket" and not order_ids:
            return ControllerDecision(self._clarify("order_id", "Please provide the order ID (for example, ORD-12345)."),
                                      "clarification", "missing_required_order_id", request_text=active_text)
        if intent == "ticket" and not self._ticket_issue_context(active_text):
            return ControllerDecision(self._clarify("ticket_details", "What issue should the support ticket describe?"),
                                      "clarification", "missing_ticket_issue_details", request_text=active_text)
        if intent == "ticket" and self._order_related_ticket(active_text) and not order_ids:
            return ControllerDecision(self._clarify("order_id", "Which order ID should this support ticket reference?"),
                                      "clarification", "missing_ticket_order_id", request_text=active_text)
        if intent in {"eligibility", "refund_estimate"} and not contextual_ids["item_id"] and not self._ids(ITEM_ID_RE, text) and self._needs_specific_item(active_text):
            return ControllerDecision(self._clarify("item_ids", "Please provide the item ID you want me to check."),
                                      "clarification", "missing_required_item_id", request_text=active_text)
        return None

    def apply(self, text: str, candidate: dict, history: list[dict] | None = None) -> ControllerDecision:
        history = history or []
        active_text, contextual_ids = self._active_context(text, history)
        boundary = self._boundary_action(active_text)
        if boundary:
            return ControllerDecision(boundary, "handoff", "security_or_financial_boundary", request_text=active_text)

        intent = self._intent(active_text)
        order_ids = self._ids(ORDER_ID_RE, text) or contextual_ids["order_id"]
        item_ids = self._ids(ITEM_ID_RE, text) or contextual_ids["item_id"]

        needs_order = intent in {"lookup_order", "list_order_items", "eligibility"} or (
            intent == "ticket" and self._order_related_ticket(active_text)
        )
        if needs_order and len(order_ids) > 1:
            return ControllerDecision(self._clarify("order_id", "Which order ID should I use?"),
                                      "clarification", "ambiguous_order_id", request_text=active_text)
        if intent in {"lookup_order", "list_order_items", "eligibility", "refund_estimate"} and not order_ids:
            return ControllerDecision(self._clarify("order_id", "Please provide the order ID (for example, ORD-12345)."),
                                      "clarification", "missing_required_order_id", request_text=active_text)

        if intent in {"eligibility", "refund_estimate"}:
            if not item_ids and self._needs_specific_item(active_text):
                return ControllerDecision(self._clarify("item_ids", "Please provide the item ID you want me to check."),
                                          "clarification", "missing_required_item_id", request_text=active_text)
            if intent == "refund_estimate":
                tool = "list_order_items"
                args = {"order_id": order_ids[0]}
                reason = "estimate_requires_trusted_eligibility_and_amount"
                ARGUMENT_SCHEMAS[tool].model_validate(args)
                return ControllerDecision(self._tool_action(tool, args, "Run the registered eligibility and estimate workflow."),
                                          "overridden", reason, request_text=active_text)
            if item_ids:
                tool = "check_refund_eligibility"
                args = {"order_id": order_ids[0], "item_ids": item_ids,
                        "reason": self._eligibility_reason(active_text)}
                reason = "eligibility_with_user_grounded_item_ids"
            else:
                # Listing first supplies authoritative item IDs to the existing
                # deterministic eligibility workflow.
                tool = "list_order_items"
                args = {"order_id": order_ids[0]}
                reason = "eligibility_requires_trusted_item_ids"
            ARGUMENT_SCHEMAS[tool].model_validate(args)
            action = self._tool_action(tool, args, "Apply the registered eligibility workflow.")
            return ControllerDecision(action, "overridden", reason, request_text=active_text)

        if intent in {"lookup_order", "list_order_items"}:
            args = {"order_id": order_ids[0]}
            ARGUMENT_SCHEMAS[intent].model_validate(args)
            action, decision = self._route_explicit_tool(candidate, intent, args)
            return ControllerDecision(action, decision, "clear_order_intent_and_grounded_id", request_text=active_text)

        if intent == "policy":
            args = {"category": self._policy_category(active_text)}
            ARGUMENT_SCHEMAS["get_return_policy"].model_validate(args)
            action, decision = self._route_explicit_tool(candidate, "get_return_policy", args)
            return ControllerDecision(action, decision, "clear_policy_intent", request_text=active_text)

        if intent == "ticket":
            if not self._ticket_issue_context(active_text):
                return ControllerDecision(self._clarify("ticket_details", "What issue should the support ticket describe?"),
                                          "clarification", "missing_ticket_issue_details", request_text=active_text)
            if self._order_related_ticket(active_text) and not order_ids:
                return ControllerDecision(self._clarify("order_id", "Which order ID should this support ticket reference?"),
                                          "clarification", "missing_ticket_order_id", request_text=active_text)
            if candidate.get("action_type") != "propose_state_change" or candidate.get("tool_name") != "create_support_ticket":
                return ControllerDecision(self._clarify("ticket_details", "What issue should the support ticket describe?"),
                                          "clarification", "ticket_proposal_not_validly_supplied", request_text=active_text)
            raw_args = candidate.get("arguments") or {}
            if not isinstance(raw_args, dict):
                return ControllerDecision(self._clarify("ticket_details", "Please provide the issue details for the support ticket."),
                                          "clarification", "ticket_arguments_not_an_object", request_text=active_text)
            properties = set(ARGUMENT_SCHEMAS["create_support_ticket"].model_fields)
            if set(raw_args) - properties:
                return ControllerDecision(self._clarify("ticket_details", "Please provide valid support ticket details."),
                                          "clarification", "ticket_unknown_argument", request_text=active_text)
            args = dict(raw_args)
            proposed_order = args.get("order_id")
            if self._order_related_ticket(active_text):
                # Order-linked tickets must use the unique order identifier from
                # the request/context. Model-invented or contradictory values fail closed.
                if len(order_ids) != 1:
                    return ControllerDecision(self._clarify("order_id", "Which order ID should this support ticket reference?"),
                                              "clarification", "ticket_order_id_not_unique", request_text=active_text)
                args["order_id"] = order_ids[0]
            elif proposed_order and proposed_order not in order_ids:
                # order_id is optional for generic tickets; discard model-only IDs.
                args["order_id"] = None
            try:
                checked = ARGUMENT_SCHEMAS["create_support_ticket"].model_validate(args).model_dump()
            except Exception:
                return ControllerDecision(self._clarify("ticket_details", "Please provide the issue details for the support ticket."),
                                          "clarification", "ticket_required_fields_invalid", request_text=active_text)
            normalized = dict(candidate, arguments=checked)
            decision = "accepted" if normalized == candidate else "repaired"
            # This is one deterministic, schema-grounded repair, not another model call.
            return ControllerDecision(normalized, decision, "ticket_remains_pending_approval",
                                      int(decision == "repaired"), active_text)

        if candidate.get("action_type") == "propose_state_change":
            action = {"action_type": "handoff", "reason": "unrequested_state_change",
                      "user_safe_message": "I can prepare a support ticket when you ask for one; no change was made."}
            return ControllerDecision(action, "handoff", "state_change_without_ticket_intent", request_text=active_text)

        if candidate.get("action_type") == "tool_call":
            name = candidate.get("tool_name")
            if name not in TOOL_REGISTRY or TOOL_REGISTRY[name].side_effect:
                return ControllerDecision(self._clarify("supported_request", "I couldn't safely match that to a supported request."),
                                          "clarification", "unknown_or_non_read_tool", request_text=active_text)
            raw_args = candidate.get("arguments") or {}
            if not isinstance(raw_args, dict):
                return ControllerDecision(self._clarify("tool_arguments", "I need more information to safely run that operation."),
                                          "clarification", "tool_arguments_not_an_object", request_text=active_text)
            allowed = set(ARGUMENT_SCHEMAS[name].model_fields)
            if set(raw_args) - allowed:
                return ControllerDecision(self._clarify("tool_arguments", "I need valid arguments to safely run that operation."),
                                          "clarification", "tool_unknown_argument", request_text=active_text)
            args = dict(raw_args)
            required = TOOL_REGISTRY[name].input_schema.model_json_schema().get("required", [])
            for field in required:
                if field == "order_id":
                    if len(order_ids) != 1:
                        return ControllerDecision(self._clarify(field, "Please provide the order ID (for example, ORD-12345)."),
                                                  "clarification", "tool_required_order_id_unavailable", request_text=active_text)
                    args[field] = order_ids[0]
                elif field == "item_ids":
                    if not item_ids:
                        return ControllerDecision(self._clarify(field, "Please provide the item ID(s), or ask me to list the order items first."),
                                                  "clarification", "tool_required_item_ids_unavailable", request_text=active_text)
                    args[field] = item_ids
                elif field == "reason" and field not in args:
                    args[field] = self._eligibility_reason(active_text)
            try:
                ARGUMENT_SCHEMAS[name].model_validate(args)
            except Exception:
                return ControllerDecision(self._clarify("tool_arguments", "I need more information to safely run that operation."),
                                          "clarification", "tool_arguments_invalid", request_text=active_text)
            if args != raw_args:
                repaired = dict(candidate, arguments=args)
                return ControllerDecision(repaired, "repaired", "grounded_identifier_normalization", 1, active_text)
        return ControllerDecision(candidate, "accepted", "no_deterministic_override", request_text=active_text)

    @staticmethod
    def _route_explicit_tool(candidate: dict, tool_name: str, arguments: dict) -> tuple[dict, str]:
        if candidate.get("action_type") == "tool_call" and candidate.get("tool_name") == tool_name:
            raw_args = candidate.get("arguments") or {}
            allowed = set(ARGUMENT_SCHEMAS[tool_name].model_fields)
            if not isinstance(raw_args, dict) or set(raw_args) - allowed:
                return HybridController._clarify("tool_arguments", "I need valid arguments to safely run that operation."), "clarification"
            # The request supplies the authoritative identifier/category. A model-only
            # identifier is replaced; unknown properties are rejected above.
            if raw_args == arguments:
                return candidate, "accepted"
            return HybridController._tool_action(tool_name, arguments, "Use the registered operation for the explicit request."), "overridden"
        return HybridController._tool_action(tool_name, arguments, "Use the registered operation for the explicit request."), "overridden"

    @staticmethod
    def _tool_action(tool_name: str, arguments: dict, reason: str) -> dict:
        return {"action_type": "tool_call", "tool_name": tool_name, "arguments": arguments,
                "reason_summary": reason}

    @staticmethod
    def _required_fields(tool_name: str) -> set[str]:
        return set(TOOL_REGISTRY[tool_name].input_schema.model_json_schema().get("required", []))

    @staticmethod
    def _ids(pattern: re.Pattern, text: str) -> list[str]:
        return sorted({value.upper() for value in pattern.findall(text or "")})

    @staticmethod
    def _active_context(text: str, history: list[dict]) -> tuple[str, dict[str, list[str]]]:
        active_text = text
        if history and history[-1].get("role") == "assistant" and HybridController._clarification_slot(history[-1].get("content", "")):
            prior_users = []
            for message in reversed(history):
                if message.get("role") == "assistant":
                    if not HybridController._clarification_slot(message.get("content", "")):
                        break
                elif message.get("role") == "user":
                    prior_users.append(message.get("content", ""))
            active_text = "\n".join([*reversed(prior_users), text])
        return active_text, {
            "order_id": HybridController._ids(ORDER_ID_RE, active_text),
            "item_id": HybridController._ids(ITEM_ID_RE, active_text),
        }

    @staticmethod
    def _clarification_slot(text: str) -> str | None:
        lowered = text.lower()
        if "item id" in lowered:
            return "item_id"
        if "order id" in lowered:
            return "order_id"
        if "support ticket" in lowered and ("issue" in lowered or "describe" in lowered):
            return "ticket_details"
        return None

    @staticmethod
    def _intent(text: str) -> str | None:
        lowered = text.lower()
        if any(term in lowered for term in ("ticket", "open a case", "contact support", "support case")) or (
            "support" in lowered and any(verb in lowered for verb in ("open", "create", "raise", "need", "prepare", "start"))
        ):
            return "ticket"
        if any(term in lowered for term in ("refund estimate", "estimate the refund", "estimated refund", "estimate a refund", "calculate a refund", "refund calculation", "estimated return amount", "return amount estimate")):
            return "refund_estimate"
        if "policy" in lowered or any(term in lowered for term in ("return window", "return period", "return terms", "return deadline")):
            return "policy"
        if any(term in lowered for term in ("eligible", "eligibility", "can i return", "return this item", "refund estimate", "estimate the refund")):
            return "eligibility"
        if any(term in lowered for term in ("items", "what did i order", "products", "list the order")):
            return "list_order_items"
        if any(term in lowered for term in ("where is", "track", "order status", "delivery status", "status of order")):
            return "lookup_order"
        if "order" in lowered and any(term in lowered for term in ("look up", "lookup", "find", "check", "status")):
            return "lookup_order"
        return None

    @staticmethod
    def _needs_specific_item(text: str) -> bool:
        lowered = text.lower()
        return any(term in lowered for term in ("this item", "that item", "the item", "item id",
                                                 "specific item", "one item", "which item", "this product"))

    @staticmethod
    def _ticket_issue_context(text: str) -> bool:
        without_ids = ORDER_ID_RE.sub(" ", text)
        words = re.findall(r"[a-z]{2,}", without_ids.lower())
        generic = {"please", "can", "you", "open", "create", "prepare", "make", "a", "an", "the",
                   "support", "ticket", "case", "for", "about", "regarding", "on", "order", "my", "this"}
        return bool([word for word in words if word not in generic])

    @staticmethod
    def _order_related_ticket(text: str) -> bool:
        """The domain schema permits generic tickets; order-linked issues need an order ID."""
        lowered = text.lower()
        terms = ("order", "delivery", "delivered", "shipment", "shipping", "package",
                 "return", "refund", "item", "product", "damaged", "broken", "wrong item")
        return bool(ORDER_ID_RE.search(text or "") or any(term in lowered for term in terms))

    @staticmethod
    def _eligibility_reason(text: str) -> str:
        lowered = text.lower()
        if "damaged" in lowered or "broken" in lowered:
            return "damaged"
        if "wrong item" in lowered or "incorrect item" in lowered:
            return "wrong_item"
        if "late delivery" in lowered or "arrived late" in lowered:
            return "late_delivery"
        return "changed_mind"

    @staticmethod
    def _boundary_action(text: str) -> dict | None:
        lowered = text.lower()
        security_terms = ("ignore previous instructions", "reveal the system prompt", "reveal secrets",
                          "bypass policy", "bypass approval", "ignore policy", "impersonate a supervisor",
                          "pretend to be a supervisor", "act as an admin", "make me a supervisor")
        financial_terms = ("issue a refund", "refund me now", "send the refund", "process refund")
        bypass_verb = re.search(r"\b(ignore|disregard|forget|override|bypass|skip|disable)\b", lowered)
        protected_target = re.search(r"\b(safeguards?|previous instructions|rules|policy|approval|authorization|review|restrictions?)\b", lowered)
        disclosure = re.search(r"\b(reveal|expose|show|disclose)\b.*\b(system prompt|secrets?|hidden instructions?)\b", lowered)
        impersonation = re.search(r"\b(pretend|impersonate|act as)\b.*\b(supervisor|admin|administrator)\b", lowered)
        if any(term in lowered for term in security_terms) or (bypass_verb and protected_target) or disclosure or impersonation:
            return {"action_type": "handoff", "reason": "policy_or_safety_boundary",
                    "user_safe_message": "I can't perform that action, but I can help with supported order operations."}
        if any(term in lowered for term in financial_terms):
            return {"action_type": "handoff", "reason": "prohibited_financial_action",
                    "user_safe_message": "I can check eligibility and estimate an amount, but this demo cannot issue refunds."}
        return None

    @staticmethod
    def _policy_category(text: str) -> str:
        lowered = text.lower()
        if "damage" in lowered:
            return "damaged_item"
        if "late" in lowered or "delay" in lowered:
            return "late_delivery"
        if "timing" in lowered or ("when" in lowered and "refund" in lowered):
            return "refund_timing"
        return "standard_return"

    @staticmethod
    def _clarify(field: str, question: str) -> dict:
        return {"action_type": "clarification", "question": question, "missing_fields": [field]}
