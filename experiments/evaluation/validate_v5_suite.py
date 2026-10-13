"""Validate V5 split integrity at the underlying template-core level."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "experiments/datasets/hybrid_controller_v5/scenarios.jsonl"
MANIFEST = ROOT / "experiments/datasets/hybrid_controller_v5/manifest.json"
ID_RE = re.compile(r"(?:ORD|ITEM)-\d+")

def normalize(text):
    return re.sub(r"\s+", " ", ID_RE.sub("<ID>", text.lower())).strip()

def main():
    rows = [json.loads(line) for line in SUITE.read_text(encoding="utf-8").splitlines() if line.strip()]
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert len(rows) == 210 and dict(Counter(r["split"] for r in rows)) == {"dev": 60, "test": 150}
    assert len({r["example_id"] for r in rows}) == 210
    assert len({r["user_message"] for r in rows}) == 210
    assert hashlib.sha256(SUITE.read_bytes()).hexdigest() == manifest["sha256"]
    dev, test = [r for r in rows if r["split"] == "dev"], [r for r in rows if r["split"] == "test"]
    assert not {r["template_core_id"] for r in dev} & {r["template_core_id"] for r in test}
    assert not {normalize(r["user_message"]) for r in dev} & {normalize(r["user_message"]) for r in test}
    assert all(r["template_pool_id"] == f"v5-{r['split']}-pool" for r in rows)
    assert all(r["dataset_version"] == "p2-hybrid-controller-v5" and r["provenance"] == "internal_synthetic_v5" for r in rows)
    assert len({r["scenario_family"] for r in rows}) == 14
    print(json.dumps({"valid": True, "rows": len(rows), "split_counts": dict(Counter(r["split"] for r in rows)), "template_core_overlap": 0, "normalized_core_overlap": 0, "sha256": manifest["sha256"]}, indent=2))

if __name__ == "__main__":
    main()
