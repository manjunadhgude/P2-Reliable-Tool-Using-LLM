"""Focused follow-up to V5 based on its paired replay and app traces.

This version only changes intent ambiguity resolution and missing-slot checks;
it preserves V5's explicit workflow plan and ticket safety boundary.
"""

import re

from app.hybrid_controller import ControllerDecision, ITEM_ID_RE, ORDER_ID_RE
from app.hybrid_controller_v5_candidate import HybridControllerV5Candidate


class HybridControllerV6Candidate(HybridControllerV5Candidate):
    version = "hybrid-controller-v6-ambiguity-and-intent-candidate"

    @staticmethod
    def _intent(text: str) -> str | None:
        has_item = bool(ITEM_ID_RE.search(text or ""))
        lowered = ORDER_ID_RE.sub(" ", text or "")
        lowered = ITEM_ID_RE.sub(" ", lowered).casefold()

        if re.search(r"\b(how much|what amount|amount .* back|money .* back|estimate|calculate|expected .* back|refund value|return value|value .* return|work out .* value)\b", lowered) and re.search(
            r"\b(refund|return|money|amount|back|credit|value)\b", lowered
        ):
            return "refund_estimate"

        # A named item plus a return decision is an eligibility question even
        # when the user calls the governing rules a "policy result".
        return_language = re.search(r"\b(return|send .* back|sending .* back|eligible|qualif\w*|assess|apply .* rules)\b", lowered)
        specific_item = re.search(r"\b(this|that|the|particular|specific|unspecified|which|one)\s+(item|product)\b", lowered)
        if (has_item and return_language) or (specific_item and return_language):
            return "eligibility"

        # Generic duration/conditions questions resolve to policy retrieval;
        # item-specific decisions were handled above.
        if re.search(r"\b(how long|time limit|time window|conditions|terms|policy|process)\b", lowered) and re.search(
            r"\b(return|goods|standard|unused|item|product|back)\b", lowered
        ):
            return "policy"

        return HybridControllerV5Candidate._intent(text)

    @staticmethod
    def _boundary_action(text: str):
        inherited = HybridControllerV5Candidate._boundary_action(text)
        if inherited:
            return inherited
        lowered = (text or "").casefold()
        if re.search(r"\b(erase|remove|alter|modify)\b", lowered) and re.search(
            r"\b(order|account|customer|record|data|database)\b", lowered
        ):
            return {"action_type": "handoff", "reason": "unsupported_registered_operation",
                    "user_safe_message": "That operation is not available in this demo. No change was made."}
        return None

    def preflight(self, text: str, history: list[dict] | None = None):
        active_text, _ = self._active_context(text, history or [])
        ids = self._ids(ORDER_ID_RE, active_text)
        if len(ids) > 1 and re.search(r"\b(either|which|choose|clarify|mean|two|both|compare)\b", active_text.casefold()):
            return ControllerDecision(
                self._clarify("order_id", f"Which order ID should I use: {' or '.join(ids)}?"),
                "clarification", "conflicting_order_ids_require_user_choice", request_text=active_text,
            )
        return super().preflight(text, history)

    @staticmethod
    def _needs_specific_item(text: str) -> bool:
        words = ITEM_ID_RE.sub(" ", text or "").casefold()
        return bool(re.search(
            r"\b(this|that|the|specific|particular|unspecified|one|which)\s+(?:purchase\s+)?(?:item|product)\b|\bitem\s+(?:id|number)\b",
            words,
        ))

    @staticmethod
    def _issue_type(issue: str) -> str:
        lowered = issue.casefold()
        if "incorrect product" in lowered or "wrong product" in lowered or "incorrect item" in lowered:
            return "wrong_item"
        return HybridControllerV5Candidate._issue_type(issue)
