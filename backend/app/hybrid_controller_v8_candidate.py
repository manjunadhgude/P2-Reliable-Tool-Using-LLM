"""Small V8 follow-up for singular item language missed by V7."""

import re

from app.hybrid_controller import ITEM_ID_RE
from app.hybrid_controller_v7_candidate import HybridControllerV7Candidate


class HybridControllerV8Candidate(HybridControllerV7Candidate):
    version = "hybrid-controller-v8-singular-item-routing-candidate"

    @staticmethod
    def _intent(text: str) -> str | None:
        lowered = ITEM_ID_RE.sub(" ", text or "").casefold()
        singular_item = re.search(
            r"\b(?:this|that|the|a|one|particular|specific|unidentified|unspecified)\b"
            r"(?:\s+\w+){0,2}\s+\b(?:item|product)\b|\bone\s+unidentified\s+item\b",
            lowered,
        )
        if singular_item and re.search(r"\b(estimate|how much|amount|value)\b", lowered):
            return "refund_estimate"
        if singular_item and re.search(r"\b(return\w*|eligible|eligibility|qualify\w*|assess\w*|send back)\b", lowered):
            return "eligibility"
        return HybridControllerV7Candidate._intent(text)

    @staticmethod
    def _needs_specific_item(text: str) -> bool:
        lowered = ITEM_ID_RE.sub(" ", text or "").casefold()
        return HybridControllerV7Candidate._needs_specific_item(text) or bool(re.search(
            r"\b(?:one|a|an|this|that|the|particular|specific|unidentified|unspecified)\b"
            r"(?:\s+\w+){0,2}\s+\b(?:item|product)\b",
            lowered,
        ))
