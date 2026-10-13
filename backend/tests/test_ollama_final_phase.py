from app.llm.backends import OllamaModelBackend


def test_ollama_final_answer_phase_disables_registered_tools(monkeypatch):
    model = OllamaModelBackend("qwen3:1.7b", "http://localhost:11434", timeout_seconds=20)
    def capture(messages, *, include_tools=True):
        include_tools_flag.append(include_tools)
        return {"message": {"content": "The estimated amount is $50.27."}}

    include_tools_flag = []
    monkeypatch.setattr(model, "_chat", capture)
    action = model.act("Estimate the return amount.", prior_result={"estimated_total": "50.27"})
    assert include_tools_flag == [False]
    assert action["action_type"] == "final_answer"
    assert "50.27" in action["answer"]


def test_post_tool_model_failure_does_not_forge_a_tool_execution(monkeypatch):
    from fastapi.testclient import TestClient
    from app import main

    class FailOnFinalAnswer:
        def __init__(self):
            self.calls = 0

        def act(self, text, prior_result=None, validate_arguments=True):
            self.calls += 1
            if prior_result is None:
                return {"action_type": "final_answer", "answer": "model proposal ignored by controller",
                        "claims": [], "needs_human_review": False}
            raise ValueError("synthetic final-response failure")

    monkeypatch.setattr(main.settings, "model_backend", "ollama")
    monkeypatch.setattr(main.settings, "hybrid_controller_enabled", True)
    model = FailOnFinalAnswer()
    monkeypatch.setattr(main, "backend", lambda: model)
    with TestClient(main.app) as client:
        login = client.post("/api/v1/auth/demo-session", json={"username": "agent"}).json()
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        conversation = client.post("/api/v1/conversations", headers=headers, json={"title": "Final failure test"}).json()
        result = client.post(f"/api/v1/conversations/{conversation['id']}/messages", headers=headers,
                             json={"content": "Can I return items from ORD-10022?"}).json()
        trace = client.get(f"/api/v1/turns/{result['turn_id']}/trace", headers=headers).json()
    assert result["status"] == "completed"
    assert "eligible" in result["assistant_message"]
    assert "ITEM-" in result["assistant_message"]
    assert model.calls == 1
    assert [event["tool_name"] for event in trace["events"]] == ["list_order_items", "check_refund_eligibility"]
    assert all(event["result_status"] == "succeeded" for event in trace["events"])
