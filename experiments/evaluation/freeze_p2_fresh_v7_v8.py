"""Freeze dataset, evaluators, application sources, controller sources, and local model."""

import argparse
import hashlib
import json
import platform
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = [
    "experiments/datasets/p2_fresh_v7_v8_v1/scenarios.jsonl",
    "experiments/datasets/p2_fresh_v7_v8_v1/ANNOTATION_POLICY.md",
    "experiments/data_generation/generate_p2_fresh_v7_v8.py",
    "experiments/evaluation/audit_p2_fresh_v7_v8_overlap.py",
    "experiments/evaluation/compare_fresh_v7_v8.py",
    "experiments/evaluation/select_p2_fresh_v7_v8_app_slice.py",
    "experiments/evaluation/run_p2_fresh_v7_v8_application.py",
    "experiments/evaluation/freeze_p2_fresh_v7_v8.py",
    "experiments/evaluation/run_ollama_benchmark.py",
    "backend/app/hybrid_controller_v7_candidate.py",
    "backend/app/hybrid_controller_v8_candidate.py",
    "backend/app/hybrid_controller_v6_candidate.py",
    "backend/app/hybrid_controller_v5_candidate.py",
    "backend/app/hybrid_controller.py",
    "backend/app/main.py",
    "backend/app/tools/domain.py",
    "backend/app/tools/registry.py",
    "backend/app/llm/backends.py",
    "backend/app/core/config.py",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3:1.7b")
    ap.add_argument("--ollama-url", default="http://localhost:11434")
    ap.add_argument("--timeout-seconds", type=int, default=30)
    ap.add_argument("--max-new-tokens", type=int, default=256)
    ap.add_argument("--output", type=Path, default=ROOT / "experiments/results/p2_fresh_v7_v8_freeze.json")
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit(f"Refusing to overwrite {args.output}")
    with urllib.request.urlopen(args.ollama_url.rstrip("/") + "/api/tags", timeout=5) as response:
        tags = json.load(response)
    model = next((item for item in tags.get("models", []) if args.model in {item.get("name"), item.get("model")}), None)
    if not model:
        raise SystemExit(f"Model {args.model!r} is not present locally; downloads are forbidden by this evaluation.")
    missing = [name for name in FILES if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit(f"Cannot freeze; missing files: {missing}")
    dataset = ROOT / FILES[0]
    rows = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    families = sorted({row["scenario_family"] for row in rows})
    if len(rows) < 120 or len({row["user_message"].casefold() for row in rows}) != len(rows) or len(families) < 12:
        raise SystemExit("Dataset failed minimum row/core/family freeze gate")
    overlap_path = ROOT / "experiments/results/p2_fresh_v7_v8_overlap_audit.json"
    overlap = json.loads(overlap_path.read_text(encoding="utf-8"))
    if overlap["dataset_sha256"] != sha(dataset) or overlap["near_duplicate_matches"]:
        raise SystemExit("Overlap audit is missing, stale, or contains matches; resolve before freeze")
    artifact = {
        "freeze_version": "p2-fresh-v7-v8-v1-frozen-before-inference",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "fresh development evaluation; internal labels; not a human-adjudicated acceptance test",
        "dataset": {"path": FILES[0], "sha256": sha(dataset), "rows": len(rows),
                    "unique_prompt_cores": len(rows), "scenario_families": len(families),
                    "family_counts": {name: sum(row["scenario_family"] == name for row in rows) for name in families},
                    "split": "dev"},
        "annotation_policy_sha256": sha(ROOT / FILES[1]),
        "application_slice": {"path": "experiments/results/p2_fresh_v7_v8_app_slice_selection.json",
                              "sha256": sha(ROOT / "experiments/results/p2_fresh_v7_v8_app_slice_selection.json"),
                              "cases": json.loads((ROOT / "experiments/results/p2_fresh_v7_v8_app_slice_selection.json").read_text(encoding="utf-8"))["case_count"]},
        "overlap_audit": {"path": "experiments/results/p2_fresh_v7_v8_overlap_audit.json",
                          "sha256": sha(overlap_path), "prior_prompts_screened": overlap["prior_prompt_count"],
                          "matches": len(overlap["near_duplicate_matches"])},
        "controllers": {"v7": "opt-in; preserved source", "v8": "opt-in; preserved source",
                        "v7_sha256": sha(ROOT / "backend/app/hybrid_controller_v7_candidate.py"),
                        "v8_sha256": sha(ROOT / "backend/app/hybrid_controller_v8_candidate.py"),
                        "default_controller": "v2", "default_backend": "deterministic_test"},
        "model": {key: model.get(key) for key in ("name", "model", "digest", "details", "modified_at")},
        "generation": {"temperature": 0, "think": False, "stream": False,
                       "timeout_seconds": args.timeout_seconds, "max_new_tokens": args.max_new_tokens,
                       "repair_retries": 1, "prompt": "OllamaModelBackend production prompt", "backend": "local Ollama"},
        "source_hashes": {name: sha(ROOT / name) for name in FILES},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "ollama_url": args.ollama_url},
        "prohibitions": ["no controller edits after this freeze", "no dataset or scoring changes after inference",
                         "no V5 test split", "no model downloads", "no paid or cloud inference"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"freeze": str(args.output), "dataset": artifact["dataset"],
                      "model": artifact["model"], "v7_sha256": artifact["controllers"]["v7_sha256"],
                      "v8_sha256": artifact["controllers"]["v8_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
