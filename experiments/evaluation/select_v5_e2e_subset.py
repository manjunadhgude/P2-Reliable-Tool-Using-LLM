"""Select a deterministic, family-balanced V5 real-application subset."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[2]
DATASET = ROOT / "experiments/datasets/hybrid_controller_v5/scenarios.jsonl"
OUTPUT = ROOT / "experiments/results/hybrid_controller_v5_e2e_selection.json"
SEED = "p2-v5-e2e-selection-20261010"

rows = [json.loads(line) for line in DATASET.open(encoding="utf-8") if line.strip()]
families = sorted({row["scenario_family"] for row in rows})
selected = []
for family in families:
    candidates = [row for row in rows if row["split"] == "test" and row["scenario_family"] == family]
    ranked = sorted(candidates, key=lambda row: hashlib.sha256(f"{SEED}:{row['example_id']}".encode()).hexdigest())
    selected.extend(ranked[:3])
selected.sort(key=lambda row: row["example_id"])
payload = {
    "selection_version": "v5-e2e-balanced-1",
    "dataset_version": "v5",
    "dataset_sha256": __import__("hashlib").sha256(DATASET.read_bytes()).hexdigest(),
    "seed": SEED,
    "rule": "test split, exactly three lowest SHA-256 ranks per scenario_family",
    "case_count": len(selected),
    "families": families,
    "example_ids": [row["example_id"] for row in selected],
    "cases": selected,
}
OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"output": str(OUTPUT), "case_count": len(selected), "families": len(families)}))
