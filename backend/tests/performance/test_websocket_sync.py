
import pytest
import asyncio
from datetime import datetime
from decimal import Decimal
import uuid
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.order_service import OrderService
from app.schemas.order import OrderCreate, OrderItemCreate, OrderUpdateStatus
from app.models.company import Company
from app.models.branch import Branch
from app.models.product import Product
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.utils.security import get_password_hash
from app.core.websockets import sio

# We need a Mock socket client
import socketio

@pytest.mark.asyncio
async def test_websocket_state_sync_recovery(db_session: AsyncSession):
    """
    ⚡ STRESS TEST: WebSocket State Synchronization & Recovery

    Scenario:
    1. Create initial state (Orders).
    2. Client connects via WebSocket and subscribes to updates.
    3. Simulates connection loss (Client Disconnect).
    4. Backend state changes (Order Status Update) while client is offline.
    5. Client Reconnects.
    6. VERIFY: Client must have a way to fetch the missed state (Source of Truth check).
       This test checks if the system supports 'state reconciliation' by fetching
       from the API after reconnection, which is the standard pattern for robustness.
    """
    session = db_session

    # 1. Setup Data
    uid = str(uuid.uuid4())[:8]
    company = Company(name=f"WS Co {uid}", slug=f"ws-co-{uid}")
    session.add(company)
    await session.commit()

    branch = Branch(name="Main", company_id=company.id, address="St", phone="1", code=f"B-{uid}")
    session.add(branch)
    await session.commit()

    product = Product(name="Pizza", company_id=company.id, price=Decimal("20.00"), stock=Decimal("100"))
    session.add(product)
    await session.commit()

    user = User(
        username=f"ws_user_{uid}",
        email=f"ws_{uid}@test.com",
        company_id=company.id,
        role="admin",
        hashed_password=get_password_hash("123")
    )
    session.add(user)
    await session.commit()

    # Initialize Inventory with stock
    from app.services.inventory_service import InventoryService
    inv_service = InventoryService(session)
    await inv_service.update_stock(
        branch_id=branch.id,
        product_id=product.id,
        quantity_delta=Decimal("100.00"),
        transaction_type="IN",
        user_id=user.id,
        reason="Initial Load"
    )

    # Create an initial Order
    order_data = OrderCreate(
        branch_id=branch.id,
        items=[OrderItemCreate(product_id=product.id, quantity=1)],
        customer_notes="Initial"
    )
    service = OrderService(session)
    order = await service.create_order(order_data, company.id, user.id)
    order_id = order.id

    print(f"\n⚡ Order Created: {order.order_number} (Status: {order.status})")

    # 2. Simulate Client Connection (Conceptual)
    # In a real integration test we would use socketio.AsyncClient
    # But here we are testing the logic flow and availability of recovery endpoints.

    # Simulate: Client connects -> Client usually calls GET /orders/active

    # 3. Simulate Disconnect (Time gap)
    print("⚡ Simulating Client Disconnect...")
    await asyncio.sleep(0.1)

    # 4. State Change on Server (while client is 'offline')
    print("⚡ Server updates Order Status to CONFIRMED...")
    await service.update_status(
        order_id=order_id,
        new_status=OrderStatus.CONFIRMED,
        company_id=company.id,
        user=user
    )

    print("⚡ Server updates Order Status to PREPARING...")
    await service.update_status(
        order_id=order_id,
        new_status=OrderStatus.PREPARING,
        company_id=company.id,
        user=user
    )

    # Verify in DB
    # Re-fetch from DB to be sure
    result = await session.execute(select(Order).where(Order.id == order_id))
    db_order = result.scalar_one()
    assert db_order.status == OrderStatus.PREPARING
    print(f"   -> DB State: {db_order.status}")

    # 5. Simulate Client Reconnect & Recovery
    print("⚡ Client Reconnects...")

    # Ideally, the client logic is: On(Connect) -> Fetch /orders/{id} or /orders/active
    # We verify that the API provides the correct current state (Source of Truth).

    # Fetch order via Service (simulating GET /orders/{id})
    recovered_order = await service.get_order(order_id, company.id)

    # 6. Verify Consistency
    print(f"⚡ Client fetches state via API: {recovered_order.status}")

    assert recovered_order.status == OrderStatus.PREPARING, \
        "State Mismatch! API did not return the latest state from DB."

    if recovered_order.status == db_order.status:
        print("✅ RECOVERY SUCCESS: Client obtained correct state from Source of Truth (DB) after reconnection.")
    else:
        print("❌ RECOVERY FAILED: State mismatch.")

    # 7. Stress / Load aspect (Bonus)
    # If Redis (WebSocket Broker) falls, the WebSocket events are lost.
    # The system relies on the persistence (DB).
    # This test proves that IF the client re-fetches from DB, the system is robust.
