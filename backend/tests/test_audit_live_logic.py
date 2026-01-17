import pytest
from httpx import AsyncClient
from app.main import app
from app.models.product import Product
from app.models.ingredient import Ingredient, IngredientType
from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem
from app.models.order import OrderStatus
from decimal import Decimal
import uuid
from sqlmodel import select

@pytest.mark.asyncio
async def test_sales_fifo_consumption(test_client, test_user, db_session, test_branch, auth_headers):
    """
    Verifies that a Sale triggers FIFO consumption of Ingredients via Recipe.
    """
    # 1. Create Ingredient (Calculated Cost mechanism)
    ingredient = Ingredient(
        company_id=test_user.company_id,
        name="Carne Preparada",
        sku="CARNE-PREP-001",
        type=IngredientType.PROCESSED,
        base_unit="und",
        current_cost=Decimal("2.50")
    )
    db_session.add(ingredient)
    await db_session.commit()
    await db_session.refresh(ingredient)

    # 2. Add Stock (Two Batches to test FIFO)
    # Batch 1: Oldest
    from app.services.inventory_service import InventoryService
    inv_service = InventoryService(db_session)
    
    # We use update_ingredient_stock to add stock (simulating Production Output)
    # Batch 1: 10 units @ $2.50
    await inv_service.update_ingredient_stock(
        branch_id=test_branch.id,
        ingredient_id=ingredient.id,
        quantity_delta=Decimal(10),
        transaction_type="PRODUCTION_IN",
        cost_per_unit=Decimal("2.50"),
        supplier="Internal Prod 1",
        user_id=test_user.id
    )
    
    # Batch 2: 10 units @ $3.00 (Newer)
    await inv_service.update_ingredient_stock(
        branch_id=test_branch.id,
        ingredient_id=ingredient.id,
        quantity_delta=Decimal(10),
        transaction_type="PRODUCTION_IN",
        cost_per_unit=Decimal("3.00"),
        supplier="Internal Prod 2", # Created slightly later
        user_id=test_user.id
    )

    # Verify Total Stock = 20
    inv = await inv_service.get_ingredient_stock(test_branch.id, ingredient.id)
    assert inv.stock == 20

    # 3. Create Product & Recipe
    product = Product(
        company_id=test_user.company_id,
        name="Hamburguesa Test",
        price=Decimal("10.00"),
        is_active=True
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    recipe = Recipe(
        company_id=test_user.company_id,
        product_id=product.id,
        name="Receta Test"
    )
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)

    # Recipe uses 1 unit of Carne per Burger
    r_item = RecipeItem(
        recipe_id=recipe.id,
        company_id=test_user.company_id,
        ingredient_id=ingredient.id,
        gross_quantity=Decimal("1.0"),
        measure_unit="und"
    )
    db_session.add(r_item)
    await db_session.commit()

    # 4. Create Order (Sale of 12 Burgers)
    # FIFO: Should consume 10 from Batch 1 (Old) and 2 from Batch 2 (New)
    order_payload = {
        "branch_id": test_branch.id,
        "customer_id": None,
        "delivery_type": "DINE_IN",
        "items": [
            {
                "product_id": product.id,
                "quantity": 12,
                "modifiers": [],
                "notes": ""
            }
        ],
        "payments": []
    }

    response = await test_client.post("/orders/", json=order_payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == OrderStatus.PENDING.value

    # 5. Verify Stock Consumption
    # Total Stock should be 20 - 12 = 8
    await db_session.refresh(inv)
    assert inv.stock == 8

    # Verify Batches logic via Intelligence Service (Implicitly checks transaction history or we check batches directly)
    # Let's check batches directly
    from app.models.ingredient_batch import IngredientBatch
    stmt = select(IngredientBatch).where(
        IngredientBatch.ingredient_id == ingredient.id, 
        IngredientBatch.branch_id == test_branch.id
    ).order_by(IngredientBatch.acquired_at.asc())
    batches = (await db_session.execute(stmt)).scalars().all()
    
    # Expected: 2 Batches.
    # Batch 1 (Old): Quantity 10. Consumed 10. Remaining 0. Active False? (If logic deactivates empty batches)
    # Batch 2 (New): Quantity 10. Consumed 2. Remaining 8.
    
    b1 = batches[0] # Internal Prod 1
    b2 = batches[1] # Internal Prod 2
    
    assert b1.supplier == "Internal Prod 1"
    assert b1.quantity_remaining == 0
    assert b1.is_active == False
    
    assert b2.supplier == "Internal Prod 2"
    assert b2.quantity_remaining == 8
    assert b2.is_active == True

    # 6. Inject Adjustment (Loss/Waste) to trigger recommendation
    # Stock is 8. We adjust it down by 2 (Simulating count of 6).
    await inv_service.update_ingredient_stock(
        branch_id=test_branch.id,
        ingredient_id=ingredient.id,
        quantity_delta=Decimal("-2"),
        transaction_type="ADJUST", # This will be picked up by analytics
        cost_per_unit=Decimal("0.00"), # Adjustment usually logs cost diff but for qty stats it matters most
        user_id=test_user.id
    )

    # 7. Test Intelligence Service
    # Theoretical: 12 units
    # Adjustments: -2 (Loss)
    # Real Usage = Theoretical (12) - Adjustment (-2) = 14
    # Efficiency = 12 / 14 = 0.857...
    # This is < 0.9, so we should get a recommendation.

    response_intel = await test_client.get(
        f"/intelligence/recipe-efficiency/{recipe.id}",
        headers=auth_headers
    )
    assert response_intel.status_code == 200
    intel_data = response_intel.json()

    rec_list = intel_data["recommendations"]
    assert len(rec_list) > 0
    rec_item = rec_list[0]
    
    assert rec_item["efficiency"] < 0.9
    # Suggested Qty = Current (1.0) / Efficiency (0.857) = 1.16...
    assert rec_item["suggested_quantity"] > 1.0

    # 8. Apply Calibration
    new_qty = rec_item["suggested_quantity"]
    calib_payload = {
        "items": [
            {
                "ingredient_id": str(ingredient.id),
                "new_quantity": new_qty
            }
        ]
    }
    resp_calib = await test_client.post(
        f"/intelligence/calibrate-recipe/{recipe.id}",
        json=calib_payload,
        headers=auth_headers
    )
    assert resp_calib.status_code == 200
    
    # Verify Recipe Item Updated
    await db_session.refresh(r_item)
    # Check approximately equal (float vs Decimal)
    assert abs(float(r_item.gross_quantity) - new_qty) < 0.001
