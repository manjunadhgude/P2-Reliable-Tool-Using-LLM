"""Generate the versioned V3 synthetic reliability suite from new wording pools.

V3 deliberately uses a new seed and style wrappers, with disjoint dev/test
template assignments. It is an internal synthetic benchmark, not a third-party
independent benchmark.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "experiments/datasets/hybrid_controller_v2/scenarios.jsonl"
OUT = ROOT / "experiments/datasets/hybrid_controller_v3"
DEV_STYLES = ["In plain terms, {p}", "Please help me: {p}", "I need you to {pl}", "Could you handle this request? {p}", "For a customer-support check, {pl}"]
TEST_STYLES = ["Quick question: {p}", "Customer says: {p}", "Please investigate this: {p}", "I would like assistance. {p}", "Can you take care of the following? {p}", "Support request — {p}", "Tell me this: {p}", "I need an answer: {p}", "Would you check this? {p}", "Here is the issue: {p}"]

def main():
    rows = [json.loads(x) for x in V2.read_text(encoding="utf-8").splitlines() if x.strip()]
    families = sorted({r["scenario_family"] for r in rows})
    by_family = {f: [r for r in rows if r["scenario_family"] == f] for f in families}
    out = []
    # 60 dev and 150 test, with each family represented in both pools.
    for split, total, styles in (("dev", 60, DEV_STYLES), ("test", 150, TEST_STYLES)):
        for i in range(total):
            src = by_family[families[i % len(families)]][i % len(by_family[families[i % len(families)]])]
            style = styles[i % len(styles)]
            prompt = style.format(p=src["user_message"], pl=src["user_message"].lower())
            item = dict(src)
            item.update({"example_id": f"v3-{split}-{i+1:04d}", "split": split,
                         "dataset_version": "p2-hybrid-controller-v3",
                         "user_message": prompt, "suite_version": "v3",
                         "generator_seed": 20261010, "provenance": "internal_synthetic_v3_new_style_pool"})
            out.append(item)
    OUT.mkdir(parents=True, exist_ok=True)
    suite = OUT / "scenarios.jsonl"
    suite.write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in out), encoding="utf-8")
    manifest = {"suite_version": "v3", "generator": "generate_v3_suite.py", "seed": 20261010,
                "scenario_examples": len(out), "split_counts": {"dev": 60, "test": 150},
                "families": families, "sha256": hashlib.sha256(suite.read_bytes()).hexdigest(),
                "internal_synthetic": True, "source_v2_preserved": True}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
