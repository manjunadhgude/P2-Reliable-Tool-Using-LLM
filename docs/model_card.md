# Model card — Qwen3-1.7B integration target

- **Repository:** `Qwen/Qwen3-1.7B`.
- **Pinned revision:** `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`, resolved from Hugging Face `refs/heads/main` on 2026-10-10 using `git ls-remote`.
- **License:** Apache-2.0 according to the official model repository.
- **Architecture/size:** 1.7B parameter causal language model; the model card lists 32,768 context tokens.
- **Template:** Qwen's guide documents Hermes-style `<tool_call>` formatting. This application requests a JSON action envelope and independently validates it.
- **Runtime:** Optional Transformers backend uses `apply_chat_template(..., enable_thinking=False)`. No hidden reasoning is persisted. The model card says Transformers 4.51.0 or newer is required.
- **Use constraints:** output is untrusted and not authority for access, eligibility, amounts, or approval.
- **Local runtime check (2026-10-10):** PyTorch 2.7.0+cu128, CUDA 12.8 and Transformers 4.51.3 installed; `torch.cuda.is_available()` is true on an NVIDIA GTX 1650 with 4 GiB VRAM. Qwen loaded with CPU offload. A schema-valid `lookup_order` action was generated at the pinned revision with a 256-token cap. GPU memory required CPU offload and resulted in tens-of-seconds-per-action latency on the validation run.
- **Evaluation:** A/B/C action-selection results are in `experiments/results/model_benchmark_analysis.md`. On validation (48 cases), all variants scored 0 exact; valid counts were A 48, B 29, C 46. On the locked test split (60 cases), exact matches were A 23, B 24, C 24; valid counts were A 38, B 27, C 55. C had lower measured latency on this device but no exact-match gain over B. The split discrepancy and synthetic dataset size limit generalization claims. Metrics exclude tool execution and task success.
- **Adapter:** 20-step NF4 QLoRA feasibility run on the 96-example training split; mean training loss 3.4263; adapter SHA-256 `fcb3ee6c6208e0b35ac489035c90af4ecda3f5bd6545555cdb5025d8460f541b`. Saved, reloaded in a fresh process and benchmarked. C also used NF4 for inference, while A/B used unquantized FP16; latency comparisons therefore combine adapter and quantization effects. This is not a production fine-tune or proven improvement.

Sources checked 2026-10-10: [official Qwen3-1.7B model card](https://huggingface.co/Qwen/Qwen3-1.7B), [Qwen3 function calling guide](https://github.com/QwenLM/Qwen3/blob/main/docs/source/framework/function_call.md), [Qwen3 Transformers guide](https://github.com/QwenLM/Qwen3/blob/main/docs/source/inference/transformers.md).
