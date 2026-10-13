from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Order, PendingAction, Ticket, User

CENT = Decimal("0.01")
POLICY_VERSION = "return-policy-2026.1"


class StrictArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OrderArgs(StrictArgs):
    order_id: str = Field(pattern=r"^ORD-[0-9]{5}$")


class PolicyArgs(StrictArgs):
    category: Literal["standard_return", "damaged_item", "late_delivery", "refund_timing"]


class EligibilityArgs(OrderArgs):
    item_ids: list[str] = Field(min_length=1, max_length=20)
    reason: Literal["changed_mind", "damaged", "wrong_item", "late_delivery"]


class EstimateArgs(OrderArgs):
    item_ids: list[str] = Field(min_length=1, max_length=20)


class TicketArgs(StrictArgs):
    order_id: str | None = Field(default=None, pattern=r"^ORD-[0-9]{5}$")
    issue_type: Literal["delivery_delay", "damaged_item", "wrong_item", "return_question", "other"]
    summary: str = Field(min_length=4, max_length=160)
    description: str = Field(min_length=8, max_length=1000)
    priority: Literal["low", "normal", "high"] = "normal"


class StrictResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class OrderLookupResult(StrictResult):
    order_id: str
    status: str
    order_date: str
    expected_delivery_date: str | None
    item_ids: list[str]


class OrderItemResult(StrictResult):
    item_id: str
    product_name: str
    quantity: int
    unit_price: str
    status: str
    delivered_date: str | None


class OrderItemsResult(StrictResult):
    order_id: str
    items: list[OrderItemResult]


class ReturnPolicyResult(StrictResult):
    category: Literal["standard_return", "damaged_item", "late_delivery", "refund_timing"]
    policy_text: str
    version: str
    as_of: str


class EligibilityItemResult(StrictResult):
    item_id: str
    eligibility: Literal["eligible", "ineligible", "needs_review"]
    reason_code: str
    delivered_date: str | None


class EligibilityResult(StrictResult):
    order_id: str
    items: list[EligibilityItemResult]
    policy_version: str


class EstimateItemResult(StrictResult):
    item_id: str
    subtotal: str
    discount: str
    tax: str
    estimate: str


class RefundEstimateResult(StrictResult):
    order_id: str
    currency: str
    items: list[EstimateItemResult]
    subtotal: str
    discounts: str
    taxes: str
    estimated_total: str
    note: str


ARGUMENT_SCHEMAS = {
    "lookup_order": OrderArgs,
    "list_order_items": OrderArgs,
    "get_return_policy": PolicyArgs,
    "check_refund_eligibility": EligibilityArgs,
    "calculate_refund_estimate": EstimateArgs,
    "create_support_ticket": TicketArgs,
}

TOOL_RESULT_SCHEMAS = {
    "lookup_order": OrderLookupResult,
    "list_order_items": OrderItemsResult,
    "get_return_policy": ReturnPolicyResult,
    "check_refund_eligibility": EligibilityResult,
    "calculate_refund_estimate": RefundEstimateResult,
}


def validate_read_result(name: str, raw_result: dict) -> dict:
    """Validate trusted tool outputs before they enter workflow/response logic."""
    return TOOL_RESULT_SCHEMAS[name].model_validate(raw_result).model_dump()

POLICIES = {
    "standard_return": "Unused items may be returned within 30 calendar days after delivery. Final eligibility is determined per item.",
    "damaged_item": "Damaged items are routed for human review; do not promise an automatic refund.",
    "late_delivery": "A delivery that is past its expected date may be escalated for support review.",
    "refund_timing": "Approved demo refunds are estimates only. This application does not issue money or contact a payment provider.",
}


