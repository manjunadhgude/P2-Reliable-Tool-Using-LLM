import csv
import hashlib
import io
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user, issue_token, require_role
from app.core.config import settings
from app.core.db import Base, SessionLocal, engine, get_db
from app.hybrid_controller import HybridController, ITEM_ID_RE, ORDER_ID_RE
from app.hybrid_controller_v4_candidate import HybridControllerV4Candidate
from app.hybrid_controller_v5_candidate import HybridControllerV5Candidate
from app.hybrid_controller_v6_candidate import HybridControllerV6Candidate
from app.hybrid_controller_v7_candidate import HybridControllerV7Candidate
from app.hybrid_controller_v8_candidate import HybridControllerV8Candidate
from app.intent_workflow import StructuredIntentWorkflowController
from app.llm.backends import DeterministicTestBackend, OllamaModelBackend, TransformersModelBackend
from app.models import AuditEvent, BenchmarkRun, Conversation, Message, PendingAction, ToolExecution, Turn, User
from app.observability.redaction import redact_sensitive
from app.schemas import Clarification, ConversationCreate, FinalAnswer, Handoff, LoginRequest, MessageCreate, TicketProposal, ToolCall
from app.seed import seed_database
from app.tools.domain import ARGUMENT_SCHEMAS, TicketArgs, create_ticket_after_approval, execute_read_tool, validate_read_result
from app.tools.registry import TOOL_REGISTRY


app = FastAPI(title=settings.app_name, version="0.1.0", description="Synthetic demo data only; no external financial actions.")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])
Base.metadata.create_all(bind=engine)
with SessionLocal() as _db:
    seed_database(_db)

_test_backend = DeterministicTestBackend()
_real_backend = None


def backend():
    global _real_backend
    if settings.model_backend == "deterministic_test":
        return _test_backend
    if settings.model_backend == "transformers":
        if _real_backend is None:
            _real_backend = TransformersModelBackend(settings.model_id, settings.model_revision,
                timeout_seconds=settings.request_timeout_seconds, max_new_tokens=settings.model_max_new_tokens,
                repair_retries=settings.max_output_repair_retries)
        return _real_backend
    if settings.model_backend == "ollama":
        if _real_backend is None:
            _real_backend = OllamaModelBackend(settings.model_id, settings.ollama_url,
                settings.request_timeout_seconds, settings.model_max_new_tokens)
        return _real_backend
    raise RuntimeError("MODEL_BACKEND must be deterministic_test, transformers, or ollama")


def safe_json(value):
    return json.loads(json.dumps(value, default=str))


def grounded_tool_response(tool: str, result: dict) -> str | None:
    """Render only direct authoritative read fields without another model call."""
    if not isinstance(result, dict):
        return None
    if tool == "lookup_order" and result.get("order_id") and result.get("status"):
        delivery = f" Expected delivery is {result['expected_delivery_date']}." if result.get("expected_delivery_date") else ""
        return f"Order {result['order_id']} is {str(result['status']).replace('_', ' ')}.{delivery}"
    if tool == "get_return_policy" and isinstance(result.get("policy_text"), str):
        policy_text = result["policy_text"].strip()
        if policy_text:
            category = result.get("category")
            prefix = f"{str(category).replace('_', ' ').capitalize()} return policy: " if isinstance(category, str) and category else "Return policy: "
            suffix = f" (Policy {result['version']}, as of {result['as_of']})." if isinstance(result.get("version"), str) and isinstance(result.get("as_of"), str) else "."
            return f"{prefix}{policy_text}{suffix}"
    if tool == "list_order_items" and result.get("order_id") and isinstance(result.get("items"), list):
        ids = [str(item.get("item_id")) for item in result["items"] if item.get("item_id")]
        return f"Order {result['order_id']} contains {', '.join(ids)}." if ids else f"Order {result['order_id']} has no listed items."
    if tool == "check_refund_eligibility" and result.get("order_id") and isinstance(result.get("items"), list):
        statuses = "; ".join(f"{item.get('item_id')}: {str(item.get('eligibility', 'unknown')).replace('_', ' ')}" for item in result["items"])
        return f"Eligibility for order {result['order_id']}: {statuses}."
    if tool == "calculate_refund_estimate" and result.get("order_id") and result.get("estimated_total") is not None:
        return f"The estimated refund for order {result['order_id']} is ${result['estimated_total']}."
    return None


