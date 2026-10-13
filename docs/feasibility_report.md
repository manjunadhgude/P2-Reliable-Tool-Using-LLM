# Environment and model feasibility report

**Date:** 2026-10-10 (Asia/Kolkata). **Workspace:** Windows 11 Home Single Language.

## Environment discovery

- CPU: 12th Gen Intel Core i5-1240P; visible RAM 7.7 GiB.
- GPU: NVIDIA GeForce GTX 1650, 4 GiB VRAM (`nvidia-smi`). Free C: drive: approximately 237.4 GiB.
- Bundled Python 3.12.14; Node 24.19.0; npm 11.17.0. Docker CLI not found in PATH; Git available; workspace began as an empty repository.
- Initial Python modules lacked FastAPI, SQLAlchemy, Alembic, Uvicorn and pytest; app/development and optional model dependencies are now installed in ignored `.venv`.

## Model check

Candidate: `Qwen/Qwen3-1.7B`, revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`. The exact revision resolved from repository `refs/heads/main` with `git ls-remote` on 2026-10-10. The official model card lists Apache-2.0. Qwen documents Hermes-style tool-call formatting; the model card says Transformers 4.51.0 or newer is required. See [model card](model_card.md).

## Feasibility and limitations

The optional Transformers adapter and A/B/C benchmark runner are implemented. PyTorch 2.7.0+cu128 and Transformers 4.51.3 are installed, and CUDA is available on the GTX 1650. Qwen3-1.7B loaded with CPU offload. A 64-token smoke was rejected as truncated; at 256 tokens it produced a schema-valid `lookup_order` action for `ORD-10021`. A/B validation runs each scored 0/48 exact actions. A 20-step NF4 QLoRA feasibility-scale run trained on the 96-example train split, saved and reloaded; C scored 0/48 exact and 46/48 schema-valid on validation. Frozen test results are A 23/60 exact, B 24/60, C 24/60. C used NF4 for inference, while A/B used FP16, so latency comparisons combine quantization and adapter effects. C did not improve exact match over B. The family-separated split and small synthetic corpus limit generalization claims. Training initially hit a Windows Application Control block on PyArrow's native extension; the script now uses an in-memory PyTorch dataset and avoids that extension. No paid resources were used. The app still defaults to the explicitly labeled fixture backend.

## Commands and results

- Bundled `python.exe --version` → Python 3.12.14.
- `.venv` probe after installing the official CUDA wheel from its local download → PyTorch 2.7.0+cu128, CUDA 12.8, `torch.cuda.is_available() == True`, device GTX 1650; Transformers 4.51.3.
- Bundled Node/npm → v24.19.0 / 11.17.0.
- `Get-CimInstance Win32_OperatingSystem`, `Win32_Processor`, `Get-PSDrive C`, and `nvidia-smi --query-gpu=name,memory.total --format=csv,noheader` → findings above.
- `docker --version` → executable not found.
- `nvidia-smi` → GTX 1650, 4096 MiB total, 0 MiB in use; driver 616.56.
- Pinned model inference returned a valid lookup action with a 256-token cap. Full A/B/C validation and locked-test results, per-family metrics and raw predictions are saved under `experiments/results/`. The 20-step QLoRA adapter was saved/reloaded and hash recorded in `experiments/results/p2-lora-20step/training_run.json`; exact actions were 0/48 validation and 24/60 test.
- `git ls-remote https://huggingface.co/Qwen/Qwen3-1.7B refs/heads/main` → pinned revision above.

## Plan

Use Python 3.12 + FastAPI/Pydantic/SQLAlchemy, SQLite locally and PostgreSQL in Compose, React/TypeScript/Vite, and optional Transformers. Keep model/training claims limited to the actual saved model smoke and benchmark artifacts; the GPU memory cap and latency constrain further experiments.
