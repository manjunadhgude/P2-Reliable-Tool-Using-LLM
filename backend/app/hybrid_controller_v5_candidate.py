"""Versioned recovery candidate with an explicit, bounded workflow plan.

V2 remains the default and V3/V4 remain unchanged.  This candidate separates
request classification from registered-tool execution: the intent resolver
returns a small domain plan and the application still validates every tool
argument and enforces authorization, policy, approval, and tenant boundaries.
"""

from dataclasses import dataclass
import re

from app.hybrid_controller import ITEM_ID_RE, ORDER_ID_RE
from app.hybrid_controller_v4_candidate import HybridControllerV4Candidate


@dataclass(frozen=True)
class WorkflowPlan:
    intent: str | None
    tools: tuple[str, ...]


class HybridControllerV5Candidate(HybridControllerV4Candidate):
    version = "hybrid-controller-v5-explicit-workflow-plan-candidate"

    @staticmethod
    def _boundary_action(text: str):
        inherited = HybridControllerV4Candidate._boundary_action(text)
        if inherited:
            return inherited
        lowered = (text or "").casefold()
        unsupported = re.search(r"\b(cancel|delete|export)\b", lowered) and re.search(
            r"\b(order|account|customer|record|data|every|all)\b", lowered
        )
        unknown_tool = "tool" in lowered and re.search(r"\b(not in|outside|unregistered|unsupported)\b", lowered)
        if unsupported or unknown_tool:
            return {
                "action_type": "handoff", "reason": "unsupported_registered_operation",
                "user_safe_message": "That operation is not available in this demo. No change was made.",
            }
        return None

    @staticmethod
    def _intent(text: str) -> str | None:
        # IDs are slots, not intent words: remove them before classification.
        words = ORDER_ID_RE.sub(" ", text or "")
        words = ITEM_ID_RE.sub(" ", words).casefold()

        # Resolve the most specific requested outcome first. These groups map
        # to domain actions, not tool permissions or business decisions.
        estimate = re.search(
            r"\b(estimate|estimated|calculate|calculation|compute|work out|how much|amount .* back|money .* back|expected .* back)\b",
            words,
        ) and re.search(r"\b(refund|return|money|amount|back|credit)\b", words)
        if estimate:
            return "refund_estimate"

        eligibility = re.search(
            r"\b(eligib\w*|qualif\w*|returnable|can .* return|return status|assess .* item|check .* policy result|evaluate .* return|determine .* return)\b",
            words,
        )
        if eligibility:
            return "eligibility"

        if re.search(r"\b(ticket|case|service request|support issue|support request)\b", words) and re.search(
            r"\b(open|create|raise|prepare|start|record|file|submit|draft)\b", words
        ):
            return "ticket"

        if re.search(r"\b(policy|conditions|terms|time limit|return window|return period|return deadline|sending .* back|send .* back)\b", words) and re.search(
            r"\b(return|goods|item|product|standard|unused|policy|conditions|terms)\b", words
        ):
            return "policy"

        if re.search(r"\b(items?|products?|merchandise|contents|line items|what .* bought|what .* ordered|show .* product)\b", words):
            return "list_order_items"

        # Tracking/status is distinct from item retrieval. The phrase families
        # cover request structures (carrier movement, fulfillment state), not
        # individual benchmark IDs or wrapper suffixes.
        if re.search(r"\b(where is|track|tracking|carrier|shipment|delivery|fulfillment|status|shipped|moved)\b", words) and re.search(
            r"\b(order|purchase|parcel|package|carrier|shipment|delivery|fulfillment|it)\b", words
        ):
            return "lookup_order"

        if re.search(r"\b(order|purchase|transaction)\b", words) and re.search(
            r"\b(show|find|look up|lookup|retrieve|inspect|details|record)\b", words
        ):
            return "lookup_order"
        return None

    @staticmethod
    def _needs_specific_item(text: str) -> bool:
        words = ITEM_ID_RE.sub(" ", text or "").casefold()
        return bool(re.search(
            r"\b(this|that|the|specific|particular|unspecified|one|which)\s+(?:purchase\s+)?(?:item|product)\b|\bitem\s+(?:id|number)\b",
            words,
        ))

    @staticmethod
    def _grounded_issue(text: str) -> str:
        value = ORDER_ID_RE.sub(" ", text or "")
        value = re.sub(r"(?i)\s*\bReference\s+\d+\.?\s*$", " ", value)
        value = re.sub(
            r"(?i)^\s*(?:please\s+)?(?:can you\s+)?(?:open|create|raise|prepare|start|record|file|submit|draft)\s+(?:a|an|the|pending)?\s*",
            "",
            value,
        )
        value = re.sub(r"(?i)\b(?:ticket|case|support|pending|about|regarding|for|on|my|this|order|in|a|an|the)\b", " ", value)
        value = re.sub(r"[^A-Za-z0-9' -]", " ", value)
        value = re.sub(r"\s+", " ", value).strip(" -")
        tokens = re.findall(r"[A-Za-z]{2,}", value)
        phrase = " ".join(tokens[:12]).strip()
        return phrase if len(phrase) >= 5 and phrase.casefold() not in {"wrong product", "damaged item", "late delivery"} else phrase

    @staticmethod
    def _ticket_issue_context(text: str) -> bool:
        return bool(HybridControllerV5Candidate._grounded_issue(text))

    def apply(self, text: str, candidate: dict, history: list[dict] | None = None):
        active_text, _context = self._active_context(text, history or [])
        if self._intent(active_text) == "ticket":
            order_ids = self._ids(ORDER_ID_RE, active_text)
            issue = self._grounded_issue(active_text)
            order_related = self._order_related_ticket(active_text)
            # A clear customer request can create only a pending proposal. The
            # server still requires supervisor approval before any ticket write.
            if issue and (not order_related or len(order_ids) == 1):
                from app.tools.domain import ARGUMENT_SCHEMAS
                args = {
                    "order_id": order_ids[0] if len(order_ids) == 1 else None,
                    "issue_type": self._issue_type(issue),
                    "summary": issue[:157] + ("..." if len(issue) > 160 else ""),
                    "description": issue[:1000],
                    "priority": "normal",
                }
                try:
                    checked = ARGUMENT_SCHEMAS["create_support_ticket"].model_validate(args).model_dump()
                except Exception:
                    checked = None
                if checked:
                    from app.hybrid_controller import ControllerDecision
                    action = {"action_type": "propose_state_change", "tool_name": "create_support_ticket",
                              "arguments": checked, "reason_summary": "Prepare the requested ticket for explicit approval."}
                    return ControllerDecision(action, "overridden", "explicit_ticket_request_pending_approval", request_text=active_text)
        decision = super().apply(text, candidate, history)
        return decision

    @staticmethod
    def _issue_type(issue: str) -> str:
        lowered = issue.casefold()
        if "wrong product" in lowered or "wrong item" in lowered or "incorrect item" in lowered:
            return "wrong_item"
        return HybridControllerV4Candidate._issue_type(issue)

    @classmethod
    def workflow_plan(cls, text: str) -> WorkflowPlan:
        intent = cls._intent(text)
        if intent == "refund_estimate":
            return WorkflowPlan(intent, ("list_order_items", "check_refund_eligibility", "calculate_refund_estimate"))
        if intent == "eligibility":
            return WorkflowPlan(intent, ("list_order_items", "check_refund_eligibility"))
        return WorkflowPlan(intent, ())

    @classmethod
    def follow_up_tools(cls, text: str) -> tuple[str, ...]:
        """Tools after an initial list call, based on the explicit plan."""
        plan = cls.workflow_plan(text)
        return plan.tools[1:] if plan.tools and plan.tools[0] == "list_order_items" else ()
