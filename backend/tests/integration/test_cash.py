
import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.company import Company
from app.models.branch import Branch
from app.models.user import User
from app.models.payment import Payment, PaymentMethod
from app.models.order import Order

@pytest.mark.asyncio
async def test_cash_closure_lifecycle(client: AsyncClient, session: AsyncSession):
    # 1. Setup Data
    company = Company(name="Cash Corp", slug="cash-corp")
    session.add(company)
    await session.flush()
    branch = Branch(name="Branch 1", company_id=company.id, address="St", phone="123", code="BR-1")
    session.add(branch)
    await session.flush()
    user = User(username="cashier2", email="cashier2@test.com", hashed_password="pw", company_id=company.id, branch_id=branch.id)
    session.add(user)
    
    # Mock Auth
    from app.auth_deps import get_current_user
    from app.main import app

    fastapi_app = app
    if hasattr(app, "other_asgi_app"):
        fastapi_app = app.other_asgi_app

    fastapi_app.dependency_overrides[get_current_user] = lambda: user
    
    # 2. Open Register
    open_payload = {"initial_cash": 1000.00}
    resp = await client.post("/cash/open", json=open_payload)
    assert resp.status_code == 200
    closure_data = resp.json()
    closure_id = closure_data["id"]
    assert closure_data["status"] == "open"
    assert closure_data["initial_cash"] == "1000.00"
    
    # 3. Create Payments (Simulate activity)
    # We can use DB directly or API. Let's use DB to be faster, or API to be more realistic.
    # Using DB for payments:
    order = Order(company_id=company.id, branch_id=branch.id, order_number="O-1", total=Decimal("500"))
    session.add(order)
    await session.commit()
    
    p1 = Payment(
        company_id=company.id, branch_id=branch.id, user_id=user.id, order_id=order.id,
        amount=Decimal("200.00"), method=PaymentMethod.CASH
    )
    p2 = Payment(
        company_id=company.id, branch_id=branch.id, user_id=user.id, order_id=order.id,
        amount=Decimal("300.00"), method=PaymentMethod.CARD
    )
    session.add(p1)
    session.add(p2)
    await session.commit()
    
    # 4. Check Current Status
    resp = await client.get("/cash/current")
    assert resp.status_code == 200
    status_data = resp.json()
    
    # Expected: Cash 200, Card 300
    assert status_data["expected_cash"] == "200.00"
    assert status_data["expected_card"] == "300.00"
    
    # 5. Close Register
    # Real logic: Cashier counts 1200 cash (1000 base + 200 sales) -> OK
    # Card voucher sum: 300 -> OK
    close_payload = {
        "real_cash": 1200.00,
        "real_card": 300.00,
        "real_transfer": 0.00,
        "notes": "All good"
    }
    resp = await client.post(f"/cash/{closure_id}/close", json=close_payload)
    assert resp.status_code == 200
    closed_data = resp.json()
    
    assert closed_data["status"] == "closed"
    assert closed_data["difference"] == "0.00"

    fastapi_app.dependency_overrides.clear()
