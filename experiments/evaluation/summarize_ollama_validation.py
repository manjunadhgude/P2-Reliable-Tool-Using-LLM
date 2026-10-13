import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
source = ROOT / "experiments/results/ollama_qwen3_1.7b_validation_v2_full.json"
data = json.loads(source.read_text(encoding="utf-8"))
families = defaultdict(lambda: Counter())
confusion = Counter()
errors = Counter()
for row in data["outcomes"]:
    family = families[row["scenario_family"]]
    family["n"] += 1
    family["valid"] += int(row["valid_action"])
    family["exact"] += int(row["valid_action"] and row["action_type_match"] and row["tool_match"] and row["arguments_exact_match"])
    predicted = (row.get("prediction") or {}).get("action_type", "error")
    confusion[(row["scenario_family"], predicted)] += 1
    if row.get("error"):
        errors[row["error"].split(":", 1)[0]] += 1
lines = ["# Ollama Qwen3-1.7B Validation Diagnostics", "", f"Source: `{source.name}`", "", "## Family results", "", "| Family | N | Valid | Exact |", "|---|---:|---:|---:|"]
for family, counts in sorted(families.items()):
    lines.append(f"| {family} | {counts['n']} | {counts['valid']} | {counts['exact']} |")
lines += ["", "## Predicted action by family", "", "| Family | Predicted action | Count |", "|---|---|---:|"]
for (family, action), count in sorted(confusion.items()):
    lines.append(f"| {family} | {action} | {count} |")
lines += ["", "## Errors", ""]
for error, count in sorted(errors.items()):
    lines.append(f"- `{error}`: {count}")
(ROOT / "experiments/results/ollama_qwen3_1.7b_validation_diagnostics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
