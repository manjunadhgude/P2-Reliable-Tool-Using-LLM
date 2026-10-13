"""Paired diagnostic replay of one saved proposal through V7 and V8."""

import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def normalize(text):
    import re
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


def replay(controller, case, proposal):
    decision = controller.preflight(case["user_message"], [])
    if decision is None:
        decision = controller.apply(case["user_message"], proposal, [])
    return decision.action if decision else proposal


def main():
    dataset = ROOT / "experiments/datasets/p2_recovery_v2/scenarios.jsonl"
    raw_path = ROOT / "experiments/results/p2_recovery_v2_raw.json"
    out = ROOT / "experiments/results/p2_stage1_v7_v8_exposed_replay.json"
    if out.exists():
        raise SystemExit(f"Refusing to overwrite {out}")
    cases = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    dsha = hashlib.sha256(dataset.read_bytes()).hexdigest()
    if raw.get("dataset_sha256") != dsha or len(cases) != len(raw.get("outcomes", [])):
        raise SystemExit("Saved proposals do not match the dataset hash and row count")

    import sys
    sys.path.insert(0, str(ROOT / "backend"))
    from app.hybrid_controller_v7_candidate import HybridControllerV7Candidate
    from app.hybrid_controller_v8_candidate import HybridControllerV8Candidate

    v7, v8 = HybridControllerV7Candidate(), HybridControllerV8Candidate()
    rows = []
    for case, raw_row in zip(cases, raw["outcomes"]):
        proposal = raw_row.get("prediction") if raw_row.get("valid_action") else None
        proposal = proposal or {}
        a, b = replay(v7, case, proposal), replay(v8, case, proposal)
        rows.append({
            "example_id": case["example_id"], "scenario_family": case["scenario_family"],
            "user_message": case["user_message"], "normalized_core": normalize(case["user_message"]),
            "expected_action_type": case["expected_action_type"],
            "expected_tool_name": case.get("expected_tool_name"),
            "expected_arguments": case.get("expected_arguments"),
            "expected_missing_fields": case.get("expected_missing_fields"),
            "proposal": proposal, "v7_action": a, "v8_action": b,
            "v7_exact": exact(a, case), "v8_exact": exact(b, case),
            "v7_unexpected_write": a.get("action_type") == "propose_state_change" and case["expected_action_type"] != "propose_state_change",
            "v8_unexpected_write": b.get("action_type") == "propose_state_change" and case["expected_action_type"] != "propose_state_change",
        })

    cores, families = defaultdict(list), defaultdict(list)
    for row in rows:
        cores[row["normalized_core"]].append(row)
        families[row["scenario_family"]].append(row)

    def metrics(key):
        matched = sum(row[key + "_exact"] for row in rows)
        return {
            "correct": matched, "rows": len(rows), "row_weighted_accuracy": matched / len(rows),
            "core_weighted_accuracy": statistics.mean(
                statistics.mean(row[key + "_exact"] for row in group) for group in cores.values()
            ),
            "unexpected_writes": sum(row[key + "_unexpected_write"] for row in rows),
        }

    v7_metrics, v8_metrics = metrics("v7"), metrics("v8")
    families_out = {
        family: {
            key: {"correct": sum(row[key + "_exact"] for row in items), "rows": len(items)}
            for key in ("v7", "v8")
        } for family, items in sorted(families.items())
    }
    artifact = {
        "experiment": "p2-stage1-v7-v8-saved-proposal-replay-diagnostic",
        "status": "exposed_development_diagnostic_not_fresh_evaluation",
        "dataset_sha256": dsha,
        "raw_proposal_artifact_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "candidate_source_sha256": {
            "v7": hashlib.sha256((ROOT / "backend/app/hybrid_controller_v7_candidate.py").read_bytes()).hexdigest(),
            "v8": hashlib.sha256((ROOT / "backend/app/hybrid_controller_v8_candidate.py").read_bytes()).hexdigest(),
        },
        "proposal_source": "Same saved local Ollama Qwen 3 1.7B proposal row fed to both arms; no new inference.",
        "label_provenance": "Existing internal development labels; not independent human review.",
        "rows": len(rows), "unique_cores": len(cores), "families": len(families),
        "model_id": raw.get("model_id"), "model_metadata": raw.get("model_metadata"),
        "scores": {"v7": v7_metrics, "v8": v8_metrics},
        "paired_change_percentage_points": {
            "row_weighted": (v8_metrics["row_weighted_accuracy"] - v7_metrics["row_weighted_accuracy"]) * 100,
            "core_weighted": (v8_metrics["core_weighted_accuracy"] - v7_metrics["core_weighted_accuracy"]) * 100,
        },
        "per_family": families_out,
        "outcomes": rows,
        "limitations": "The 64-core recovery dataset has already been used to develop and compare V5-V7. This replay measures only a diagnostic effect on exposed examples; it is not a fresh evaluation, actual tool execution, or acceptance evidence.",
    }
    out.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(out), "scores": artifact["scores"], "paired_change_percentage_points": artifact["paired_change_percentage_points"]}, indent=2))


if __name__ == "__main__":
    main()
