from app.hybrid_controller import ControllerDecision
from app.hybrid_controller_v6_candidate import HybridControllerV6Candidate


def test_v6_prioritizes_item_anchored_eligibility_over_policy_language():
    controller = HybridControllerV6Candidate()
    assert controller._intent("Apply the return rules to ITEM-2201 from ORD-10022; the reason is changed_mind.") == "eligibility"
    assert controller._intent("Can I send this particular product from ORD-10021 back?") == "eligibility"
    assert controller._needs_specific_item("Can I send this particular product from ORD-10021 back?")


def test_v6_policy_duration_wording_routes_to_authoritative_policy_tool():
    controller = HybridControllerV6Candidate()
    assert controller._intent("How long does the standard return process allow?") == "policy"
    decision = controller.apply(
        "How long does the standard return process allow?",
        {"action_type": "final_answer", "answer": "30 days", "claims": [], "needs_human_review": False},
    )
    assert decision.action["action_type"] == "tool_call"
    assert decision.action["tool_name"] == "get_return_policy"


def test_v6_ambiguous_order_reference_preflight_asks_which_to_use():
    decision = HybridControllerV6Candidate().preflight(
        "Compare ORD-10021 and ORD-10022, but ask me which record I mean before checking."
    )
    assert isinstance(decision, ControllerDecision)
    assert decision.action["action_type"] == "clarification"
    assert decision.action["missing_fields"] == ["order_id"]
    assert "ORD-10021" in decision.action["question"] and "ORD-10022" in decision.action["question"]


def test_v6_incorrect_product_ticket_is_grounded_and_classified_as_wrong_item():
    controller = HybridControllerV6Candidate()
    decision = controller.apply(
        "Please raise a case about the incorrect product on ORD-10021.",
        {"action_type": "final_answer", "answer": "No action", "claims": [], "needs_human_review": False},
    )
    assert decision.action["action_type"] == "propose_state_change"
    assert decision.action["arguments"]["issue_type"] == "wrong_item"
    assert "incorrect product" in decision.action["arguments"]["description"].casefold()
