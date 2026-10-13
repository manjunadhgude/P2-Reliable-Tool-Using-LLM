"""Paired raw, V2, and explicit-workflow V5 replay over saved model proposals."""

import argparse
import hashlib
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def normalize(text):
    text = re.sub(r"(?i)\s*\breference\s+\d+\.?\s*$", "", text or "")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.casefold()).split())


def exact(action, case):
    if not isinstance(action, dict) or action.get("action_type") != case["expected_action_type"]:
        return False
    if action.get("tool_name") != case.get("expected_tool_name"):
        return False
    if isinstance(case.get("expected_missing_fields"), list):
        return action.get("missing_fields") == case["expected_missing_fields"]
    expected = case.get("expected_arguments")
    return not isinstance(expected, dict) or action.get("arguments", {}) == expected


def action_for(controller, text, prediction):
    decision = controller.preflight(text, [])
    if decision is None and prediction is not None:
        decision = controller.apply(text, prediction, [])
    return decision.action if decision else (prediction or {}), decision


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "experiments/datasets/p2_recovery_v1/scenarios.jsonl")
    parser.add_argument("--raw", type=Path, default=ROOT / "experiments/results/p2_recovery_raw_v1.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dataset_path = args.dataset.resolve()
    cases = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    dataset_hash = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    if raw["dataset_sha256"] != dataset_hash or len(cases) != len(raw["outcomes"]):
        raise SystemExit("Dataset hash or row count does not match the saved model run")

    from app.hybrid_controller import HybridController
    from app.hybrid_controller_v5_candidate import HybridControllerV5Candidate

    baseline_controller = HybridController()
    candidate_controller = HybridControllerV5Candidate()
    rows = []
    for case, prediction_row in zip(cases, raw["outcomes"]):
        prediction = prediction_row.get("prediction") if prediction_row.get("valid_action") else None
        baseline, baseline_decision = action_for(baseline_controller, case["user_message"], prediction)
        candidate, candidate_decision = action_for(candidate_controller, case["user_message"], prediction)
        rows.append({
            "example_id": case["example_id"], "scenario_family": case["scenario_family"],
            "user_message": case["user_message"], "normalized_core": normalize(case["user_message"]),
            "expected_action_type": case["expected_action_type"], "expected_tool_name": case.get("expected_tool_name"),
            "expected_arguments": case.get("expected_arguments"), "expected_missing_fields": case.get("expected_missing_fields"),
            "raw": prediction or {}, "baseline": baseline, "candidate": candidate,
            "raw_exact": exact(prediction, case), "baseline_exact": exact(baseline, case), "candidate_exact": exact(candidate, case),
            "baseline_decision": baseline_decision.reason if baseline_decision else "no_action",
            "candidate_decision": candidate_decision.reason if candidate_decision else "no_action",
        })
    groups = defaultdict(list)
    families = defaultdict(list)
    for row in rows:
        groups[row["normalized_core"]].append(row)
        families[row["scenario_family"]].append(row)

    def score(key):
        matched = sum(row[key + "_exact"] for row in rows)
        tool_rows = [row for row in rows if row["expected_tool_name"]]
        arg_rows = [row for row in rows if isinstance(row["expected_arguments"], dict)]
        clarifications = [row for row in rows if row["expected_action_type"] == "clarification"]
        handoffs = [row for row in rows if row["expected_action_type"] == "handoff"]
        return {
            "exact_action": matched, "rows": len(rows), "row_weighted_exact_accuracy": matched / len(rows),
            "tool_selection_correct": sum(row[key].get("tool_name") == row["expected_tool_name"] for row in tool_rows),
            "tool_selection_denominator": len(tool_rows),
            "exact_arguments_correct": sum(row[key].get("arguments", {}) == row["expected_arguments"] for row in arg_rows),
            "exact_arguments_denominator": len(arg_rows),
            "correct_clarifications": sum(row[key].get("action_type") == "clarification" and row[key].get("missing_fields") == row["expected_missing_fields"] for row in clarifications),
            "clarification_denominator": len(clarifications),
            "correct_handoffs": sum(row[key].get("action_type") == "handoff" for row in handoffs),
            "handoff_denominator": len(handoffs),
            "unexpected_write_proposals": sum(row[key].get("action_type") == "propose_state_change" and row["expected_action_type"] != "propose_state_change" for row in rows),
        }

    def core_score(key):
        return statistics.mean(statistics.mean(row[key + "_exact"] for row in group) for group in groups.values())

    results = {key: score(key) for key in ("raw", "baseline", "candidate")}
    results["raw"]["core_weighted_exact_accuracy"] = core_score("raw")
    results["baseline"]["core_weighted_exact_accuracy"] = core_score("baseline")
    results["candidate"]["core_weighted_exact_accuracy"] = core_score("candidate")
    latencies = [row["latency_ms"] for row in raw["outcomes"] if row.get("latency_ms") is not None]
    artifact = {
        "comparison_version": "p2-recovery-v1-paired-saved-proposal-replay",
        "scope": "Actual local Ollama model proposals followed by offline V2/V5 action replay; replay executes no business tools.",
        "dataset_sha256": dataset_hash, "rows": len(rows), "unique_normalized_prompt_cores": len(groups),
        "repeated_core_count": sum(len(group) > 1 for group in groups.values()),
        "core_multiplicities": sorted((len(group) for group in groups.values() if len(group) > 1), reverse=True),
        "scenario_families": len(families), "model_id": raw.get("model_id"), "model_metadata": raw.get("model_metadata"),
        "generation": raw.get("generation"), "raw_model_latency_ms_p50": statistics.median(latencies) if latencies else None,
        "raw_model_latency_ms_p95": sorted(latencies)[max(0, int(len(latencies) * .95 + .999999) - 1)] if latencies else None,
        "scores": results,
        "paired_improvement_pp": {
            "v5_minus_v2_row_weighted": (results["candidate"]["row_weighted_exact_accuracy"] - results["baseline"]["row_weighted_exact_accuracy"]) * 100,
            "v5_minus_v2_core_weighted": (results["candidate"]["core_weighted_exact_accuracy"] - results["baseline"]["core_weighted_exact_accuracy"]) * 100,
        },
        "per_family": {
            name: {key: {"correct": sum(row[key + "_exact"] for row in group), "rows": len(group)} for key in ("raw", "baseline", "candidate")}
            for name, group in sorted(families.items())
        },
        "outcomes": rows,
        "limitations": "Labels are internal and not independently reviewed. Action replay is not tool execution or end-to-end completion. This new set is exposed development/evaluation evidence after the run and must not be reused as untouched validation.",
    }
    dest = args.output.resolve()
    if dest.exists():
        raise SystemExit(f"Refusing to overwrite existing artifact: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"scores": results, "paired_improvement_pp": artifact["paired_improvement_pp"], "path": str(dest)}, indent=2))


if __name__ == "__main__":
    main()
