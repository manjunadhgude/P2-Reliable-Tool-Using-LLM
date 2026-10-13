from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Order, OrderItem, User

TENANT = "tenant-demo"


def seed_database(db: Session) -> None:
    if db.scalar(select(User.id).limit(1)):
        return
    users = [
        User(username="agent", display_name="Demo Support Agent", role="support_agent", tenant_id=TENANT),
        User(username="supervisor", display_name="Demo Supervisor", role="supervisor", tenant_id=TENANT),
        User(username="evaluator", display_name="Demo Evaluator", role="evaluator", tenant_id=TENANT),
        User(username="other-tenant", display_name="Other Tenant Agent", role="support_agent", tenant_id="tenant-other"),
    ]
    db.add_all(users)
    db.flush()
    today = date(2026, 10, 10)
    specs = [
        ("ORD-10021", "in_transit", today - timedelta(days=3), today + timedelta(days=2), None, [("ITEM-2101", "Everyday Backpack", "49.95", 1, "shipped", None)]),
        ("ORD-10022", "delivered", today - timedelta(days=22), today - timedelta(days=18), today - timedelta(days=18), [("ITEM-2201", "Ceramic Travel Mug", "24.50", 2, "delivered", today - timedelta(days=18)), ("ITEM-2202", "Wool Scarf", "39.00", 1, "delivered", today - timedelta(days=18))]),
        ("ORD-10023", "delivered", today - timedelta(days=48), today - timedelta(days=43), today - timedelta(days=43), [("ITEM-2301", "Desk Lamp", "64.00", 1, "delivered", today - timedelta(days=43))]),
    ]
    for code, status, ordered, expected, delivered, item_specs in specs:
        order = Order(tenant_id=TENANT, order_code=code, customer_code="CUST-DEMO-01", status=status,
                      order_date=ordered, expected_delivery_date=expected, delivered_date=delivered, currency="USD")
        for item_code, name, price, quantity, item_status, item_delivered in item_specs:
            order.items.append(OrderItem(item_code=item_code, product_name=name, quantity=quantity,
                                         unit_price=Decimal(price), discount_rate=Decimal("0.05"),
                                         tax_rate=Decimal("0.08"), status=item_status,
                                         delivered_date=item_delivered))
        db.add(order)
    db.add(Order(tenant_id="tenant-other", order_code="ORD-90001", customer_code="CUST-OTHER-01",
                 status="delivered", order_date=today - timedelta(days=4), currency="USD"))
    db.commit()
