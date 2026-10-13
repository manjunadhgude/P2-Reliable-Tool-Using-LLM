"""Apply the frozen deterministic controller to saved model-only proposals."""

import argparse
import csv
import hashlib
import json
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def exact_match(action, case):
    if action is None or action.get("action_type") != case["expected_action_type"]:
        return False
    expected_tool = case.get("expected_tool_name")
    if action.get("tool_name") != expected_tool:
        return False
    expected_arguments = case.get("expected_arguments")
    expected_missing_fields = case.get("expected_missing_fields")
    if isinstance(expected_missing_fields, list):
        return action.get("missing_fields") == expected_missing_fields
    return not isinstance(expected_arguments, dict) or action.get("arguments", {}) == expected_arguments


def incorrect_tool_proposal(prediction, case):
    if not prediction or prediction.get("action_type") not in {"tool_call", "propose_state_change"}:
        return False
    return (prediction.get("action_type") != case["expected_action_type"]
            or prediction.get("tool_name") != case.get("expected_tool_name"))


def percentile(values, fraction):
    values = sorted(values)
    if not values:
        return None
    index = max(0, min(len(values) - 1, int(len(values) * fraction + 0.999999) - 1))
    return values[index]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-only", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, help="Versioned JSONL suite; defaults to historical v1 scenarios.")
    args = parser.parse_args()
    model_only_path = args.model_only.resolve()
    output_path = args.output.resolve()
    model_only = json.loads(model_only_path.read_text(encoding="utf-8"))
    dataset_path = args.dataset.resolve() if args.dataset else ROOT / "experiments/datasets/scenarios.jsonl"
    all_cases = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    case_by_id = {row["example_id"]: row for row in all_cases if row["split"] == model_only["split"]}
    proposals = {row["example_id"]: row for row in model_only["outcomes"]}
    if set(case_by_id) != set(proposals):
        raise SystemExit("Model-only outcomes do not match the selected split; refusing to score partial data.")
    if model_only["dataset_sha256"] != hashlib.sha256(dataset_path.read_bytes()).hexdigest():
        raise SystemExit("Dataset checksum differs from the model-only run; refusing to score mismatched labels.")

    from app.hybrid_controller import HybridController
    controller = HybridController()
    outcomes = []
    controller_latencies = []
    used_model_latencies = []
    decisions = Counter()
    invalid_model_actions = sum(not row["valid_action"] for row in proposals.values())
    wrong_model_tool_proposals = 0
    for example_id, case in case_by_id.items():
        model_row = proposals[example_id]
        candidate = model_row.get("prediction")
        history = []
        start = time.perf_counter()
        decision = controller.preflight(case["user_message"], history)
        preflight_used = decision is not None
        if decision is None and candidate is not None and model_row["valid_action"]:
            # The raw runner retains action type/tool/arguments and intentionally
            # omits generated free text. Controller policy does not inspect it.
            decision = controller.apply(case["user_message"], candidate, history)
            used_model_latencies.append(model_row["latency_ms"])
        controller_ms = (time.perf_counter() - start) * 1000
        controller_latencies.append(controller_ms)
        final_action = decision.action if decision else None
        decision_name = decision.decision if decision else "failed_closed"
        reason = decision.reason if decision else "model_proposal_unavailable_or_invalid"
        retry_count = decision.retry_count if decision else 0
        decisions[decision_name] += 1

        model_prediction = model_row.get("prediction") or {}
        if incorrect_tool_proposal(model_prediction, case):
            wrong_model_tool_proposals += 1
        outcome = {
            "example_id": example_id,
            "scenario_family": case["scenario_family"],
            "expected_action_type": case["expected_action_type"],
            "expected_tool_name": case.get("expected_tool_name"),
            "expected_arguments": case.get("expected_arguments"),
            "expected_missing_fields": case.get("expected_missing_fields"),
            "model_only_valid_action": model_row["valid_action"],
            "model_only_prediction": model_row.get("prediction"),
            "hybrid_action": final_action,
            "hybrid_exact_action_match": exact_match(final_action, case),
            "correct_clarification": final_action is not None and final_action.get("action_type") == "clarification" and case["expected_action_type"] == "clarification" and (not isinstance(case.get("expected_missing_fields"), list) or final_action.get("missing_fields") == case["expected_missing_fields"]),
            "correct_handoff": final_action is not None and final_action.get("action_type") == "handoff" and case["expected_action_type"] == "handoff",
            "model_tool_proposal_incorrect": incorrect_tool_proposal(model_prediction, case),
            "model_prohibited_write_proposal": model_prediction.get("action_type") == "propose_state_change" and case["expected_action_type"] != "propose_state_change",
            "model_write_proposal_preempted_by_preflight": preflight_used and model_prediction.get("action_type") == "propose_state_change",
            "controller_decision": decision_name,
            "controller_reason": reason,
            "retry_count": retry_count,
            "estimated_model_calls": int(not preflight_used),
            "controller_duration_ms": round(controller_ms, 4),
            "model_action_latency_ms": model_row.get("latency_ms"),
        }
        # A preflight response means the live application would not call Ollama.
        # The candidate is retained only as model-only evidence for a paired view.
        outcomes.append(outcome)

    denominator = len(outcomes)
    exact = sum(row["hybrid_exact_action_match"] for row in outcomes)
    clarification_rows = [row for row in outcomes if row["expected_action_type"] == "clarification"]
    handoff_rows = [row for row in outcomes if row["expected_action_type"] == "handoff"]
    tool_rows = [row for row in outcomes if row["expected_tool_name"] is not None]
    argument_rows = [row for row in outcomes if isinstance(row["expected_arguments"], dict)]
    correct_tool = sum(row["hybrid_action"] is not None and row["hybrid_action"].get("tool_name") == row["expected_tool_name"] for row in tool_rows)
    correct_args = sum(row["hybrid_action"] is not None and row["hybrid_action"].get("arguments", {}) == row["expected_arguments"] for row in argument_rows)
    correct_clarifications = sum(row["correct_clarification"] for row in clarification_rows)
    correct_handoffs = sum(row["correct_handoff"] for row in handoff_rows)
    per_family = defaultdict(lambda: {"denominator": 0, "hybrid_exact_action_matches": 0})
    for row in outcomes:
        per_family[row["scenario_family"]]["denominator"] += 1
        per_family[row["scenario_family"]]["hybrid_exact_action_matches"] += int(row["hybrid_exact_action_match"])

    metrics = {
        "denominator": denominator,
        "hybrid_exact_action_matches": exact,
        "hybrid_exact_action_rate": exact / denominator if denominator else None,
        "correct_tool_selections": correct_tool,
        "tool_selection_denominator": len(tool_rows),
        "tool_selection_rate": correct_tool / len(tool_rows) if tool_rows else None,
        "exact_argument_matches": correct_args,
        "argument_denominator": len(argument_rows),
        "argument_exact_rate": correct_args / len(argument_rows) if argument_rows else None,
        "correct_clarifications": correct_clarifications,
        "clarification_denominator": len(clarification_rows),
        "correct_clarification_rate": correct_clarifications / len(clarification_rows) if clarification_rows else None,
        "correct_handoffs": correct_handoffs,
        "handoff_denominator": len(handoff_rows),
        "correct_no_tool_handoff_rate": correct_handoffs / len(handoff_rows) if handoff_rows else None,
        "invalid_model_actions": invalid_model_actions,
        "incorrect_model_tool_proposals": wrong_model_tool_proposals,
        "model_prohibited_write_proposals": sum(row["model_prohibited_write_proposal"] for row in outcomes),
        "model_write_proposals_preempted_by_preflight": sum(row["model_write_proposal_preempted_by_preflight"] for row in outcomes),
        "hybrid_state_change_proposals": sum(bool(row["hybrid_action"] and row["hybrid_action"].get("action_type") == "propose_state_change") for row in outcomes),
        "controller_decisions": dict(decisions),
        "controller_repair_count": sum(row["retry_count"] for row in outcomes),
        "controller_retry_count": 0,
        "estimated_model_calls_for_hybrid_path": sum(row["estimated_model_calls"] for row in outcomes),
        "model_action_latency_ms_p50_for_used_proposals": statistics.median(used_model_latencies) if used_model_latencies else None,
        "model_action_latency_ms_p95_for_used_proposals": percentile(used_model_latencies, 0.95),
        "controller_duration_ms_p50": statistics.median(controller_latencies) if controller_latencies else None,
        "controller_duration_ms_p95": percentile(controller_latencies, 0.95),
        "unsafe_state_changes_executed": None,
        "duplicate_state_changes_executed": None,
        "per_scenario_family": dict(per_family),
    }
    artifact = {
        "run_id": ("hybrid-controller-v2-" if args.dataset else "hybrid-controller-v1-") + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "controller_version": controller.version,
        "controller_source_sha256": hashlib.sha256((ROOT / "backend/app/hybrid_controller.py").read_bytes()).hexdigest(),
        "backend": "ollama_plus_hybrid_controller",
        "model_id": model_only["model_id"],
        "model_metadata": model_only.get("model_metadata"),
        "prompt_version": model_only.get("prompt_version", "ollama-native-v1"),
        "action_schema_version": model_only.get("action_schema_version", "1.0.0"),
        "model_only_source_artifact": str(model_only_path.relative_to(ROOT)),
        "dataset_version": model_only["dataset_version"],
        "dataset_sha256": model_only["dataset_sha256"],
        "split": model_only["split"],
        "denominator": denominator,
        "metrics": metrics,
        "metric_definitions": {
            "hybrid_exact_action_match": "Compare final controller action type, tool name, and complete expected arguments against dataset labels; for no-tool actions compare type and absence of a tool only.",
            "task_completion": "Not measured by this offline action-level evaluator; no database tools are executed here.",
            "estimated_model_calls_for_hybrid_path": "Controller preflight decisions are counted as zero; other valid proposals count one. The paired raw model artifact still queried every example to provide model-only evidence.",
            "controller_duration": "Local time to run preflight and controller policy over saved proposals; excludes database execution and model inference.",
        },
        "outcomes": outcomes,
        "provenance": "Application-plus-model action-level simulation over saved, unmodified model-only proposals. It scores no hidden labels in controller code and executes no business tools.",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    csv_path = output_path.with_suffix(".csv")
    fields = list(outcomes[0]) if outcomes else []
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(outcomes)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
