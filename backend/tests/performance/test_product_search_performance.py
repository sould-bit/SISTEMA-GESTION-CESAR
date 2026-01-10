
import pytest
import time
import asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.product_service import ProductService
from app.models.company import Company
from app.models.category import Category
from app.models.product import Product
from app.schemas.products import ProductCreate
import uuid

@pytest.mark.asyncio
@pytest.mark.performance
async def test_product_search_load(db_session: AsyncSession):
    """
    ⚡ PERFORMANCE TEST: Measure Product Search latency under load.

    Target: Search should take < 50ms (0.05s) even with 1000 items in DB.
    """
    session = db_session

    # 1. Setup Data - Create a Company and Category
    uid = str(uuid.uuid4())[:8]
    company = Company(name=f"Perf Search Co {uid}", slug=f"perf-search-{uid}")
    session.add(company)
    await session.commit()

    category = Category(name=f"Perf Cat {uid}", company_id=company.id)
    session.add(category)
    await session.commit()

    service = ProductService(session)

    # 2. Seed DB with 1000 products
    print("\n⚡ Seeding 1000 products...")
    start_seed = time.time()

    products_to_add = []
    for i in range(1000):
        # We use direct DB add for speed in setup, avoiding service overhead for seeding
        p = Product(
            name=f"PerfItem {i} {uid}",
            company_id=company.id,
            category_id=category.id,
            price=Decimal("10.00"),
            stock=Decimal("100"),
            is_active=True
        )
        session.add(p)
        if i % 100 == 0:
            await session.flush() # Periodic flush

    await session.commit()
    seed_time = time.time() - start_seed
    print(f"⚡ Seeding took: {seed_time:.2f}s")

    # 3. Measure Search Performance (Single Request Latency)
    # Search for a term that matches subset or none
    search_term = "PerfItem 500"

    start_search = time.time()
    results = await service.get_products_for_list(company.id, search=search_term)
    end_search = time.time()

    latency = end_search - start_search
    print(f"⚡ Search Latency (1 item): {latency:.4f}s")

    assert len(results) == 1
    assert results[0].name == f"PerfItem 500 {uid}"

    # 4. Measure Search Performance (Broad Search - returning many items)
    search_term_broad = "PerfItem"
    start_search = time.time()
    results_broad = await service.get_products_for_list(company.id, search=search_term_broad)
    end_search = time.time()

    latency_broad = end_search - start_search
    print(f"⚡ Search Latency (1000 items): {latency_broad:.4f}s")

    # Assertions
    # In SQLite memory DB it should be very fast.
    # We set a strict threshold for single item search.
    assert latency < 0.05, f"Search latency too high: {latency:.4f}s (limit: 50ms)"

    # Broad search might take longer due to object overhead
    assert latency_broad < 0.20, f"Broad search latency too high: {latency_broad:.4f}s"
