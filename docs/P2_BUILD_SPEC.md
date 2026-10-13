# P2 — Reliable Tool-Using LLM for Business Operations
## Complete A-to-Z Build Specification for an AI Coding / Project-Building Agent

**Specification status:** Locked project direction. Implement this specification rather than redesigning the project.

**Project category:** Applied AI Engineering, Agentic AI, Open-Weight LLM Engineering, Model Evaluation, Production AI Systems.

**Primary hiring targets:** AI Engineer, GenAI Engineer, Applied AI Engineer, AI Software Engineer, AI Application Engineer, selected LLM Engineer / Model Engineering internships.

**Important instruction to the build agent:** Build a working, testable, documented application. Do not stop after generating an architecture diagram, a UI mockup, or a scaffold. Do not invent benchmark results. Implement in stages, run tests, fix failures, and document any limitations honestly.

---

# 0. Executive summary

Build a business-operations assistant powered by an open-weight language model. The assistant receives a natural-language request, decides whether it needs an approved tool, creates a structured tool call with validated arguments, receives trusted results from the application, and returns a clear answer. For requests that require a state-changing action, the system must apply policy checks and, where required, obtain explicit human confirmation before execution.

The initial business domain is **synthetic e-commerce customer support and order operations**. It is deliberately narrow and demo-friendly. Available operations include looking up an order, listing order items, checking return/refund eligibility, retrieving return policy, calculating a refund estimate, and creating a support ticket. The project must not issue real refunds, access real customer accounts, send real emails, or perform destructive external actions.

The project has two connected goals:

1. **Engineering goal:** Deliver a reliable and secure tool-using LLM application with a clean backend, auditable execution, tests, deployment, and a usable interface.
2. **Research/measurement goal:** Compare a pretrained open-weight model, a prompt-engineered version of the same model, and a LoRA/QLoRA-adapted version where feasible. Measure whether fine-tuning improves tool selection and argument correctness, and measure the trade-offs in latency, memory, throughput, and task success. The experiment must be able to conclude that fine-tuning did not help if the results do not support an improvement.

The project is **not** a general-purpose autonomous agent, another RAG knowledge assistant, a multi-agent framework, or a model trained from scratch.

# 1. Project positioning and relationship to P1

P1 is the Adaptive Enterprise Knowledge & Evidence Copilot. P1 primarily demonstrates retrieval, hybrid search, learned retrieval routing, SQL/structured-data retrieval, grounded answers, evidence validation, and confidence/abstention.

P2 must add different evidence:

- Reliable selection and invocation of approved tools.
- Schema-valid argument generation.
- Controlled multi-step action workflows.
- Fine-tuning experimentation on tool-use examples.
- Model-level benchmarking and, where feasible, quantization/inference optimization.
- Safe handling of tools that can change state.

Do not duplicate P1's full retrieval stack inside P2. A simple read-only database lookup is a tool in P2; it is not a new RAG pipeline. Do not add GraphRAG, a general knowledge base, multi-agent orchestration, voice, document OCR, computer vision, or unrelated tools to increase feature count.

# 2. Target users and core user stories

## 2.1 Demo users

- **Customer-support agent:** asks the assistant to check an order, understand a policy, or prepare a ticket.
- **Supervisor/reviewer:** approves or rejects a proposed state-changing action and inspects the execution trace.
- **Developer/evaluator:** runs benchmark suites, compares model configurations, inspects error cases, and exports results.

Use a seeded demo login or lightweight development authentication for the first iteration. Preserve tenant/role authorization boundaries in the backend design. Do not make front-end-only authorization decisions.

## 2.2 Core user stories

1. As a support user, I can ask “Where is order ORD-10021?” and get the order status from the database, not a model guess.
2. I can ask “Can item X from this order be returned?” and get a rules-based eligibility result plus the relevant reason.
3. I can ask “What is the estimated refund for the eligible items?” and receive a deterministic calculation with a breakdown.
4. I can ask the assistant to open a support ticket; the system shows the proposed action and obtains confirmation if the action is state-changing.
5. If I provide an incomplete or ambiguous order reference, the assistant asks for the missing information rather than inventing it.
6. If I ask it to access another customer's order, bypass a policy, or run an unsupported operation, the system refuses or safely asks for authorized details.
7. I can inspect which model response triggered each tool, the arguments sent, the tool result, validation steps, timings, and final answer.
8. I can run the same test suite against baseline and fine-tuned models and compare the measurements.

# 3. Scope

## 3.1 Must-have product features

- Chat-based interface for a synthetic business-operations support workflow.
- Session/conversation history.
- Open-weight LLM backend abstraction.
- Explicit tool registry with typed input and output schemas.
- Internal normalized action format regardless of model-specific output format.
- Argument validation, permission checks, policy checks, execution timeouts, maximum step limits, and safe error handling.
- Read-only tools for order lookup, order items, policy lookup, refund eligibility, and refund estimate calculation.
- One state-changing tool: create a support ticket in the project's own database. Require confirmation before creation.
- Human approval/rejection flow for pending actions.
- Structured execution trace and audit events.
- Benchmark runner and metrics dashboard.
- Training data generation/versioning and an optional model-training pipeline that becomes a required experiment when compute is available.
- Automated tests, Docker-based local run, documented deployment path, CI checks, README, model card/experiment report, and demo script.

## 3.2 Must-have model experiment

Compare these configurations on the same locked test cases:

- **Baseline A — Pretrained:** the chosen open-weight base/instruct model with a minimal, correct tool description and the minimum required safety rules.
- **Baseline B — Prompt-engineered:** the same model with improved tool instructions, examples, action schema and recovery prompt.
- **Experiment C — Fine-tuned:** the same model with a LoRA/QLoRA adapter trained on a separated set of tool-use examples, plus the same inference-time safety and validation layer.

All three must use the same executor, tool schemas, test dataset, authorization checks, and policy implementation. If the model does not support native tool calls in a usable format, generate a strict internal JSON action envelope and normalize it into the same internal representation. Do not compare different executors or policies across model configurations.

Optional fourth configuration: quantized inference of one of the above, if the selected backend/hardware supports it. Treat quantization as an experiment to measure, not a guaranteed improvement.

## 3.3 Out of scope

- Real financial transactions or real refunds.
- Real customer data, production credentials, or third-party customer systems.
- General web browsing or unbounded internet actions.
- Shell/terminal/code execution as an LLM-accessible tool.
- Database write queries generated freely by the model.
- Arbitrary SQL generation and execution. Only predefined, parameterized functions are allowed.
- Email sending, payment processing, account deletion, order cancellation, or other high-risk integrations.
- Multiple collaborating agents.
- Graph RAG or another document knowledge system.
- Training a foundation model from scratch.
- Claims of state-of-the-art results or employment/salary guarantees.

