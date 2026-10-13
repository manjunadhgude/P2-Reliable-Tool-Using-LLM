from dataclasses import dataclass

from app.tools.domain import ARGUMENT_SCHEMAS


@dataclass(frozen=True)
class ToolMetadata:
    name: str
    description: str
    input_schema: type
    risk_category: str
    side_effect: bool
    required_roles: tuple[str, ...]
    timeout_seconds: float = 3.0
    max_retries: int = 0
    approval_required: bool = False
    idempotency_required: bool = False


TOOL_REGISTRY = {
    "lookup_order": ToolMetadata("lookup_order", "Find a tenant-scoped synthetic order.", ARGUMENT_SCHEMAS["lookup_order"], "low", False, ("support_agent", "supervisor", "admin")),
    "list_order_items": ToolMetadata("list_order_items", "List items belonging to an authorized order.", ARGUMENT_SCHEMAS["list_order_items"], "low", False, ("support_agent", "supervisor", "admin")),
    "get_return_policy": ToolMetadata("get_return_policy", "Return source-of-truth policy text.", ARGUMENT_SCHEMAS["get_return_policy"], "low", False, ("support_agent", "supervisor", "admin")),
    "check_refund_eligibility": ToolMetadata("check_refund_eligibility", "Apply deterministic return eligibility rules.", ARGUMENT_SCHEMAS["check_refund_eligibility"], "medium", False, ("support_agent", "supervisor", "admin")),
    "calculate_refund_estimate": ToolMetadata("calculate_refund_estimate", "Calculate a Decimal estimate for eligible items.", ARGUMENT_SCHEMAS["calculate_refund_estimate"], "medium", False, ("support_agent", "supervisor", "admin")),
    "create_support_ticket": ToolMetadata("create_support_ticket", "Propose a synthetic support ticket for explicit review.", ARGUMENT_SCHEMAS["create_support_ticket"], "write", True, ("support_agent", "supervisor", "admin"), timeout_seconds=5.0, approval_required=True, idempotency_required=True),
}
