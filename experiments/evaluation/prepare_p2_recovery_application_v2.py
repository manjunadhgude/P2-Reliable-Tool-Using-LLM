"""Freeze a balanced 42-case slice of recovery V2 before inference."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiments/datasets/p2_recovery_v2/scenarios.jsonl"
OUT = ROOT / "experiments/results/p2_recovery_v2_application_selection.json"


def main():
    rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    groups = defaultdict(list)
    for row in rows:
        groups[row["scenario_family"]].append(row)
    extra = {"return_policy", "eligibility", "refund_estimate", "multi_step_workflow", "ticket_proposal"}
    selected = [row for family, items in sorted(groups.items()) for row in items[: (4 if family in extra else 2)]]
    assert len(selected) == 42
    artifact = {"selection_version": "p2-recovery-v2-app-42", "dataset_version": "p2-recovery-v2",
                "dataset_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
                "selection_rule": "Two examples from each of 16 families and two extra examples from return policy, eligibility, estimates, multi-step, and ticket workflows; frozen before model inference.",
                "case_count": 42, "scenario_families": len(groups), "cases": selected}
    if OUT.exists():
        raise SystemExit(f"Refusing to overwrite {OUT}")
    OUT.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUT), "cases": 42, "families": len(groups), "dataset_sha256": artifact["dataset_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