# 4. Business workflow and tool design

Use an invented e-commerce support business with synthetic records. Use fake identifiers and fake customer data only.

## 4.1 Initial tool registry

Implement the following tools. Keep each tool small and testable; the LLM must never call arbitrary code or raw database queries.

### Tool 1: `lookup_order`
- Purpose: Find an order from an order ID.
- Input: `order_id` string.
- Output: order ID, order status, order date, expected delivery date if available, customer-safe delivery information, and a list of item IDs. Do not return unnecessary sensitive information.
- Side effect: none.
- Authorization: the backend checks whether the authenticated demo user/role is allowed to view the order. Never trust a customer ID supplied only by the model.

### Tool 2: `list_order_items`
- Purpose: Retrieve items for an order.
- Input: `order_id` string.
- Output: item ID, product name, quantity, unit price, item status, and return-window-relevant dates when available.
- Side effect: none.
- Authorization: same order-level access check as `lookup_order`.

### Tool 3: `get_return_policy`
- Purpose: Retrieve a deterministic policy summary from the application's policy table or code-backed configuration.
- Input: a constrained enum/category such as `standard_return`, `damaged_item`, `late_delivery`, `refund_timing`.
- Output: policy text, applicable conditions, policy version, and last-updated timestamp.
- Side effect: none.
- Do not ask the model to invent policy wording. The tool returns the source of truth.

### Tool 4: `check_refund_eligibility`
- Purpose: Determine refund/return eligibility using business rules in ordinary code.
- Input: `order_id`, one or more `item_ids`, and a constrained `reason` enum.
- Output: per-item eligibility (`eligible`, `ineligible`, `needs_review`), policy reason codes, deadline/date data used, and policy version.
- Side effect: none.
- Important: the LLM may request this tool, but may not set the eligibility outcome. The business rules calculate it.

### Tool 5: `calculate_refund_estimate`
- Purpose: Calculate an estimate for eligible items.
- Input: `order_id`, `item_ids`, optional allowed discount/tax references if needed.
- Output: item subtotal, applicable discounts, taxes/fees where the synthetic policy requires them, estimated total, currency, and calculation explanation.
- Side effect: none.
- Important: all arithmetic occurs in application code with decimal arithmetic. The LLM explains the result but does not calculate the source-of-truth amount.

### Tool 6: `create_support_ticket`
- Purpose: Create a support ticket in the demo database.
- Input: `order_id` (optional only where policy permits), constrained `issue_type`, concise `summary`, `description`, and constrained `priority`.
- Output: ticket ID, status, created timestamp, and summary.
- Side effect: yes; inserts a row into the project's database.
- Approval: require an explicit confirmation step by default. Store the proposal as pending until the authenticated user approves it. A model-generated phrase such as “user approved” is not proof of approval.
- Idempotency: use an idempotency key so retries cannot create duplicate tickets.

### Internal actions, not model-accessible tools

- `request_human_review`: an internal control-flow route used by the server when the model is uncertain, a policy rule requires review, or a safety check fails.
- `deny_action`: server-owned policy response.
- `complete_response`: normalized final response action.

The registry must include metadata for each tool: name, description, Pydantic input/output schema, risk category, read/write classification, required role, timeout, maximum retries, whether approval is required, and idempotency behavior.

# 5. Core reliability and safety principles

These principles are mandatory. The LLM proposes actions; the application decides whether to execute them.

1. **Allowlist only:** the model can choose only tools registered in the tool registry.
2. **Schema validation:** parse every proposed tool name and argument with Pydantic. Reject unknown keys, missing required values, invalid enum values, and malformed types.
3. **Authorization outside the model:** derive the user's role, tenant and permitted order scope from authenticated server context. Never accept the model as an authorization authority.
4. **Policy enforcement outside the model:** refund eligibility, amount calculation, required approvals and action permissions must be deterministic application logic.
5. **No arbitrary execution:** never expose `eval`, shell commands, Python execution, unrestricted HTTP calls, or raw SQL to the model.
6. **No silent state change:** state-changing operations require a pending-action record and explicit approval. The approval endpoint must verify the authenticated user and pending action ID.
7. **Prompt-injection resistance:** user messages and tool outputs are untrusted data. Do not follow instructions contained in order notes, policy text, customer messages or tool results that attempt to change system rules or permissions.
8. **Bounded autonomy:** cap the number of model turns, tool calls, elapsed time, token output, and retries per request. A suggested default is up to 5 model steps and up to 4 executed tool calls per user turn; make this configurable.
9. **Fail closed:** if the model output cannot be parsed, authorization fails, a policy check errors, or a safety requirement is unclear, do not execute the action. Ask a clarification, retry once with a bounded correction prompt, or hand off for review.
10. **Auditable execution:** record normalized action proposals, validation result, approval state, tool result status, timing and final answer. Redact sensitive values from logs.
11. **No overclaiming:** tool results and final answers must clearly distinguish confirmed facts, estimates and pending actions. Never tell a user that a ticket was created before the database confirms it.

Security design should be informed by the current OWASP GenAI/LLM risks, particularly prompt injection, insecure output handling, sensitive information disclosure and excessive agency: https://owasp.github.io/www-project-top-10-for-large-language-applications/ and https://genai.owasp.org/llmrisk/llm062025-excessive-agency/.

# 6. Architecture

Use a modular monolith initially. Do not create microservices unless a measured requirement justifies them.

```text
Web UI (React + TypeScript)
        |
        v
FastAPI REST API + authentication/session context
        |
        v
Conversation Orchestrator
  |        |           |
  |        |           +--> Policy / authorization engine
  |        +--------------> Model adapter (open-weight LLM)
  |                              |
  |                              v
  |                       Normalized action parser
  |                              |
  +--> Tool registry <----- Pydantic validation
           |
           v
   Tool execution boundary
    |       |        |
    v       v        v
Order DB  Policy DB  Ticket DB
           |
           v
Trace / audit / metrics store

Separate developer workflows:
Dataset generator -> dataset validator -> training job -> adapter artifact
Benchmark runner -> result store -> evaluation dashboard
```

## 6.1 Main backend layers

- **API layer:** request validation, authentication, response schemas and HTTP status codes.
- **Conversation service:** stores messages and coordinates a single user turn.
- **Orchestrator:** controls model-tool-model flow, budgets, retries, pending approvals and final response.
- **Model adapter:** loads the selected open-weight model through a configurable runtime and translates model outputs into a normalized action.
- **Tool registry/executor:** validates, authorizes, runs and records tools.
- **Policy service:** deterministic rules for eligibility, amounts, permissions, action approval and escalation.
- **Persistence layer:** SQLAlchemy models, migrations and repositories.
- **Evaluation subsystem:** dataset/version handling, benchmark jobs, metric calculation and export.
- **Observability layer:** structured logs, traces, health checks and aggregate metrics.

