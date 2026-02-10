import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models import Product, Company, Branch, User, Inventory
from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem
from app.models.ingredient import Ingredient, IngredientType
from app.schemas.order import OrderCreate, OrderItemCreate, OrderItemUpdate
from app.services.order_service import OrderService
from app.services.inventory_service import InventoryService
from sqlalchemy.orm import selectinload
import uuid

@pytest.mark.asyncio
async def test_order_edit_flow(db_session: AsyncSession):
    """
    Test Integration: Order Edit -> Inventory
    1. Create Order
    2. Update Item (Increase Quantity) -> Deduct more stock
    3. Update Item (Decrease Quantity) -> Restore stock
    4. Remove Item -> Restore all stock
    """
    session = db_session
    uid = str(uuid.uuid4())[:8]

    # 1. Setup
    company = Company(name=f"OrderEdit Co {uid}", slug=f"ord-edit-{uid}", owner_name="Ow", owner_email=f"o{uid}@t.com")
    session.add(company)
    await session.commit()
    
    branch = Branch(name=f"Main {uid}", code=f"M_{uid}", address="St", phone="1", company_id=company.id)
    session.add(branch)
    await session.commit()
    
    # Products
    # A: Soda - Direct Product Stock - Quantity 20
    prod_soda = Product(name=f"Soda {uid}", company_id=company.id, price=Decimal("2.00"), stock=None, is_active=True)
    session.add(prod_soda)
    
    # B: Burger - Recipe Product - No Stock
    prod_burger = Product(name=f"Burger {uid}", company_id=company.id, price=Decimal("10.00"), stock=None, is_active=True)
    session.add(prod_burger)
    
    # Ingredients for Burger
    ing_meat = Ingredient(
        name=f"Meat {uid}", 
        sku=f"meat-{uid}", 
        base_unit="kg", 
        ingredient_type=IngredientType.RAW,
        company_id=company.id
    )
    ing_bun = Ingredient(
        name=f"Bun {uid}", 
        sku=f"bun-{uid}", 
        base_unit="und", 
        ingredient_type=IngredientType.RAW,
        company_id=company.id
    )
    session.add(ing_meat)
    session.add(ing_bun)
    
    # User for Order
    user = User(username=f"waiter_{uid}", email=f"w_{uid}@test.com", hashed_password="pw", company_id=company.id, role_id=None)
    session.add(user)

    await session.commit()
    await session.refresh(prod_soda)
    await session.refresh(prod_burger)
    await session.refresh(ing_meat)
    await session.refresh(ing_bun)
    
    # 2. Init Inventory
    inv_service = InventoryService(session)
    
    # Soda (Product): 20
    await inv_service.update_stock(branch.id, prod_soda.id, Decimal("20.00"), "IN", user.id, "Init")
    
    # Meat (Ingredient): 10 kg
    await inv_service.update_ingredient_stock(
        branch_id=branch.id, 
        ingredient_id=ing_meat.id, 
        quantity_delta=Decimal("10.00"), 
        transaction_type="IN", 
        user_id=user.id, 
        reference_id="Init",
        cost_per_unit=Decimal("5.00"),
        supplier="Test"
    )
    
    # Bun (Ingredient): 10 und
    await inv_service.update_ingredient_stock(
        branch_id=branch.id, 
        ingredient_id=ing_bun.id, 
        quantity_delta=Decimal("10.00"), 
        transaction_type="IN", 
        user_id=user.id, 
        reference_id="Init",
        cost_per_unit=Decimal("1.00"),
        supplier="Test"
    )
    
    # 3. Create Recipe (1 Meat + 1 Bun)
    recipe = Recipe(company_id=company.id, product_id=prod_burger.id, name="Std Burger", total_cost=Decimal("6.00"))
    session.add(recipe)
    await session.commit()
    await session.refresh(recipe)
    
    # Recipe Items linked to Ingredients
    r_item1 = RecipeItem(
        recipe_id=recipe.id, 
        ingredient_id=ing_meat.id, 
        company_id=company.id,
        gross_quantity=Decimal("1.00"), 
        measure_unit="kg"
    )
    r_item2 = RecipeItem(
        recipe_id=recipe.id, 
        ingredient_id=ing_bun.id, 
        company_id=company.id,
        gross_quantity=Decimal("1.00"), 
        measure_unit="und"
    )
    session.add(r_item1)
    session.add(r_item2)
    await session.commit()
    
    # 4. Create Order
    # 2 Sodas + 2 Burgers
    # Expected Consumption:
    # Soda: 2 -> Remaining 18
    # Meat: 2*1 = 2 -> Remaining 8
    # Bun: 2*1 = 2 -> Remaining 8
    
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
    
    # Verify Initial Stocks
    inv_soda = await inv_service.get_stock(branch.id, prod_soda.id)
    inv_meat = await inv_service.get_ingredient_stock(branch.id, ing_meat.id)
    inv_bun = await inv_service.get_ingredient_stock(branch.id, ing_bun.id)
    
    assert inv_soda.stock == Decimal("18.00")
    assert inv_meat.stock == Decimal("8.00")
    assert inv_bun.stock == Decimal("8.00")

    print(f"Initial Order Created & Stock Correct. Order ID: {order.id}")
    
    # Need to reload order to get items with IDs
    # Using helper from OrderService
    full_order = await order_service.get_order_orm(order.id, company.id)
    
    # 5. Get Items
    item_soda = next(i for i in full_order.items if i.product_id == prod_soda.id)
    item_burger = next(i for i in full_order.items if i.product_id == prod_burger.id)

    # 6. UPDATE ITEM: Increase Soda from 2 to 3
    # Delta: +1 consumption.
    # Expected: Soda Stock 18 -> 17
    print("Updating Soda Quantity 2 -> 3")
    update_data = OrderItemUpdate(quantity=Decimal("3.00"))
    
    # Using the update_order_item method which handles transaction internally?
    # No, OrderService methods usually reuse session but commit. 
    # Let's verify if update_order_item commits. Yes it does.
    # So we should be careful with session used in test?
    # db_session fixture usually is a transaction that rolls back? 
    # If the service commits, it might break test isolation or subsequent queries.
    # But let's assume standard behavior.
    
    updated_order = await order_service.update_order_item(
        order.id, item_soda.id, update_data.model_dump(exclude_unset=True), company.id, user.id
    )
    
    # Refresh inventory
    # Need to start new transaction or use session correctly?
    # Since service commits, the session is active for next query.
    inv_soda_2 = await inv_service.get_stock(branch.id, prod_soda.id)
    assert inv_soda_2.stock == Decimal("17.00") # 20 - 3 = 17
    print("Soda Stock updated correctly to 17")

    # 7. UPDATE ITEM: Decrease Burger from 2 to 1
    # Delta: -1 consumption (Restore 1)
    # Expected: Meat Stock 8 -> 9
    print("Updating Burger Quantity 2 -> 1")
    update_data_burger = OrderItemUpdate(quantity=Decimal("1.00"))
    updated_order_2 = await order_service.update_order_item(
        order.id, item_burger.id, update_data_burger.model_dump(exclude_unset=True), company.id, user.id
    )

    inv_meat_2 = await inv_service.get_ingredient_stock(branch.id, ing_meat.id)
    assert inv_meat_2.stock == Decimal("9.00")
    print("Meat Stock updated correctly to 9")

    # 8. REMOVE ITEM: Remove Burger (remaining 1)
    # Expected: Meat Stock 9 -> 10 (Restored fully)
    print("Removing Burger Item")
    # Need to get item id again? Iterate updated_order_2
    item_burger_latest = next(i for i in updated_order_2.items if i.product_id == prod_burger.id)
    
    await order_service.remove_order_item(order.id, item_burger_latest.id, company.id, user.id)

    inv_meat_3 = await inv_service.get_ingredient_stock(branch.id, ing_meat.id)
    assert inv_meat_3.stock == Decimal("10.00")
    print("Meat Stock restored correctly to 10")