def grounded_workflow_response(executions: list[dict], *, requested_estimate: bool = False) -> str | None:
    """Render multi-step business answers only from successful tool evidence."""
    if not executions:
        return None
    failed = next((item for item in executions if item.get("status") != "succeeded"), None)
    if failed is not None:
        successful = [item for item in executions if item.get("status") == "succeeded"]
        partial = grounded_workflow_response(successful, requested_estimate=requested_estimate)
        if partial is None and successful and successful[-1].get("tool_name") == "list_order_items":
            partial = grounded_tool_response(successful[-1].get("tool_name", ""), successful[-1].get("result", {}))
        if partial is None:
            return None
        tool_name = failed.get("tool_name", "requested step")
        return f"{partial} The {tool_name.replace('_', ' ')} step could not be completed."
    final = executions[-1]
    result = final.get("result")
    if not isinstance(result, dict):
        return None

    if final.get("tool_name") == "check_refund_eligibility":
        order_id, items = result.get("order_id"), result.get("items")
        if not isinstance(order_id, str) or not isinstance(items, list) or not items:
            return None
        checked = []
        for item in items:
            if not isinstance(item, dict) or not all(
                isinstance(item.get(key), str) for key in ("item_id", "eligibility", "reason_code")
            ):
                return None
            checked.append(
                f"{item['item_id']}: {item['eligibility'].replace('_', ' ')} "
                f"({item['reason_code'].replace('_', ' ').lower()})"
            )
        response = f"Eligibility for order {order_id}: " + "; ".join(checked) + "."
        if result.get("policy_version"):
            response += f" Rules version: {result['policy_version']}."
        if requested_estimate and all(item["eligibility"] != "eligible" for item in items):
            response += " No refund estimate applies because none of the checked items is eligible."
        return response + " Eligibility follows the demo return rules; damaged items may require human review."

    if final.get("tool_name") == "calculate_refund_estimate":
        money_fields = ("subtotal", "discounts", "taxes", "estimated_total")
        if not isinstance(result.get("order_id"), str) or not isinstance(result.get("currency"), str):
            return None
        if any(not isinstance(result.get(key), str) for key in money_fields):
            return None
        rows = result.get("items")
        if not isinstance(rows, list) or not rows or any(
            not isinstance(row, dict) or not isinstance(row.get("item_id"), str)
            or not isinstance(row.get("estimate"), str) for row in rows
        ):
            return None
        item_summary = ", ".join(
            f"{row['item_id']} ({result['currency']} {row['estimate']})" for row in rows
        )
        eligibility_rows = next((
            execution["result"].get("items") for execution in reversed(executions[:-1])
            if execution.get("tool_name") == "check_refund_eligibility"
            and isinstance(execution.get("result"), dict)
        ), [])
        excluded = [
            f"{row['item_id']} is {row['eligibility'].replace('_', ' ')}"
            for row in eligibility_rows if isinstance(row, dict)
            and isinstance(row.get("item_id"), str) and isinstance(row.get("eligibility"), str)
            and row["eligibility"] != "eligible"
        ]
        exclusion_note = (" Eligibility results: " + "; ".join(excluded) + ".") if excluded else ""
        return (
            f"For order {result['order_id']}, the estimate covers {item_summary}. "
            f"Subtotal: {result['currency']} {result['subtotal']}; discounts: {result['currency']} "
            f"{result['discounts']}; taxes: {result['currency']} {result['taxes']}; "
            f"estimated total: {result['currency']} {result['estimated_total']}. "
            f"This is an estimate only; no refund is issued.{exclusion_note}"
        )
    return None


def guard_untraced_business_claim(answer: str, *, executions: list[dict], pending: dict | None,
                                 controller, request_text: str) -> str:
    """Do not let free text invent business state or deny registered capabilities."""
    import re

    completed_state = re.compile(
        r"\b(ticket|refund|refund amount|payment)\b.{0,50}\b(created|filed|submitted|approved|issued|processed|refunded)\b|"
        r"\b(created|filed|submitted|approved|issued|processed|refunded)\b.{0,50}\b(ticket|refund|payment)\b",
        re.IGNORECASE,
    )
    negated_state = re.search(r"\b(not|never|hasn't|haven't|didn't|wasn't|was not)\b.{0,35}\b(created|filed|submitted|approved|issued|processed|refunded)\b", answer, re.IGNORECASE)
    if completed_state.search(answer) and not negated_state and not executions and pending is None:
        return "I can't confirm that a business action occurred because this request has no matching action record."

    unavailable_tracking = re.search(
        r"\b(no|not|don't|do not|cannot|can't|without)\b.{0,60}\b(tracking|delivery status|order status)\b.{0,40}\b(tool|access|available|support)\b|"
        r"\b(no|not|don't|do not|cannot|can't|without)\b.{0,40}\b(tool|access|available|support)\b.{0,40}\b(tracking|delivery status|order status)\b|"
        r"\btools?\s+(?:do not|don't|does not|doesn't)\s+(?:include|support|provide)\b.{0,70}\b(tracking|delivery status|order status)\b|"
        r"\bno\s+(?:registered\s+)?(?:tool|function|capability)\b.{0,70}\b(tracking|delivery status|order status)\b",
        answer, re.IGNORECASE,
    )
    if unavailable_tracking and "lookup_order" in TOOL_REGISTRY:
        return "I can check the order status. Please provide the order ID."

    intent = controller._intent(request_text) if controller is not None else None
    business_terms = re.search(
        r"\b(order|delivery|tracking|return|refund|eligibility|item|product|support ticket)\b",
        request_text, re.IGNORECASE,
    )
    if intent is None and business_terms and not executions and pending is None:
        return "Which supported order or support operation would you like help with?"
    return answer


def add_audit(db: Session, user: User, action: str, resource_id: str | None, details: dict | None = None):
    db.add(AuditEvent(tenant_id=user.tenant_id, actor_id=user.id, action=action, resource_id=resource_id, details=details or {}))