## 6.2 Model backend abstraction

Define a common interface such as:

- `generate(messages, tool_schemas, generation_config) -> ModelAction`
- `health_check() -> ModelHealth`
- `get_model_info() -> ModelInfo`
- `close()`

Use at least:

1. `TransformersModelBackend` for the main open-weight model and adapter experiments.
2. `DeterministicTestModelBackend` for unit tests and CI only. The UI and documentation must clearly identify it as a test backend; never present its outputs as genuine LLM results.
3. Optional `VLLMModelBackend` if compatible infrastructure is available and measured serving comparisons justify it. Do not make vLLM mandatory for local development.

Normalize native tool calls and JSON action outputs into one internal action schema. Never couple the entire application to one provider's exact response fields.

# 7. Model-selection and compute-feasibility gate

Do not hard-code a large model because it appears impressive. The user's GTX 1650-class laptop should not be assumed capable of fine-tuning a multi-billion-parameter model. Plan for CPU/local smoke tests and, if needed, a controlled cloud GPU session.

## 7.1 Candidate approach

Begin by evaluating a compact open-weight instruction model with a clearly reviewed licence and usable function/tool-call behavior. Qwen3-1.7B and Qwen3-4B-Instruct-2507 are candidates for a feasibility test, not irrevocable dependencies. Their official model pages currently list Apache-2.0 licensing; confirm the exact model card, license file, usage restrictions, chat template and revision at implementation time:

- https://huggingface.co/Qwen/Qwen3-1.7B
- https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507
- Qwen tool/function-call documentation: https://github.com/QwenLM/Qwen3/blob/main/docs/source/framework/function_call.md

Choose the model based on benchmark performance, native/normalized tool-use compatibility, VRAM, available compute, training support, latency and reproducibility—not name recognition.

## 7.2 Mandatory feasibility test before fine-tuning

Implement a small proof of feasibility before the full application is expanded:

1. Load the candidate model or access an approved GPU environment.
2. Generate a simple normalized tool-call action.
3. Record GPU memory or host memory, load time and inference latency.
4. Complete a tiny supervised fine-tuning/LoRA run on a small dataset subset.
5. Save and reload the adapter and verify output.
6. Record runtime, failure mode and cost, if rented GPU is used.

If a model is too large, choose a smaller supported model. If local hardware is insufficient, run the training experiment on an explicitly configured and budgeted GPU environment. Do not silently skip fine-tuning but still claim it was completed. If cloud compute is unavailable, implement the rest of the system, report the training experiment as blocked, and make no fine-tuning claims in the resume.

## 7.3 Training library guidance

A reasonable Python stack is PyTorch + Transformers + Datasets + TRL + PEFT, with bitsandbytes where compatible. Hugging Face TRL documents SFT with PEFT/LoRA/QLoRA: https://huggingface.co/docs/trl/peft_integration. PEFT's quantization guide explains the 4-bit QLoRA approach and its requirements: https://huggingface.co/docs/peft/developer_guides/quantization.

Pin versions after a successful installation and test, record them in the repository, and don't mix incompatible package versions by guessing. The training workflow should run separately from the user-facing API so the API does not need training dependencies in its runtime image.

# 8. Model action protocol and orchestration

Use a model-independent internal action envelope. A suggested schema:

```json
{
  "action_type": "tool_call",
  "tool_name": "lookup_order",
  "arguments": {"order_id": "ORD-10021"},
  "reason_summary": "The user asks for the status of a specific order.",
  "confidence": 0.91
}
```

For a final answer:

```json
{
  "action_type": "final_answer",
  "answer": "Order ORD-10021 is currently in transit.",
  "claims": [
    {"text": "The order is in transit.", "source_type": "tool_result", "source_id": "execution-id"}
  ],
  "needs_human_review": false
}
```

Confidence may be used as a feature, but do not treat a self-reported model confidence number as a calibrated probability. Calibrate decisions from evaluation data and deterministic rules.

For a ticket proposal:

```json
{
  "action_type": "propose_state_change",
  "tool_name": "create_support_ticket",
  "arguments": {
    "order_id": "ORD-10021",
    "issue_type": "delivery_delay",
    "summary": "Order delivery delayed",
    "description": "Customer reports the order has not arrived.",
    "priority": "normal"
  },
  "requires_confirmation": true
}
```

The server, not the model, decides that confirmation is required. A model may suggest a proposal, but the backend sets the actual approval state.

## 8.1 Orchestration algorithm

For each incoming user message:

1. Authenticate user and load authorized session context.
2. Persist the user message.
3. Construct prompt from a versioned system instruction, recent conversation, available tool schemas, policy reminders and budget constraints. Do not dump all database records into the prompt.
4. Request one model action.
5. Parse output into normalized schema. If invalid, retry at most once with a concise correction message; otherwise safely fail.
6. If action is final, validate claims against the available tool results/policy and return it.
7. If action is a tool call, confirm the tool exists, validate exact arguments, authorize the user, validate state-changing policy and run the tool only after all gates pass.
8. Store the tool execution record and bounded, redacted result.
9. Add the tool result to model context and continue within configured turn/tool/time limits.
10. If a state-changing action requires user confirmation, persist a pending action and return a confirmation card. Do not execute yet.
11. If limits are reached, tool fails repeatedly, or the model appears stuck in a loop, stop and return a clear safe message or human-review route.
12. Persist the final assistant response and close the trace for that user turn.

Use separate IDs for conversation, user turn, model run, tool execution, and approval record. Make all write actions idempotent.

# 9. Dataset design and experiment methodology

## 9.1 Dataset objectives

The data should train and test the model on deciding when to call a tool, selecting the right tool, creating correct arguments, asking questions when information is missing, refusing unauthorized requests, and finishing after sufficient evidence.

Do not train only on easy direct examples. Include variations in wording, order ID formats, incomplete requests, multi-step tasks, contradictions, policy edge cases, no-tool questions, injection attempts and tool errors.

## 9.2 Data source

Use synthetic records created by deterministic scripts and hand-reviewed examples. No real customer data, personal information, real payment data or confidential company records. Generate the underlying order/policy database from seeded fixtures, then derive question/action labels from those fixtures so expected outcomes are reproducible.

## 9.3 Suggested initial dataset size

Start with:

