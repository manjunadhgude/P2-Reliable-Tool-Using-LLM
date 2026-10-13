"""Audit new prompt cores against saved P2 corpora and artifacts."""

import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiments/datasets/p2_fresh_v7_v8_v1/scenarios.jsonl"
OUT = ROOT / "experiments/results/p2_fresh_v7_v8_overlap_audit.json"
THRESHOLD = 0.78


def normalize(text):
    text = re.sub(r"(?i)\s*\breference\s+\d+\.?\s*$", "", str(text or ""))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.casefold()).split())


def grams(text):
    padded = f"  {normalize(text)}  "
    return {padded[i:i + 3] for i in range(max(0, len(padded) - 2))}


def strings(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"user_message", "prompt", "input_text", "prompt_text"} and isinstance(item, str):
                yield item
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def corpus_files():
    for path in (ROOT / "experiments").rglob("*"):
        if not path.is_file() or path == DATA or path == OUT:
            continue
        if path.suffix.casefold() in {".jsonl", ".json", ".csv"}:
            yield path


def read_texts(path):
    try:
        if path.suffix.casefold() == ".jsonl":
            for line in path.read_text(encoding="utf-8-sig").splitlines():
                if line.strip():
                    yield from strings(json.loads(line))
        elif path.suffix.casefold() == ".json":
            yield from strings(json.loads(path.read_text(encoding="utf-8-sig")))
        else:
            with path.open(encoding="utf-8-sig", newline="") as stream:
                for row in csv.DictReader(stream):
                    for key in ("user_message", "prompt", "input_text", "prompt_text"):
                        if row.get(key):
                            yield row[key]
    except (OSError, UnicodeError, json.JSONDecodeError, csv.Error):
        return


def main():
    if OUT.exists():
        raise SystemExit(f"Refusing to overwrite {OUT}")
    cases = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    new = [(case["example_id"], case["user_message"], normalize(case["user_message"]), grams(case["user_message"])) for case in cases]
    old = []
    sources = []
    for path in corpus_files():
        found = list(read_texts(path))
        if found:
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            sources.append({"path": rel, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "prompt_count": len(found)})
            old.extend((rel, text, normalize(text), grams(text)) for text in found)
    matches = []
    for case_id, prompt, core, new_grams in new:
        best = (0.0, None, None)
        for path, old_prompt, old_core, old_grams in old:
            if core == old_core:
                score = 1.0
            else:
                union = len(new_grams | old_grams)
                score = len(new_grams & old_grams) / union if union else 0.0
            if score > best[0]:
                best = (score, path, old_prompt)
        if best[0] >= THRESHOLD:
            matches.append({"example_id": case_id, "similarity": round(best[0], 4), "source": best[1],
                            "new_prompt": prompt, "prior_prompt": best[2]})
    artifact = {
        "audit_version": "p2-prompt-overlap-3gram-v1", "dataset_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
        "dataset_rows": len(new), "prior_prompt_count": len(old), "source_artifact_count": len(sources),
        "normalization": "remove terminal synthetic Reference N. suffix; case-fold; non-alphanumeric to spaces; collapse whitespace",
        "similarity": "character 3-gram Jaccard", "near_duplicate_threshold": THRESHOLD,
        "exact_core_overlaps": sum(item["similarity"] == 1.0 for item in matches),
        "near_duplicate_matches": matches, "source_artifacts": sources,
        "limitations": "Lexical overlap screening cannot prove semantic novelty or independently validate labels.",
    }
    OUT.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUT), "dataset_rows": len(new), "prior_prompt_count": len(old),
                      "source_artifact_count": len(sources), "matches": len(matches),
                      "exact_overlaps": artifact["exact_core_overlaps"]}, indent=2))


if __name__ == "__main__":
    main()
