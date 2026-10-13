from app.hybrid_controller_v8_candidate import HybridControllerV8Candidate


def test_v8_clarifies_singular_unidentified_item_instead_of_processing_all_items():
    decision = HybridControllerV8Candidate().preflight(
        "Estimate a return for one unidentified item on ORD-10022."
    )

    assert decision is not None
    assert decision.action["action_type"] == "clarification"
    assert decision.action["missing_fields"] == ["item_ids"]
    assert decision.action["question"] == "Please provide the item ID you want me to check."


def test_v8_keeps_eligibility_and_estimate_intents_distinct():
    controller = HybridControllerV8Candidate()
    assert controller._intent("Can this particular product be returned from ORD-10022?") == "eligibility"
    assert controller._intent("How much is the estimate for this specific item in ORD-10022?") == "refund_estimate"
