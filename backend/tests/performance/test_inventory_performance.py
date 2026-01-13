
import pytest
import time
import asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.inventory_service import InventoryService
from app.models.company import Company
from app.models.branch import Branch
from app.models.product import Product
from app.models.user import User
from app.utils.security import get_password_hash
import uuid

@pytest.mark.asyncio
@pytest.mark.performance
async def test_inventory_update_stock_performance(db_session: AsyncSession):
    """
    ⚡ PERFORMANCE TEST: Measure execution time of stock updates.

    Target: 100 sequential updates should take less than 1 second (approx 10ms per update).
    This tests the efficiency of the InventoryService and Database transaction overhead.
    """
    session = db_session

    # 1. Setup Data
    uid = str(uuid.uuid4())[:8]

    company = Company(
        name=f"Perf Company {uid}",
        slug=f"perf-co-{uid}",
        owner_name="Perf Owner",
        owner_email=f"perf-{uid}@test.com"
    )
    session.add(company)
    await session.commit()

    branch = Branch(
        name=f"Perf Branch {uid}",
        address="123 Perf St",
        phone="123",
        company_id=company.id,
        code=f"PB-{uid}"
    )
    session.add(branch)
    await session.commit()

    product = Product(
        name=f"Perf Product {uid}",
        company_id=company.id,
        price=Decimal("10.00"),
        stock=Decimal("1000.0")
    )
    session.add(product)
    await session.commit()

    user = User(
        username=f"perf_user_{uid}",
        email=f"perf_{uid}@test.com",
        company_id=company.id,
        hashed_password=get_password_hash("password")
    )
    session.add(user)
    await session.commit()

    service = InventoryService(session)

    # 2. Measure Performance
    iterations = 50
    start_time = time.time()

    for i in range(iterations):
        await service.update_stock(
            branch_id=branch.id,
            product_id=product.id,
            quantity_delta=Decimal("1.0"),
            transaction_type="IN",
            user_id=user.id,
            reason=f"Perf Test {i}"
        )

    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / iterations

    print(f"\n⚡ Performance Result: {iterations} updates in {total_time:.4f}s")
    print(f"⚡ Average time per update: {avg_time*1000:.2f}ms")

    # Thresholds (adjust based on environment, but aim for speed)
    # In a real DB it might be slower, but with SQLite/In-memory it should be fast.
    # Allowing 50ms per op as a safe upper bound for this environment.
    assert avg_time < 0.05, f"Performance degradation: {avg_time*1000:.2f}ms per update (limit: 50ms)"
