
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.company import Company
from app.models.branch import Branch
from app.models.user import User
from app.models.product import Product
from app.models.inventory import Inventory
from decimal import Decimal

@pytest.mark.asyncio
async def test_order_stock_concurrency(client: AsyncClient, session: AsyncSession):
    # 1. Setup Data
    company = Company(name="Race Corp", slug="race-corp")
    session.add(company)
    await session.flush()
    branch = Branch(name="Main Branch", company_id=company.id, address="123", phone="555", code="BR-1")
    session.add(branch)
    await session.flush()
    user = User(username="racer", email="race@test.com", hashed_password="pw", company_id=company.id, branch_id=branch.id)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    session.expunge(user) # Detach from session to avoid concurrency issues with lazy loading in other threads/tasks
    
    # 2. Setup Product with Stock = 1
    product = Product(name="Limited Item", price=Decimal("100.00"), code="LIM-001", company_id=company.id)
    session.add(product)
    await session.flush()
    
    inventory = Inventory(branch_id=branch.id, product_id=product.id, stock=Decimal("1.000"), min_stock=Decimal("0"))
    session.add(inventory)
    await session.commit()
    
    # Mock Auth
    from app.auth_deps import get_current_user
    from app.main import app
    from app.database import get_session
    
    # Remove session override to allow concurrent sessions
    if get_session in app.dependency_overrides:
        del app.dependency_overrides[get_session]
        
    app.dependency_overrides[get_current_user] = lambda: user
    
    # 3. Define concurrent request function
    async def place_order():
        payload = {
            "branch_id": branch.id,
            "items": [{"product_id": product.id, "quantity": 1}]
        }
        resp = await client.post("/orders/", json=payload)
        return resp.status_code

    # 4. Launch 5 concurrent orders
    tasks = [place_order() for _ in range(5)]
    results = await asyncio.gather(*tasks)
    
    # 5. Verify Results
    # Only ONE should succeed (201 or 200). Others should fail (400 Insufficient Stock).
    success_count = results.count(201)
    fail_count = results.count(400) + results.count(422) # 422 for validation error? ideally 400 for stock
    
    print(f"Results: {results}")
    
    # Reload inventory
    await session.refresh(inventory)
    
    assert success_count == 1, f"Expected exactly 1 success, got {success_count}. Results: {results}"
    assert inventory.stock == Decimal("0.000"), f"Stock should be 0, got {inventory.stock}"

    app.dependency_overrides.clear()
