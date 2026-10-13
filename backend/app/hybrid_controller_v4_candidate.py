"""Fail-closed controller candidate with grounded ticket proposals.

This remains opt-in. It builds on the reviewed V3 candidate and does not alter
the CI/default controller or any frozen benchmark configuration.
"""

import re

from app.hybrid_controller import ITEM_ID_RE, ORDER_ID_RE
from app.hybrid_controller_v3_candidate import HybridControllerV3Candidate
from app.tools.domain import ARGUMENT_SCHEMAS


class HybridControllerV4Candidate(HybridControllerV3Candidate):
    version = "hybrid-controller-v4-grounded-ticket-candidate"

    @staticmethod
    def _intent(text: str) -> str | None:
        lowered = ORDER_ID_RE.sub(" ", text or "")
        lowered = ITEM_ID_RE.sub(" ", lowered).casefold()

        # More specific calculations outrank generic policy/eligibility wording.
        if re.search(r"\b(estimate|estimated|calculate|calculation|compute|work out)\b.{0,60}\b(refund|amount|return amount|comes back)\b|\b(refund|return amount|refund value|refund amount)\b.{0,50}\b(estimate|estimated|calculate|calculation|compute|expect|anticipate)\b|\bwhat amount might be refunded\b", lowered):
            return "refund_estimate"

        ticket_action = re.search(r"\b(open|create|raise|prepare|start|record|file|submit)\b", lowered)
        ticket_subject = re.search(r"\b(ticket|case|service request|support issue|support request)\b", lowered)
        if ticket_action and ticket_subject:
            return "ticket"

        # Security/financial-boundary detection is run before this classifier by
        # preflight/apply; eligibility/calculation outrank general policy.
        if re.search(r"\b(eligible|eligibility|qualif(?:y|ies|ies for)|can .* return(?:ed)?|returnable|returnability|returned|meet the return rules)\b", lowered) or (
            ITEM_ID_RE.search(text or "") and re.search(r"\b(assess|check|review)\b", lowered)
            and re.search(r"\b(damaged|broken|wrong item|late|delayed)\b", lowered)
        ):
            return "eligibility"
        if re.search(r"\b(policy|return window|time window|return period|return terms|return deadline|deadline|usual process|time limit|return process|how long do i have)\b", lowered) and re.search(r"\b(return|send back|sending back|unused|policy|item|how long)\b", lowered):
            return "policy"
        if re.search(r"\b(items?|products?|merchandise|contents|lines|line items|enumerate|line-by-line|what .* bought|what .* ordered|what was included|show .* product|product list)\b", lowered):
            return "list_order_items"

        has_order_reference = bool(ORDER_ID_RE.search(text or ""))
        if has_order_reference and re.search(r"\b(first|before|prior to)\b.{0,80}\b(then|next|decid|return|eligib)\b", lowered):
            return "list_order_items"
        if len(HybridControllerV3Candidate._ids(ORDER_ID_RE, text)) > 1:
            return "lookup_order"
        if has_order_reference and re.search(r"\b(look up|lookup|find|check|inspect|review|track|status|where|delivery|shipment)\b", lowered):
            return "lookup_order"
        if re.search(r"\b(where is|track|trace|order status|delivery status|status of order|delivery update|delivery progress|package|box|parcel|consignment)\b", lowered):
            return "lookup_order"
        if has_order_reference and re.search(r"\b(retrieve|access|report|inspect|review)\b", lowered):
            return "lookup_order"
        return None

    @staticmethod
    def _needs_specific_item(text: str) -> bool:
        lowered = text.casefold()
        return HybridControllerV3Candidate._needs_specific_item(text) or any(
            term in lowered for term in ("particular item", "particular product", "specific product")
        )

    @staticmethod
    def _eligibility_reason(text: str) -> str:
        lowered = text.casefold()
        if any(term in lowered for term in ("damaged", "broken")):
            return "damaged"
        if "wrong item" in lowered or "incorrect item" in lowered:
            return "wrong_item"
        if any(term in lowered for term in ("late delivery", "arrived late", "arriving late", "late arrival", "delayed", "past its expected")) or re.search(r"\b(late|delay)\b", lowered):
            return "late_delivery"
        return "changed_mind"

    @staticmethod
    def _ticket_issue_context(text: str) -> bool:
        return bool(HybridControllerV4Candidate._grounded_issue(text))

    @staticmethod
    def _grounded_issue(text: str) -> str:
        """Return a concise issue phrase from the user's words, never model text."""
        value = ORDER_ID_RE.sub(" ", text or "")
        value = re.sub(r"(?i)\s*\bReference\s+\d+\.?\s*$", " ", value)
        value = re.sub(r"(?i)^\s*(?:please\s+)?(?:can you\s+)?(?:open|create|raise|prepare|start|record|file|submit)\s+", "", value)
        value = re.sub(r"(?i)^\s*(?:a|an|the)\s+", "", value)
        value = re.sub(r"(?i)\b(?:pending|support|ticket|case|customer|service|service request|support issue|issue|request)\b", " ", value)
        value = re.sub(r"(?i)\b(?:linked to|linking|concerning|regarding|about|for|on|my|this|order)\b", " ", value)
        value = re.sub(r"[^A-Za-z0-9' -]", " ", value)
        value = re.sub(r"\s+", " ", value).strip(" -")
        words = re.findall(r"[A-Za-z]{2,}", value)
        if not words:
            return ""
        phrase = " ".join(words[:12]).strip()
        if phrase.casefold() in {"the", "item", "product", "order", "damaged", "support", "customer service"}:
            return ""
        # Generic ticket language plus a reference number is not an issue.
        return phrase if len(phrase) >= 5 else ""

    def apply(self, text: str, candidate: dict, history: list[dict] | None = None):
        decision = super().apply(text, candidate, history)
        if decision.action.get("action_type") != "propose_state_change":
            return decision

        active_text = decision.request_text or text
        issue = self._grounded_issue(active_text)
        if not issue:
            return type(decision)(
                self._clarify("ticket_details", "What specific problem should the support ticket describe?"),
                "clarification", "ticket_issue_not_grounded_in_request", request_text=active_text,
            )

        # Derive all free-text business fields from the user request. Ignore
        # model-invented or synthetic wrapper content such as "Reference 28.".
        raw = decision.action.get("arguments") or {}
        issue_type = self._issue_type(issue)
        args = {
            "order_id": raw.get("order_id"),
            "issue_type": issue_type,
            "summary": issue[:157] + ("..." if len(issue) > 160 else ""),
            "description": issue[:1000],
            "priority": raw.get("priority", "normal"),
        }
        try:
            checked = ARGUMENT_SCHEMAS["create_support_ticket"].model_validate(args).model_dump()
        except Exception:
            return type(decision)(
                self._clarify("ticket_details", "Please provide a specific problem for the support ticket."),
                "clarification", "ticket_grounded_arguments_invalid", request_text=active_text,
            )
        action = dict(decision.action, arguments=checked)
        changed = action != decision.action
        return type(decision)(action, "repaired" if changed else decision.decision,
                              "ticket_arguments_grounded_in_user_request", int(changed), active_text)

    @staticmethod
    def _issue_type(issue: str) -> str:
        lowered = issue.casefold()
        if "damag" in lowered or "broken" in lowered:
            return "damaged_item"
        if "wrong item" in lowered or "incorrect item" in lowered or "missing product" in lowered:
            return "wrong_item"
        if any(word in lowered for word in ("delivery", "shipment", "shipping", "package", "late")):
            return "delivery_delay"
        if "return" in lowered or "refund" in lowered:
            return "return_question"
        return "other"