- Training: about 1,000–2,000 tool-use/dialog examples.
- Validation: about 150–250 examples.
- Locked held-out test: at least 300 examples if time/compute allows.

These are project planning targets, not magic sample sizes. If fewer are feasible, report the exact sample size and the evaluation limitation. Ensure the test set is large and diverse enough to be meaningful. Split by scenario template/family and seed, not by random copies of nearly identical examples, to reduce leakage.

## 9.4 Required scenario families

1. Direct order lookup.
2. Multi-step order + item + policy lookup.
3. Refund eligibility and deterministic estimate.
4. Ticket creation proposal and approval/rejection.
5. Missing order ID or ambiguous item reference.
6. Nonexistent order/item.
7. User lacks authorization to an order.
8. Request outside available tools.
9. No-tool general explanation (only based on allowed policy/context).
10. Conflicting or outdated data.
11. Tool timeout/error and safe retry.
12. Duplicate ticket submission/idempotency.
13. Prompt injection in user text or synthetic order notes/tool output.
14. Requests to bypass business rules, reveal secrets or make an unauthorized update.
15. Long/noisy but benign requests.
16. Multi-turn repair after the user clarifies missing information.
17. Requests for a prohibited action such as “issue the refund now”; system must explain that it can only estimate eligibility and follow the configured approval workflow.

## 9.5 Dataset format

Store JSONL with fields such as:

- `example_id`
- `scenario_family`
- `scenario_seed`
- `split`
- `messages` (or model-native chat representation)
- `available_tools_version`
- `expected_action_type`
- `expected_tool_name` (when applicable)
- `expected_arguments`
- `expected_final_state`
- `expected_refusal_or_clarification` (when applicable)
- `risk_category`
- `annotation_source` (synthetic/template/manual-reviewed)

Do not include test examples in the training file. Keep dataset generation scripts, dataset version, checksums and split manifests in the repository. Provide a validator that checks schema, duplicate IDs, split overlap, tool names, argument schemas and label consistency.

## 9.6 Fine-tuning procedure

- Fine-tune only one compact model initially; do not run a zoo of models.
- Use supervised fine-tuning for the target action format/tool-use pattern.
- Use LoRA or QLoRA where supported.
- Begin with a small smoke run and verify adapter save/load before running the full experiment.
- Track learning rate, epochs, rank/alpha, dropout, max sequence length, batch size/gradient accumulation, precision, random seed, dataset version and model revision.
- Stop on validation metrics and inspect output examples for overfitting, catastrophic degradation, incorrect tool arguments and failure to ask clarifying questions.
- Compare the adapter against the same model's baseline, not a different model or different tool inventory.
- Record compute time and approximate cost.

# 10. Evaluation framework

The project must produce numerical results from actual runs. Never prefill fabricated benchmark results.

## 10.1 Core metrics

- **Tool selection accuracy:** correct tool selected when a tool is needed.
- **Exact argument accuracy:** all required arguments exactly match the expected normalized values.
- **Argument field F1:** useful when multiple argument fields can be independently correct.
- **Valid action rate:** model outputs that parse and pass schema validation.
- **Task completion rate:** full workflow completed correctly, including correct sequencing across tools.
- **Clarification accuracy:** asks for necessary missing information and avoids a guessed action.
- **No-tool correctness:** answers or abstains correctly when no tool call is justified.
- **Policy violation rate:** attempted unauthorized/prohibited actions per benchmark case.
- **Unsafe execution rate:** actually executed unauthorized or unapproved actions. This must be zero in the defined safety test suite; the executor should enforce this independently of model quality.
- **Duplicate write rate:** duplicate ticket records for retries or repeated delivery; must be zero for idempotency tests.
- **Final answer factuality:** important claims agree with the trusted tool result and deterministic business rules.
- **Latency:** average and p50/p95 end-to-end latency; separate model generation and tool execution time.
- **Throughput:** completed requests per second under a stated test load, if concurrent serving is supported.
- **Memory use:** peak RAM/VRAM under a defined setup.
- **Inference cost:** report actual cloud runtime cost or a clearly defined local resource estimate. Do not call approximate estimates “measured cloud cost.”

## 10.2 Experimental controls

- Same held-out test examples for all model variants.
- Same tool descriptions and schemas unless the experiment explicitly tests prompt changes.
- Fixed decoding parameters where appropriate; report any differences.
- Save model revision, adapter revision, prompt version, dataset version, tool schema version, environment versions, hardware, seed and benchmark command.
- Report each score with the numerator/denominator. Where feasible, estimate confidence intervals for principal metrics.
- Perform error analysis by scenario family, not only one overall accuracy number.
- Include examples where fine-tuning makes results worse.
- Do not select prompt/model configuration based on held-out test scores; use validation for tuning.

## 10.3 Initial acceptance targets

These are target gates for the initial benchmark, not claims about expected results. Review them after an initial baseline and document any evidence-based revision before looking at final test performance.

- All unit/integration/security test suites pass.
- Zero unauthorized state-changing operations execute in the safety suite.
- Zero duplicate tickets in the idempotency suite.
- At least 85% tool selection accuracy on the locked test set.
- At least 80% exact argument accuracy on cases that require a tool call.
- At least 80% task completion on the agreed in-scope test scenarios.
- Fine-tuned model: seek at least a 5 percentage-point improvement in one primary tool-use metric over the prompt-engineered baseline without a material regression in safety, clarification behavior or task success. If this is not achieved, report the outcome honestly and analyze why.
- Set p95 latency and memory goals after measuring the model on the target inference hardware. Record environment and test load; do not promise device-independent latency.

These goals should not be manipulated by removing difficult examples. Keep the locked test set intact, and report any failures transparently.

# 11. Persistence and database design

Use PostgreSQL for the integrated application; allow SQLite only for quick tests if the implementation genuinely supports it. Use SQLAlchemy 2.x, typed models and Alembic migrations. All queries must be parameterized through ORM/driver APIs.

Recommended entities:

## 11.1 `users`
- `id` UUID/primary key
- `email` or demo username
- `password_hash` if password login is implemented; never store plaintext passwords
- `role` enum (`support_agent`, `supervisor`, `admin`, `evaluator`)
- `tenant_id`
- `is_active`
- timestamps

## 11.2 `customers`
- `id`
- `tenant_id`
- `customer_code` (synthetic)
- `display_name` (fake data)
- minimum optional contact fields needed for the demo
- timestamps

## 11.3 `orders`
- `id`
- `tenant_id`
- `order_code` unique per tenant
- `customer_id`
- `status` enum
- `order_date`
- `expected_delivery_date` nullable
- currency
- timestamps

