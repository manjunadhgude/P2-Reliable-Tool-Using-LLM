# Demo script

1. Sign in as `agent`; ask `Where is order ORD-10021?` and inspect the trace.
2. Ask `Can I return items from ORD-10022?` and review deterministic eligibility.
3. Ask `Estimate the refund for ORD-10022`; inspect the Decimal breakdown and estimate-only note.
4. Propose a ticket for `ORD-10021`; verify it remains pending.
5. Sign in as `supervisor`, approve it, and verify the ticket result. Repeating approval returns the existing outcome.
6. Sign in as `evaluator` and run validation. The result identifies fixture behavior, not LLM performance.
