"""Explicit intent-to-workflow preflight candidate (opt-in only).

Clear, supported requests are converted into validated actions before model
generation. The model remains available for ambiguous/general conversation;
authorization, tools, policy, and approval remain server-owned.
"""

from app.hybrid_controller_v6_candidate import HybridControllerV6Candidate


class HybridControllerV7Candidate(HybridControllerV6Candidate):
    version = "hybrid-controller-v7-intent-workflow-preflight-candidate"

    def preflight(self, text: str, history: list[dict] | None = None):
        # V6 already handles safety boundaries, ambiguous identifiers, and
        # required-slot clarification. Preserve that priority ordering.
        guarded = super().preflight(text, history)
        if guarded is not None:
            return guarded
        active_text, _context = self._active_context(text, history or [])
        intent = self._intent(active_text)
        if intent is None:
            return None
        # Reuse the exact schema-checked decision policy used after proposals,
        # supplying a neutral candidate. Clear requests no longer depend on the
        # small model selecting a tool or fabricating the missing slots.
        neutral = {"action_type": "final_answer", "answer": "", "claims": [], "needs_human_review": False}
        decision = self.apply(text, neutral, history)
        if decision.action.get("action_type") in {"tool_call", "clarification", "handoff", "propose_state_change"}:
            return type(decision)(decision.action, "preflight_" + decision.decision, "intent_plan:" + decision.reason,
                                  decision.retry_count, decision.request_text)
        return None
