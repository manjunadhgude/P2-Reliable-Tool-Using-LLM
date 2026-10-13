"""Run a model-only Ollama action benchmark. Business tools are never executed."""

import argparse
import hashlib
import json
import math
import platform
import statistics
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def percentile(values, p):
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, math.ceil(len(ordered) * p) - 1))] if ordered else None


def ollama_model_metadata(base_url, model_id):
    request = urllib.request.Request(base_url.rstrip("/") + "/api/tags")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.load(response)
        for item in payload.get("models", []):
            if model_id in {item.get("name"), item.get("model")}:
                return {key: item.get(key) for key in ("name", "model", "digest", "details", "modified_at")}
        return {"lookup_status": "model_not_listed", "requested_model_id": model_id}
    except Exception as exc:
        return {"lookup_status": "metadata_unavailable", "error_type": type(exc).__name__}


def expected_metrics(action, case):
    expected_tool = case.get("expected_tool_name")
    expected_args = case.get("expected_arguments")
    type_match = action is not None and action.get("action_type") == case["expected_action_type"]
    tool_match = None
    args_match = None
    if expected_tool:
        tool_match = action is not None and action.get("tool_name") == expected_tool
    else:
        tool_match = action is not None and action.get("tool_name") is None
    if isinstance(expected_args, dict):
        args_match = action is not None and action.get("arguments", {}) == expected_args
    expected_missing_fields = case.get("expected_missing_fields")
    if isinstance(expected_missing_fields, list):
        args_match = action is not None and action.get("missing_fields") == expected_missing_fields
    exact = bool(type_match and tool_match and (args_match is not False))
    return type_match, tool_match, args_match, exact


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=("validation", "test", "dev"), required=True)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--dataset", type=Path, help="Optional versioned JSONL suite; defaults to historical v1 scenarios.")
    args = ap.parse_args()
    dataset = args.dataset.resolve() if args.dataset else ROOT / "experiments/datasets/scenarios.jsonl"
    cases = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines()
             if line.strip() and json.loads(line)["split"] == args.split]
    if args.limit:
        cases = cases[:args.limit]

    from app.core.config import settings
    from app.llm.backends import OllamaModelBackend
    from app.main import validate_action

    if settings.model_backend != "ollama":
        raise SystemExit("Set MODEL_BACKEND=ollama explicitly before running this real-model evaluator.")
    model = OllamaModelBackend(settings.model_id, settings.ollama_url, settings.request_timeout_seconds,
                               settings.model_max_new_tokens)
    outcomes = []
    latencies = []
    for case in cases:
        started = time.perf_counter()
        try:
            action = validate_action(model.act(case["user_message"]))
            valid = True
            type_match, tool_match, args_match, exact = expected_metrics(action, case)
            error = None
            prediction = {key: action[key] for key in ("action_type", "tool_name", "arguments", "missing_fields") if key in action}
        except Exception as exc:
            valid = type_match = exact = False
            tool_match = False if case.get("expected_tool_name") else None
            args_match = False if isinstance(case.get("expected_arguments"), dict) else None
            error = type(exc).__name__ + ": " + str(exc)[:240]
            prediction = None
        elapsed = (time.perf_counter() - started) * 1000
        latencies.append(elapsed)
        outcomes.append({
            "example_id": case["example_id"],
            "scenario_family": case["scenario_family"],
            "expected_action_type": case["expected_action_type"],
            "expected_tool_name": case.get("expected_tool_name"),
            "expected_arguments": case.get("expected_arguments"),
            "expected_missing_fields": case.get("expected_missing_fields"),
            "valid_action": valid,
            "action_type_match": type_match,
            "tool_match": tool_match,
            "arguments_exact_match": args_match,
            "exact_action_match": exact,
            "error": error,
            "prediction": prediction,
            "latency_ms": round(elapsed, 2),
        })
        print(json.dumps(outcomes[-1]), flush=True)

    denominator = len(outcomes)
    valid = sum(row["valid_action"] for row in outcomes)
    exact = sum(row["exact_action_match"] for row in outcomes)
    tool_rows = [row for row in outcomes if row["expected_tool_name"] is not None]
    argument_rows = [row for row in outcomes if isinstance(row["expected_arguments"], dict)]
    non_tool_rows = [row for row in outcomes if row["expected_tool_name"] is None]
    family_stats = defaultdict(lambda: {"denominator": 0, "valid": 0, "exact_action_matches": 0,
                                        "tool_selection_matches": 0, "tool_selection_denominator": 0,
                                        "argument_exact_matches": 0, "argument_exact_denominator": 0})
    for row in outcomes:
        stats = family_stats[row["scenario_family"]]
        stats["denominator"] += 1
        stats["valid"] += int(row["valid_action"])
        stats["exact_action_matches"] += int(row["exact_action_match"])
        if row["expected_tool_name"] is not None:
            stats["tool_selection_denominator"] += 1
            stats["tool_selection_matches"] += int(row["tool_match"] is True)
        if isinstance(row["expected_arguments"], dict):
            stats["argument_exact_denominator"] += 1
            stats["argument_exact_matches"] += int(row["arguments_exact_match"] is True)

    tool_matches = sum(row["tool_match"] is True for row in tool_rows)
    argument_matches = sum(row["arguments_exact_match"] is True for row in argument_rows)
    non_tool_matches = sum(row["action_type_match"] and row["tool_match"] is True for row in non_tool_rows)
    result = {
        "run_id": "ollama-modelonly-corrected-v1-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "evaluator_version": "ollama-modelonly-corrected-v2" if args.dataset else "ollama-modelonly-corrected-v1",
        "backend": "ollama",
        "model_id": settings.model_id,
        "model_metadata": ollama_model_metadata(settings.ollama_url, settings.model_id),
        "prompt_version": "ollama-native-v1",
        "action_schema_version": "1.0.0",
        "generation": {"think": False, "temperature": 0, "stream": False,
                       "timeout_seconds": settings.request_timeout_seconds,
                       "max_new_tokens": settings.model_max_new_tokens,
                       "max_model_steps": settings.max_model_steps},
        "dataset_version": cases[0].get("dataset_version", "p2-synthetic-v1") if cases else "empty",
        "dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
        "split": args.split,
        "denominator": denominator,
        "metrics": {
            "valid_actions": valid,
            "valid_action_rate": valid / denominator if denominator else None,
            "exact_action_matches": exact,
            "exact_action_denominator": denominator,
            "exact_action_rate": exact / denominator if denominator else None,
            "tool_selection_matches": tool_matches,
            "tool_selection_denominator": len(tool_rows),
            "tool_selection_rate": tool_matches / len(tool_rows) if tool_rows else None,
            "argument_exact_matches": argument_matches,
            "argument_exact_denominator": len(argument_rows),
            "argument_exact_rate": argument_matches / len(argument_rows) if argument_rows else None,
            "non_tool_action_matches": non_tool_matches,
            "non_tool_action_denominator": len(non_tool_rows),
            "non_tool_action_rate": non_tool_matches / len(non_tool_rows) if non_tool_rows else None,
            "latency_ms_p50": statistics.median(latencies) if latencies else None,
            "latency_ms_p95": percentile(latencies, 0.95),
            "timeouts_or_errors": sum(not row["valid_action"] for row in outcomes),
            "per_scenario_family": dict(family_stats),
        },
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "runtime": "Ollama local HTTP API", "ollama_url": settings.ollama_url},
        "outcomes": outcomes,
        "metric_definitions": {
            "exact_action_match": "Action type and expected tool must match; full arguments must also match for examples with expected arguments. Non-tool actions have no argument comparison.",
            "tool_selection_rate": "Correct tool among examples with an expected tool; non-tool examples excluded.",
            "argument_exact_rate": "Exact argument dictionary among examples with expected arguments; non-tool examples excluded.",
            "latency": "Wall-clock time around one model-only action call, including local Ollama HTTP and parsing; no business tool execution.",
        },
        "provenance": "Measured normalized Ollama proposal. This evaluator does not invoke the hybrid controller or execute business tools. Existing historical benchmark artifacts were not modified.",
    }
    default_tag = "v2" if args.dataset else "v1"
    output = args.output or ROOT / f"experiments/results/ollama_{settings.model_id.replace(':', '_')}_{args.split}_modelonly_corrected_{default_tag}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["metrics"], indent=2))


if __name__ == "__main__":
    main()
