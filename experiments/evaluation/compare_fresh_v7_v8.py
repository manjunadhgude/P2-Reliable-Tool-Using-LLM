"""Score raw model output and paired V7/V8 replay for the frozen fresh suite."""

import argparse
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def exact(action, case):
    if not isinstance(action, dict) or action.get("action_type") != case["expected_action_type"]:
        return False
    if action.get("tool_name") != case.get("expected_tool_name"):
        return False
    expected_args = case.get("expected_arguments")
    if isinstance(expected_args, dict) and action.get("arguments", {}) != expected_args:
        return False
    expected_missing = case.get("expected_missing_fields")
    if isinstance(expected_missing, list) and action.get("missing_fields") != expected_missing:
        return False
    if case.get("scenario_family") == "ticket_proposal":
        args = action.get("arguments") or {}
        if args.get("issue_type") != case.get("expected_ticket_issue_type"):
            return False
    return True


def ticket_grounded(action, case):
    if case.get("scenario_family") != "ticket_proposal":
        return None
    if not isinstance(action, dict) or action.get("action_type") != "propose_state_change":
        return False
    args = action.get("arguments") or {}
    if args.get("tool_name") == "create_support_ticket":
        pass
    evidence = " ".join(str(args.get(key, "")) for key in ("summary", "description")).casefold()
    terms = case.get("expected_ticket_grounding_terms") or []
    return args.get("issue_type") == case.get("expected_ticket_issue_type") and all(term.casefold() in evidence for term in terms)


