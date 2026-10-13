"""Run one locally bounded, real-Ollama structured-intent application smoke.

This is a diagnostic on one known synthetic order, not a benchmark or acceptance
evaluation. The parent process enforces a hard deadline around the application
worker so a stuck inference cannot hold the shell indefinitely.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL = "qwen3:1.7b"
OLLAMA = "http://127.0.0.1:11434"


def paths(workflow: str) -> tuple[Path, Path, str]:
    if workflow == "lookup":
        name = "p2_structured_intent_real_smoke_v5"
        prompt = "Where is order ORD-10021?"
    else:
        name = "p2_structured_intent_ticket_approval_real_smoke_v4"
        prompt = "Open a support ticket for order ORD-10021: The package arrived damaged and the mug is cracked."
    if workflow == "estimate":
        name = "p2_structured_intent_real_estimate_smoke_v4"
        prompt = "Estimate the refund for all items in order ORD-10022."
    return ROOT / f"experiments/results/{name}.json", ROOT / f"experiments/results/{name}_freeze.json", prompt


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metadata() -> dict:
    request = urllib.request.Request(OLLAMA + "/api/tags")
    with urllib.request.urlopen(request, timeout=4) as response:
        models = json.load(response).get("models", [])
    for model in models:
        if MODEL in {model.get("name"), model.get("model")}:
            return {key: model.get(key) for key in ("name", "digest", "size", "details", "modified_at")}
    raise RuntimeError(f"Cached model {MODEL!r} is not listed by Ollama")


def save(path: Path, content: dict) -> None:
    path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def worker() -> int:
    workflow = os.environ["P2_SMOKE_WORKFLOW"]
    default_result_path, _, prompt = paths(workflow)
    result_path = Path(os.environ.get("P2_SMOKE_RESULT", str(default_result_path)))
    db_path = Path(os.environ["P2_SMOKE_DB"]).resolve()
    os.environ.update({
        "DATABASE_URL": "sqlite:///" + db_path.as_posix(),
        "MODEL_BACKEND": "ollama",
        "MODEL_ID": MODEL,
        "OLLAMA_URL": OLLAMA,
        "HYBRID_CONTROLLER_ENABLED": "true",
        "HYBRID_CONTROLLER_VERSION": "structured_intent_candidate",
        "REQUEST_TIMEOUT_SECONDS": "25",
        "MODEL_MAX_NEW_TOKENS": "128",
    })

    sys.path.insert(0, str(ROOT / "backend"))
    from fastapi.testclient import TestClient
    from sqlalchemy import select
    from app import main
    app = main.app

    # Capture the exact parsed schema response returned by the real backend,
    # without replacing, editing, or synthesizing any model content.
    backend_instance = main.backend()
    interpret_intent = backend_instance.interpret_intent
    captured_intents: list[dict] = []

    def capture_intent(text: str):
        parsed = interpret_intent(text)
        captured_intents.append(parsed.model_dump(mode="json"))
        return parsed

    backend_instance.interpret_intent = capture_intent
    main.backend = lambda: backend_instance

    checkpoint = result_path.with_suffix(".checkpoint.json")
    run = {
        "status": "running",
        "run_id": result_path.stem,
        "workflow": workflow,
        "prompt": prompt,
        "database": "temporary SQLite with seeded synthetic records",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    save(checkpoint, run)
    started = time.perf_counter()
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/demo-session", json={"username": "agent"})
        login.raise_for_status()
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        conv = client.post("/api/v1/conversations", headers=headers,
                           json={"title": "Structured intent real-model smoke"})
        conv.raise_for_status()
        response = client.post(
            f"/api/v1/conversations/{conv.json()['id']}/messages",
            headers=headers,
            json={"content": prompt},
        )
        response.raise_for_status()
        body = response.json()
        trace_response = client.get(f"/api/v1/turns/{body['turn_id']}/trace", headers=headers)
        trace_response.raise_for_status()
        approval_results = None
        approval_checks = {}
        if workflow == "ticket":
            from app.core.db import SessionLocal
            from app.models import PendingAction, Ticket

            pending = body.get("pending_action")
            no_ticket_before = False
            if pending:
                with SessionLocal() as db:
                    pending_row = db.get(PendingAction, pending["id"])
                    no_ticket_before = bool(pending_row and pending_row.status == "pending" and db.scalar(
                        select(Ticket.id).where(Ticket.idempotency_key == pending_row.idempotency_key)) is None)
                supervisor = client.post("/api/v1/auth/demo-session", json={"username": "supervisor"})
                supervisor.raise_for_status()
                supervisor_headers = {"Authorization": f"Bearer {supervisor.json()['access_token']}"}
                first = client.post(f"/api/v1/pending-actions/{pending['id']}/approve", headers=supervisor_headers)
                second = client.post(f"/api/v1/pending-actions/{pending['id']}/approve", headers=supervisor_headers)
                approval_results = [first.json(), second.json()]
                one_ticket = False
                if first.status_code == second.status_code == 200:
                    with SessionLocal() as db:
                        pending_row = db.get(PendingAction, pending["id"])
                        one_ticket = len(list(db.scalars(select(Ticket).where(
                            Ticket.idempotency_key == pending_row.idempotency_key)))) == 1
                approval_checks = {
                    "proposal_pending_before_approval": body.get("status") == "pending_approval" and no_ticket_before,
                    "supervisor_approval_created_ticket": first.status_code == 200
                    and approval_results[0].get("status") == "completed",
                    "duplicate_approval_returns_same_ticket": first.status_code == second.status_code == 200
                    and approval_results[0].get("ticket_id") == approval_results[1].get("ticket_id"),
                    "exactly_one_ticket_row": one_ticket,
                }

    trace = trace_response.json()
    expected_tools = (
        ["lookup_order"] if workflow == "lookup" else
        ["create_support_ticket"] if workflow == "ticket" else
        ["list_order_items", "check_refund_eligibility", "calculate_refund_estimate"]
    )
    tool_events = [event for event in trace.get("events", []) if event.get("tool_name") in expected_tools]
    controller = next(iter(trace.get("controller_events", [])), {})
    intent = controller.get("structured_intent")
    tool_result = next((event.get("result") for event in tool_events
                        if event.get("result_status") == "succeeded"), None)
    answer = body.get("assistant_message", "")
    if workflow == "lookup":
        status = str((tool_result or {}).get("status", "")).replace("_", " ")
        checks = {
            "real_model_backend": controller.get("backend") == "ollama",
            "structured_intent_returned": isinstance(intent, dict) and intent.get("intent") == "lookup_order",
            "registered_tool_succeeded": bool(tool_result),
            "answer_status_matches_tool": bool(status and status in answer.lower()),
            "turn_completed": body.get("status") == "completed",
        }
    elif workflow == "ticket":
        checks = {
            "real_model_backend": controller.get("backend") == "ollama",
            "structured_ticket_intent_returned": isinstance(intent, dict) and intent.get("intent") == "support_ticket",
            "registered_ticket_proposal_traced": controller.get("final_action_type") == "propose_state_change"
            and controller.get("final_tool_name") == "create_support_ticket",
            **approval_checks,
        }
    else:
        results = {event.get("tool_name"): event.get("result") for event in tool_events
                   if event.get("result_status") == "succeeded"}
        estimate = results.get("calculate_refund_estimate") or {}
        amount = str(estimate.get("estimated_total", ""))
        checks = {
            "real_model_backend": controller.get("backend") == "ollama",
            "structured_estimate_intent_returned": isinstance(intent, dict)
            and intent.get("intent") == "refund_estimate",
            "all_registered_workflow_tools_succeeded": set(results) == set(expected_tools),
            "final_amount_matches_tool_result": bool(amount and amount in answer),
            "final_identifies_estimate_not_refund": "estimate only" in answer.lower()
            or "no refund is issued" in answer.lower(),
        }
        run["workflow_tool_results"] = results
    run.update({
        "status": "completed" if all(checks.values()) else "completed_with_failed_checks",
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        "checks": checks,
        "model_intent_output": captured_intents[0] if captured_intents else None,
        "application_trace_intent_summary": intent,
        "assistant_message": answer,
        "tool_result": tool_result,
        "controller_trace": controller,
        "execution_trace": trace.get("events", []),
        "approval_results": approval_results,
        "turn_status": body.get("status"),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    save(result_path, run)
    checkpoint.unlink(missing_ok=True)
    print(json.dumps({"status": run["status"], "checks": checks, "elapsed_ms": run["elapsed_ms"]}))
    return 0 if all(checks.values()) else 2


def supervise(deadline: int, workflow: str) -> int:
    model = metadata()
    result_path, freeze_path, prompt = paths(workflow)
    if result_path.exists() or freeze_path.exists():
        suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        result_path = result_path.with_name(f"{result_path.stem}_{suffix}.json")
        freeze_path = freeze_path.with_name(f"{freeze_path.stem}_{suffix}.json")
    sources = [
        ROOT / "backend/app/main.py",
        ROOT / "backend/app/intent_workflow.py",
        ROOT / "backend/app/llm/backends.py",
        ROOT / "backend/app/tools/domain.py",
        Path(__file__).resolve(),
    ]
    save(freeze_path, {
        "run_id": result_path.stem,
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "single diagnostic prompt; not benchmark evidence",
        "workflow": workflow,
        "prompt": prompt,
        "result_artifact": str(result_path.relative_to(ROOT)),
        "model": model,
        "backend": "ollama",
        "controller": "structured_intent_candidate",
        "generation": {"max_new_tokens": 128, "request_timeout_seconds": 25},
        "hard_process_deadline_seconds": deadline,
        "source_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in sources},
    })
    fd, db_name = tempfile.mkstemp(prefix="p2_structured_intent_", suffix=".db")
    os.close(fd)
    Path(db_name).unlink(missing_ok=True)
    child_env = os.environ.copy()
    child_env["P2_SMOKE_DB"] = db_name
    child_env["P2_SMOKE_WORKFLOW"] = workflow
    child_env["P2_SMOKE_RESULT"] = str(result_path)
    command = [sys.executable, str(Path(__file__).resolve()), "--worker"]
    child = subprocess.Popen(command, cwd=ROOT, env=child_env, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True)
    try:
        output, _ = child.communicate(timeout=deadline)
        if output:
            print(output, end="")
        return child.returncode
    except subprocess.TimeoutExpired:
        child.kill()
        output, _ = child.communicate(timeout=5)
        if output:
            print(output, end="")
        save(result_path, {
            "run_id": result_path.stem,
            "status": "blocked_hard_deadline",
            "hard_process_deadline_seconds": deadline,
            "model": model,
            "workflow": workflow,
            "prompt": prompt,
            "worker_output": output,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        })
        return 124
    finally:
        Path(db_name).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--workflow", choices=("lookup", "ticket", "estimate"), default="lookup")
    parser.add_argument("--hard-deadline-seconds", type=int, default=45)
    args = parser.parse_args()
    if args.worker:
        return worker()
    os.environ["P2_SMOKE_WORKFLOW"] = args.workflow
    return supervise(max(10, min(args.hard_deadline_seconds, 90)), args.workflow)


if __name__ == "__main__":
    raise SystemExit(main())
