"""Structured intent input and deterministic workflow planning.

The model may classify a request and copy candidate spans. It cannot choose
authorization, business outcomes, arbitrary tools, or final business claims.
"""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.hybrid_controller import ControllerDecision, HybridController, ITEM_ID_RE, ORDER_ID_RE
from app.hybrid_controller_v4_candidate import HybridControllerV4Candidate
from app.tools.domain import ARGUMENT_SCHEMAS


class IntentEnvelope(BaseModel):
    """Closed-set model output. Every identifier must be copied from user text."""

    model_config = ConfigDict(extra="forbid", strict=True)

    intent: Literal[
        "lookup_order", "list_order_items", "return_policy", "eligibility",
        "refund_estimate", "support_ticket", "smalltalk", "unsupported", "ambiguous",
    ]
    order_ids: list[str] = Field(max_length=4)
    item_ids: list[str] = Field(max_length=20)
    item_scope: Literal["all", "specific", "unknown"]
    requested_outputs: list[Literal["order_status", "items", "policy", "eligibility", "estimate"]] = Field(max_length=5)
    policy_category: Literal["standard_return", "damaged_item", "late_delivery", "refund_timing"] | None
    reason: Literal["changed_mind", "damaged", "wrong_item", "late_delivery"] | None
    issue_quote: str | None = Field(max_length=240)