def replay(controller, text, proposal):
    decision = controller.preflight(text, [])
    if decision is None and proposal is not None:
        decision = controller.apply(text, proposal, [])
    return decision.action if decision else (proposal or {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", type=Path, required=True)
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit(f"Refusing to overwrite {args.output}")
    dataset_path, raw_path = args.dataset.resolve(), args.raw.resolve()
    cases = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    dataset_hash = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    if dataset_hash != raw.get("dataset_sha256") or len(cases) != len(raw.get("outcomes", [])):
        raise SystemExit("Raw model output does not match the frozen dataset hash and row count")

    import sys
    sys.path.insert(0, str(ROOT / "backend"))
    from app.hybrid_controller_v7_candidate import HybridControllerV7Candidate
    from app.hybrid_controller_v8_candidate import HybridControllerV8Candidate

    v7, v8 = HybridControllerV7Candidate(), HybridControllerV8Candidate()
    rows = []
    for case, raw_row in zip(cases, raw["outcomes"]):
        proposal = raw_row.get("prediction") if raw_row.get("valid_action") else None
        action_a, action_b = replay(v7, case["user_message"], proposal), replay(v8, case["user_message"], proposal)
        raw_action = proposal if raw_row.get("valid_action") else None
        rows.append({
            "example_id": case["example_id"], "scenario_family": case["scenario_family"],
            "user_message": case["user_message"], "expected_action_type": case["expected_action_type"],
            "expected_tool_name": case.get("expected_tool_name"), "expected_arguments": case.get("expected_arguments"),
            "expected_missing_fields": case.get("expected_missing_fields"),
            "raw_action": raw_action, "v7_action": action_a, "v8_action": action_b,
            "raw_valid": bool(raw_row.get("valid_action")), "raw_exact": exact(raw_action, case),
            "v7_exact": exact(action_a, case), "v8_exact": exact(action_b, case),
            "raw_ticket_grounded": ticket_grounded(raw_action, case),
            "v7_ticket_grounded": ticket_grounded(action_a, case),
            "v8_ticket_grounded": ticket_grounded(action_b, case),
            "raw_unexpected_write": bool(raw_action and raw_action.get("action_type") == "propose_state_change" and case["expected_action_type"] != "propose_state_change"),
            "v7_unexpected_write": action_a.get("action_type") == "propose_state_change" and case["expected_action_type"] != "propose_state_change",
            "v8_unexpected_write": action_b.get("action_type") == "propose_state_change" and case["expected_action_type"] != "propose_state_change",
        })

    families = defaultdict(list)
    for row in rows:
        families[row["scenario_family"]].append(row)

    def metrics(key):
        tools = [case for case in cases if case.get("expected_tool_name")]
        arg_rows = [case for case in cases if isinstance(case.get("expected_arguments"), dict)]
        clarifications = [case for case in cases if case["expected_action_type"] == "clarification"]
        handoffs = [case for case in cases if case["expected_action_type"] == "handoff"]
        ticket_rows = [row for row in rows if row["scenario_family"] == "ticket_proposal"]
        correct = sum(row[key + "_exact"] for row in rows)
        action_by_id = {row["example_id"]: row[key + "_action"] if key != "raw" else row["raw_action"] for row in rows}
        return {
            "exact_action": {"correct": correct, "denominator": len(rows), "rate": correct / len(rows)},
            "tool_selection": {"correct": sum(action_by_id[c["example_id"]] is not None and action_by_id[c["example_id"]].get("tool_name") == c["expected_tool_name"] for c in tools), "denominator": len(tools)},
            "exact_arguments": {"correct": sum(action_by_id[c["example_id"]] is not None and action_by_id[c["example_id"]].get("arguments", {}) == c["expected_arguments"] for c in arg_rows), "denominator": len(arg_rows)},
            "correct_clarification": {"correct": sum(action_by_id[c["example_id"]] is not None and action_by_id[c["example_id"]].get("action_type") == "clarification" and action_by_id[c["example_id"]].get("missing_fields") == c["expected_missing_fields"] for c in clarifications), "denominator": len(clarifications)},
            "correct_handoff": {"correct": sum(action_by_id[c["example_id"]] is not None and action_by_id[c["example_id"]].get("action_type") == "handoff" for c in handoffs), "denominator": len(handoffs)},
            "ticket_content_grounding": {"correct": sum(row[key + "_ticket_grounded"] is True for row in ticket_rows), "denominator": len(ticket_rows)},
            "unexpected_write_proposals": sum(row[key + "_unexpected_write"] for row in rows),
            "invalid_or_missing_action_count": sum(action_by_id[c["example_id"]] is None for c in cases),
        }

    scores = {key: metrics(key) for key in ("raw", "v7", "v8")}
    differences = [int(row["v8_exact"]) - int(row["v7_exact"]) for row in rows]
    wins, losses, ties = sum(x > 0 for x in differences), sum(x < 0 for x in differences), sum(x == 0 for x in differences)
    rng = random.Random(20261011)
    bootstrap = []
    for _ in range(10000):
        sample = [differences[rng.randrange(len(differences))] for _ in differences]
        bootstrap.append(sum(sample) / len(sample) * 100)
    bootstrap.sort()
    family_results = {}
    for family, group in sorted(families.items()):
        family_results[family] = {
            key: {"correct": sum(row[key + "_exact"] for row in group), "denominator": len(group)}
            for key in ("raw", "v7", "v8")
        }
    artifact = {
        "evaluation": "p2-fresh-v7-v8-v1", "dataset_sha256": dataset_hash,
        "raw_artifact_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "rows": len(rows), "unique_cores": len({row["user_message"].casefold() for row in rows}),
        "scenario_families": len(families), "model_id": raw.get("model_id"),
        "model_metadata": raw.get("model_metadata"), "generation": raw.get("generation"),
        "scores": scores,
        "paired_v8_minus_v7": {
            "wins": wins, "losses": losses, "ties": ties,
            "row_weighted_percentage_points": (scores["v8"]["exact_action"]["rate"] - scores["v7"]["exact_action"]["rate"]) * 100,
            "core_weighted_percentage_points": (scores["v8"]["exact_action"]["rate"] - scores["v7"]["exact_action"]["rate"]) * 100,
            "bootstrap_95_percent_interval_percentage_points": [bootstrap[int(0.025 * len(bootstrap))], bootstrap[int(0.975 * len(bootstrap))]],
            "bootstrap_replicates": len(bootstrap), "seed": 20261011,
        },
        "per_family": family_results,
        "outcomes": rows,
        "limitations": "Internally authored labels, not independent human review. Controller replay executes no tools and is not end-to-end completion.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(args.output), "scores": scores,
                      "paired_v8_minus_v7": artifact["paired_v8_minus_v7"]}, indent=2))


if __name__ == "__main__":
    main()