def controller_proposal_details(raw: dict | None, validated: dict | None) -> dict:
    """Keep action routing evidence; omit model free text and redact argument data."""
    if raw is None:
        return {"proposal_action_type": None, "proposal_tool_name": None,
                "proposal_arguments": None, "proposal_envelope_valid": None}
    if not isinstance(raw, dict):
        return {"proposal_action_type": None, "proposal_tool_name": None,
                "proposal_arguments": None, "proposal_envelope_valid": False}
    arguments = raw.get("arguments")
    tool_name = raw.get("tool_name")
    if isinstance(arguments, dict) and tool_name in ARGUMENT_SCHEMAS:
        allowed = set(ARGUMENT_SCHEMAS[tool_name].model_fields)
        sanitized = redact_sensitive({key: value for key, value in arguments.items() if key in allowed})
    else:
        sanitized = None
    if sanitized is not None and len(json.dumps(sanitized, default=str)) > 4000:
        sanitized = {"omitted": "argument_payload_over_trace_limit"}
    action_type = raw.get("action_type")
    return {
        "proposal_action_type": action_type[:48] if isinstance(action_type, str) else None,
        "proposal_tool_name": tool_name[:48] if isinstance(tool_name, str) else None,
        "proposal_arguments": sanitized,
        "proposal_envelope_valid": validated is not None,
    }


def controller_validation_failure(reason: str | None) -> str | None:
    failure_categories = {
        "unknown_or_non_read_tool", "tool_arguments_not_an_object", "tool_unknown_argument",
        "tool_required_order_id_unavailable", "tool_required_item_ids_unavailable", "tool_arguments_invalid",
        "ticket_proposal_not_validly_supplied", "ticket_arguments_not_an_object", "ticket_unknown_argument",
        "ticket_required_fields_invalid", "model_proposal_unavailable_or_invalid",
    }
    return reason if reason in failure_categories else None


@app.get("/health/live")
def live():
    return {"status": "alive"}


@app.get("/health/ready")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(select(User.id).limit(1)).first()
        model_ready = settings.model_backend == "deterministic_test" or _real_backend is not None
        return {"status": "ready" if model_ready else "degraded", "database": "ready", "model_backend": settings.model_backend, "model_ready": model_ready}
    except Exception:
        raise HTTPException(503, detail={"code": "database_unavailable", "message": "The database is not ready."})


@app.get("/api/v1/system/info")
def system_info():
    test = settings.model_backend == "deterministic_test"
    hybrid_enabled = settings.model_backend == "ollama" and settings.hybrid_controller_enabled
    return {"app_version": "0.1.0", "backend_type": settings.model_backend,
            "backend_label": "Deterministic test backend — not an LLM" if test else f"Open-weight model ({settings.model_backend})",
            "controller_mode": settings.hybrid_controller_version if hybrid_enabled else "model_only_or_backend_default",
            "model_id": "Deterministic fixture rules" if test else settings.model_id,
            "model_revision": None if test or settings.model_backend == "ollama" else settings.model_revision,
            "adapter_revision": None, "synthetic_data": True, "external_actions": False,
            "capabilities": {"tool_calls": True, "approvals": True, "benchmarks": True}}


@app.post("/api/v1/auth/demo-session")
def demo_session(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == body.username, User.active.is_(True)))
    if user is None:
        raise HTTPException(401, detail={"code": "invalid_demo_user", "message": "Unknown demo user."})
    return {"access_token": issue_token(user), "token_type": "bearer", "user": {"id": user.id, "username": user.username, "display_name": user.display_name, "role": user.role}, "expires_in_seconds": 43200}


@app.get("/api/v1/auth/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "display_name": user.display_name, "role": user.role, "tenant_id": user.tenant_id}


@app.post("/api/v1/conversations")
def create_conversation(body: ConversationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conversation = Conversation(tenant_id=user.tenant_id, user_id=user.id, title=body.title)
    db.add(conversation)
    db.commit()
    return {"id": conversation.id, "title": conversation.title, "created_at": conversation.created_at}


@app.get("/api/v1/conversations")
def list_conversations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Conversation).where(Conversation.tenant_id == user.tenant_id, Conversation.user_id == user.id).order_by(Conversation.created_at.desc())).all()
    return [{"id": x.id, "title": x.title, "created_at": x.created_at} for x in rows]


