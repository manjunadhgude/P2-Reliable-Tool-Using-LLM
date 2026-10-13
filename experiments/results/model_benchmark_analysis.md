# Qwen3-1.7B tool-action benchmark

Each configuration was evaluated on the same family-separated synthetic validation and locked test splits. Validation was used to assess configurations; the configuration and 20-step LoRA adapter were frozen before test evaluation. Results measure normalized action selection only; no tools were executed. Exact match requires action type, tool name and the complete argument object to match.

## Results

| Split | Configuration | Inference | Valid actions | Exact actions | p50 latency | p95 latency |
|---|---|---|---:|---:|---:|---:|
| validation | baseline_a | none | 48/48 | 0/48 | 24.77s | 27.01s |
| validation | baseline_b | none | 29/48 | 0/48 | 33.97s | 44.39s |
| validation | lora_c | nf4_4bit | 46/48 | 0/48 | 17.62s | 18.86s |
| test | baseline_a | none | 38/60 | 23/60 | 26.69s | 43.68s |
| test | baseline_b | none | 27/60 | 24/60 | 44.10s | 49.15s |
| test | lora_c | nf4_4bit | 55/60 | 24/60 | 13.62s | 21.61s |

## Scenario-family exact matches

| Split | Family | Baseline A | Baseline B | LoRA C |
|---|---|---:|---:|---:|
| validation | eligibility_check | 0/12 | 0/12 | 0/12 |
| validation | missing_order_id | 0/12 | 0/12 | 0/12 |
| validation | no_tool_explanation | 0/12 | 0/12 | 0/12 |
| validation | prompt_injection | 0/12 | 0/12 | 0/12 |
| test | cross_tenant_order | 12/12 | 12/12 | 12/12 |
| test | missing_ticket_order | 0/12 | 0/12 | 0/12 |
| test | nonexistent_order | 11/12 | 12/12 | 12/12 |
| test | refund_estimate | 0/12 | 0/12 | 0/12 |
| test | unsafe_policy_bypass | 0/12 | 0/12 | 0/12 |

## Interpretation and limits

All variants scored 0 exact matches on validation, while test exact matches were similar (A 23/60, B 24/60, C 24/60). C substantially increased schema-valid outputs on test (55/60 versus A 38/60 and B 27/60), but did not improve exact action accuracy over B. C was trained with NF4 QLoRA and also loaded in 4-bit NF4 for inference; A/B used unquantized FP16 with CPU offload. Therefore latency differences combine adapter and inference-quantization effects and cannot be attributed to LoRA alone. The family-separated validation/test distribution differs by scenario family; interpret the test as an out-of-family synthetic benchmark, not an IID generalization guarantee. C is a 20-step feasibility-scale LoRA run, not a production fine-tune. No end-to-end tool execution, task success, throughput or peak-memory measurements are represented.

The base model is pinned at `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`. Dataset checksum is `a4c83c7dc28ffba20a4c08c6bd318a6dcf7ece14688806340fea531897ff42a2`. C adapter SHA-256 is `fcb3ee6c6208e0b35ac489035c90af4ecda3f5bd6545555cdb5025d8460f541b`.

Latency p95 uses the nearest-rank method; p50 is the median.

## Source artifacts

- `baseline_a_validation_model_run.json`
- `baseline_b_validation_model_run.json`
- `lora_c_validation_model_run.json`
- `baseline_a_test_model_run.json`
- `baseline_b_test_model_run.json`
- `lora_c_test_model_run.json`
- `lora_smoke_report.json` and `p2-lora-20step/training_run.json`