## 11.4 `order_items`
- `id`
- `order_id`
- `item_code`
- product name
- quantity
- unit price and currency using Decimal-safe numeric types
- discount/tax data required by the deterministic calculation
- delivered date/status

## 11.5 `return_policies`
- `id`
- `policy_key`
- version
- effective start/end dates
- policy content/structured rules
- enabled flag
- timestamps

## 11.6 `support_tickets`
- `id`
- `tenant_id`
- generated `ticket_code`
- `order_id` nullable where the issue does not require an order
- `created_by_user_id`
- issue type, summary, description, priority, status
- `idempotency_key` unique
- timestamps

## 11.7 `conversations` and `messages`
Conversation fields: id, tenant id, user id, title, created/updated timestamps. Message fields: id, conversation id, role, content, structured content if applicable, sequence number, model run ID nullable, timestamps. Do not store hidden chain-of-thought. Store concise user-visible reasoning summaries and tool trace events only.

## 11.8 `model_runs`
- id, conversation/turn ID
- model ID/revision, adapter ID/revision
- prompt version, decoding config, input/output token counts if available
- duration, status, error category
- timestamps

## 11.9 `tool_executions`
- id, conversation turn ID, model run ID
- tool name/schema version
- redacted normalized arguments
- authorization and validation outcomes
- approval record ID if applicable
- result status, redacted result summary, error code
- duration, retry count, idempotency key where relevant
- timestamps

## 11.10 `pending_actions` / `approvals`
- id, proposed tool/action, normalized arguments, user/session context, risk category
- status (`pending`, `approved`, `rejected`, `expired`, `failed`, `completed`)
- proposed-by user, approved-by user, approval timestamp, expiration timestamp
- idempotency key and resulting execution ID

## 11.11 `benchmark_runs` and `benchmark_results`
Store model and adapter revisions, dataset/version/checksum, prompt/schema versions, environment/hardware, parameters, aggregate metrics, per-scenario metrics, failures, start/end time and result artifact paths.

Add indexes on tenant IDs, order code, conversation ID, created timestamps, tool executions and benchmark run IDs. Use migrations for schema changes. Seed data must be reproducible using a fixed seed.

# 12. API contracts

Use prefix `/api/v1`. Provide OpenAPI docs through FastAPI. Use Pydantic request and response types with consistent error codes. Do not return internal stack traces or secrets.

## 12.1 System
- `GET /health/live` — process is alive.
- `GET /health/ready` — checks database and model backend readiness without leaking configuration secrets.
- `GET /api/v1/system/info` — app version, configured model ID, active adapter revision, backend type and capability flags.

## 12.2 Authentication and sessions
- `POST /api/v1/auth/login` if password-based login is implemented.
- `POST /api/v1/conversations` — create a conversation.
- `GET /api/v1/conversations` — list only the authenticated user's authorized sessions.
- `GET /api/v1/conversations/{conversation_id}` — details/history with authorization.
- `POST /api/v1/conversations/{conversation_id}/messages` — submit user message and receive a final response, pending action, or safe error.

The send-message response should include `turn_id`, `status`, `assistant_message`, `tool_executions` summary, and optional `pending_action` metadata. Never expose unauthorized data or raw internal prompts.

## 12.3 Approval workflow
- `GET /api/v1/pending-actions` — list actions the authenticated supervisor/user is authorized to review.
- `POST /api/v1/pending-actions/{action_id}/approve` — require authenticated approval and idempotent execution.
- `POST /api/v1/pending-actions/{action_id}/reject` — reject and record who/when.
- `GET /api/v1/pending-actions/{action_id}` — inspect proposal and status.

Approval must be a server-side state transition. A repeated approve request must not execute the action twice.

## 12.4 Execution trace
- `GET /api/v1/turns/{turn_id}/trace` — step list with redacted inputs, validation results, tool outputs, durations and failures.
- `GET /api/v1/tool-executions/{execution_id}` — authorized single execution detail.

## 12.5 Evaluation
- `GET /api/v1/benchmarks` — list prior runs.
- `POST /api/v1/benchmarks` — run a benchmark from an approved dataset split/configuration; require evaluator/admin access.
- `GET /api/v1/benchmarks/{run_id}` — aggregate result and status.
- `GET /api/v1/benchmarks/{run_id}/errors` — categorized error cases.
- `GET /api/v1/benchmarks/{run_id}/export` — export CSV/JSON report.

## 12.6 API errors
Use standard statuses: 400 malformed request, 401 unauthenticated, 403 unauthorized, 404 not found (without leaking protected record existence when inappropriate), 409 state/idempotency conflict, 422 input/schema validation, 429 rate/budget limit, 500 unexpected internal failure, 503 model/database unavailable, 504 timed-out operation. The error body should have `code`, safe `message`, `request_id`, and optional field-level validation details.

# 13. Front-end requirements

Build a clean responsive React + TypeScript interface. Prioritize clarity and explainability over decorative effects.

## 13.1 Required screens

1. **Dashboard:** project description, service/backend status, current model and adapter labels, recent tasks, and real benchmark summaries. Never display fabricated metrics as if real.
2. **Assistant workspace:** chat history, user message composer, tool execution timeline, returned results, final answer, pending approval card, clarification UI and clear error states.
3. **Action review:** proposed ticket/action details, policy checks, approve/reject controls, authenticated reviewer identity and execution result after approval.
4. **Trace detail:** chronological model/action/tool events, normalized arguments, schema validation, authorization result, tool return summary and latency. Redact sensitive values.
5. **Benchmark lab:** choose baseline/prompted/fine-tuned model configurations, run a benchmark, compare metrics, inspect errors by scenario family and export results.
6. **Experiment history:** model revision, dataset and prompt versions, training configs, environment, status and artifact paths.
7. **Settings/health:** show safe config information and whether the system is running in real-model or deterministic-test mode.

## 13.2 UX requirements

- Clearly label simulated/demo data.
- Clearly label pending versus completed actions.
- Require explicit confirmation for state-changing actions.
- Show errors in plain language and allow safe retry when appropriate.
- Keep an accessible focus order, readable contrast, responsive layout and keyboard operation.
- Do not make color the only status indicator.
- Do not show “confidence 99%” unless it is genuinely calibrated; prefer statuses such as `verified by tool`, `needs clarification`, `pending approval` or `review required`.
- Do not expose system prompts, passwords, secret keys or other users' data.

# 14. Authentication, authorization and security

For a portfolio demo, security should be realistic but intentionally bounded.

