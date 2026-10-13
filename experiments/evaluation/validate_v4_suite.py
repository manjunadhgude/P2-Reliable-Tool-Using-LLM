"""Validate V4 counts, family coverage, prompt leakage and checksum."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "experiments/datasets/hybrid_controller_v4/scenarios.jsonl"
MANIFEST = ROOT / "experiments/datasets/hybrid_controller_v4/manifest.json"

def main():
    rows = [json.loads(line) for line in SUITE.read_text(encoding="utf-8").splitlines() if line.strip()]
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    counts = Counter(row["split"] for row in rows)
    assert len(rows) == 210 and dict(counts) == {"dev": 60, "test": 150}
    assert len({row["example_id"] for row in rows}) == 210
    assert len({row["user_message"] for row in rows}) == 210
    assert hashlib.sha256(SUITE.read_bytes()).hexdigest() == manifest["sha256"]
    assert all(row["dataset_version"] == "p2-hybrid-controller-v4" and row["provenance"] == "internal_synthetic_v4" for row in rows)
    families = set(row["scenario_family"] for row in rows)
    assert len(families) == 14 and all(any(row["scenario_family"] == family and row["split"] == "test" for row in rows) for family in families)
    print(json.dumps({"valid": True, "rows": len(rows), "split_counts": dict(counts), "families": sorted(families), "sha256": manifest["sha256"]}, indent=2))

if __name__ == "__main__":
    main()
