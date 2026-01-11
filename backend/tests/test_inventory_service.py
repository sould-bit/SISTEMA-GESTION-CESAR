import pytest
from decimal import Decimal
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.inventory import Inventory, InventoryTransaction
from app.services.inventory_service import InventoryService
from app.models.product import Product
from app.models.branch import Branch
from app.models.company import Company
from app.models.user import User

@pytest.mark.asyncio
async def test_inventory_flow(db_session: AsyncSession):
    """
    Test completo del flujo de inventario (ASYNC Refactor):
    NOTE: Argument name must be `db_session` to match conftest fixture.
    """
    session = db_session
    
    # 1. Setup Data
    import uuid
    uid = str(uuid.uuid4())[:8]
    
    company = Company(
        name=f"Test Company Inv {uid}", 
        slug=f"test-inv-co-{uid}", 
        owner_name="Test Owner", 
        owner_email=f"test-{uid}@inv.com"
    )
    session.add(company)
    await session.commit()
    
    branch = Branch(
        name=f"Main Branch {uid}", 
        code=f"TST{uid[:4].upper()}",  # Required field
        address="123 St", 
        phone="123", 
        company_id=company.id
    )
    session.add(branch)
    await session.commit()
    
    product = Product(
        name=f"Burger Meat {uid}", 
        company_id=company.id, 
        price=Decimal("10.00"), 
        stock=None
    )
    session.add(product)
    await session.commit()
    
    user = User(
        username=f"inv_manager_{uid}", 
        email=f"inv_{uid}@test.com", 
        company_id=company.id, 
        role_id=None
    )
    session.add(user)
    await session.commit()
    
    service = InventoryService(session)

    # 2. Update Stock (First time - Should Initialize)
    print("\n--- Testing Initialization & IN Movement (Async) ---")
    inventory = await service.update_stock(
        branch_id=branch.id,
        product_id=product.id,
        quantity_delta=Decimal("100.000"),
        transaction_type="IN",
        user_id=user.id,
        reason="Initial Load"
    )
    
    assert inventory.stock == Decimal("100.000")
    assert inventory.branch_id == branch.id
    
    # Verify Transaction
    result = await session.exec(select(InventoryTransaction).where(InventoryTransaction.inventory_id == inventory.id))
    txn = result.first()
    assert txn is not None
    assert txn.transaction_type == "IN"
    assert txn.quantity == Decimal("100.000")

    # 3. Update Stock (OUT Movement)
    print("\n--- Testing OUT Movement (Async) ---")
    inventory = await service.update_stock(
        branch_id=branch.id,
        product_id=product.id,
        quantity_delta=Decimal("-5.500"),
        transaction_type="SALE",
        user_id=user.id,
        reference_id="ORDER-123"
    )
    
    assert inventory.stock == Decimal("94.500")

    # 4. Low Stock Alert
    print("\n--- Testing Low Stock Alert (Async) ---")
    inventory.min_stock = Decimal("10.000")
    session.add(inventory)
    await session.commit()
    
    # Stock 94.5 > 10
    alerts = await service.get_low_stock_alerts(branch.id)
    assert len(alerts) == 0
    
    # Drain stock
    await service.update_stock(branch.id, product.id, Decimal("-90.000"), "WASTE", user.id)
    # Stock 4.5 < 10
    alerts = await service.get_low_stock_alerts(branch.id)
    
    assert len(alerts) == 1
    assert alerts[0].id == inventory.id
    
    print("Inventory Async Tests Passed!")