- Use environment-based secrets and password hashes if credentials exist.
- Implement server-side user/role authorization and tenant scoping for all queries.
- Use synthetic records and document the demo credentials only in local development instructions, never as production secrets.
- Use request validation, body-size limits, rate limiting/budgets and timeouts.
- Restrict CORS to configured origins.
- Apply least privilege to the database account.
- Use parameterized SQL only; do not execute generated raw SQL.
- Redact secrets, personal data and full prompt contents from default logs.
- Keep a record of approval, rejection and state-change events.
- Treat all user inputs and tool outputs as untrusted. Use explicit separators/labels in prompts, but do not rely on prompt instructions alone as a security boundary.
- Maintain a tool allowlist and deny unknown tools.
- Apply separate policies to read-only and state-changing tools.
- Limit action count, execution time and retries.
- Test direct and indirect prompt injection, malformed model output, role bypass, cross-tenant access, unauthorized approval and replay/duplicate requests.
- Never include credentials, `.env` files, customer data or model access tokens in Git.
- Pin/scan dependencies and keep a software license inventory, including the selected model license.

# 15. Reliability and error handling

Required failure cases and behavior:

- Model not loaded/unavailable: show safe service-unavailable response; do not claim that work was completed.
- Model output invalid: retry once with a bounded correction instruction, then fail safely.
- Tool arguments invalid: reject tool call, log an error category, and ask for clarification or return a safe failure.
- Unknown order/item: state that the record wasn't found and ask the user to verify it; do not hallucinate details.
- Authorization denied: do not reveal protected record details.
- Tool timeout: bounded retry only for read-only/idempotent actions; do not retry a write action unless idempotency guarantees it.
- Database unavailable: do not state that a ticket exists or that a lookup succeeded.
- Contradictory policy or ambiguous eligibility: require human review.
- Repeated tool-call loop: stop at limits and return a safe message.
- Pending action expires: mark it expired and require a fresh proposal.
- Approve endpoint is retried: reuse the idempotency key and return the existing result, not a duplicate write.
- User cancels before approval: mark pending action rejected/cancelled and do not execute.

Use explicit domain exceptions and centralized exception handling. Do not catch all exceptions and silently return success. Retry only transient failures and set a retry budget.

# 16. Observability and operational metrics

Add structured logging with request/trace IDs. Record model generation duration, tool execution duration, total turn duration, number of tool calls, validation failures, retries, approvals, policy denials and outcome categories.

Add:
- Health and readiness endpoints.
- A simple `/metrics` or equivalent metrics endpoint for request counts, failures, latency and tool execution metrics.
- Correlation between conversation turn and model/tool events.
- Redaction helpers used before logging.
- A local dashboard for aggregate task and benchmark metrics.

Avoid storing hidden chain-of-thought. Store short action rationale summaries, tool selection, schema-validation and policy outcomes, tool result references, and user-visible explanations only.

# 17. Suggested repository structure

Use a single repository, with separate `backend`, `frontend`, and `experiments` folders. Adjust names if the chosen framework conventions require it, but preserve module boundaries.

```text
reliable-tool-using-llm/
  README.md
  LICENSE
  .gitignore
  .env.example
  docker-compose.yml
  Makefile
  docs/
    architecture.md
    security.md
    api.md
    dataset_card.md
    model_card.md
    experiment_protocol.md
    benchmark_report_template.md
    deployment.md
    demo_script.md
    decisions/
  backend/
    pyproject.toml
    alembic.ini
    alembic/
    app/
      main.py
      core/                 # settings, logging, security, exceptions
      api/v1/                # routes and dependencies
      schemas/               # Pydantic input/output models
      db/                    # SQLAlchemy base, session, migrations helpers
      models/                # ORM models
      repositories/          # database access
      services/              # conversations, approvals, policies, evaluation
      orchestrator/          # model-tool loop and limits
      llm/                   # interface and backend adapters
      tools/                 # registry, validation, execution, concrete tools
      observability/         # trace records, metrics, redaction
      seed/                  # deterministic synthetic data generation
      tests/
  frontend/
    package.json
    src/
      app/
      components/
      features/chat/
      features/approvals/
      features/traces/
      features/benchmarks/
      features/settings/
      lib/api.ts
      types/
  experiments/
    README.md
    configs/
    data_generation/
    datasets/.gitkeep
    training/
    evaluation/
    results/.gitkeep
    scripts/
  scripts/
    dev_setup.sh
    dev_setup.ps1
    run_checks.sh
    seed_demo_data.py
  .github/workflows/ci.yml
```

Do not commit large model weights, private datasets, or training outputs. Provide scripts and instructions to regenerate or retrieve them. Store adapter artifacts through a documented release or artifact directory with checksums.

# 18. Recommended technology stack

Use stable, maintained versions and pin versions after validating interoperability.

## Backend
- Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic.
- PostgreSQL for full-stack usage; SQLite may be used for isolated unit tests only where behavior is equivalent.
- HTTPX for outbound test/client calls.
- pytest and pytest-asyncio as needed.
- Ruff and mypy or pyright for linting/type checking.
- Structured logging (JSON format) and OpenTelemetry-compatible traces if practical.

## Model experimentation
- PyTorch, Hugging Face Transformers, Datasets, TRL, PEFT.
- bitsandbytes for QLoRA only when compatible with the selected environment.
- An inference/serving backend chosen after the feasibility test: Transformers is the default research backend; vLLM may be added for a supported GPU serving benchmark. Tool-calling options and parser requirements are model/template specific; follow official vLLM and model documentation.
- Use the official docs: https://huggingface.co/docs/trl/peft_integration, https://huggingface.co/docs/peft/developer_guides/quantization, https://docs.vllm.ai/en/stable/features/tool_calling/, and the selected model card.

## Frontend
- React + TypeScript, Vite, a consistent component system, a typed API client and accessible charts/tables.
- Keep charts based on actual saved benchmark data.

## Deployment
- Docker and Docker Compose for repeatable local setup.
- CI checks on pull requests.
- Document one practical deployment path for frontend/backend and a separate model-serving path if GPU inference is needed. It is acceptable for the model inference service to be external to the public web host; do not promise free always-on GPU hosting.

# 19. Environment configuration

Create `.env.example` and document each variable. Suggested variables:

```env
APP_ENV=development
APP_SECRET_KEY=replace-me
DATABASE_URL=postgresql+psycopg://app:app@db:5432/reliable_llm
CORS_ORIGINS=http://localhost:5173
MODEL_BACKEND=transformers
MODEL_ID=Qwen/Qwen3-1.7B
MODEL_REVISION=main-or-pinned-commit
ADAPTER_PATH=
MODEL_DEVICE=auto
MODEL_DTYPE=auto
MAX_MODEL_STEPS=5
MAX_TOOL_CALLS_PER_TURN=4
MODEL_TIMEOUT_SECONDS=60
TOOL_TIMEOUT_SECONDS=10
MAX_REPAIR_RETRIES=1
DEMO_AUTH_ENABLED=true
BENCHMARK_DATASET_VERSION=v1
LOG_LEVEL=INFO
```

