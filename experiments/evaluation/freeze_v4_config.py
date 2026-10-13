"""Freeze V4 dataset and current local runtime identity before scoring."""
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = ("backend/app/hybrid_controller.py", "backend/app/main.py", "backend/app/llm/backends.py", "experiments/data_generation/generate_v4_suite.py", "experiments/evaluation/validate_v4_suite.py", "experiments/evaluation/run_ollama_benchmark.py", "experiments/evaluation/evaluate_hybrid_controller.py", "experiments/datasets/hybrid_controller_v4/scenarios.jsonl", "experiments/datasets/hybrid_controller_v4/manifest.json", "config/action_envelope.schema.json")

def main():
    with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as response:
        models = json.load(response).get("models", [])
    model = next((item for item in models if item.get("name") == "qwen3:1.7b"), None)
    if not model:
        raise SystemExit("Cached qwen3:1.7b is unavailable; refusing to freeze another model.")
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}
    bundle = hashlib.sha256("\0".join(f"{name}\0{hashes[name]}" for name in sorted(hashes)).encode()).hexdigest()
    manifest = json.loads((ROOT / "experiments/datasets/hybrid_controller_v4/manifest.json").read_text(encoding="utf-8"))
    freeze = {"freeze_version": "p2-hybrid-controller-v4-freeze-1", "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "dataset_version": "v4", "dataset_sha256": manifest["sha256"], "dev_scenarios": 60, "test_scenarios": 150, "model_id": "qwen3:1.7b", "model_digest": model.get("digest"), "model_quantization": model.get("details", {}).get("quantization_level"), "backend": "ollama", "prompt_version": "ollama-native-v1", "schema_version": "1.0.0", "controller_version": "hybrid-controller-v2", "temperature": 0, "think": False, "max_new_tokens": 256, "request_timeout_seconds": 90, "source_files": hashes, "source_bundle_sha256": bundle, "old_results_mutated": False, "test_use_policy": "run once after freeze; later changes require V5 or a new exploratory report"}
    target = ROOT / "experiments/results/hybrid_controller_v4_frozen_config.json"
    target.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(freeze, indent=2))

if __name__ == "__main__":
    main()
