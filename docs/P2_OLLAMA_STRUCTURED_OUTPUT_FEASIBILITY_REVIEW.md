# Review of Qwen's Ollama Structured-Output Feasibility Study

**Review date:** 2026-10-12  
**Scope:** Check the pasted feasibility study against current P2 adapter code, local Ollama inventory and official Ollama documentation. No inference, model download, quantization change, or benchmark modification was performed.

## Verdict

**The mechanism is already implemented and has narrow real-model evidence.** P2's Ollama adapter sends the Pydantic `IntentEnvelope.model_json_schema()` through the native `/api/chat` request field `format`, then parses the returned content with `IntentEnvelope.model_validate_json`. Ollama's official documentation describes `format` as accepting either `json` or a JSON Schema and demonstrates passing a Pydantic-generated schema. The exact approach in the study is therefore not merely a future feasibility idea; it is already in the P2 candidate path.

Three saved bounded real-Qwen FastAPI workflows previously passed their predeclared checks through this code path. This shows it worked for those selected cases. It does not establish that constrained decoding caused better accuracy than unconstrained generation, that every schema feature is supported, or that the candidate generalizes.

## Directly checked local evidence

- Local Ollama reported version `0.40.3` during this review.
- `ollama list` showed these cached model tags at review time: `qwen3:1.7b` (1.4 GB, digest prefix `8f68893c685c`) and `llama3.2:3b` (2.0 GB, digest prefix `a80c4f17acd5`). This time-specific inventory may change.
- The project adapter uses `format=IntentEnvelope.model_json_schema()` and strict Pydantic JSON validation in `backend/app/llm/backends.py`.
- Existing real-Qwen evidence is the three saved lookup, estimate, and ticket-approval workflows listed in `docs/STRUCTURED_INTENT_WORKFLOW.md`; they are selected smokes, not a comparative benchmark.
- P2's default and historical result files remain unchanged.

## What the supplied study gets right

- It distinguishes structural/schema validity from semantic correctness. A valid `IntentEnvelope` can still contain the wrong intent or omit a needed slot; trusted application checks remain necessary.
- It proposes freezing the current model and quantization while evaluating the native structured-output path, avoiding confounding an API change with a model change.
- It recommends recording exact model identity, runtime version, schema, request settings, response, latency and validation outcome.
- It calls for reviewer calibration and honest single-reviewer limitations.

## Corrections and unsupported claims

### The core API feasibility question is already answered

The official Ollama API documentation confirms the `format` JSON Schema interface. P2 source confirms it is wired into the local request, and saved smokes show parsed intent plus successful application flows. A broad model-size survey is not needed to establish that this API path can work.

What is not established is a **paired quality benefit** from enabling schema-constrained output. That would require a small controlled comparison on frozen, reviewed cases using the same cached model, prompt and generation settings under a hard process deadline. Compare structural validity and semantic intent/slot accuracy separately. Proceed only if that comparison answers a real decision question and does not alter the accepted P2 default.

### The proposed model survey exceeds the frozen local inventory

The study recommends Qwen2.5 7B/32B, Qwen coder/VL, and Llama 3.1, plus multiple quantizations. None appeared in the checked local Ollama inventory. Downloading them, changing quantization, or increasing model size would violate the cached-only/frozen scope. The locally cached `llama3.2:3b` is a possible already-present non-Qwen comparison candidate, but its presence alone does not demonstrate fit or quality. Any use would need a separate bounded resource/compatibility pilot and freeze; no inference was run here.

### Community instability reports are not evidence about this installation

The pasted study's numbered citations have no bibliography or direct links, so claims about version-specific Qwen crashes, infinite loops, token-boundary/quantization interactions, decode overhead, and model suitability could not be checked from the submitted text. Reports about Qwen3.5 or fine-tuned Qwen2.5 GGUF variants do not establish failure of this exact cached Qwen3-1.7B Q4_K_M artifact under local Ollama 0.40.3. Do not generalize them to P2 without exact reproducible evidence.

Descriptions of low-level GBNF/logit-mask implementation and numerical overhead estimates likewise require primary implementation sources or controlled measurements. The Ollama API docs establish the supported `format` interface, not every internal mechanism/performance assertion in the pasted report.

### A single reviewer cannot establish inter-rater reliability

One person can calibrate on examples and apply a fixed rubric, but a single reviewer cannot measure agreement between raters or establish independent adjudication. Report the result as single-reviewer reviewed. If no independent reviewer is available, do not call the labels independently validated; preserve the exploratory/inconclusive limitation.

### Keep traces observable

Save schema-validity, normalized intent/slots, decision reason codes, registered tool calls/results, authorization decisions, outcome and timing. Never save hidden chain-of-thought. Do not treat an inferred reasoning narrative as a diagnostic metric.

## Smallest useful next experiment

No model-size survey is warranted to answer whether native Ollama `format` works: it already does in the candidate path. If a controlled quality-benefit test is desired, predeclare a small reviewed synthetic set of distinct cores and a simple fixed schema; freeze Qwen3:1.7b digest, Ollama version, prompt and limits; compare native JSON Schema `format` against a clearly defined safe baseline; enforce the existing parent-process deadline; and record raw response, parse/schema validity, exact intent/slot score, latency and failure class. Do not use held-out V5 for tuning. If no independent reviewer is available, report that limitation. Stop if the test requires a download, quantization change, expanded budget or weakened safety control.

This is a proposal, not a test result. The larger P2 acceptance gap remains broad reviewed task quality, actual-app reliability on fresh distinct cores, and the original accuracy/safety targets.

## Sources

- [Ollama — Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs): official documentation says to provide a JSON Schema in the `format` field and demonstrates Pydantic schema generation/validation.
- [Ollama — Generate a chat message API](https://docs.ollama.com/api/chat): official request schema documents `format` as `json` or a JSON Schema.
- Local project evidence: `backend/app/llm/backends.py`, `.env.structured-intent-candidate-real-llm-smoke.example`, `docs/STRUCTURED_INTENT_WORKFLOW.md`, and the saved structured-intent smoke result/freeze artifacts.

## Conclusion

Ollama native structured output is compatible with the existing P2 candidate path and has passed three selected end-to-end synthetic smokes. The pasted study did not run a comparative feasibility or quality experiment. Its broader model recommendations exceed the frozen cached-only scope, and its unlinked stability claims are not verified for this installation. Overall P2 remains **PARTIAL**.
