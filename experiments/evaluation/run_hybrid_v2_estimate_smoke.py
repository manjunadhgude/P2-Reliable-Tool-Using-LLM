"""Run one actual Ollama multi-step eligibility + estimate task on fresh synthetic SQLite."""

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen3:1.7b")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--timeout-seconds", type=int, default=90)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    os.environ["DATABASE_URL"] = f"sqlite:///./p2_v2_estimate_smoke_{stamp}.db"
    os.environ["MODEL_BACKEND"] = "ollama"
    os.environ["HYBRID_CONTROLLER_ENABLED"] = "true"
    os.environ["MODEL_ID"] = args.model
    os.environ["OLLAMA_URL"] = args.ollama_url
    os.environ["REQUEST_TIMEOUT_SECONDS"] = str(args.timeout_seconds)
    os.environ["MODEL_MAX_NEW_TOKENS"] = "256"

    from fastapi.testclient import TestClient
    from app.hybrid_controller import HybridController
    from app.main import app
    from run_hybrid_real_integration import model_metadata

    prompt = "Estimate a refund for item ITEM-2201 from order ORD-10022 after checking eligibility."
    with TestClient(app) as client:
        auth = client.post("/api/v1/auth/demo-session", json={"username": "agent"})
        auth.raise_for_status()
        headers = {"Authorization": f"Bearer {auth.json()['access_token']}"}
        conversation = client.post("/api/v1/conversations", headers=headers,
                                   json={"title": "V2 estimate smoke"})
        conversation.raise_for_status()
        started = time.perf_counter()
        response = client.post(f"/api/v1/conversations/{conversation.json()['id']}/messages",
                               headers=headers, json={"content": prompt})
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        response.raise_for_status()
        turn = response.json()
        trace_response = client.get(f"/api/v1/turns/{turn['turn_id']}/trace", headers=headers)
        trace_response.raise_for_status()
        trace = trace_response.json()
    tools = [event["tool_name"] for event in trace["events"]]
    estimate = next((event["result"].get("estimated_total") for event in trace["events"]
                     if event["tool_name"] == "calculate_refund_estimate"), None)
    output = turn["assistant_message"]
    checks = {
        "turn_completed": turn["status"] == "completed",
        "correct_registered_tool_sequence": tools == ["list_order_items", "check_refund_eligibility", "calculate_refund_estimate"],
        "eligibility_succeeded": any(event["tool_name"] == "check_refund_eligibility" and event["result_status"] == "succeeded" for event in trace["events"]),
        "estimate_from_tool_result": estimate == "50.27",
        "final_answer_mentions_tool_amount": estimate is not None and estimate in output,
        "no_ticket_write": not any(event["tool_name"] == "create_support_ticket" for event in trace["events"]),
    }
    artifact = {
        "run_id": "hybrid-v2-estimate-smoke-" + stamp,
        "dataset_version": "p2-hybrid-controller-v2-smoke",
        "backend": "ollama_plus_hybrid_controller",
        "controller_version": HybridController.version,
        "model_id": args.model,
        "model_metadata": model_metadata(args.ollama_url, args.model),
        "prompt": prompt,
        "assistant_output": output,
        "request_ms": elapsed_ms,
        "model_call_durations_ms": trace.get("controller_events", [{}])[0].get("model_call_durations_ms", []),
        "trace": trace,
        "tool_estimate": estimate,
        "checks": checks,
        "passed": all(checks.values()),
        "database": "fresh synthetic SQLite; no external integrations",
        "generation": {"temperature": 0, "think": False, "stream": False, "max_new_tokens": 256,
                       "timeout_seconds": args.timeout_seconds},
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "suite_sha256": hashlib.sha256((ROOT / "experiments/datasets/hybrid_controller_v2/scenarios.jsonl").read_bytes()).hexdigest(),
        "provenance": "One supplemental real-model application-path workflow. The actual model response, registered tool sequence, trusted estimate, and trace are recorded; this is a smoke test, not a benchmark score.",
    }
    path = args.output.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "passed": artifact["passed"], "tool_estimate": estimate,
                      "request_ms": elapsed_ms, "model_call_durations_ms": artifact["model_call_durations_ms"],
                      "artifact": str(path)}, indent=2))


if __name__ == "__main__":
    main()
