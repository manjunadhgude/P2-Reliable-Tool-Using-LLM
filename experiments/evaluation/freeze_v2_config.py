"""Freeze the v2 source, evaluator, dataset, and local model identities before test inference."""

import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiments/datasets/hybrid_controller_v2/scenarios.jsonl"
FAULTS = ROOT / "experiments/datasets/hybrid_controller_v2/control_faults.jsonl"
MANIFEST = ROOT / "experiments/datasets/hybrid_controller_v2/manifest.json"
FILES = (
    "backend/app/hybrid_controller.py", "backend/app/main.py", "backend/app/llm/backends.py",
    "backend/app/schemas.py", "backend/app/tools/domain.py", "backend/app/tools/registry.py",
    "experiments/data_generation/generate_v2_suite.py", "experiments/evaluation/validate_v2_suite.py",
    "experiments/evaluation/run_ollama_benchmark.py", "experiments/evaluation/evaluate_hybrid_controller.py",
    "experiments/evaluation/run_hybrid_real_integration.py", "experiments/evaluation/freeze_v2_config.py",
    "experiments/datasets/hybrid_controller_v2/scenarios.jsonl",
    "experiments/datasets/hybrid_controller_v2/control_faults.jsonl",
    "experiments/datasets/hybrid_controller_v2/manifest.json", "config/action_envelope.schema.json",
)


def model_metadata():
    with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as response:
        models = json.load(response).get("models", [])
    return next((item for item in models if item.get("name") == "qwen3:1.7b"), None)


def main():
    suite = json.loads(MANIFEST.read_text(encoding="utf-8"))
    model = model_metadata()
    if not model or model.get("digest") != "8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7":
        raise SystemExit("Expected cached qwen3:1.7b digest is unavailable; refusing to freeze a different model.")
    source_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}
    source_digest = hashlib.sha256("\0".join(f"{name}\0{source_hashes[name]}" for name in sorted(source_hashes)).encode()).hexdigest()
    freeze = {
        "freeze_version": "p2-hybrid-controller-v2-freeze-1",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "controller_version": "hybrid-controller-v2",
        "backend": "ollama",
        "model_id": "qwen3:1.7b",
        "model_digest": model["digest"],
        "model_quantization": model.get("details", {}).get("quantization_level"),
        "ollama_runtime": "local Ollama HTTP API",
        "temperature": 0,
        "think": False,
        "stream": False,
        "max_new_tokens": 256,
        "request_timeout_seconds": 30,
        "hybrid_controller_enabled_for_raw_model_run": False,
        "hybrid_controller_enabled_for_application_run": True,
        "dataset_version": suite["dataset_version"],
        "test_scenarios": suite["split_counts"]["test"],
        "dev_scenarios": suite["split_counts"]["dev"],
        "test_dataset_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
        "control_fault_count": suite["deterministic_control_fault_count"],
        "control_faults_sha256": hashlib.sha256(FAULTS.read_bytes()).hexdigest(),
        "source_files": source_hashes,
        "source_bundle_sha256": source_digest,
        "old_v1_results_mutated": False,
        "test_use_policy": "run once after freeze; if a correctness defect is found, this set becomes diagnostic and cannot be reused as fresh final test",
    }
    dest = ROOT / "experiments/results/hybrid_controller_v2_frozen_config.json"
    dest.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(dest), "source_bundle_sha256": source_digest,
                      "test_dataset_sha256": freeze["test_dataset_sha256"], "model_digest": model["digest"]}, indent=2))


if __name__ == "__main__":
    main()
