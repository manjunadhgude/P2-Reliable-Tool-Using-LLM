from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username: Mapped[str] = mapped_column(String(40), unique=True)
    display_name: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(24))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    order_code: Mapped[str] = mapped_column(String(24), index=True)
    customer_code: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(24))
    order_date: Mapped[date] = mapped_column(Date)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    delivered_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("tenant_id", "order_code"),)


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    item_code: Mapped[str] = mapped_column(String(24))
    product_name: Mapped[str] = mapped_column(String(120))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    discount_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0"))
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0"))
    status: Mapped[str] = mapped_column(String(24))
    delivered_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    order: Mapped[Order] = relationship(back_populates="items")


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(160), default="New support conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Turn(Base):
    __tablename__ = "turns"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    status: Mapped[str] = mapped_column(String(24))
    model_steps: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    tool_calls: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ToolExecution(Base):
    __tablename__ = "tool_executions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    turn_id: Mapped[str] = mapped_column(ForeignKey("turns.id"), index=True)
    tool_name: Mapped[str] = mapped_column(String(48))
    arguments: Mapped[dict] = mapped_column(JSON)
    validation_status: Mapped[str] = mapped_column(String(24))
    authorization_status: Mapped[str] = mapped_column(String(24))
    result_status: Mapped[str] = mapped_column(String(24))
    result_summary: Mapped[dict] = mapped_column(JSON)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class PendingAction(Base):
    __tablename__ = "pending_actions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    turn_id: Mapped[str] = mapped_column(ForeignKey("turns.id"), index=True)
    proposed_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    tool_name: Mapped[str] = mapped_column(String(48))
    arguments: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(24), default="pending")
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True)
    approved_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    ticket_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Ticket(Base):
    __tablename__ = "support_tickets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    ticket_code: Mapped[str] = mapped_column(String(24), unique=True)
    order_id: Mapped[str | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    issue_type: Mapped[str] = mapped_column(String(32))
    summary: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(20), default="open")
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(48))
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    backend: Mapped[str] = mapped_column(String(32))
    dataset_version: Mapped[str] = mapped_column(String(32))
    split: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(20))
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
