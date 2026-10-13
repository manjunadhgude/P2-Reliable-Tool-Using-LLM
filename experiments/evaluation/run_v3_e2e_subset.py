"""Run the predeclared representative V3 application subset.

This is intentionally bounded for the local Qwen runtime. It delegates to the
existing application integration runner and records that the subset is an
executed task track, separate from raw/offline action metrics.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--timeout-seconds", type=int, default=90)
    a = p.parse_args()
    raw = a.output.with_suffix(".integration.json")
    cmd = [sys.executable, str(ROOT / "experiments/evaluation/run_hybrid_real_integration.py"), "--timeout-seconds", str(a.timeout_seconds), "--output", str(raw)]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    record = {"suite_version":"v3", "track":"actual_end_to_end_application", "subset_declared_size":8,
              "subset_selection":"representative existing application workflows; one fresh DB per run",
              "started_at":datetime.now(timezone.utc).isoformat(), "runner_returncode":completed.returncode,
              "runner_artifact":str(raw), "stdout":completed.stdout[-4000:], "stderr":completed.stderr[-4000:]}
    if raw.exists():
        payload = json.loads(raw.read_text(encoding="utf-8"))
        record.update({"model": payload.get("model"), "outcomes": payload.get("outcomes"), "summary": payload.get("summary"), "status": payload.get("status")})
    a.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))
    raise SystemExit(completed.returncode)

if __name__ == "__main__":
    main()
