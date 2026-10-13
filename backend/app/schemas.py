from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginRequest(StrictModel):
    username: Literal["agent", "supervisor", "evaluator"]


class ConversationCreate(StrictModel):
    title: str = Field(default="Support conversation", min_length=1, max_length=160)


class MessageCreate(StrictModel):
    content: str = Field(min_length=1, max_length=4000)


class Claim(StrictModel):
    text: str = Field(min_length=1)
    source_type: Literal["tool_result", "policy", "conversation_context", "general_explanation"]
    source_id: str | None


class ToolCall(StrictModel):
    action_type: Literal["tool_call"]
    tool_name: Literal["lookup_order", "list_order_items", "get_return_policy", "check_refund_eligibility", "calculate_refund_estimate"]
    arguments: dict
    reason_summary: str = Field(max_length=500)
    confidence: float | None = Field(default=None, ge=0, le=1)


class FinalAnswer(StrictModel):
    action_type: Literal["final_answer"]
    answer: str
    claims: list[Claim] = Field(default_factory=list)
    needs_human_review: bool = False
    confidence: float | None = Field(default=None, ge=0, le=1)


class TicketProposal(StrictModel):
    action_type: Literal["propose_state_change"]
    tool_name: Literal["create_support_ticket"]
    arguments: dict
    reason_summary: str = Field(max_length=500)
    confidence: float | None = Field(default=None, ge=0, le=1)


class Clarification(StrictModel):
    action_type: Literal["clarification"]
    question: str
    missing_fields: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1)


class Handoff(StrictModel):
    action_type: Literal["handoff"]
    reason: str
    user_safe_message: str
