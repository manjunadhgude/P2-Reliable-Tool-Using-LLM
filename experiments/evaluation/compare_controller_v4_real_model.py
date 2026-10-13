"""Paired raw Qwen, v2 baseline and opt-in V4 controller evaluation."""

import argparse
import hashlib
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def exact(action, case):
    if (
        not isinstance(action, dict)
        or action.get("action_type") != case["expected_action_type"]
        or action.get("tool_name") != case.get("expected_tool_name")
    ):
        return False
    if case.get("expected_missing_fields") is not None:
        return action.get("missing_fields") == case["expected_missing_fields"]
    expected = case.get("expected_arguments")
    return not isinstance(expected, dict) or action.get("arguments", {}) == expected


def metrics(rows, key):
    from app.hybrid_controller import ORDER_ID_RE, ITEM_ID_RE
    from app.tools.domain import ARGUMENT_SCHEMAS

    def schema_ok(r):
        a = r[key]
        if a.get("action_type") not in {"tool_call", "propose_state_change"}:
            return True
        name = a.get("tool_name")
        if name not in ARGUMENT_SCHEMAS:
            return False
        try:
            ARGUMENT_SCHEMAS[name].model_validate(a.get("arguments") or {})
        except Exception:
            return False
        return True

    def ids_grounded(r):
        a = r[key]
        args = a.get("arguments") or {}
        prompt = r.get("user_message", "")
        order_ids = {x.upper() for x in ORDER_ID_RE.findall(prompt)}
        item_ids = {x.upper() for x in ITEM_ID_RE.findall(prompt)}
        if (
            "order_id" in args
            and args["order_id"] is not None
            and order_ids
            and args["order_id"] not in order_ids
        ):
            return False
        if "order_id" in args and args["order_id"] is not None and not order_ids:
            return False
        if "item_ids" in args and not set(args["item_ids"]).issubset(item_ids):
            return False
        return True

    ticket_rows = [
        r for r in rows if r[key].get("action_type") == "propose_state_change"
    ]
    exact = sum(r[key + "_exact"] for r in rows)
    action_only = [
        r
        for r in rows
        if r.get("expected_arguments") is None
        and r.get("expected_missing_fields") is None
    ]
    schema_valid = sum(schema_ok(r) for r in rows)
    grounded = sum(ids_grounded(r) for r in rows)
    return {
        "rows": len(rows),
        "exact_action": exact,
        "exact_action_rate": exact / len(rows) if rows else None,
        "action_only_correct": sum(r[key + "_exact"] for r in action_only),
        "action_only_denominator": len(action_only),
        "tool_selection_denominator": sum(
            r["expected_tool_name"] is not None for r in rows
        ),
        "tool_selection_correct": sum(
            r[key].get("tool_name") == r["expected_tool_name"]
            for r in rows
            if r["expected_tool_name"] is not None
        ),
        "argument_denominator": sum(
            isinstance(r["expected_arguments"], dict) for r in rows
        ),
        "arguments_exact": sum(
            r[key].get("arguments", {}) == r["expected_arguments"]
            for r in rows
            if isinstance(r["expected_arguments"], dict)
        ),
        "registered_schema_valid_actions": schema_valid,
        "registered_schema_denominator": len(rows),
        "entity_id_grounded_actions": grounded,
        "entity_id_grounding_denominator": len(rows),
        "unexpected_write_proposals": sum(
            r[key].get("action_type") == "propose_state_change"
            and r["expected_action_type"] != "propose_state_change"
            for r in rows
        ),
        "handoff_correct": sum(
            r[key].get("action_type") == "handoff"
            and r["expected_action_type"] == "handoff"
            for r in rows
        ),
        "clarification_correct": sum(
            r[key].get("action_type") == "clarification"
            and r["expected_action_type"] == "clarification"
            and r[key].get("missing_fields") == r["expected_missing_fields"]
            for r in rows
            if r["expected_action_type"] == "clarification"
        ),
        "ticket_grounded_proposals": sum(
            r["ticket_grounded_" + key] for r in ticket_rows
        ),
        "ticket_proposal_denominator": len(ticket_rows),
        "ticket_grounding_failures": sum(
            not r["ticket_grounded_" + key] for r in ticket_rows
        ),
        "unauthorized_execution_count": "not measured by offline action replay",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dataset",
        type=Path,
        default=ROOT / "experiments/datasets/p2_controller_v4_eval/scenarios.jsonl",
    )
    ap.add_argument(
        "--raw",
        type=Path,
        default=ROOT
        / "experiments/results/ollama_qwen3_1.7b_p2_v4_eval_modelonly.json",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=ROOT / "experiments/results/p2_v4_real_model_eval_v1.json",
    )
    args = ap.parse_args()
    ds = args.dataset.resolve()
    rawp = args.raw.resolve()
    cases = [
        json.loads(x)
        for x in ds.read_text(encoding="utf-8-sig").splitlines()
        if x.strip()
    ]
    raw = json.loads(rawp.read_text(encoding="utf-8"))
    if raw["dataset_sha256"] != hashlib.sha256(ds.read_bytes()).hexdigest() or len(
        cases
    ) != len(raw["outcomes"]):
        raise SystemExit("Dataset/hash/denominator mismatch")
    from app.hybrid_controller import HybridController
    from app.hybrid_controller_v4_candidate import HybridControllerV4Candidate
    from app.tools.domain import ARGUMENT_SCHEMAS

    ctl = HybridControllerV4Candidate()
    baseline_ctl = HybridController()
    outs = []
    for c, p in zip(cases, raw["outcomes"]):
        pred = p.get("prediction")
        d = ctl.preflight(c["user_message"], [])
        if d is None and p.get("valid_action") and pred is not None:
            d = ctl.apply(c["user_message"], pred, [])
        cand = d.action if d else (pred or {})
        old = baseline_ctl.preflight(c["user_message"], [])
        if old is None and p.get("valid_action") and pred is not None:
            old = baseline_ctl.apply(c["user_message"], pred, [])
        baseline = old.action if old else (pred or {})
        row = {
            "example_id": c["example_id"],
            "scenario_family": c["scenario_family"],
            "user_message": c["user_message"],
            "normalized_core": " ".join(c["user_message"].casefold().split()),
            "expected_action_type": c["expected_action_type"],
            "expected_tool_name": c.get("expected_tool_name"),
            "expected_arguments": c.get("expected_arguments"),
            "expected_missing_fields": c.get("expected_missing_fields"),
            "raw": pred or {},
            "baseline": baseline,
            "candidate": cand,
            "raw_exact": exact(pred, c),
            "baseline_exact": exact(baseline, c),
            "candidate_exact": exact(cand, c),
            "candidate_decision": d.decision if d else "no_action",
            "candidate_reason": d.reason if d else "invalid_or_missing_model_output",
        }
        for key, action in [
            ("raw", pred or {}),
            ("baseline", baseline),
            ("candidate", cand),
        ]:
            grounded = True
            if action.get("action_type") == "propose_state_change":
                a = action.get("arguments") or {}
                try:
                    ARGUMENT_SCHEMAS["create_support_ticket"].model_validate(a)
                except Exception:
                    grounded = False
                issue = ctl._grounded_issue(c["user_message"])
                grounded = (
                    grounded
                    and bool(issue)
                    and issue.casefold() in str(a.get("description", "")).casefold()
                    and "reference" not in str(a.get("description", "")).casefold()
                )
            row["ticket_grounded_" + key] = grounded
        outs.append(row)
    groups = defaultdict(list)
    fam = defaultdict(list)
    for r in outs:
        groups[r["normalized_core"]].append(r)
        fam[r["scenario_family"]].append(r)
    core = {
        k: {
            "raw": statistics.mean(x["raw_exact"] for x in v),
            "candidate": statistics.mean(x["candidate_exact"] for x in v),
        }
        for k, v in groups.items()
    }
    rawm = metrics(outs, "raw")
    basem = metrics(outs, "baseline")
    candm = metrics(outs, "candidate")
    latencies = sorted(x["latency_ms"] for x in raw["outcomes"])
    result = {
        "comparison_version": "p2-v4-real-model-eval-v3",
        "scope": f"One frozen local Ollama model-only pass ({len(outs)} cases), followed by offline controller replay; controller replay executes no tools or database writes.",
        "model": raw.get("model_id"),
        "model_metadata": raw.get("model_metadata"),
        "dataset_sha256": hashlib.sha256(ds.read_bytes()).hexdigest(),
        "rows": len(outs),
        "unique_cores": len(groups),
        "scenario_families": len(fam),
        "raw": rawm,
        "v2_baseline": basem,
        "candidate": candm,
        "core_weighted_raw_exact": statistics.mean(v["raw"] for v in core.values()),
        "core_weighted_baseline_exact": statistics.mean(
            statistics.mean(x["baseline_exact"] for x in group)
            for group in groups.values()
        ),
        "core_weighted_candidate_exact": statistics.mean(
            v["candidate"] for v in core.values()
        ),
        "per_family": {
            k: {
                "rows": len(v),
                "raw_exact": sum(x["raw_exact"] for x in v),
                "baseline_exact": sum(x["baseline_exact"] for x in v),
                "candidate_exact": sum(x["candidate_exact"] for x in v),
                "candidate_ticket_grounding_failures": sum(
                    x["candidate"].get("action_type") == "propose_state_change"
                    and not x["ticket_grounded_candidate"]
                    for x in v
                ),
            }
            for k, v in sorted(fam.items())
        },
        "latency_ms_p50_raw_model": statistics.median(latencies),
        "latency_ms_p95_raw_model": latencies[
            max(0, math.ceil(len(latencies) * 0.95) - 1)
        ],
        "outcomes": outs,
        "label_limit": "Internal AI-authored labels; not independent human adjudication. Action replay is not end-to-end task completion; authorization/tool execution not exercised here.",
    }
    dest = args.output.resolve()
    if dest.exists():
        raise SystemExit(f"refusing overwrite {dest}")
    dest.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ("outcomes", "per_family")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
