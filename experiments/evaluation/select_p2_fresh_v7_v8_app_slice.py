"""Preselect two actual-application cases per frozen fresh-set family."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiments/datasets/p2_fresh_v7_v8_v1/scenarios.jsonl"
OUT = ROOT / "experiments/results/p2_fresh_v7_v8_app_slice_selection.json"


def main():
    if OUT.exists():
        raise SystemExit(f"Refusing to overwrite {OUT}")
    cases = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    families = defaultdict(list)
    for case in cases:
        families[case["scenario_family"]].append(case)
    selected = [case for name in sorted(families) for case in families[name][:2]]
    if len(selected) < 24 or any(sum(row["scenario_family"] == name for row in selected) < 2 for name in families):
        raise SystemExit("Application slice must include at least two examples per scenario family")
    suite = {
        "selection_version": "p2-fresh-v7-v8-real-app-slice-v1",
        "dataset_version": "p2-fresh-v7-v8-v1",
        "dataset_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
        "selection_policy": "First two pre-authored cases per family, selected before any model inference; same cases in separate fresh DBs for V7 and V8.",
        "case_count": len(selected), "cases": selected,
    }
    OUT.write_text(json.dumps(suite, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUT), "case_count": len(selected),
                      "families": len(families), "family_counts": {name: 2 for name in sorted(families)}}, indent=2))


if __name__ == "__main__":
    main()
