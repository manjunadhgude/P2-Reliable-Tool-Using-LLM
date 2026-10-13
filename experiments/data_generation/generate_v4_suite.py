"""Generate V4 with a distinct wrapper pool from V1-V3."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/datasets/hybrid_controller_v3/scenarios.jsonl"
OUT = ROOT / "experiments/datasets/hybrid_controller_v4"
DEV = ["Agent note: {p}", "Please resolve: {p}", "The customer asks, {p}", "Work this request: {p}"]
TEST = ["New case received — {p}", "Customer message follows: {p}", "Handle this support item: {p}", "Can the operations team answer this? {p}", "Incoming request: {p}"]

def main():
    rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]
    families = sorted({row["scenario_family"] for row in rows})
    grouped = {family: [row for row in rows if row["scenario_family"] == family] for family in families}
    output = []
    for split, count, styles in (("dev", 60, DEV), ("test", 150, TEST)):
        for index in range(count):
            family = families[index % len(families)]
            source = grouped[family][(index * 3) % len(grouped[family])]
            text = source["user_message"]
            item = dict(source)
            item.update({"example_id": f"v4-{split}-{index + 1:04d}", "split": split,
                         "dataset_version": "p2-hybrid-controller-v4", "suite_version": "v4",
                         "user_message": f"{styles[index % len(styles)].format(p=text)} Reference {index + 1}.",
                         "generator_version": "v4-wrapper-pool-1", "provenance": "internal_synthetic_v4"})
            output.append(item)
    OUT.mkdir(parents=True, exist_ok=True)
    suite = OUT / "scenarios.jsonl"
    suite.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in output), encoding="utf-8")
    manifest = {"suite_version": "v4", "generator_version": "v4-wrapper-pool-1", "seed": 20261010,
                "scenario_examples": 210, "split_counts": {"dev": 60, "test": 150},
                "families": families, "template_pools": {"dev": "v4-dev-wrapper", "test": "v4-test-wrapper"},
                "sha256": hashlib.sha256(suite.read_bytes()).hexdigest(), "internal_synthetic": True}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
