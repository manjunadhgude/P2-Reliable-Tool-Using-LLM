from experiments.evaluation.run_ollama_benchmark import expected_metrics
from experiments.evaluation.evaluate_hybrid_controller import incorrect_tool_proposal


def test_non_tool_actions_do_not_require_an_empty_arguments_dictionary():
    action = {"action_type": "final_answer", "answer": "Supported tools are order lookup and policy.",
              "claims": [], "needs_human_review": False}
    case = {"expected_action_type": "final_answer", "expected_tool_name": None,
            "expected_arguments": None}
    type_match, tool_match, args_match, exact = expected_metrics(action, case)
    assert type_match is True
    assert tool_match is True
    assert args_match is None
    assert exact is True


def test_tool_action_requires_exact_expected_arguments():
    action = {"action_type": "tool_call", "tool_name": "lookup_order",
              "arguments": {"order_id": "ORD-10021"}}
    case = {"expected_action_type": "tool_call", "expected_tool_name": "lookup_order",
            "expected_arguments": {"order_id": "ORD-10022"}}
    type_match, tool_match, args_match, exact = expected_metrics(action, case)
    assert type_match is True
    assert tool_match is True
    assert args_match is False
    assert exact is False


def test_unrequested_write_proposal_counts_as_incorrect_tool_action():
    prediction = {"action_type": "propose_state_change", "tool_name": "create_support_ticket"}
    case = {"expected_action_type": "handoff", "expected_tool_name": None}
    assert incorrect_tool_proposal(prediction, case) is True
