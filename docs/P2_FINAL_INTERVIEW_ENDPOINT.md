# P2 Final Interview Endpoint

**Presentation endpoint:** V4 controller experiment and the current bounded local-Qwen application smokes.  
**Project acceptance status:** **PARTIAL**.  
**Scope:** Documentation freeze for interview presentation; no new implementation or benchmark is implied.

## The ending point to present

Present P2 as a **working local prototype for safe, synthetic customer-support operations**, with an opt-in controller that achieved the strongest recorded safety-gated offline replay score in this project. Do not present P2 as a 96.4%-accurate production agent or as having passed its original acceptance criteria.

## Best result by evidence type

| Evidence type | Best relevant result | Proper interpretation |
|---|---:|---|
| V4 controller offline development replay | **27/28 (96.4%)** exact actions; 17/18 tool choices; 15/16 exact arguments; zero unexpected write proposals | Highest recorded safety-gated replay score. 28 distinct cores/16 families, internal AI-authored labels. Saved model proposals were replayed; no tools or database operations executed. |
| V4 separate small final set | **16/18 (88.9%)** exact actions; zero unexpected write proposals | More cautious indicator; 18 distinct cores/17 families, AI-authored labels, below the 90% action target. This is not an independently reviewed external holdout. |
| V4 real FastAPI smoke | **8/8** fixed synthetic workflow checks | Actual local Qwen and registered-tool execution, including lookup, policy, eligibility, clarification, injection handoff, tenant denial and ticket approval/replay. It is a fixed smoke suite, not a broad test. |
| Later structured-intent real-model smokes | **17/17** checks across three selected workflows | Actual lookup, estimate and ticket approval/idempotency paths. These are curated integration smokes and have no broad comparison denominator. |
| Broadest later actual-app slice with highest historical pass count | Recovery V1 **34/42** | Internal synthetic application checks on a different suite; later recovery runs were 28/42. Do not compare as a paired version test or treat as a generalization score. |
| Original frozen V5 acceptance evidence | Raw model **25/150**; V2 replay **31/150**; clarifications **6/43** | Official historical scores remain unchanged and below targets. Replay is offline. V5 also has prompt/gold ID conflicts and repeated cores documented in the forensic audit. |

## Interview-ready summary

> “I built a local tool-using support prototype over synthetic e-commerce data. The application validates actions, limits execution to registered tools, enforces tenant and business rules server-side, and requires supervisor approval with idempotency for ticket creation. My strongest controller result was 27/28 exact actions (96.4%) on a small exploratory development replay with no unexpected write proposals. Because that replay did not execute tools and its labels were internally authored, I also report the separate 18-core result of 16/18 and the bounded real-application smokes. The overall project remains partial: broad independent evaluation and the original quality targets were not met.”

## Recommended five-minute demonstration

1. Show the project architecture and synthetic-only boundary.
2. Use local Ollama and look up `ORD-10021`; show the registered tool trace and database-grounded status.
3. Propose a support ticket; show that it is pending and that no ticket row exists before supervisor approval.
4. Approve once as supervisor, repeat the approval request, and show the same ticket ID/one row.
5. Show the experiment table in this document or the V4 report. Explain the difference between the 96.4% offline replay and the 8/8 actual-app smoke, then disclose the 88.9% separate-set result and PARTIAL verdict.

Use the [demo runbook](DEMO_RUNBOOK.md) for setup. Confirm that the interface labels the backend as Ollama/Qwen before calling it real-model behavior. If startup or the model stalls, present the saved artifacts and explain the bounded local-runtime limitation; do not switch to the deterministic test backend and call it an LLM result.

## Questions to answer plainly

**What does 96.4% mean?** The V4 controller's final action matched the internally authored expected action on 27 of 28 development replay rows using saved Qwen proposals. It measures controller action selection on that set, not model accuracy or task completion.

**Why is the project still partial?** The separate 18-core V4 set scored 88.9%, labels were not independently reviewed, the original frozen V5 goals remain unmet, broad real-app reliability was not established, and the fresh V7/V8 comparison did not finish.

**What is real and what is simulated?** Ollama/Qwen is a real local model; the application and tools ran against synthetic SQLite records. The deterministic CI backend is a test fixture and is not included as model evidence. No production customers, payments, or external business systems are connected.

**Why stop here?** This is the chosen interview endpoint. It presents the strongest useful engineering result plus its failure analysis and limitations without extending the project or overstating evidence.

## Evidence links

- Full V4 experiment and limitations: [P2 V4 controller reliability report](P2_CONTROLLER_V4_EXPERIMENT_REPORT.md)
- Current actual model smokes: [structured-intent workflow evidence](STRUCTURED_INTENT_WORKFLOW.md)
- Historical result comparison: [longitudinal root-cause report](P2_LONGITUDINAL_ROOT_CAUSE_REPORT.md)
- Current acceptance state: [acceptance checklist](ACCEPTANCE_CHECKLIST.md)
- Current demo steps: [demo runbook](DEMO_RUNBOOK.md)

## Stop decision

No further model, controller, dataset or benchmark work is planned for this interview endpoint. Historical results and defaults remain as recorded; V4 and the structured-intent candidate are opt-in. The overall verdict remains **PARTIAL**, not PASS or 100% completion.
