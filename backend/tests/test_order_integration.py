import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models import Product, Company, Branch, User, Inventory
from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order_service import OrderService
from app.services.inventory_service import InventoryService
import uuid

@pytest.mark.asyncio
async def test_order_stock_deduction(db_session: AsyncSession):
    """
    Test Integration: Order -> Inventory
    1. Direct Product Sale: Deduct stock from the product itself.
    2. Recipe Sale: Deduct stock from ingredients.
    """
    session = db_session
    uid = str(uuid.uuid4())[:8]

    # 1. Setup
    company = Company(name=f"OrderInt Co {uid}", slug=f"ord-int-{uid}", owner_name="Ow", owner_email=f"o{uid}@t.com")
    session.add(company)
    await session.commit()
    
    branch = Branch(name=f"Main {uid}", code=f"M_{uid}", address="St", phone="1", company_id=company.id)
    session.add(branch)
    await session.commit()
    
    # Products
    # A: Simple Item (Soda) - Stock 20
    prod_soda = Product(name=f"Soda {uid}", company_id=company.id, price=Decimal("2.00"), stock=None, is_active=True)
    session.add(prod_soda)
    
    # B: Burger (Recipe) - No Stock (made on demand)
    prod_burger = Product(name=f"Burger {uid}", company_id=company.id, price=Decimal("10.00"), stock=None, is_active=True)
    session.add(prod_burger)
    
    # Ingredients for Burger
    ing_meat = Product(name=f"Meat {uid}", company_id=company.id, price=Decimal("5.00"), stock=None, is_active=True)
    ing_bun = Product(name=f"Bun {uid}", company_id=company.id, price=Decimal("1.00"), stock=None, is_active=True)
    session.add(ing_meat)
    session.add(ing_bun)
    
    # User for Order
    user = User(username=f"waiter_{uid}", email=f"w_{uid}@test.com", hashed_password="pw", company_id=company.id, role_id=None)
    session.add(user)

    await session.commit()
    
    # 2. Init Inventory
    inv_service = InventoryService(session)
    # Soda: 20
    await inv_service.update_stock(branch.id, prod_soda.id, Decimal("20.00"), "IN", 1, "Init")
    # Meat: 10
    await inv_service.update_stock(branch.id, ing_meat.id, Decimal("10.00"), "IN", 1, "Init")
    # Bun: 10
    await inv_service.update_stock(branch.id, ing_bun.id, Decimal("10.00"), "IN", 1, "Init")
    
    # 3. Create Recipe (1 Meat + 1 Bun)
    recipe = Recipe(company_id=company.id, product_id=prod_burger.id, name="Std Burger", total_cost=Decimal("6.00"))
    session.add(recipe)
    await session.commit()
    
    r_item1 = RecipeItem(recipe_id=recipe.id, ingredient_product_id=ing_meat.id, quantity=Decimal("1.00"), unit="pc")
    r_item2 = RecipeItem(recipe_id=recipe.id, ingredient_product_id=ing_bun.id, quantity=Decimal("1.00"), unit="pc")
    session.add(r_item1)
    session.add(r_item2)
    await session.commit()
    
    # 4. Create Order
    # 2 Sodas + 2 Burgers
    # Expected Deductions:
    # Soda: -2 => Remaining 18
    # Meat: -2 => Remaining 8
    # Bun: -2 => Remaining 8
    
    order_service = OrderService(session)
    
    order_data = OrderCreate(
        branch_id=branch.id,
        customer_notes="Test",
        items=[
            OrderItemCreate(product_id=prod_soda.id, quantity=Decimal("2.00")),
            OrderItemCreate(product_id=prod_burger.id, quantity=Decimal("2.00"))
        ]
    )
    
    print("\n--- Creating Order ---")
    order = await order_service.create_order(order_data, company.id, user_id=user.id)
    
    assert order.id is not None
    print(f"Order Created: {order.order_number}")
    
    # 5. Verify Stocks
    inv_soda = await inv_service.get_stock(branch.id, prod_soda.id)
    inv_meat = await inv_service.get_stock(branch.id, ing_meat.id)
    inv_bun = await inv_service.get_stock(branch.id, ing_bun.id)
    
    assert inv_soda.stock == Decimal("18.00")
    print(f"Soda Stock: {inv_soda.stock} (Expected 18)")
    
    assert inv_meat.stock == Decimal("8.00")
    print(f"Meat Stock: {inv_meat.stock} (Expected 8)")
    
    assert inv_bun.stock == Decimal("8.00")
    print(f"Bun Stock: {inv_bun.stock} (Expected 8)")
    
    print("Integration Tests Passed!")
