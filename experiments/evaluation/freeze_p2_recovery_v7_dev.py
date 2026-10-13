"""Freeze P2 recovery candidate, data, evaluator and cached Ollama identity."""

import argparse
import hashlib
import json
import platform
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/results/p2_recovery_v7_dev_freeze.json")
    parser.add_argument("--model", default="qwen3:1.7b")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    args = parser.parse_args()
    model_tags = urllib.request.urlopen(args.ollama_url.rstrip("/") + "/api/tags", timeout=5)
    tags = json.load(model_tags)
    model = next((item for item in tags.get("models", []) if args.model in {item.get("name"), item.get("model")}), None)
    if not model:
        raise SystemExit(f"Model {args.model!r} is not already present in local Ollama; refusing downloads.")
    tracked = [
        "backend/app/hybrid_controller.py", "backend/app/hybrid_controller_v3_candidate.py",
        "backend/app/hybrid_controller_v4_candidate.py", "backend/app/hybrid_controller_v5_candidate.py",
        "backend/app/hybrid_controller_v6_candidate.py", "backend/app/hybrid_controller_v7_candidate.py",
        "backend/app/main.py", "backend/app/tools/domain.py", "backend/app/tools/registry.py",
        "backend/app/core/config.py", "backend/app/llm/backends.py",
        "backend/tests/test_hybrid_controller_v5_candidate.py", "backend/tests/test_hybrid_controller_v6_candidate.py", "backend/tests/test_hybrid_controller_v7_candidate.py",
        "experiments/data_generation/generate_p2_recovery_v2.py",
        "experiments/evaluation/run_ollama_benchmark.py",
        "experiments/evaluation/compare_controller_v6_real_model.py",
        "experiments/evaluation/freeze_p2_recovery_v2.py",
        "experiments/evaluation/prepare_p2_recovery_application_v2.py",
        "experiments/evaluation/run_p2_recovery_v2_application_v1.py",
        "experiments/datasets/p2_recovery_v2/scenarios.jsonl",
        "experiments/datasets/p2_recovery_v2/manifest.json",
        "experiments/datasets/p2_recovery_v2/ANNOTATION_POLICY.md",
        "experiments/results/p2_recovery_v2_application_selection.json",
    ]
    freeze = {
        "freeze_version": "p2-recovery-v7-development-diagnostic-freeze",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository_git_limitation": "No commits exist on the current master branch; hashes identify the frozen files but cannot establish historical ancestry.",
        "dataset_sha256": sha(ROOT / "experiments/datasets/p2_recovery_v2/scenarios.jsonl"),
        "dataset_manifest_sha256": sha(ROOT / "experiments/datasets/p2_recovery_v2/manifest.json"),
        "application_selection_sha256": sha(ROOT / "experiments/results/p2_recovery_v2_application_selection.json"),
        "candidate": "hybrid-controller-v7-intent-workflow-preflight-candidate; opt-in only; default V2 unchanged",
        "model_backend": "local Ollama; no network/cloud inference",
        "model_id": args.model,
        "model_metadata": {key: model.get(key) for key in ("name", "model", "digest", "details", "modified_at")},
        "generation": {"temperature": 0, "think": False, "stream": False, "timeout_seconds": 30, "max_new_tokens": 256},
        "application_defaults": {"model_backend": "deterministic_test", "hybrid_controller_enabled": False, "hybrid_controller_version": "v2"},
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "ollama_url": args.ollama_url},
        "source_hashes": {name: sha(ROOT / name) for name in tracked},
        "artifact_paths": {
            "raw_model": "experiments/results/p2_recovery_v2_raw.json",
            "paired_replay": "experiments/results/p2_recovery_v7_dev_comparison.json",
            "application": "experiments/results/p2_recovery_v7_dev_application.json",
        },
    }
    dest = args.output.resolve()
    if dest.exists():
        raise SystemExit(f"Refusing to overwrite existing freeze: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"freeze": str(dest), "dataset_sha256": freeze["dataset_sha256"], "model": freeze["model_metadata"]}, indent=2))


if __name__ == "__main__":
    main()
