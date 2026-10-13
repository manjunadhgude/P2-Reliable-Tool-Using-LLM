"""Validate V3 counts, family coverage, leakage and manifest checksum."""
import hashlib
import json
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "experiments/datasets/hybrid_controller_v3/scenarios.jsonl"
MANIFEST = ROOT / "experiments/datasets/hybrid_controller_v3/manifest.json"
def main():
    rows = [json.loads(x) for x in SUITE.read_text(encoding="utf-8").splitlines() if x.strip()]
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    counts = Counter(r["split"] for r in rows)
    assert len(rows) == 210 and dict(counts) == {"dev": 60, "test": 150}
    assert len({r["example_id"] for r in rows}) == len(rows)
    assert hashlib.sha256(SUITE.read_bytes()).hexdigest() == manifest["sha256"]
    assert len({r["user_message"] for r in rows if r["split"] == "dev"}.intersection(
        {r["user_message"] for r in rows if r["split"] == "test"})) == 0
    assert all(r.get("expected_action_type") and r.get("scenario_family") and r.get("provenance") == "internal_synthetic_v3_new_style_pool" for r in rows)
    families = {r["scenario_family"] for r in rows}
    assert len(families) >= 14 and all(any(r["scenario_family"] == f and r["split"] == "test" for r in rows) for f in families)
    print(json.dumps({"valid": True, "suite_version": "v3", "rows": len(rows), "split_counts": dict(counts), "families": sorted(families), "sha256": manifest["sha256"]}, indent=2))
if __name__ == "__main__":
    main()
