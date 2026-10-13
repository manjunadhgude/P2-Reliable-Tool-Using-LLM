"""Freeze V3 dataset, evaluator, controller source and cached model identity."""
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiments/datasets/hybrid_controller_v3/scenarios.jsonl"
MANIFEST = ROOT / "experiments/datasets/hybrid_controller_v3/manifest.json"
FILES = ("backend/app/hybrid_controller.py", "backend/app/main.py", "backend/app/llm/backends.py", "backend/app/schemas.py", "backend/app/tools/domain.py", "backend/app/tools/registry.py", "experiments/data_generation/generate_v3_suite.py", "experiments/evaluation/validate_v3_suite.py", "experiments/evaluation/run_ollama_benchmark.py", "experiments/evaluation/evaluate_hybrid_controller.py", "experiments/evaluation/run_v3_e2e_subset.py", "experiments/datasets/hybrid_controller_v3/scenarios.jsonl", "experiments/datasets/hybrid_controller_v3/manifest.json", "config/action_envelope.schema.json")

def main():
    with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as response:
        models = json.load(response).get("models", [])
    model = next((item for item in models if item.get("name") == "qwen3:1.7b"), None)
    if not model:
        raise SystemExit("Cached qwen3:1.7b is unavailable; refusing to freeze a different model.")
    source_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}
    source_digest = hashlib.sha256("\0".join(f"{n}\0{source_hashes[n]}" for n in sorted(source_hashes)).encode()).hexdigest()
    freeze = {"freeze_version": "p2-hybrid-controller-v3-freeze-1", "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "controller_version": "hybrid-controller-v2", "backend": "ollama", "model_id": "qwen3:1.7b", "model_digest": model.get("digest"), "model_quantization": model.get("details", {}).get("quantization_level"), "max_new_tokens": 256, "request_timeout_seconds": 90, "hybrid_controller_enabled_for_raw_model_run": False, "hybrid_controller_enabled_for_application_run": True, "dataset_version": "v3", "test_scenarios": 150, "dev_scenarios": 60, "test_dataset_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(), "source_files": source_hashes, "source_bundle_sha256": source_digest, "old_results_mutated": False, "test_use_policy": "run once after freeze; any later source change requires a new V3.1 freeze"}
    dest = ROOT / "experiments/results/hybrid_controller_v3_frozen_config.json"
    dest.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(freeze, indent=2))

if __name__ == "__main__":
    main()
