from sqlalchemy import select
from fastapi.testclient import TestClient

from app.hybrid_controller_v5_candidate import HybridControllerV5Candidate
from app.main import app
from app.core.db import SessionLocal
from app.models import PendingAction, Ticket


def _call(tool="lookup_order", arguments=None):
    return {"action_type": "tool_call", "tool_name": tool, "arguments": arguments or {}, "reason_summary": "test"}


def test_v5_classifies_observed_policy_eligibility_estimate_and_tracking_failures():
    controller = HybridControllerV5Candidate()
    assert controller._intent("State the conditions for sending standard goods back.") == "policy"
    assert controller._intent("Check the policy result for ITEM-2201 under ORD-10022.") == "eligibility"
    assert controller._intent("How much money is expected back for ITEM-2201 on ORD-10022?") == "refund_estimate"
    assert controller._intent("Has the carrier moved ORD-10021 yet?") == "lookup_order"
    assert controller.follow_up_tools("How much money is expected back for ITEM-2201 on ORD-10022?") == (
        "check_refund_eligibility", "calculate_refund_estimate"
    )


def test_v5_clarifies_singular_missing_item_but_does_not_clarify_all_items():
    controller = HybridControllerV5Candidate()
    missing = controller.apply(
        "Assess my unspecified purchase item from ORD-10022.",
        {"action_type": "final_answer", "answer": "guess", "claims": [], "needs_human_review": False},
    )
    assert missing.action["action_type"] == "clarification"
    assert missing.action["missing_fields"] == ["item_ids"]
    all_items = controller.apply(
        "Determine return status only after loading the items for ORD-10022.",
        {"action_type": "final_answer", "answer": "guess", "claims": [], "needs_human_review": False},
    )
    assert all_items.action["tool_name"] == "list_order_items"


def test_v5_explicit_ticket_intent_creates_only_grounded_pending_proposal():
    decision = HybridControllerV5Candidate().apply(
        "Draft a pending ticket about a wrong product in ORD-10021. Reference 70.",
        {"action_type": "final_answer", "answer": "no ticket", "claims": [], "needs_human_review": False},
    )
    assert decision.action["action_type"] == "propose_state_change"
    assert decision.action["tool_name"] == "create_support_ticket"
    assert decision.action["arguments"]["order_id"] == "ORD-10021"
    assert decision.action["arguments"]["issue_type"] == "wrong_item"
    assert decision.action["arguments"]["description"] == "wrong product"
    assert "pending_approval" in decision.reason


class _Model:
    def __init__(self):
        self.calls = []

    def act(self, text, prior_result=None, validate_arguments=True):
        self.calls.append((text, prior_result))
        return {"action_type": "final_answer", "answer": "model response", "claims": [], "needs_human_review": False}


def _login(client, username):
    response = client.post("/api/v1/auth/demo-session", json={"username": username})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_v5_api_executes_estimate_plan_through_registered_tools(monkeypatch):
    from app import main
    model = _Model()
    monkeypatch.setattr(main.settings, "model_backend", "ollama")
    monkeypatch.setattr(main.settings, "hybrid_controller_enabled", True)
    monkeypatch.setattr(main.settings, "hybrid_controller_version", "v5_candidate")
    monkeypatch.setattr(main, "backend", lambda: model)
    with TestClient(app) as client:
        headers = _login(client, "agent")
        conversation = client.post("/api/v1/conversations", headers=headers, json={"title": "V5 workflow regression"}).json()
        response = client.post(
            f"/api/v1/conversations/{conversation['id']}/messages", headers=headers,
            json={"content": "How much money is expected back for ITEM-2201 on transaction ORD-10022?"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"
        assert [event["tool_name"] for event in body["tool_executions"]] == [
            "list_order_items", "check_refund_eligibility", "calculate_refund_estimate"
        ]
        amount = str(body["tool_executions"][-1]["result"]["estimated_total"])
        assert amount in body["assistant_message"]
        assert "estimate" in body["assistant_message"].casefold() or "estimated" in body["assistant_message"].casefold()


def test_v5_api_ticket_stays_pending_until_supervisor_and_duplicate_is_idempotent(monkeypatch):
    from app import main
    model = _Model()
    monkeypatch.setattr(main.settings, "model_backend", "ollama")
    monkeypatch.setattr(main.settings, "hybrid_controller_enabled", True)
    monkeypatch.setattr(main.settings, "hybrid_controller_version", "v5_candidate")
    monkeypatch.setattr(main, "backend", lambda: model)
    with TestClient(app) as client:
        agent = _login(client, "agent")
        supervisor = _login(client, "supervisor")
        conversation = client.post("/api/v1/conversations", headers=agent, json={"title": "V5 ticket regression"}).json()
        response = client.post(
            f"/api/v1/conversations/{conversation['id']}/messages", headers=agent,
            json={"content": "Draft a pending ticket about a wrong product in ORD-10021."},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "pending_approval"
        pending_id = body["pending_action"]["id"]
        with SessionLocal() as db:
            pending = db.get(PendingAction, pending_id)
            assert pending is not None and pending.status == "pending"
            assert db.scalar(select(Ticket.id).where(Ticket.idempotency_key == pending.idempotency_key)) is None
        first = client.post(f"/api/v1/pending-actions/{pending_id}/approve", headers=supervisor)
        second = client.post(f"/api/v1/pending-actions/{pending_id}/approve", headers=supervisor)
        assert first.status_code == second.status_code == 200
        assert first.json()["ticket_id"] == second.json()["ticket_id"]
        with SessionLocal() as db:
            pending = db.get(PendingAction, pending_id)
            assert len(list(db.scalars(select(Ticket).where(Ticket.idempotency_key == pending.idempotency_key)))) == 1
