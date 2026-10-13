"""Run one frozen prompt configuration against a single synthetic split.

Invoke once per prompt variant so model memory is released between configurations.
No tools are executed and no prompts, references, or raw model outputs are saved.
"""
import argparse
import hashlib
import json
import math
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def percentile(values: list[float], p: float):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, math.ceil(len(ordered) * p) - 1))]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=("baseline_a", "baseline_b", "lora_c"), required=True)
    parser.add_argument("--adapter", type=Path, help="Saved PEFT adapter directory; required for lora_c.")
    parser.add_argument("--qlora", action="store_true", help="Load the adapter's base model in NF4 4-bit mode.")
    parser.add_argument("--split", choices=("validation", "test"), default="validation")
    parser.add_argument("--limit", type=int, help="Optional smoke limit; such results are not full benchmarks.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if (args.variant == "lora_c") != (args.adapter is not None):
        raise SystemExit("Pass --adapter for lora_c, and only for lora_c.")
    dataset = ROOT / "experiments" / "datasets" / "scenarios.jsonl"
    cases = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines()
             if line.strip() and json.loads(line).get("split") == args.split]
    if args.limit:
        cases = cases[:args.limit]
    if not cases:
        raise SystemExit("No examples found for the selected split.")

    from app.core.config import settings
    from app.llm.backends import TransformersModelBackend
    from app.main import validate_action

    model = TransformersModelBackend(settings.model_id, settings.model_revision,
                                     timeout_seconds=settings.request_timeout_seconds,
                                     max_new_tokens=settings.model_max_new_tokens,
                                     repair_retries=settings.max_output_repair_retries,
                                     prompt_version="baseline_b" if args.variant == "lora_c" else args.variant,
                                     adapter_path=str(args.adapter) if args.adapter else None,
                                     quantize_4bit=args.qlora)
    outcomes = []
    latencies = []
    for case in cases:
        start = time.perf_counter()
        try:
            action = validate_action(model.act(case["user_message"]))
            valid = True
            action_match = action["action_type"] == case["expected_action_type"]
            expected_tool = case.get("expected_tool_name")
            tool_match = action.get("tool_name") == expected_tool if expected_tool else action.get("tool_name") is None
            args_match = action.get("arguments", {}) == case.get("expected_arguments", {})
            category = None if action_match and tool_match and args_match else "action_mismatch"
            prediction = {key: action[key] for key in ("action_type", "tool_name", "arguments") if key in action}
        except Exception as exc:
            valid, action_match, tool_match, args_match = False, False, False, False
            category = type(exc).__name__
            prediction = None
        elapsed = (time.perf_counter() - start) * 1000
        latencies.append(elapsed)
        outcomes.append({"example_id": case["example_id"], "valid_action": valid,
                         "action_type_match": action_match, "tool_match": tool_match,
                         "arguments_exact_match": args_match, "error_category": category,
                         "prediction": prediction,
                         "latency_ms": round(elapsed, 2)})

    valid_count = sum(x["valid_action"] for x in outcomes)
    exact_count = sum(x["valid_action"] and x["action_type_match"] and x["tool_match"] and x["arguments_exact_match"] for x in outcomes)
    family_metrics = {}
    for case, outcome in zip(cases, outcomes):
        family = family_metrics.setdefault(case["scenario_family"], {"denominator": 0, "valid_actions": 0, "exact_action_matches": 0})
        family["denominator"] += 1
        family["valid_actions"] += int(outcome["valid_action"])
        family["exact_action_matches"] += int(outcome["valid_action"] and outcome["action_type_match"] and outcome["tool_match"] and outcome["arguments_exact_match"])
    import torch
    environment = {"python": platform.python_version(), "platform": platform.platform(), "torch": torch.__version__,
                   "cuda": torch.version.cuda, "cuda_available": torch.cuda.is_available(),
                   "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}
    result = {
        "run_id": f"{args.variant}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "name": args.variant, "backend": "transformers", "prompt_variant": "baseline_b" if args.variant == "lora_c" else args.variant,
        "adapter_path": str(args.adapter) if args.adapter else None,
        "adapter_sha256": hashlib.sha256((args.adapter / "adapter_model.safetensors").read_bytes()).hexdigest() if args.adapter else None,
        "inference_quantization": "nf4_4bit" if args.qlora else "none",
        "model_id": settings.model_id, "model_revision": settings.model_revision,
        "dataset_version": "p2-synthetic-v1", "dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
        "split": args.split, "status": "completed", "started_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {"denominator": len(outcomes), "valid_actions": valid_count,
                    "valid_action_rate": valid_count / len(outcomes), "exact_action_match_count": exact_count,
                    "exact_action_match_rate": exact_count / len(outcomes),
                    "action_type_match_count": sum(x["action_type_match"] for x in outcomes),
                    "tool_match_count": sum(x["tool_match"] for x in outcomes),
                    "arguments_exact_match_count": sum(x["arguments_exact_match"] for x in outcomes),
                    "latency_ms_p50": statistics.median(latencies), "latency_ms_p95": percentile(latencies, .95),
                    "latency_percentile_method": "nearest_rank",
                    "per_scenario_family": family_metrics, "environment": environment,
                    "provenance": "Measured open-weight model generation; no tool execution. Exact action match includes action type, tool and complete argument object."},
        "outcomes": outcomes,
    }
    output = args.output or ROOT / "experiments" / "results" / f"{args.variant}_{args.split}_model_run.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "split": args.split, "denominator": len(outcomes),
                      "valid_actions": valid_count, "exact_action_matches": exact_count,
                      "latency_ms_p50": result["metrics"]["latency_ms_p50"],
                      "latency_ms_p95": result["metrics"]["latency_ms_p95"]}, indent=2))


if __name__ == "__main__":
    main()