def _order(db: Session, user: User, order_code: str) -> Order:
    order = db.scalar(select(Order).where(Order.tenant_id == user.tenant_id, Order.order_code == order_code))
    if order is None:
        raise LookupError("Order not found or not available to this demo user.")
    return order


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def execute_read_tool(db: Session, user: User, name: str, raw_args: dict) -> dict:
    args = ARGUMENT_SCHEMAS[name].model_validate(raw_args)
    a = args.model_dump()
    if name == "get_return_policy":
        return {"category": a["category"], "policy_text": POLICIES[a["category"]], "version": POLICY_VERSION, "as_of": "2026-10-10"}
    order = _order(db, user, a["order_id"])
    if name == "lookup_order":
        return {"order_id": order.order_code, "status": order.status, "order_date": order.order_date.isoformat(),
                "expected_delivery_date": order.expected_delivery_date.isoformat() if order.expected_delivery_date else None,
                "item_ids": [i.item_code for i in order.items]}
    if name == "list_order_items":
        return {"order_id": order.order_code, "items": [{"item_id": i.item_code, "product_name": i.product_name,
                "quantity": i.quantity, "unit_price": str(i.unit_price), "status": i.status,
                "delivered_date": i.delivered_date.isoformat() if i.delivered_date else None} for i in order.items]}
    items = {i.item_code: i for i in order.items}
    if any(item_id not in items for item_id in a["item_ids"]):
        raise LookupError("One or more items were not found on this order.")
    if name == "check_refund_eligibility":
        output = []
        for item_id in a["item_ids"]:
            item = items[item_id]
            if a["reason"] == "damaged":
                result, code = "needs_review", "DAMAGE_REQUIRES_REVIEW"
            elif item.status != "delivered" or item.delivered_date is None:
                result, code = "ineligible", "ITEM_NOT_DELIVERED"
            elif (date(2026, 10, 10) - item.delivered_date).days > 30:
                result, code = "ineligible", "RETURN_WINDOW_CLOSED"
            else:
                result, code = "eligible", "WITHIN_RETURN_WINDOW"
            output.append({"item_id": item_id, "eligibility": result, "reason_code": code,
                           "delivered_date": item.delivered_date.isoformat() if item.delivered_date else None})
        return {"order_id": order.order_code, "items": output, "policy_version": POLICY_VERSION}
    eligible = [items[i] for i in a["item_ids"]]
    if any(i.status != "delivered" or i.delivered_date is None or (date(2026, 10, 10) - i.delivered_date).days > 30 for i in eligible):
        raise ValueError("Estimate is available only for delivered items within the return window.")
    rows = []
    subtotal = discounts = taxes = Decimal("0")
    for item in eligible:
        gross = item.unit_price * item.quantity
        discount = _money(gross * item.discount_rate)
        taxable = gross - discount
        tax = _money(taxable * item.tax_rate)
        net = taxable + tax
        subtotal += gross
        discounts += discount
        taxes += tax
        rows.append({"item_id": item.item_code, "subtotal": str(_money(gross)), "discount": str(discount), "tax": str(tax), "estimate": str(_money(net))})
    return {"order_id": order.order_code, "currency": order.currency, "items": rows,
            "subtotal": str(_money(subtotal)), "discounts": str(_money(discounts)),
            "taxes": str(_money(taxes)), "estimated_total": str(_money(subtotal - discounts + taxes)),
            "note": "Estimate only; no refund is issued."}


def create_ticket_after_approval(db: Session, action: PendingAction, reviewer: User) -> Ticket:
    # Revalidate persisted pending data at the point of execution. Approval is
    # not a substitute for a valid, schema-conforming proposal.
    args = TicketArgs.model_validate(action.arguments)
    existing = db.scalar(select(Ticket).where(Ticket.idempotency_key == action.idempotency_key))
    if existing:
        return existing
    order = _order(db, reviewer, args.order_id) if args.order_id else None
    ticket = Ticket(tenant_id=reviewer.tenant_id, ticket_code=f"TKT-{datetime.now(timezone.utc).strftime('%y%m%d')}-{action.id[:8].upper()}",
                    order_id=order.id if order else None, created_by=reviewer.id, issue_type=args.issue_type,
                    summary=args.summary, description=args.description, priority=args.priority,
                    idempotency_key=action.idempotency_key)
    db.add(ticket)
    db.flush()
    return ticket
