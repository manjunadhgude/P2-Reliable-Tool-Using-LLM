"""One-shot dev candidate for broader, fail-closed intent and slot recognition.

This candidate is compared once with the frozen v2 controller using saved V5
development proposals and a separate prompt-first review overlay. It is not
enabled in the application unless it passes the predeclared development gate.
"""

import re

from app.hybrid_controller import HybridController, ORDER_ID_RE


class HybridControllerV3Candidate(HybridController):
    version = "hybrid-controller-v3-dev-candidate"

    @staticmethod
    def _intent(text: str) -> str | None:
        lowered = text.lower()
        order_count = len(HybridController._ids(ORDER_ID_RE, text))

        ticket_action = any(verb in lowered for verb in (
            "open", "create", "raise", "prepare", "start", "record", "file", "submit",
        ))
        ticket_subject = any(noun in lowered for noun in (
            "ticket", "case", "service request", "support issue", "support",
        ))
        if ticket_action and ticket_subject:
            return "ticket"

        if any(term in lowered for term in (
            "refund estimate", "estimate the refund", "estimated refund", "estimate a refund",
            "calculate a refund", "refund calculation", "estimated return amount",
            "return amount estimate", "expected refund", "refund amount",
        )):
            return "refund_estimate"

        specific_item_context = any(term in lowered for term in (
            "particular product", "unspecified item", "one product", "specific item",
            "which item", "this item", "that item", "the item", "item id",
        ))
        if specific_item_context or any(term in lowered for term in (
            "eligible", "eligibility", "qualifies for return", "qualify for return",
            "can i return", "can the customer send", "return this item", "returnable",
        )):
            return "eligibility"

        if any(term in lowered for term in (
            "policy", "return window", "return period", "return terms", "return deadline",
            "return conditions", "usual process", "time limit for returns",
            "sending an item back", "sending a product back", "return process",
        )):
            return "policy"

        if any(term in lowered for term in (
            "items", "what did i order", "products", "product list", "merchandise",
            "order contents", "line items", "item inventory", "goods billed",
        )):
            return "list_order_items"

        if order_count > 1:
            return "lookup_order"

        if any(term in lowered for term in (
            "where is", "track", "order status", "delivery status", "status of order",
            "delivery update", "where my package", "package without an order",
            "delivery question",
        )):
            return "lookup_order"
        if "order" in lowered and any(term in lowered for term in ("look up", "lookup", "find", "check", "status")):
            return "lookup_order"
        return None

    @staticmethod
    def _needs_specific_item(text: str) -> bool:
        lowered = text.lower()
        return any(term in lowered for term in (
            "this item", "that item", "the item", "item id", "specific item", "one item",
            "which item", "this product", "particular product", "unspecified item",
            "one product",
        ))

    @staticmethod
    def _ticket_issue_context(text: str) -> bool:
        without_ids = ORDER_ID_RE.sub(" ", text)
        words = re.findall(r"[a-z]{2,}", without_ids.lower())
        generic = {
            "please", "can", "you", "open", "create", "prepare", "make", "raise", "start",
            "record", "file", "submit", "a", "an", "the", "support", "ticket", "case",
            "service", "request", "issue", "problem", "linked", "linking", "concerning",
            "for", "about", "regarding", "on", "to", "order", "my", "this",
        }
        return bool([word for word in words if word not in generic])
