
import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.company import Company
from app.models.branch import Branch
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.models.payment import PaymentMethod

@pytest.mark.asyncio
async def test_payment_flow(client: AsyncClient, session: AsyncSession):
    # 1. Setup Data
    company = Company(name="Test Corp", slug="test-corp")
    session.add(company)
    await session.flush()
    
    branch = Branch(name="Main Branch", company_id=company.id, address="123", phone="555", code="BR-1")
    session.add(branch)
    await session.flush()
    
    # Create User (Cashier)
    user = User(username="cashier", email="cashier@test.com", hashed_password="pw", company_id=company.id, branch_id=branch.id)
    session.add(user)
    await session.flush()
    await session.refresh(user)
    
    # Create Order
    order = Order(
        company_id=company.id, 
        branch_id=branch.id, 
        order_number="ORD-101", 
        total=Decimal("100.00"), 
        status=OrderStatus.PENDING
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    
    # We need a token for the user to hit the API, OR we mock get_current_user in the test.
    # For integration testing API, mocking get_current_user is easier than full login flow if we just want to test Payment logic via API.
    # Let's mock get_current_user in this test file or use a fixture if we had one.
    # For now, let's override the dependency.
    
    from app.auth_deps import get_current_user
    from app.main import app
    
    def mock_get_current_user():
        return user

    fastapi_app = app
    if hasattr(app, "other_asgi_app"):
        fastapi_app = app.other_asgi_app
        
    fastapi_app.dependency_overrides[get_current_user] = mock_get_current_user
    
    # 2. Test Partial Payment
    payload = {
        "order_id": order.id,
        "amount": 50.00,
        "method": "cash"
    }
    resp = await client.post("/payments/", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["amount"] == "50.00"
    assert data["status"] == "completed"
    
    # Verify Order Status (Should remain PENDING)
    await session.refresh(order)
    assert order.status == OrderStatus.PENDING
    
    # 3. Test Remaining Payment
    payload["amount"] = 50.00
    resp = await client.post("/payments/", json=payload)
    assert resp.status_code == 200
    
    # Verify Order Status (Should be CONFIRMED)
    await session.refresh(order)
    assert order.status == OrderStatus.CONFIRMED

    fastapi_app.dependency_overrides.clear()
