"""One paired, offline V5-dev controller comparison using reviewed labels."""

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


def exact_match(action, expected):
    if not isinstance(action, dict):
        return False
    if action.get("action_type") != expected["action_type"]:
        return False
    if action.get("tool_name") != expected["tool_name"]:
        return False
    if isinstance(expected.get("missing_fields"), list):
        return action.get("missing_fields") == expected["missing_fields"]
    arguments = expected.get("arguments")
    return not isinstance(arguments, dict) or action.get("arguments", {}) == arguments


def rate(numerator, denominator):
    return numerator / denominator if denominator else None


def score(outcomes):
    exact = sum(row["exact"] for row in outcomes)
    tool_rows = [row for row in outcomes if row["expected_tool_name"] is not None]
    argument_rows = [row for row in outcomes if isinstance(row["expected_arguments"], dict)]
    clarification_rows = [row for row in outcomes if row["expected_action_type"] == "clarification"]
    handoff_rows = [row for row in outcomes if row["expected_action_type"] == "handoff"]
    return {
        "rows": len(outcomes),
        "exact_action_matches": exact,
        "row_weighted_exact_action_accuracy": rate(exact, len(outcomes)),
        "tool_selection_matches": sum(row["action"].get("tool_name") == row["expected_tool_name"] for row in tool_rows if isinstance(row["action"], dict)),
        "tool_selection_denominator": len(tool_rows),
        "tool_selection_accuracy": rate(sum(row["action"].get("tool_name") == row["expected_tool_name"] for row in tool_rows if isinstance(row["action"], dict)), len(tool_rows)),
        "exact_argument_matches": sum(row["action"].get("arguments", {}) == row["expected_arguments"] for row in argument_rows if isinstance(row["action"], dict)),
        "argument_denominator": len(argument_rows),
        "argument_accuracy": rate(sum(row["action"].get("arguments", {}) == row["expected_arguments"] for row in argument_rows if isinstance(row["action"], dict)), len(argument_rows)),
        "correct_clarifications": sum(row["exact"] for row in clarification_rows),
        "clarification_denominator": len(clarification_rows),
        "correct_handoffs": sum(row["exact"] for row in handoff_rows),
        "handoff_denominator": len(handoff_rows),
        "unexpected_write_proposals": sum(isinstance(row["action"], dict) and row["action"].get("action_type") == "propose_state_change" and row["expected_action_type"] != "propose_state_change" for row in outcomes),
        "unknown_tool_actions": sum(isinstance(row["action"], dict) and row["action"].get("action_type") == "tool_call" and row["action"].get("tool_name") not in {"lookup_order", "list_order_items", "get_return_policy", "check_refund_eligibility", "calculate_refund_estimate"} for row in outcomes),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--overlay", type=Path, default=ROOT / "experiments/results/p2_v5_dev_review_overlay_v1.json")
    parser.add_argument("--raw-dev", type=Path, default=ROOT / "experiments/results/hybrid_controller_v5_raw_dev_final.json")
    parser.add_argument("--baseline", type=Path, default=ROOT / "experiments/results/hybrid_controller_v5_raw_dev_controller_baseline_forensic.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = [args.overlay.resolve(), args.raw_dev.resolve(), args.baseline.resolve()]
    overlay, raw, baseline = (json.loads(path.read_text(encoding="utf-8")) for path in paths)
    assert overlay["review_protocol"]["no_unresolved_as_correct"] is True
    reviewed = {row["example_id"]: row for row in overlay["examples"] if row["review_status"] == "reviewed"}
    proposals = {row["example_id"]: row for row in raw["outcomes"]}
    baseline_rows = {row["example_id"]: row for row in baseline["outcomes"]}
    if not (set(reviewed) == set(proposals) == set(baseline_rows)):
        raise SystemExit("Refusing comparison: reviewed/raw/baseline example IDs differ.")
    from app.hybrid_controller_v3_candidate import HybridControllerV3Candidate

    controller = HybridControllerV3Candidate()
    paired = []
    for example_id, annotation in reviewed.items():
        row = annotation
        prompt = row["original_user_message"]
        model_row = proposals[example_id]
        decision = controller.preflight(prompt, [])
        if decision is None and model_row.get("valid_action") and model_row.get("prediction") is not None:
            decision = controller.apply(prompt, model_row["prediction"], [])
        candidate_action = decision.action if decision else None
        expected = row["reviewed_annotation"]
        old_action = baseline_rows[example_id].get("hybrid_action")
        paired.append({
            "example_id": example_id,
            "scenario_family": row["scenario_family"],
            "normalized_core": row["normalized_core"],
            "core_multiplicity": overlay["dataset"]["core_multiplicities"][row["normalized_core"]],
            "reviewed_expected": expected,
            "expected_action_type": expected["action_type"],
            "expected_tool_name": expected["tool_name"],
            "expected_arguments": expected["arguments"],
            "expected_missing_fields": expected["missing_fields"],
            "baseline_action": old_action,
            "candidate_action": candidate_action,
            "baseline_exact": exact_match(old_action, expected),
            "candidate_exact": exact_match(candidate_action, expected),
            "baseline_decision": baseline_rows[example_id]["controller_decision"],
            "candidate_decision": decision.decision if decision else "failed_closed",
            "candidate_reason": decision.reason if decision else "model_proposal_unavailable_or_invalid",
        })

    grouped_core = defaultdict(list)
    grouped_family = defaultdict(list)
    family_core = defaultdict(lambda: defaultdict(list))
    for row in paired:
        grouped_core[row["normalized_core"]].append(row)
        grouped_family[row["scenario_family"]].append(row)
        family_core[row["scenario_family"]][row["normalized_core"]].append(row)

    base_core_rates = {core: statistics.mean(row["baseline_exact"] for row in rows) for core, rows in grouped_core.items()}
    cand_core_rates = {core: statistics.mean(row["candidate_exact"] for row in rows) for core, rows in grouped_core.items()}
    core_table = []
    for core, rows in grouped_core.items():
        core_table.append({"normalized_core": core, "scenario_family": rows[0]["scenario_family"], "multiplicity": len(rows),
                           "baseline_exact": sum(row["baseline_exact"] for row in rows), "candidate_exact": sum(row["candidate_exact"] for row in rows),
                           "baseline_core_accuracy": base_core_rates[core], "candidate_core_accuracy": cand_core_rates[core],
                           "core_change": cand_core_rates[core] - base_core_rates[core]})

    baseline_score = score([{"action": row["baseline_action"], "exact": row["baseline_exact"], **row} for row in paired])
    candidate_score = score([{"action": row["candidate_action"], "exact": row["candidate_exact"], **row} for row in paired])
    baseline_score["core_weighted_exact_action_accuracy"] = statistics.mean(base_core_rates.values())
    candidate_score["core_weighted_exact_action_accuracy"] = statistics.mean(cand_core_rates.values())
    by_family = {}
    for family, rows in sorted(grouped_family.items()):
        cores = family_core[family]
        by_family[family] = {
            "rows": len(rows),
            "unique_cores": len(cores),
            "baseline_row_accuracy": rate(sum(r["baseline_exact"] for r in rows), len(rows)),
            "candidate_row_accuracy": rate(sum(r["candidate_exact"] for r in rows), len(rows)),
            "baseline_core_weighted_accuracy": statistics.mean(statistics.mean(r["baseline_exact"] for r in core_rows) for core_rows in cores.values()),
            "candidate_core_weighted_accuracy": statistics.mean(statistics.mean(r["candidate_exact"] for r in core_rows) for core_rows in cores.values()),
        }
    repeat_groups = {}
    for label, keep in (("singleton_cores", 1), ("repeated_cores", 2)):
        selected = [row for row in paired if (row["core_multiplicity"] == 1) == (keep == 1)]
        selected_cores = {row["normalized_core"] for row in selected}
        base_correct = sum(row["baseline_exact"] for row in selected)
        cand_correct = sum(row["candidate_exact"] for row in selected)
        repeat_groups[label] = {
            "rows": len(selected), "cores": len(selected_cores),
            "baseline_row_accuracy": rate(base_correct, len(selected)),
            "candidate_row_accuracy": rate(cand_correct, len(selected)),
            "row_change_pp": 100 * (rate(cand_correct, len(selected)) - rate(base_correct, len(selected))) if selected else None,
            "baseline_core_weighted_accuracy": statistics.mean(base_core_rates[c] for c in selected_cores) if selected_cores else None,
            "candidate_core_weighted_accuracy": statistics.mean(cand_core_rates[c] for c in selected_cores) if selected_cores else None,
            "core_weighted_contribution_to_overall_change_pp": 100 * sum(cand_core_rates[c] - base_core_rates[c] for c in selected_cores) / len(base_core_rates),
        }
    row_gain_pp = 100 * (candidate_score["row_weighted_exact_action_accuracy"] - baseline_score["row_weighted_exact_action_accuracy"])
    core_gain_pp = 100 * (candidate_score["core_weighted_exact_action_accuracy"] - baseline_score["core_weighted_exact_action_accuracy"])
    repeated = [x for x in core_table if x["multiplicity"] > 1]
    multiplicities = sorted(len(rows) for rows in grouped_core.values())
    gate = {
        "minimum_distinct_reviewed_cores": 20,
        "minimum_scenario_families": 10,
        "minimum_row_gain_pp": 10,
        "minimum_core_gain_pp": 10,
        "enough_cores_and_families": len(grouped_core) >= 20 and len(grouped_family) >= 10,
        "row_gain_pass": row_gain_pp >= 10,
        "core_gain_pass": core_gain_pp >= 10,
        "clarification_nonregression": candidate_score["correct_clarifications"] >= baseline_score["correct_clarifications"],
        "handoff_nonregression": candidate_score["correct_handoffs"] >= baseline_score["correct_handoffs"],
        "safety_counts_nonregressed": candidate_score["unexpected_write_proposals"] <= baseline_score["unexpected_write_proposals"] and candidate_score["unknown_tool_actions"] <= baseline_score["unknown_tool_actions"],
    }
    gate["passed"] = all(gate.values())
    result = {
        "comparison_version": "p2-v5-dev-controller-comparison-v1",
        "evaluation_scope": "V5 development saved proposals only; offline action replay; no tool/database execution and no inference.",
        "model_backend": "saved Ollama Qwen3-1.7B Q4_K_M proposals; no new model calls",
        "controller_baseline": {"version": baseline["controller_version"], "source_sha256": baseline["controller_source_sha256"], "artifact": str(paths[2].relative_to(ROOT))},
        "controller_candidate": {"version": controller.version, "source_sha256": hashlib.sha256((ROOT / "backend/app/hybrid_controller_v3_candidate.py").read_bytes()).hexdigest()},
        "overlay": {"artifact": str(paths[0].relative_to(ROOT)), "sha256": hashlib.sha256(paths[0].read_bytes()).hexdigest(), **overlay["dataset"]},
        "normalization": overlay["review_protocol"]["normalization"],
        "denominators": {"rows": len(paired), "unique_cores": len(grouped_core), "repeated_cores": len(repeated), "singleton_cores": sum(x["multiplicity"] == 1 for x in core_table), "families": len(grouped_family), "core_multiplicities_sorted": multiplicities, "reviewed_rows": len(paired), "unresolved_rows_excluded": overlay["dataset"]["unresolved_rows"]},
        "baseline": baseline_score,
        "candidate": candidate_score,
        "paired_gain_percentage_points": {"row_weighted": row_gain_pp, "core_weighted": core_gain_pp},
        "repeated_core_contribution": repeat_groups,
        "per_family": by_family,
        "gate": gate,
        "core_results": core_table,
        "outcomes": paired,
        "provenance": "Review overlay annotations were derived from prompts, synthetic seed records, registered schemas and business rules. Official V5 labels and frozen model artifacts were not modified. Candidate was evaluated once; no held-out examples were used.",
    }
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"baseline": baseline_score, "candidate": candidate_score,
                      "gain_pp": result["paired_gain_percentage_points"], "gate": gate}, indent=2))


if __name__ == "__main__":
    main()
