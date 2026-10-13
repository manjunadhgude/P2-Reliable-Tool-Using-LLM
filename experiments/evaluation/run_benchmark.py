"""Run action-shape metrics against one selected backend; no metric is pre-populated."""
import json
import hashlib
import platform
import sys
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.llm.backends import DeterministicTestBackend  # noqa: E402


def main() -> None:
    rows = [json.loads(line) for line in (ROOT / "experiments/datasets/scenarios.jsonl").read_text(encoding="utf-8").splitlines()]
    rows = [row for row in rows if row["split"] == "validation"]
    backend = DeterministicTestBackend()
    valid = correct = 0
    results = []
    per_family = {}
    for row in rows:
        family = row["scenario_family"]
        family_metrics = per_family.setdefault(family, {"denominator": 0, "action_match_count": 0})
        family_metrics["denominator"] += 1
        try:
            action = backend.act(row["user_message"])
            valid += int(action.get("action_type") in {"tool_call", "final_answer", "propose_state_change", "clarification", "handoff"})
            match = action.get("action_type") == row["expected_action_type"] and (not row["expected_tool_name"] or action.get("tool_name") == row["expected_tool_name"])
            correct += int(match)
            family_metrics["action_match_count"] += int(match)
            if not match:
                results.append({"example_id": row["example_id"], "expected": row["expected_action_type"], "actual": action.get("action_type"), "error_category": "action_mismatch"})
        except Exception as exc:
            results.append({"example_id": row["example_id"], "error_category": type(exc).__name__})
    data_path = ROOT / "experiments/datasets/scenarios.jsonl"
    report = {"run_id": str(uuid4()), "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "backend": "deterministic_test", "label": "Fixture backend; not model performance", "model_id": None,
        "model_revision": None, "dataset_version": "p2-synthetic-v1", "dataset_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
        "split": "validation", "denominator": len(rows), "valid_actions": valid, "action_match_count": correct,
        "action_match_rate": correct / len(rows) if rows else None, "valid_action_rate": valid / len(rows) if rows else None,
        "per_scenario_family": per_family, "environment": {"python": platform.python_version(), "platform": platform.platform()}, "errors": results}
    target = ROOT / "experiments/results"
    target.mkdir(exist_ok=True)
    path = target / "latest_fixture_run.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
