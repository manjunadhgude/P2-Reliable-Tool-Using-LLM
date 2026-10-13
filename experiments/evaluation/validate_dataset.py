import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiments" / "datasets" / "scenarios.jsonl"
MANIFEST = ROOT / "experiments" / "datasets" / "manifest.json"
ALLOWED = {"tool_call", "final_answer", "propose_state_change", "clarification", "handoff"}


def main() -> int:
    errors = []
    rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [r.get("example_id") for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate example_id")
    family_splits: dict[str, set[str]] = {}
    for row in rows:
        family_splits.setdefault(row["scenario_family"], set()).add(row["split"])
        if row["split"] not in {"train", "validation", "test"} or row["expected_action_type"] not in ALLOWED:
            errors.append(f"invalid split/action in {row['example_id']}")
        needs_tool = row["expected_action_type"] in {"tool_call", "propose_state_change"}
        if needs_tool != bool(row["expected_tool_name"]):
            errors.append(f"tool label/action mismatch in {row['example_id']}")
    if any(len(splits) != 1 for splits in family_splits.values()):
        errors.append("scenario family leakage across splits")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    digest = hashlib.sha256(DATA.read_bytes()).hexdigest()
    if manifest["sha256"] != digest or manifest["total_examples"] != len(rows):
        errors.append("manifest checksum/count mismatch")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Dataset valid: {len(rows)} examples; sha256={digest}; split counts={manifest['split_counts']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