These are example placeholders. Verify the actual supported values for the chosen backend. Pin an immutable model revision/commit for final benchmarks instead of relying on a moving `main` branch. Keep secrets out of source control. The app should validate configuration at startup and explain missing required configuration without printing secret values.

# 20. Testing plan

Tests are not optional. Include unit, integration, security, end-to-end and model-evaluation tests.

## 20.1 Unit tests
- Each tool returns a correct typed result for valid input.
- Each tool rejects malformed input and invalid enum values.
- Refund rules handle boundary dates, returned/delivered states, multiple items, discounts, taxes and rounding correctly.
- Unknown tool name is rejected.
- Role/tenant policies are enforced.
- Action schema parser rejects extra or malformed fields.
- Step, time and retry budgets are enforced.
- Idempotency logic prevents duplicate tickets.
- Log redaction removes configured sensitive fields.

## 20.2 Integration tests
- Full lookup-order conversation.
- Multi-tool refund-eligibility conversation.
- Missing information prompts for clarification.
- Ticket proposal returns pending state; ticket is not written before approval.
- Approval creates exactly one ticket.
- Repeated approval returns the same result.
- Rejected/expired action does not execute.
- Tool failure produces an honest safe response.
- Model service unavailable gives 503/safe UI state.
- DB authorization prevents cross-tenant access.

## 20.3 Security tests
- Prompt injection in user message asks model to ignore rules.
- Prompt injection embedded in order notes/tool result.
- Model attempts an unregistered tool.
- Model arguments attempt to select a different customer or tenant.
- Attempt to access another customer's order.
- Attempt to bypass approval or claim that the user approved.
- Replayed approval/action request.
- Oversized input and excessive tool-call loops.
- Sensitive data leakage from another session.
- SQL injection strings in user input/order code; parameterized queries must keep them inert.

## 20.4 End-to-end UI tests
- User can send a request and view a response.
- Execution trace is shown with correct status.
- Pending action allows approve/reject by authorized role only.
- Benchmark page can launch and display a run's true state.
- Error, loading, empty and no-model states are usable.

## 20.5 Model evaluation tests
- Tool name exact match.
- Required arguments exact match/field F1.
- Multi-step task success.
- Correct clarification and no-tool behavior.
- Invalid tool requests denied by executor.
- Regression report between base, prompted and fine-tuned configurations.

# 21. CI/CD and code quality

On every pull request or main-branch push:
1. Install pinned dependencies.
2. Run formatting/lint checks.
3. Run static typing checks for the backend.
4. Run unit and integration tests.
5. Run frontend type-check/build and unit tests.
6. Run dependency/security checks available in the repository.
7. Build container images.

CI must not download a multi-gigabyte model or require a GPU. Use a deterministic test model backend in CI and mark those tests clearly. Provide a separate manually run workflow for real-model integration/benchmarks. Never let CI's deterministic backend metrics appear in the genuine model benchmark dashboard.

# 22. Performance measurement

Do not state that the system is “fast,” “low-cost” or “production-ready” without measurements. Report:

- Hardware/CPU/GPU and RAM/VRAM.
- OS, Python, package versions, model revision, adapter revision and backend.
- Dataset split and number of cases.
- Warm-up procedure and concurrency level.
- p50/p95 total latency, model latency, tool latency, throughput if measured.
- Peak memory and quantization settings.
- Actual cloud cost if using paid GPU; clearly label estimates separately.
- Accuracy and task success before/after optimization.

If comparing quantized and unquantized inference, hold test prompts and decoding settings constant. Quantization can lower memory and sometimes improve throughput, but it may also degrade quality or have hardware-dependent behavior.

# 23. Deployment

Minimum required deployment modes:

## Local development
- `docker compose up --build` should start the API, database and frontend (or provide a clearly documented equivalent command).
- `.env.example` and seed command make setup reproducible.
- A deterministic test model can run the application for UI/backend development, and must be visibly labelled as test/simulation mode.
- Real-model mode requires the selected model to be installed/retrieved and the correct device/backend configured.

## Demonstration deployment
- Frontend and API can be deployed to ordinary web hosting/container hosting.
- Model inference may run as a separate service or locally for a live demo if free/affordable GPU hosting is not available.
- Use synthetic data only.
- Protect benchmark and admin endpoints.
- Document sleep/cold-start, GPU availability, model-loading latency, rate limits, and any recurring costs.

## Reproducible research run
- Provide a single documented command or script to validate data, run evaluation for each config, and export metrics to versioned JSON/CSV artifacts.
- Provide a training command/config to create the LoRA adapter, with checks before it spends significant GPU time.

# 24. Implementation phases and stop/go gates

The coding agent should implement phases in order. Each phase must pass its gate before major work begins in the next phase.

## Phase 0 — Repository inspection and feasibility
- Inspect existing repo/environment before modifying anything.
- Record hardware, Python/Node versions, GPU/VRAM visibility and disk space.
- Verify model licence and supported chat/tool template.
- Run model-load and one tool-call smoke test.
- Run a tiny LoRA/QLoRA smoke test in the chosen environment.
- Output: `docs/feasibility_report.md` with findings and exact model/runtime versions.
- Gate: model selection and compute plan are documented; if fine-tuning is blocked, do not claim it works—identify a feasible fallback.

## Phase 1 — Backend core and deterministic domain
- Create typed schemas, DB models/migrations, seed data, policy rules and tool registry.
- Implement tools and unit tests.
- Add authentication/role/tenant scope and idempotency.
- Gate: all tool/policy/security unit tests pass without any LLM.

## Phase 2 — Orchestrator and model adapter
- Implement model interface, test backend, real model adapter, normalized action parser, tool loop and budgets.
- Add trace persistence and safe error handling.
- Gate: core multi-step flows work with deterministic test backend; real model backend passes smoke test.

## Phase 3 — API and frontend
- Implement session/chat APIs, trace APIs, pending approvals and benchmark APIs.
- Build interface, approval flow, errors/loading/empty states and trace timeline.
- Gate: end-to-end UI and backend tests pass.

## Phase 4 — Dataset and benchmark baseline
- Implement deterministic dataset generation/validation/splitting.
- Run baseline A and prompt baseline B on validation/test with pinned configs.
- Implement error categorization and result export.
- Gate: test data is isolated and benchmark can be rerun reproducibly.