@app.get("/api/v1/conversations/{conversation_id}")
def get_conversation(conversation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.tenant_id == user.tenant_id, Conversation.user_id == user.id))
    if not conversation:
        raise HTTPException(404, detail={"code": "conversation_not_found", "message": "Conversation not found."})
    messages = db.scalars(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)).all()
    return {"id": conversation.id, "title": conversation.title, "messages": [{"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at} for m in messages]}


def validate_action(raw: dict) -> dict:
    kind = raw.get("action_type") if isinstance(raw, dict) else None
    required = {"tool_call": {"action_type", "tool_name", "arguments", "reason_summary"},
                "propose_state_change": {"action_type", "tool_name", "arguments", "reason_summary"},
                "final_answer": {"action_type", "answer", "claims", "needs_human_review"},
                "clarification": {"action_type", "question", "missing_fields"},
                "handoff": {"action_type", "reason", "user_safe_message"}}
    optional = {"tool_call": {"confidence"}, "propose_state_change": {"confidence"},
                "final_answer": {"confidence"}, "clarification": {"confidence"}, "handoff": set()}
    if kind not in required or set(raw) - required[kind] - optional[kind] or required[kind] - set(raw):
        raise ValueError("Malformed or unknown action envelope.")
    action_models = {"tool_call": ToolCall, "propose_state_change": TicketProposal,
                     "final_answer": FinalAnswer, "clarification": Clarification, "handoff": Handoff}
    raw = action_models[kind].model_validate(raw).model_dump()
    if kind == "tool_call" and (raw["tool_name"] not in TOOL_REGISTRY or TOOL_REGISTRY[raw["tool_name"]].side_effect):
        raise ValueError("Tool is not registered as a read-only action.")
    if kind == "propose_state_change" and (raw["tool_name"] not in TOOL_REGISTRY or not TOOL_REGISTRY[raw["tool_name"]].approval_required):
        raise ValueError("State-changing tool is not registered.")
    return raw


def execute_for_turn(db: Session, user: User, turn: Turn, tool_name: str, args: dict) -> dict:
    started = time.perf_counter()
    metadata = TOOL_REGISTRY[tool_name]
    deadline = getattr(turn, "deadline_monotonic", None)
    if turn.tool_calls >= max(0, settings.max_tool_calls):
        result, status = {"error": "This turn reached its tool-call limit."}, "budget_exceeded"
    elif deadline is not None and time.perf_counter() >= deadline:
        result, status = {"error": "This turn reached its time limit."}, "timeout"
    elif user.role not in metadata.required_roles:
        result, status = {"error": "This role is not authorized for the requested tool."}, "denied"
    else:
        try:
            result = validate_read_result(tool_name, execute_read_tool(db, user, tool_name, args))
            status = "succeeded"
        except LookupError as exc:
            result, status = {"error": str(exc)}, "not_found"
        except ValueError as exc:
            result, status = {"error": str(exc)}, "rejected"
        except Exception:
            result, status = {"error": "The tool request could not be validated."}, "validation_failed"
    ms = int((time.perf_counter() - started) * 1000)
    turn.tool_calls += 1
    if ms > metadata.timeout_seconds * 1000 and status == "succeeded":
        result, status = {"error": "The read tool exceeded its time budget."}, "timeout"
    auth_status = "denied" if status == "denied" else "allowed"
    record = ToolExecution(turn_id=turn.id, tool_name=tool_name, arguments=redact_sensitive(args), validation_status="valid" if status != "validation_failed" else "invalid", authorization_status=auth_status, result_status=status, result_summary=redact_sensitive(result), duration_ms=ms)
    db.add(record)
    db.flush()
    return {"execution_id": record.id, "tool_name": tool_name, "status": status, "result": result, "duration_ms": ms}


@app.post("/api/v1/conversations/{conversation_id}/messages")
def send_message(conversation_id: str, body: MessageCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.tenant_id == user.tenant_id, Conversation.user_id == user.id))
    if not conversation:
        raise HTTPException(404, detail={"code": "conversation_not_found", "message": "Conversation not found."})
    user_message = Message(conversation_id=conversation.id, role="user", content=body.content)
    turn = Turn(conversation_id=conversation.id, status="running")
    db.add_all([user_message, turn])
    db.flush()
    request_started = time.perf_counter()
    turn.deadline_monotonic = request_started + max(1, settings.request_timeout_seconds)
    hybrid_enabled = settings.model_backend == "ollama" and settings.hybrid_controller_enabled
    controller = None
    if hybrid_enabled:
        if settings.hybrid_controller_version == "v4_candidate":
            controller = HybridControllerV4Candidate()
        elif settings.hybrid_controller_version == "v5_candidate":
            controller = HybridControllerV5Candidate()
        elif settings.hybrid_controller_version == "v6_candidate":
            controller = HybridControllerV6Candidate()
        elif settings.hybrid_controller_version == "v7_candidate":
            controller = HybridControllerV7Candidate()
        elif settings.hybrid_controller_version == "v8_candidate":
            controller = HybridControllerV8Candidate()
        elif settings.hybrid_controller_version == "structured_intent_candidate":
            controller = StructuredIntentWorkflowController()
        elif settings.hybrid_controller_version == "v2":
            controller = HybridController()
        else:
            raise HTTPException(500, detail={"code": "invalid_controller_version", "message": "Unsupported controller version."})
    controller_decision = None
    proposal = None
    raw_proposal = None
    model_call_count = 0
    model_call_durations_ms = []
    controller_duration_ms = 0
    workflow_text = body.content
    structured_intent = None
    try:
        if controller is not None:
            history_messages = db.scalars(select(Message).where(
                Message.conversation_id == conversation.id,
                Message.id != user_message.id,
            ).order_by(Message.created_at, Message.id)).all()
            history = [{"role": m.role, "content": m.content} for m in history_messages]
            started_controller = time.perf_counter()
            controller_decision = controller.preflight(body.content, history)
            controller_duration_ms += (time.perf_counter() - started_controller) * 1000
            if isinstance(controller, StructuredIntentWorkflowController) and controller_decision is None:
                if settings.max_model_steps < 1:
                    raise TimeoutError("Model-step budget is zero.")
                model_call_count += 1
                turn.model_steps += 1
                started_model = time.perf_counter()
                try:
                    active_text, _ = HybridController._active_context(body.content, history)
                    structured_intent = backend().interpret_intent(active_text)
                finally:
                    model_call_durations_ms.append(round((time.perf_counter() - started_model) * 1000, 3))
                raw_proposal = {"action_type": "intent_decision", **structured_intent.model_dump()}
                proposal = raw_proposal
                started_controller = time.perf_counter()
                controller_decision = controller.plan(body.content, structured_intent, history)
                controller_duration_ms += (time.perf_counter() - started_controller) * 1000
            if controller_decision is None:
                if settings.max_model_steps < 1:
                    raise TimeoutError("Model-step budget is zero.")
                model_call_count += 1
                turn.model_steps += 1
                started_model = time.perf_counter()
                try:
                    raw_proposal = backend().act(body.content, validate_arguments=False)
                    proposal = validate_action(raw_proposal)
                finally:
                    model_call_durations_ms.append(round((time.perf_counter() - started_model) * 1000, 3))
                started_controller = time.perf_counter()
                controller_decision = controller.apply(body.content, proposal, history)
                controller_duration_ms += (time.perf_counter() - started_controller) * 1000
            action = validate_action(controller_decision.action)
            workflow_text = controller_decision.request_text or body.content
        else:
            if settings.max_model_steps < 1:
                raise TimeoutError("Model-step budget is zero.")
            model_call_count += 1
            turn.model_steps += 1
            started_model = time.perf_counter()
            try:
                action = validate_action(backend().act(body.content))
            finally:
                model_call_durations_ms.append(round((time.perf_counter() - started_model) * 1000, 3))
        if time.perf_counter() > turn.deadline_monotonic:
            raise TimeoutError("Model generation exceeded the turn deadline.")
    except Exception as exc:
        turn.status, turn.finished_at = "failed", datetime.now(timezone.utc)
        assistant = "I couldn't safely interpret that request. Please rephrase it or choose a supported action."
        db.add(Message(conversation_id=conversation.id, role="assistant", content=assistant))
        if controller is not None:
            failure_category = (
                "structured_intent_failed" if isinstance(controller, StructuredIntentWorkflowController) and model_call_count else
                "invalid_action_envelope" if raw_proposal is not None and proposal is None else
                "model_timeout" if isinstance(exc, TimeoutError) and model_call_count else
                "model_backend_failed" if model_call_count else "model_step_budget_exhausted"
            )
            add_audit(db, user, "hybrid_controller_decision", turn.id, {
                "controller_version": controller.version,
                "backend": settings.model_backend,
                "model_id": settings.model_id,
                "proposal_action_type": None,
                "proposal_tool_name": None,
                "final_action_type": None,
                "final_tool_name": None,
                "decision": "failed_closed",
                "reason": failure_category,
                "retry_count": 0,
                "model_calls": model_call_count,
                "model_call_durations_ms": model_call_durations_ms,
                "controller_duration_ms": round(controller_duration_ms, 3),
                **controller_proposal_details(raw_proposal, proposal),
                "validation_failure_category": failure_category,
            })
        db.commit()
        return {"turn_id": turn.id, "status": "failed", "assistant_message": assistant, "tool_executions": [], "pending_action": None}
    executions = []
    pending = None
    proposal_failed = False
    turn_failed = False
    if action["action_type"] == "tool_call":
        tool = action["tool_name"]
        try:
            ARGUMENT_SCHEMAS[tool].model_validate(action["arguments"])
            execution = execute_for_turn(db, user, turn, tool, action["arguments"])
            executions.append(execution)
            result = execution["result"]
            planned_followups = controller.follow_up_tools(workflow_text) if isinstance(
                controller, (HybridControllerV5Candidate, StructuredIntentWorkflowController)
            ) else ()
            if tool == "list_order_items" and execution["status"] == "succeeded" and (
                (isinstance(controller, (HybridControllerV5Candidate, StructuredIntentWorkflowController)) and planned_followups)
                or (not isinstance(controller, (HybridControllerV5Candidate, StructuredIntentWorkflowController)) and any(w in workflow_text.lower() for w in ("eligible", "eligibility", "can i return", "refund estimate", "estimate the refund", "how much", "estimate", "return rules", "returnable", "qualify for return", "assess return", "evaluate return")))
            ):
                requested_ids = sorted({value.upper() for value in ITEM_ID_RE.findall(workflow_text)}) if controller is not None else []
                available_ids = {i["item_id"] for i in result["items"]}
                ids = requested_ids if requested_ids else [i["item_id"] for i in result["items"]]
                if isinstance(controller, StructuredIntentWorkflowController):
                    reason = controller._reason_from_user_text(workflow_text)
                elif controller is not None:
                    reason = controller._eligibility_reason(workflow_text)
                else:
                    reason = "damaged" if "damaged" in workflow_text.lower() else "wrong_item" if "wrong item" in workflow_text.lower() else "late_delivery" if "late delivery" in workflow_text.lower() else "changed_mind"
                if not set(ids).issubset(available_ids):
                    ids = requested_ids
                second = execute_for_turn(db, user, turn, "check_refund_eligibility", {"order_id": result["order_id"], "item_ids": ids, "reason": reason})
                executions.append(second)
                result = second["result"]
                estimate_requested = (
                    isinstance(controller, (HybridControllerV5Candidate, StructuredIntentWorkflowController))
                    and "calculate_refund_estimate" in planned_followups
                ) or (not isinstance(controller, (HybridControllerV5Candidate, StructuredIntentWorkflowController)) and "estimate" in workflow_text.lower())
                if estimate_requested and second["status"] == "succeeded":
                    eligible = [i["item_id"] for i in result["items"] if i["eligibility"] == "eligible"]
                    if eligible:
                        third = execute_for_turn(db, user, turn, "calculate_refund_estimate", {"order_id": result["order_id"], "item_ids": eligible})
                        executions.append(third)
                        result = third["result"]
            # Tool results are data, never instructions. Give them to the model only
            # through the backend's explicit untrusted-result wrapper and bound the
            # synthesis step by the same per-turn step and wall-clock budgets.
            if executions[-1]["status"] == "succeeded":
                grounded = (
                    grounded_tool_response(tool, result)
                    if len(executions) == 1
                    else grounded_workflow_response(
                        executions,
                        requested_estimate=any(term in workflow_text.casefold() for term in ("estimate", "how much", "what amount")),
                    )
                )
                if grounded is not None:
                    assistant = grounded
                    turn_failed = False
                    add_audit(db, user, "grounded_response", turn.id, {"response_path": "grounded_template", "tool_name": tool})
                elif len(executions) > 1:
                    assistant = "The tools returned results that I couldn't safely combine. Please try again or request human review."
                    turn_failed = True
                elif turn.model_steps >= max(1, settings.max_model_steps) or time.perf_counter() >= turn.deadline_monotonic:
                    assistant = "I retrieved the approved data but couldn't safely finish within this turn's limits."
                    turn_failed = True
                else:
                    model_call_count += 1
                    turn.model_steps += 1
                    started_model = time.perf_counter()
                    try:
                        final_action = validate_action(backend().act(workflow_text, prior_result=result))
                    finally:
                        model_call_durations_ms.append(round((time.perf_counter() - started_model) * 1000, 3))
                    if time.perf_counter() > turn.deadline_monotonic:
                        raise TimeoutError("Final response exceeded the turn deadline.")
                    if final_action["action_type"] != "final_answer":
                        raise ValueError("A tool result may only lead to a final answer in this bounded flow.")
                    assistant = final_action["answer"]
            else:
                partial = grounded_workflow_response(
                    executions,
                    requested_estimate=any(term in workflow_text.casefold() for term in ("estimate", "how much", "what amount")),
                ) if len(executions) > 1 else None
                assistant = partial or result.get("error", "The request could not be completed.")
        except Exception:
            turn_failed = True
            if executions and executions[-1]["status"] == "succeeded":
                # A final-answer/model failure must not be recorded as a failed
                # second tool call. The successful tool trace remains truthful.
                assistant = "The approved tools returned a result, but I couldn't safely produce the final response. Please try again."
            else:
                assistant = "The requested tool action did not pass validation. Please check the order and item details."
                db.add(ToolExecution(turn_id=turn.id, tool_name=tool, arguments=safe_json(action.get("arguments", {})), validation_status="invalid", authorization_status="not_run", result_status="validation_failed", result_summary={"error": "strict_argument_validation_failed"}, duration_ms=0))
    elif action["action_type"] == "propose_state_change":
        try:
            if turn.tool_calls >= max(0, settings.max_tool_calls):
                raise ValueError("Tool-call budget exhausted.")
            if time.perf_counter() >= turn.deadline_monotonic:
                raise TimeoutError("Turn deadline exceeded.")
            args = TicketArgs.model_validate(action["arguments"]).model_dump()
            # Enforce order-link completeness at the API boundary too. The
            # controller is a quality guard; it is not the authorization boundary.
            request_order_ids = sorted({value.upper() for value in ORDER_ID_RE.findall(workflow_text)})
            if HybridController._order_related_ticket(workflow_text):
                if len(request_order_ids) != 1 or args.get("order_id") != request_order_ids[0]:
                    raise ValueError("An order-related ticket needs one request-grounded order ID.")
            elif args.get("order_id") and args["order_id"] not in request_order_ids:
                raise ValueError("Ticket order ID must be grounded in the user request.")
            if user.role not in TOOL_REGISTRY["create_support_ticket"].required_roles:
                raise PermissionError("Role cannot propose this action.")
            if args["order_id"]:
                # Scope-check the proposed order without writing a ticket.
                execute_read_tool(db, user, "lookup_order", {"order_id": args["order_id"]})
            pending_record = PendingAction(tenant_id=user.tenant_id, conversation_id=conversation.id, turn_id=turn.id,
                proposed_by=user.id, tool_name="create_support_ticket", arguments=args, idempotency_key=str(uuid4()))
            db.add(pending_record)
            db.flush()
            turn.tool_calls += 1
            db.add(ToolExecution(turn_id=turn.id, tool_name="create_support_ticket", arguments=redact_sensitive(args), validation_status="valid", authorization_status="approval_required", result_status="pending_approval", result_summary={"pending_action_id": pending_record.id}, duration_ms=0))
            pending = {"id": pending_record.id, "status": "pending", "tool_name": pending_record.tool_name, "arguments": args}
            assistant = "I prepared this support ticket for review. It has not been created. A supervisor must approve it."
        except Exception:
            proposal_failed = True
            assistant = "I couldn't prepare that ticket with the information provided. Please check the order ID and ticket details."
    elif action["action_type"] == "clarification":
        assistant = action["question"]
    elif action["action_type"] == "handoff":
        assistant = action["user_safe_message"]
    else:
        assistant = guard_untraced_business_claim(
            action["answer"], executions=executions, pending=pending,
            controller=controller, request_text=workflow_text,
        )
    status = "failed" if proposal_failed or turn_failed else "pending_approval" if pending else "completed"
    turn.status, turn.finished_at = status, datetime.now(timezone.utc)
    db.add(Message(conversation_id=conversation.id, role="assistant", content=assistant))
    add_audit(db, user, "conversation_turn", turn.id, {"status": status, "tool_count": len(executions)})
    if controller is not None and controller_decision is not None:
        add_audit(db, user, "hybrid_controller_decision", turn.id, {
            "controller_version": controller.version,
            "structured_intent": ({
                "intent": structured_intent.intent,
                "order_id_count": len(structured_intent.order_ids),
                "item_id_count": len(structured_intent.item_ids),
                "item_scope": structured_intent.item_scope,
                "requested_outputs": structured_intent.requested_outputs,
            } if structured_intent is not None else None),
            "backend": settings.model_backend,
            "model_id": settings.model_id,
            **controller_proposal_details(raw_proposal, proposal),
            "final_action_type": action.get("action_type"),
            "final_tool_name": action.get("tool_name"),
            "decision": controller_decision.decision,
            "reason": controller_decision.reason,
            "outcome": "clarification_required" if action.get("action_type") == "clarification" else action.get("action_type"),
            "validation_failure_category": controller_validation_failure(controller_decision.reason),
            "retry_count": controller_decision.retry_count,
            "model_calls": model_call_count,
            "model_call_durations_ms": model_call_durations_ms,
            "controller_duration_ms": round(controller_duration_ms, 3),
        })
    db.commit()
    return {"turn_id": turn.id, "status": status, "assistant_message": assistant, "tool_executions": executions, "pending_action": pending}


@app.get("/api/v1/pending-actions")
def list_pending(db: Session = Depends(get_db), user: User = Depends(require_role("supervisor", "admin"))):
    rows = db.scalars(select(PendingAction).where(PendingAction.tenant_id == user.tenant_id).order_by(PendingAction.created_at.desc())).all()
    return [{"id": r.id, "status": r.status, "tool_name": r.tool_name, "arguments": r.arguments, "created_at": r.created_at, "ticket_id": r.ticket_id} for r in rows]


@app.get("/api/v1/pending-actions/{action_id}")
def get_pending(action_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("supervisor", "admin"))):
    row = db.scalar(select(PendingAction).where(PendingAction.id == action_id, PendingAction.tenant_id == user.tenant_id).with_for_update())
    if not row:
        raise HTTPException(404, detail={"code": "action_not_found", "message": "Pending action not found."})
    return {"id": row.id, "status": row.status, "tool_name": row.tool_name, "arguments": row.arguments, "created_at": row.created_at, "ticket_id": row.ticket_id}


@app.post("/api/v1/pending-actions/{action_id}/approve")
def approve(action_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("supervisor", "admin"))):
    row = db.scalar(select(PendingAction).where(PendingAction.id == action_id, PendingAction.tenant_id == user.tenant_id))
    if not row:
        raise HTTPException(404, detail={"code": "action_not_found", "message": "Pending action not found."})
    if row.status == "completed" and row.ticket_id:
        return {"id": row.id, "status": row.status, "ticket_id": row.ticket_id, "message": "This approval was already completed."}
    if row.status != "pending":
        raise HTTPException(409, detail={"code": "action_resolved", "message": f"Action is already {row.status}."})
    try:
        ticket = create_ticket_after_approval(db, row, user)
        row.status, row.approved_by, row.ticket_id, row.resolved_at = "completed", user.id, ticket.id, datetime.now(timezone.utc)
        add_audit(db, user, "ticket_approved_and_created", row.id, {"ticket_code": ticket.ticket_code})
        db.commit()
        return {"id": row.id, "status": row.status, "ticket_id": ticket.id, "ticket_code": ticket.ticket_code, "message": "Ticket created after supervisor approval."}
    except LookupError:
        db.rollback()
        raise HTTPException(422, detail={"code": "order_scope_invalid", "message": "The referenced order is unavailable to this tenant."})
    except (ValueError, TypeError):
        db.rollback()
        raise HTTPException(422, detail={"code": "pending_action_invalid", "message": "The pending ticket failed validation and was not created."})


