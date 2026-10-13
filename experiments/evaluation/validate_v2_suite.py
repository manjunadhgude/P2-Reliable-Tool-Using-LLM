"""Validate v2 suite shape, disjoint prompt pools, and manifest checksum."""

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "experiments/datasets/hybrid_controller_v2/scenarios.jsonl"
MANIFEST = ROOT / "experiments/datasets/hybrid_controller_v2/manifest.json"
FAULTS = ROOT / "experiments/datasets/hybrid_controller_v2/control_faults.jsonl"


def main():
    rows = [json.loads(line) for line in SUITE.read_text(encoding="utf-8").splitlines() if line.strip()]
    faults = [json.loads(line) for line in FAULTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    prompts = {split: [row["user_message"] for row in rows if row["split"] == split] for split in ("dev", "test")}
    counts = Counter(row["split"] for row in rows)
    assert hashlib.sha256(SUITE.read_bytes()).hexdigest() == manifest["sha256"]
    assert len(rows) == manifest["scenario_examples"]
    assert len(rows) + len(faults) == manifest["total_examples"]
    assert len(faults) == manifest["deterministic_control_fault_count"] == 30
    assert hashlib.sha256(FAULTS.read_bytes()).hexdigest() == manifest["control_faults_sha256"]
    assert dict(counts) == manifest["split_counts"] == {"dev": 28, "test": 140}
    assert set(prompts["dev"]).isdisjoint(prompts["test"])
    assert len({row["example_id"] for row in rows}) == len(rows)
    assert all(row.get("expected_action_type") and row.get("scenario_family") and row.get("user_message") for row in rows)
    required = {"order_lookup", "item_listing", "return_policy", "eligibility", "refund_estimate",
                "multi_step_read", "missing_order", "missing_item", "ticket_missing_order",
                "ticket_proposal", "conflicting_order", "no_tool", "prompt_injection", "cross_tenant"}
    test_families = {row["scenario_family"] for row in rows if row["split"] == "test"}
    assert required == test_families
    assert {row["scenario_family"] for row in faults} == {"malformed_output", "unknown_tool", "runtime_failure"}
    print(json.dumps({"valid": True, "scenario_examples": len(rows), "control_faults": len(faults),
                      "total": len(rows) + len(faults), "split_counts": dict(counts),
                      "test_families": sorted(test_families), "sha256": manifest["sha256"],
                      "control_faults_sha256": manifest["control_faults_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