## Phase 5 — Fine-tuning experiment
- Run LoRA/QLoRA smoke test then full chosen experiment.
- Save adapter, training config/logs and artifact checksum.
- Evaluate fine-tuned model and compare against A/B.
- Gate: do not proceed to performance claims until evaluation artifacts exist.

## Phase 6 — Inference experiment
- Test quantization/alternate serving only if supported.
- Measure accuracy/memory/latency/throughput under a documented setup.
- Gate: record both benefits and regressions.

## Phase 7 — Hardening, docs and portfolio demo
- Complete security tests, regression checks, dependency scan and deployment docs.
- Write dataset card, model card and experiment report.
- Add screenshots/demo walkthrough and architecture diagram.
- Prepare resume bullet points based only on measured outcomes.
- Gate: fresh clone setup works from README; core tests pass; no fabricated metrics; all claimed features function.

# 25. Acceptance criteria for project completion

The project is complete only when all mandatory criteria below are met:

1. Fresh clone can be installed and run from documented instructions.
2. A user can complete order lookup, return-policy lookup, refund eligibility/estimate and support-ticket proposal flows through the UI.
3. State-changing ticket creation cannot occur before approval where required.
4. Unauthorized data access is blocked on the backend.
5. Tool names and arguments are validated; arbitrary code/raw SQL execution is not available.
6. Every turn has an inspectable trace with tool arguments/results redacted as appropriate, validation decisions and timing.
7. Deterministic test backend is clearly labelled and never presented as real model performance.
8. A real open-weight model can execute the main workflow in the documented configuration.
9. Dataset generator/validator and held-out benchmark are present.
10. At least baseline A and B evaluation results are saved. Fine-tuned configuration results are required if the training feasibility gate succeeds; if not, documentation must clearly state the blocker and must not claim completed fine-tuning.
11. Benchmark report gives metrics, denominators, model/dataset versions, environment and limitations.
12. Automated tests cover tool logic, approvals/idempotency, auth, safety and major user flows.
13. Docker/local deployment is reproducible.
14. README, architecture, security, API, dataset, model, experiment and deployment docs are present.
15. No real secrets or private customer data are committed.
16. No metric, accuracy gain or business impact is claimed without an actual saved experiment or test result.

# 26. README structure

The README should contain:
1. Project title and one-sentence value proposition.
2. Short demo GIF/screenshots or link if available.
3. Key features.
4. Architecture diagram.
5. Example workflow.
6. Tech stack.
7. Prerequisites and tested hardware.
8. Quick start and configuration.
9. Running database migrations and seed data.
10. Running tests and linters.
11. Running the app in test/simulation mode versus real-model mode.
12. Dataset creation, model training and benchmark commands.
13. Results table generated from actual experiment artifacts.
14. Threat model and safety limits.
15. Known limitations.
16. Project folder structure.
17. Model/dataset licenses and citations.
18. Roadmap limited to genuinely justified future improvements.

# 27. Required project deliverables

Deliver all of the following:

- Working full-stack application.
- Source code organized by modules.
- Seeded synthetic database and deterministic data-generation scripts.
- Versioned tool schemas and policy implementation.
- Model adapter interface and real-model integration.
- Fine-tuning script/config for LoRA/QLoRA where feasible.
- Locked benchmark test set and benchmark runner.
- Benchmark artifacts (JSON/CSV) and an analysis report.
- Automated unit/integration/security/end-to-end tests.
- Docker/Compose setup and CI workflow.
- `.env.example` without secrets.
- README, architecture doc, security doc, API doc, dataset card, model card, experiment protocol/report, deployment guide and demo script.
- A concise portfolio demonstration showing a normal tool task, a multi-step task, a blocked unsafe task, a pending approval and the benchmark comparison.

# 28. Portfolio and resume framing

Do not write resume bullets until the system and experiments exist. A future bullet can describe the engineering scope and measured outcomes, for example:

“Built a tool-using open-weight LLM system with schema-validated function calls, policy-gated actions, approval workflows and traceable execution; evaluated pretrained, prompt-engineered and LoRA-adapted variants on a held-out benchmark.”

Only add numerical metrics such as exact tool-call accuracy, task success, latency or memory after they have been produced by the benchmark and can be reproduced. Do not say “improved by X%” until there is an actual baseline and final measurement.

# 29. Things the coding agent must not do

- Do not silently change the project into another RAG chatbot.
- Do not add multi-agent orchestration or arbitrary tool execution.
- Do not replace fine-tuning with a hosted API call and claim model adaptation.
- Do not show invented benchmark charts or dummy “95% accuracy” metrics.
- Do not use real financial, customer or production data.
- Do not make state-changing calls based only on model text.
- Do not skip authorization or approval logic to make a demo easier.
- Do not overfit by changing the test set after seeing results.
- Do not lock the project to an unverified model/version/license.
- Do not attempt a large expensive training job before a small feasibility run succeeds.
- Do not create a huge microservice architecture for this portfolio project.
- Do not consider a page complete merely because it renders; connect it to working APIs and test its user flows.

# 30. Official technical references to consult during implementation

Use these official references and verify current compatibility/version details when building:

- Qwen3 tool/function calling guide: https://github.com/QwenLM/Qwen3/blob/main/docs/source/framework/function_call.md
- Qwen3-1.7B model card and license information: https://huggingface.co/Qwen/Qwen3-1.7B
- Qwen3-4B-Instruct-2507 model card and license information: https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507
- Hugging Face TRL PEFT/LoRA/QLoRA integration: https://huggingface.co/docs/trl/peft_integration
- Hugging Face PEFT quantization guide: https://huggingface.co/docs/peft/developer_guides/quantization
- vLLM tool-calling support and setup: https://docs.vllm.ai/en/stable/features/tool_calling/
- vLLM serving metrics: https://docs.vllm.ai/en/stable/usage/metrics/
- OWASP GenAI/LLM Top 10: https://owasp.github.io/www-project-top-10-for-large-language-applications/
- OWASP Excessive Agency guidance: https://genai.owasp.org/llmrisk/llm062025-excessive-agency/

These references are guidance, not permission to ignore model-specific licenses or environment compatibility.

# 31. Final instruction to the coding agent

Build **P2 — Reliable Tool-Using LLM for Business Operations** as specified above. First inspect the existing environment and write the feasibility report. Then implement phases in order and keep the application runnable throughout development. Use small commits or clearly separated stages. Run tests after each meaningful change. Produce actual working code and documentation, not just a plan.

The project succeeds by demonstrating reliable, permission-aware tool use and experimentally measured model behavior—not by having the largest model, the most tools, or the most frameworks. Preserve scope, be honest about limitations, and do not make performance claims without reproducible evidence.