@app.post("/api/v1/pending-actions/{action_id}/reject")
def reject(action_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("supervisor", "admin"))):
    row = db.scalar(select(PendingAction).where(PendingAction.id == action_id, PendingAction.tenant_id == user.tenant_id))
    if not row:
        raise HTTPException(404, detail={"code": "action_not_found", "message": "Pending action not found."})
    if row.status != "pending":
        return {"id": row.id, "status": row.status, "message": "This action was already resolved."}
    row.status, row.approved_by, row.resolved_at = "rejected", user.id, datetime.now(timezone.utc)
    add_audit(db, user, "ticket_proposal_rejected", row.id)
    db.commit()
    return {"id": row.id, "status": row.status}


@app.get("/api/v1/turns/{turn_id}/trace")
def trace(turn_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    turn = db.scalar(select(Turn).join(Conversation).where(Turn.id == turn_id, Conversation.tenant_id == user.tenant_id, Conversation.user_id == user.id))
    if not turn:
        raise HTTPException(404, detail={"code": "turn_not_found", "message": "Turn not found."})
    events = db.scalars(select(ToolExecution).where(ToolExecution.turn_id == turn.id).order_by(ToolExecution.created_at)).all()
    controller_events = db.scalars(select(AuditEvent).where(
        AuditEvent.resource_id == turn.id, AuditEvent.action == "hybrid_controller_decision",
        AuditEvent.tenant_id == user.tenant_id,
    ).order_by(AuditEvent.created_at)).all()
    return {"turn_id": turn.id, "status": turn.status,
            "events": [{"execution_id": e.id, "tool_name": e.tool_name, "arguments": e.arguments, "validation": e.validation_status, "authorization": e.authorization_status, "result_status": e.result_status, "result": e.result_summary, "duration_ms": e.duration_ms} for e in events],
            "controller_events": [e.details for e in controller_events]}


@app.get("/api/v1/benchmarks")
def benchmarks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    runs = db.scalars(select(BenchmarkRun).order_by(BenchmarkRun.started_at.desc())).all()
    return [{"id": r.id, "backend": r.backend, "dataset_version": r.dataset_version, "split": r.split, "status": r.status, "metrics": r.metrics, "started_at": r.started_at} for r in runs]


@app.get("/api/v1/experiments")
def experiment_history(db: Session = Depends(get_db), user: User = Depends(require_role("evaluator", "admin"))):
    """Return persisted run history and locally saved result artifacts, with no prompt/example contents."""
    runs = db.scalars(select(BenchmarkRun).order_by(BenchmarkRun.started_at.desc())).all()
    items = [{"id": r.id, "source": "database", "name": f"{r.backend} · {r.split}", "backend": r.backend,
              "dataset_version": r.dataset_version, "split": r.split, "status": r.status,
              "started_at": r.started_at, "metrics": r.metrics} for r in runs]
    results_dir = Path(__file__).resolve().parents[2] / "experiments" / "results"
    if results_dir.exists():
        for path in sorted(results_dir.glob("*.json")):
            try:
                artifact = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            metrics = artifact.get("metrics", {})
            items.append({"id": f"artifact:{path.name}", "source": "artifact", "name": path.stem,
                          "backend": artifact.get("backend", "saved artifact"),
                          "dataset_version": artifact.get("dataset_version", "unknown"),
                          "split": artifact.get("split", "unknown"), "status": artifact.get("status", "saved"),
                          "started_at": artifact.get("started_at"), "metrics": metrics})
    return sorted(items, key=lambda x: str(x.get("started_at") or ""), reverse=True)


@app.post("/api/v1/benchmarks")
def run_benchmark(db: Session = Depends(get_db), user: User = Depends(require_role("evaluator", "admin"))):
    path = Path(__file__).resolve().parents[2] / "experiments" / "datasets" / "scenarios.jsonl"
    if not path.exists():
        raise HTTPException(503, detail={"code": "dataset_missing", "message": "Generate the synthetic evaluation dataset first."})
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and json.loads(line).get("split") == "validation"]
    model = backend()
    matched = valid = 0
    errors = []
    per_family: dict[str, dict[str, int]] = {}
    for case in cases:
        family = case["scenario_family"]
        family_metrics = per_family.setdefault(family, {"denominator": 0, "action_match_count": 0})
        family_metrics["denominator"] += 1
        try:
            action = validate_action(model.act(case["user_message"]))
            valid += 1
            ok = action["action_type"] == case["expected_action_type"] and (case.get("expected_tool_name") is None or action.get("tool_name") == case.get("expected_tool_name"))
            matched += int(ok)
            family_metrics["action_match_count"] += int(ok)
            if not ok:
                errors.append({"example_id": case["example_id"], "category": "action_mismatch"})
        except Exception:
            errors.append({"example_id": case["example_id"], "category": "invalid_action"})
    run = BenchmarkRun(backend=settings.model_backend, dataset_version="p2-synthetic-v1", split="validation", status="completed",
        metrics={"denominator": len(cases), "valid_actions": valid, "action_match_count": matched,
                 "action_match_rate": matched / len(cases) if cases else None, "valid_action_rate": valid / len(cases) if cases else None,
                 "per_scenario_family": per_family, "errors": errors,
                 "model_id": settings.model_id if settings.model_backend == "transformers" else None,
                 "model_revision": settings.model_revision if settings.model_backend == "transformers" else None,
                 "dataset_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                 "environment": {"python": platform.python_version(), "platform": platform.platform()},
                 "provenance": "Measured from saved synthetic validation data; fixture backend is not LLM performance."})
    db.add(run)
    add_audit(db, user, "benchmark_run", run.id, {"split": "validation", "count": len(cases)})
    db.commit()
    return {"id": run.id, "backend": run.backend, "dataset_version": run.dataset_version, "split": run.split, "status": run.status, "metrics": run.metrics}


@app.get("/api/v1/benchmarks/{run_id}/export")
def export_benchmark(run_id: str, format: str = "json", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    run = db.get(BenchmarkRun, run_id)
    if not run:
        raise HTTPException(404, detail={"code": "run_not_found", "message": "Benchmark run not found."})
    payload = {"id": run.id, "backend": run.backend, "dataset_version": run.dataset_version, "split": run.split, "metrics": run.metrics}
    if format == "csv":
        buff = io.StringIO()
        writer = csv.writer(buff)
        writer.writerow(["run_id", "backend", "dataset_version", "split", "metric", "value"])
        for key, value in run.metrics.items():
            if not isinstance(value, (dict, list)):
                writer.writerow([run.id, run.backend, run.dataset_version, run.split, key, value])
        return Response(buff.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={run.id}.csv"})
    if format != "json":
        raise HTTPException(422, detail={"code": "invalid_format", "message": "format must be json or csv."})
    return payload


@app.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    return {"turns": db.query(Turn).count(), "tool_executions": db.query(ToolExecution).count(), "pending_actions": db.query(PendingAction).filter_by(status="pending").count(), "benchmark_runs": db.query(BenchmarkRun).count()}
