# Dataset card — P2 synthetic scenarios

- **Version:** `p2-synthetic-v1`; generator: `experiments/data_generation/generate_dataset.py`.
- **Format:** JSONL; manifest includes SHA-256 and split counts.
- **Content:** synthetic prompts and expected action/tool labels across 17 scenario families; no real people, orders, or payment data.
- **Splits:** scenario families are wholly assigned to train, validation, or locked test to prevent template leakage. Use validation for development; reserve test for final reporting.
- **Limits:** generated variations are repeated prompt forms, not human preference annotations. They measure action selection shape only; they do not establish business-task or model quality.
- **Validation:** `python experiments/evaluation/validate_dataset.py` checks duplicate IDs, labels, splits, leakage and checksum.
- **Benchmark:** current runner reads validation only. Fixture results are not LLM performance.
