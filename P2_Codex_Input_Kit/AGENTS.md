# AGENTS.md — Rules for this repository

## Mission and scope
Implement P2 — **Reliable Tool-Using LLM for Business Operations**. The authoritative specification is `docs/P2_BUILD_SPEC.md`. Read it before significant changes. Scope is deliberately limited to synthetic e-commerce customer support/order operations and the six specified business tools.

## Mandatory rules
- Make the application usable end-to-end. A visual mockup, scaffold, or architecture-only result is not completion.
- Keep the code modular and understandable. Prefer a modular monolith over microservices.
- Inspect existing work before changing files. Avoid destructive changes and never overwrite unrelated work.
- Keep API contracts, database migrations, tool schemas and docs in sync.
- Validate all model-generated output with strict typed schemas. Reject unknown tools, invalid arguments, unknown properties and malformed actions.
- Server-side authorization and business rules are authoritative. Never rely on prompts or the frontend for permissions, refund eligibility, calculations, approvals or tenant isolation.
- Only registered tools may execute. No shell execution, `eval`, unrestricted HTTP, raw model-generated SQL, or arbitrary Python/code execution is exposed to the model.
- Any state-changing operation must be pending until the authenticated user explicitly approves it through a server-side approval endpoint. Model text is never proof of approval. Use idempotency keys to prevent duplicate tickets.
- Treat user messages and tool outputs as untrusted input. Defend against prompt injection and attempts to bypass policy.
- Use fake, seeded data only. Never add real customer or payment data or real external financial actions.
- Bound model steps, tool calls, tokens, timeouts and retries. Fail closed if a security or policy decision cannot be made.
- Keep useful execution traces and audit events, but never store hidden chain-of-thought. Redact sensitive values from logs.
- Clearly identify test/simulated backends. Never represent test fixtures as real model output or real benchmark metrics.
- Never invent accuracy, latency, costs, throughput, improvements, training results, tests or deployment status. Reports must derive from saved run artifacts.
- Keep a locked, isolated test split. Do not tune against the held-out test set or quietly omit difficult cases.
- Do not claim fine-tuning happened unless training actually ran, the adapter was saved and reloaded, and evaluation artifacts exist.
- Do not spend money, start paid cloud resources, or use external credentials without explicit user authorization.
- Use `.env.example`; never commit secrets. Add appropriate `.gitignore` rules.
- Pin tested dependencies and document exact versions and known compatibility constraints.
- Update `docs/PROGRESS.md` with decisions, commands, results, failures and next action.

## Working style
- Make a short plan, then act. Do not stop after returning a plan.
- Work in small, verifiable stages. Run relevant tests after each meaningful change and fix failures before continuing.
- Do not ask the user routine technical preference questions; choose a sensible default consistent with the spec.
- If blocked by unavailable hardware, credentials, paid resources, or current model support, record the evidence and blocker, keep building the parts that can work, and document honest alternatives.
- No dead UI controls. Every displayed action should work or be explicitly disabled with a useful explanation.
- Use accessible UI states: loading, empty, success, validation error, server error, and pending approval.
- Do not add GraphRAG, generalized RAG, multi-agent orchestration, voice, OCR/VLM, real email/payment integrations, or unrelated features unless a concrete acceptance requirement cannot otherwise be met.

## Completion protocol
Before declaring completion:
1. Run all feasible automated tests and linters.
2. Run the documented smoke test and end-to-end workflow.
3. Validate database migrations and seed scripts from a clean state if feasible.
4. Verify that unapproved ticket actions cannot execute and that idempotency works.
5. Verify test backend labelling and benchmark data provenance.
6. Verify docs and quick-start commands against the current code.
7. Update `docs/ACCEPTANCE_CHECKLIST.md` with evidence. Unmet items remain unchecked and explain why.
8. Give the user exact commands to install, configure, run, test and launch the real model backend.
