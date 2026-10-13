"""Rebuild the A/B/C validation and locked-test report from saved run artifacts."""
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments" / "results"
VARIANTS = ("baseline_a", "baseline_b", "lora_c")
SPLITS = ("validation", "test")


def main():
    summaries = {}
    artifacts = {}
    for split in SPLITS:
        dataset_path = ROOT / "experiments" / "datasets" / "scenarios.jsonl"
        cases = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines()
                 if line.strip() and json.loads(line).get("split") == split]
        by_id = {case["example_id"]: case for case in cases}
        summaries[split] = {}
        for variant in VARIANTS:
            path = RESULTS / f"{variant}_{split}_model_run.json"
            run = json.loads(path.read_text(encoding="utf-8"))
            latencies = sorted(outcome["latency_ms"] for outcome in run["outcomes"])
            run["metrics"]["latency_ms_p50"] = statistics.median(latencies)
            run["metrics"]["latency_ms_p95"] = latencies[max(0, math.ceil(len(latencies) * .95) - 1)]
            run["metrics"]["latency_percentile_method"] = "nearest_rank"
            family_metrics = {}
            for outcome in run["outcomes"]:
                case = by_id[outcome["example_id"]]
                metrics = family_metrics.setdefault(case["scenario_family"], {
                    "denominator": 0, "valid_actions": 0, "exact_action_matches": 0})
                metrics["denominator"] += 1
                metrics["valid_actions"] += int(outcome["valid_action"])
                metrics["exact_action_matches"] += int(outcome["valid_action"] and outcome["action_type_match"]
                                                         and outcome["tool_match"] and outcome["arguments_exact_match"])
            run["metrics"]["per_scenario_family"] = family_metrics
            path.write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
            metrics = run["metrics"]
            summaries[split][variant] = {
                "denominator": metrics["denominator"], "valid": metrics["valid_actions"],
                "exact": metrics["exact_action_match_count"],
                "p50": metrics["latency_ms_p50"], "p95": metrics["latency_ms_p95"],
                "families": family_metrics,
                "adapter_sha256": run.get("adapter_sha256"),
                "inference_quantization": run.get("inference_quantization", "none"),
            }
            artifacts[f"{variant}_{split}"] = path.name

    lines = ["# Qwen3-1.7B tool-action benchmark", "",
             "Each configuration was evaluated on the same family-separated synthetic validation and locked test splits. Validation was used to assess configurations; the configuration and 20-step LoRA adapter were frozen before test evaluation. Results measure normalized action selection only; no tools were executed. Exact match requires action type, tool name and the complete argument object to match.", "",
             "## Results", "",
             "| Split | Configuration | Inference | Valid actions | Exact actions | p50 latency | p95 latency |",
             "|---|---|---|---:|---:|---:|---:|"]
    for split in SPLITS:
        for variant in VARIANTS:
            m = summaries[split][variant]
            lines.append(f"| {split} | {variant} | {m['inference_quantization']} | {m['valid']}/{m['denominator']} | {m['exact']}/{m['denominator']} | {m['p50']/1000:.2f}s | {m['p95']/1000:.2f}s |")
    lines += ["", "## Scenario-family exact matches", "",
              "| Split | Family | Baseline A | Baseline B | LoRA C |", "|---|---|---:|---:|---:|"]
    for split in SPLITS:
        families = sorted(set().union(*(summaries[split][v]["families"] for v in VARIANTS)))
        for family in families:
            vals = []
            for variant in VARIANTS:
                data = summaries[split][variant]["families"].get(family, {})
                vals.append(f"{data.get('exact_action_matches', 0)}/{data.get('denominator', 0)}")
            lines.append(f"| {split} | {family} | {vals[0]} | {vals[1]} | {vals[2]} |")
    lines += ["", "## Interpretation and limits", "",
              "All variants scored 0 exact matches on validation, while test exact matches were similar (A 23/60, B 24/60, C 24/60). C substantially increased schema-valid outputs on test (55/60 versus A 38/60 and B 27/60), but did not improve exact action accuracy over B. C was trained with NF4 QLoRA and also loaded in 4-bit NF4 for inference; A/B used unquantized FP16 with CPU offload. Therefore latency differences combine adapter and inference-quantization effects and cannot be attributed to LoRA alone. The family-separated validation/test distribution differs by scenario family; interpret the test as an out-of-family synthetic benchmark, not an IID generalization guarantee. C is a 20-step feasibility-scale LoRA run, not a production fine-tune. No end-to-end tool execution, task success, throughput or peak-memory measurements are represented.", "",
              "The base model is pinned at `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`. Dataset checksum is `a4c83c7dc28ffba20a4c08c6bd318a6dcf7ece14688806340fea531897ff42a2`. C adapter SHA-256 is `" + summaries['test']['lora_c']['adapter_sha256'] + "`.", "",
              "Latency p95 uses the nearest-rank method; p50 is the median.", "",
              "## Source artifacts", ""]
    lines += [f"- `{name}`" for name in artifacts.values()]
    lines.append("- `lora_smoke_report.json` and `p2-lora-20step/training_run.json`")
    (RESULTS / "model_benchmark_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:18]))


if __name__ == "__main__":
    main()
