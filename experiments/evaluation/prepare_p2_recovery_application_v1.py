"""Create a deterministic 42-case real-application selection before inference."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiments/datasets/p2_recovery_v1/scenarios.jsonl"
OUT = ROOT / "experiments/results/p2_recovery_application_selection_v1.json"


def main():
    rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_family = defaultdict(list)
    for row in rows:
        by_family[row["scenario_family"]].append(row)
    extra_families = {"return_policy", "eligibility", "refund_estimate", "multi_step_workflow", "ticket_proposal"}
    selected = []
    for family in sorted(by_family):
        selected.extend(by_family[family][:4 if family in extra_families else 2])
    assert len(selected) == 42 and len({row["example_id"] for row in selected}) == 42
    artifact = {
        "selection_version": "p2-recovery-app-42-v1",
        "dataset_version": "p2-recovery-v1",
        "dataset_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
        "selection_rule": "Two first-listed rows from all 16 families plus the two remaining rows from return_policy, eligibility, refund_estimate, multi_step_workflow, and ticket_proposal. Selection was frozen before real-model inference.",
        "case_count": len(selected),
        "scenario_families": len(by_family),
        "cases": selected,
    }
    if OUT.exists():
        raise SystemExit(f"Refusing to overwrite {OUT}")
    OUT.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUT), "cases": len(selected), "families": len(by_family), "dataset_sha256": artifact["dataset_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