class StructuredIntentWorkflowController:
    """Map validated intent and user-grounded spans to fixed application actions."""

    version = "structured-intent-workflow-v1-candidate"
    _id_token = re.compile(r"\b(?:ORD|ITEM)-[A-Z0-9-]+\b", re.IGNORECASE)

    def __init__(self) -> None:
        self._followups: tuple[str, ...] = ()
        self.intent_payload: dict | None = None

    def preflight(self, text: str, history: list[dict] | None = None) -> ControllerDecision | None:
        active_text, _ = HybridController._active_context(text, history or [])
        boundary = HybridController._boundary_action(active_text)
        if boundary:
            return ControllerDecision(boundary, "handoff", "security_or_financial_boundary", request_text=active_text)
        return None

    def follow_up_tools(self, _text: str = "") -> tuple[str, ...]:
        return self._followups

    def plan(self, text: str, intent: IntentEnvelope, history: list[dict] | None = None) -> ControllerDecision:
        active_text, context = HybridController._active_context(text, history or [])
        self.intent_payload = intent.model_dump()
        self._followups = ()

        boundary = HybridController._boundary_action(active_text)
        if boundary:
            return self._decision(boundary, "handoff", "security_or_financial_boundary", active_text)

        explicit_all_items = bool(re.search(
            r"\b(?:all|every|each)\b.{0,30}\b(?:items?|products?)\b|\b(?:items?|products?)\b.{0,30}\b(?:all|every|each)\b",
            active_text, re.IGNORECASE,
        ))
        mentioned = {value.upper() for value in self._id_token.findall(active_text)}
        order_ids_are_relevant = intent.intent in {
            "lookup_order", "list_order_items", "eligibility", "refund_estimate", "support_ticket",
        }
        item_ids_are_relevant = intent.intent in {"eligibility", "refund_estimate"} and not explicit_all_items
        supplied = {
            value.upper()
            for value in (
                (intent.order_ids if order_ids_are_relevant else [])
                + (intent.item_ids if item_ids_are_relevant else [])
            )
        }
        if not supplied.issubset(mentioned):
            return self._clarify("identifier_grounding", "Please provide the order or item ID you want me to use.", active_text)

        order_ids = sorted({value.upper() for value in ORDER_ID_RE.findall(active_text)}) or context["order_id"]
        item_ids = sorted({value.upper() for value in ITEM_ID_RE.findall(active_text)}) or context["item_id"]
        malformed_order = any(t.upper().startswith("ORD-") and not ORDER_ID_RE.fullmatch(t) for t in self._id_token.findall(active_text))
        malformed_item = any(t.upper().startswith("ITEM-") and not ITEM_ID_RE.fullmatch(t) for t in self._id_token.findall(active_text))
        needs_order = intent.intent in {"lookup_order", "list_order_items", "eligibility", "refund_estimate"}

        if intent.intent in {"ambiguous", "unsupported"}:
            return self._clarify("supported_request", "I couldn't safely identify a supported request. Could you clarify what you need?", active_text)
        if intent.intent == "smalltalk":
            return self._decision({
                "action_type": "final_answer",
                "answer": "I can look up synthetic orders, list items, retrieve return policy, check return eligibility, estimate a refund, or prepare a support ticket for approval.",
                "claims": [], "needs_human_review": False,
            }, "planned", "closed_set_smalltalk", active_text)

        if needs_order and (malformed_order or len(order_ids) != 1):
            question = "Please provide a valid order ID." if malformed_order else "Which order ID should I use?" if len(order_ids) > 1 else "Please provide the order ID (for example, ORD-10021)."
            return self._clarify("order_id", question, active_text)
        if malformed_item:
            return self._clarify("item_ids", "Please provide a valid item ID, or tell me to check all items on the order.", active_text)

        # A model label alone cannot expand a specific request into a bulk
        # operation. Only explicit all/every/each wording establishes that scope.
        item_scope = "specific" if item_ids else "all" if explicit_all_items else "unknown"

        if intent.intent == "lookup_order":
            return self._tool("lookup_order", {"order_id": order_ids[0]}, active_text)

        if intent.intent == "return_policy":
            category = self._policy_category_from_user_text(active_text)
            return self._tool("get_return_policy", {"category": category}, active_text)

        if intent.intent in {"eligibility", "refund_estimate", "list_order_items"}:
            if intent.intent == "list_order_items" and "eligibility" not in intent.requested_outputs and "estimate" not in intent.requested_outputs:
                return self._tool("list_order_items", {"order_id": order_ids[0]}, active_text)

            wants_eligibility = intent.intent in {"eligibility", "refund_estimate"} or "eligibility" in intent.requested_outputs
            wants_estimate = intent.intent == "refund_estimate" or "estimate" in intent.requested_outputs
            wants_items = intent.intent == "list_order_items" or "items" in intent.requested_outputs
            if intent.intent == "list_order_items":
                self._followups = (("check_refund_eligibility",) if wants_eligibility else ()) + (
                    ("calculate_refund_estimate",) if wants_estimate else ()
                )
                return self._tool("list_order_items", {"order_id": order_ids[0]}, active_text)
            if item_ids and wants_items:
                self._followups = ("check_refund_eligibility",) + (
                    ("calculate_refund_estimate",) if wants_estimate else ()
                )
                return self._tool("list_order_items", {"order_id": order_ids[0]}, active_text)
            if not item_ids and item_scope != "all":
                return self._clarify("item_ids", "Which item should I check, or do you want me to check all items on the order?", active_text)
            if item_ids:
                self._followups = ("calculate_refund_estimate",) if wants_estimate else ()
                if wants_estimate:
                    # Verify the item belongs to the stated order before eligibility.
                    self._followups = ("check_refund_eligibility", "calculate_refund_estimate")
                    return self._tool("list_order_items", {"order_id": order_ids[0]}, active_text)
                return self._tool("check_refund_eligibility", {
                    "order_id": order_ids[0], "item_ids": item_ids,
                    "reason": self._reason_from_user_text(active_text),
                }, active_text)
            self._followups = ("check_refund_eligibility",) + (("calculate_refund_estimate",) if wants_estimate else ())
            return self._tool("list_order_items", {"order_id": order_ids[0]}, active_text)

        if intent.intent == "support_ticket":
            issue = intent.issue_quote
            if not issue or issue.casefold() not in active_text.casefold() or len(issue.strip()) < 8:
                return self._clarify("ticket_details", "What specific problem should the support ticket describe?", active_text)
            related_to_order = bool(re.search(r"\b(order|purchase|shipment|delivery)\b", active_text, re.IGNORECASE))
            if related_to_order and len(order_ids) != 1:
                return self._clarify("order_id", "Which order should this support ticket reference?", active_text)
            issue = issue.strip()
            args = {
                "order_id": order_ids[0] if len(order_ids) == 1 else None,
                "issue_type": HybridControllerV4Candidate._issue_type(issue),
                "summary": issue[:157] + ("..." if len(issue) > 160 else ""),
                "description": issue[:1000],
                "priority": "normal",
            }
            return self._action({
                "action_type": "propose_state_change", "tool_name": "create_support_ticket",
                "arguments": args, "reason_summary": "Prepare the user-described issue for supervisor approval.",
            }, "planned", "user_grounded_ticket_proposal", active_text)

        return self._clarify("supported_request", "I couldn't safely map that request to an available operation.", active_text)

    @staticmethod
    def _action(action: dict, status: str, reason: str, text: str) -> ControllerDecision:
        kind = action.get("action_type")
        if kind in {"tool_call", "propose_state_change"}:
            ARGUMENT_SCHEMAS[action["tool_name"]].model_validate(action["arguments"])
        return ControllerDecision(action, status, reason, request_text=text)

    @classmethod
    def _tool(cls, name: str, arguments: dict, text: str) -> ControllerDecision:
        return cls._action({
            "action_type": "tool_call", "tool_name": name, "arguments": arguments,
            "reason_summary": "Execute the validated registered workflow.",
        }, "planned", "structured_intent_workflow", text)

    @staticmethod
    def _decision(action: dict, status: str, reason: str, text: str) -> ControllerDecision:
        return ControllerDecision(action, status, reason, request_text=text)

    @classmethod
    def _clarify(cls, field: str, question: str, text: str) -> ControllerDecision:
        return cls._decision({
            "action_type": "clarification", "question": question, "missing_fields": [field],
        }, "clarification", "structured_intent_requires_clarification", text)

    @staticmethod
    def _reason_from_user_text(text: str) -> str:
        lowered = text.casefold()
        if any(term in lowered for term in ("damaged", "broken")):
            return "damaged"
        if any(term in lowered for term in ("wrong item", "incorrect item", "wrong product")):
            return "wrong_item"
        if any(term in lowered for term in ("late delivery", "arrived late", "delayed", "delay")):
            return "late_delivery"
        return "changed_mind"

    @staticmethod
    def _policy_category_from_user_text(text: str) -> str:
        lowered = text.casefold()
        if any(term in lowered for term in ("damaged", "broken")):
            return "damaged_item"
        if any(term in lowered for term in ("late delivery", "arrived late", "delayed", "delay")):
            return "late_delivery"
        if "refund timing" in lowered or "refund time" in lowered:
            return "refund_timing"
        return "standard_return"
