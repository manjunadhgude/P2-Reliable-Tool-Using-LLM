"""Optional LoRA/QLoRA SFT using an in-memory torch dataset (no PyArrow required)."""
import argparse
import gc
import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.config import settings  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "experiments" / "results" / "p2-lora-adapter")
    parser.add_argument("--max-steps", type=int, default=20, help="Use a small smoke run before a full experiment.")
    parser.add_argument("--qlora", action="store_true", help="Request 4-bit NF4; requires compatible CUDA/bitsandbytes.")
    parser.add_argument("--reload-smoke", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        import torch
        from peft import AutoPeftModelForCausalLM, LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    except ImportError as exc:
        raise SystemExit(f"Optional training packages are missing: {exc}. Install backend[model,train].") from exc

    if args.reload_smoke:
        reload_started = time.perf_counter()
        report_path = args.output / "training_run.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        tokenizer = AutoTokenizer.from_pretrained(settings.model_id, revision=settings.model_revision)
        quant_config = None
        if report["qlora_requested"]:
            quant_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
        reloaded = AutoPeftModelForCausalLM.from_pretrained(args.output, revision=settings.model_revision,
            device_map="auto", torch_dtype=torch.float16 if torch.cuda.is_available() else "auto",
            quantization_config=quant_config)
        smoke = tokenizer.apply_chat_template([{"role": "user", "content": "Where is order ORD-10021?"}], tokenize=False,
                                             add_generation_prompt=True, enable_thinking=False)
        encoded = tokenizer(smoke, return_tensors="pt").to(reloaded.device)
        generated = reloaded.generate(**encoded, max_new_tokens=160, do_sample=False,
                                      temperature=None, top_p=None, top_k=None)
        report["status"] = "trained_and_reloaded"
        report["reload_smoke_output"] = tokenizer.decode(generated[0][encoded.input_ids.shape[-1]:], skip_special_tokens=True)
        report["reload_seconds"] = round(time.perf_counter() - reload_started, 2)
        report["elapsed_seconds"] = round(report["elapsed_seconds"] + report["reload_seconds"], 2)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (ROOT / "experiments" / "results" / "lora_smoke_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return

    dataset_path = ROOT / "experiments" / "datasets" / "scenarios.jsonl"
    manifest_path = ROOT / "experiments" / "datasets" / "manifest.json"
    if not dataset_path.exists() or not manifest_path.exists():
        raise SystemExit("Generate the dataset first: python experiments/data_generation/generate_dataset.py")
    rows = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    train_rows = [row for row in rows if row["split"] == "train"]
    if not train_rows or any(row["split"] != "train" for row in train_rows):
        raise SystemExit("No valid train split is available.")
    tokenizer = AutoTokenizer.from_pretrained(settings.model_id, revision=settings.model_revision)

    def render(row):
        return tokenizer.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=False, enable_thinking=False)

    texts = [render(row) for row in train_rows]

    class EncodedTrainingSet(torch.utils.data.Dataset):
        def __init__(self):
            self.examples = [tokenizer(text, truncation=True, max_length=1024) for text in texts]

        def __len__(self):
            return len(self.examples)

        def __getitem__(self, index):
            return self.examples[index]

    dataset = EncodedTrainingSet()
    quant_config = None
    if args.qlora:
        if not torch.cuda.is_available():
            raise SystemExit("QLoRA was requested but CUDA is unavailable; no training was run.")
        quant_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
    model_dtype = torch.float16 if torch.cuda.is_available() else "auto"
    model = AutoModelForCausalLM.from_pretrained(settings.model_id, revision=settings.model_revision,
        device_map="auto", torch_dtype=model_dtype, quantization_config=quant_config)
    if args.qlora:
        model = prepare_model_for_kbit_training(model)
    model.config.use_cache = False
    lora = LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    model = get_peft_model(model, lora)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=1e-4)
    loader = torch.utils.data.DataLoader(dataset, batch_size=1, shuffle=True,
        generator=torch.Generator().manual_seed(17), collate_fn=lambda batch: tokenizer.pad(batch, padding=True, return_tensors="pt"))
    loader_iter = iter(loader)
    optimizer.zero_grad(set_to_none=True)
    total_loss = 0.0
    gradient_accumulation_steps = 4
    for step in range(args.max_steps):
        for _ in range(gradient_accumulation_steps):
            try:
                batch = next(loader_iter)
            except StopIteration:
                loader_iter = iter(loader)
                batch = next(loader_iter)
            batch = {key: value.to(model.device) for key, value in batch.items()}
            labels = batch["input_ids"].clone()
            labels[batch["attention_mask"] == 0] = -100
            loss = model(**batch, labels=labels).loss
            (loss / gradient_accumulation_steps).backward()
            total_loss += float(loss.detach().cpu()) / gradient_accumulation_steps
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
    model.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)
    del loss, batch, labels, optimizer, trainable, model
    gc.collect()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    adapter_weights = args.output / "adapter_model.safetensors"
    report = {"status": "trained_and_saved", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model_id": settings.model_id, "model_revision": settings.model_revision, "adapter_path": str(args.output),
        "adapter_sha256": hashlib.sha256(adapter_weights.read_bytes()).hexdigest(),
        "dataset_version": manifest["dataset_version"], "dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
        "split": "train", "train_examples": len(train_rows), "max_steps": args.max_steps, "seed": 17,
        "qlora_requested": args.qlora, "mean_training_loss": total_loss / max(1, args.max_steps),
        "gradient_accumulation_steps": gradient_accumulation_steps,
        "torch_version": torch.__version__, "python": platform.python_version(),
        "platform": platform.platform(), "elapsed_seconds": round(time.perf_counter() - started, 2),
        "held_out_evaluation": "not run by this script"}
    (args.output / "training_run.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (ROOT / "experiments" / "results" / "lora_smoke_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Reload the saved adapter in a fresh process with: python experiments/training/train_lora.py --output {args.output} --reload-smoke" + (" --qlora" if args.qlora else ""))


if __name__ == "__main__":
    main()
