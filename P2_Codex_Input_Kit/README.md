# P2 Codex Input Kit

This is the instruction package for building **P2 — Reliable Tool-Using LLM for Business Operations** with Codex. It is not the finished software application.

## Start using it

1. Extract the ZIP.
2. Open the extracted folder in Codex as the workspace (or copy these files into the existing project repo, preserving existing work).
3. Open `START_HERE.md` and follow its instructions. The easiest route is to paste the full contents of `prompts/CODEX_BOOTSTRAP_PROMPT.txt` into Codex.
4. Let Codex inspect the environment, create the feasibility report, and proceed through the implementation plan. It should keep `docs/PROGRESS.md` updated.
5. Review the final handoff and run commands Codex provides. Do not treat blocked model-training work as complete.

## Package contents

- `START_HERE.md`: main build instructions for the coding agent.
- `AGENTS.md`: persistent repository rules.
- `docs/P2_BUILD_SPEC.md`: full locked A-to-Z project specification.
- `docs/IMPLEMENTATION_PLAN.md`: phased implementation and stop/go gates.
- `docs/ACCEPTANCE_CHECKLIST.md`: evidence-based definition of done.
- `docs/PROGRESS_TEMPLATE.md`: template for the working progress log.
- `config/project_manifest.json`: machine-readable project scope and constraints.
- `config/action_envelope.schema.json`: JSON Schema for normalized model actions.
- `config/benchmark_config.example.json`: example configuration for reproducible model comparisons.
- `prompts/CODEX_BOOTSTRAP_PROMPT.txt`: paste-ready first prompt for Codex.

## Important

The kit tells Codex what to build; it does not itself contain the finished application. Model availability, GPU access, external accounts and dependency compatibility can affect model or fine-tuning execution. The application must remain honest about what ran and what is blocked.
