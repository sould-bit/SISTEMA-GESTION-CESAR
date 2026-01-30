import pytest
import uuid
from decimal import Decimal
from app.services.inventory_service import InventoryService
from app.services.recipe_service import RecipeService
from app.models.ingredient import Ingredient
from app.models.unit_conversion import UnitConversion

@pytest.mark.asyncio
@pytest.mark.integration
async def test_live_recipe_explosion(db_session, test_company, test_branch, test_product):
    """
    Test the "Live Recipe" logic:
    1. Create Ingredient with Stock.
    2. Create Recipe for Product using Ingredient.
    3. Simulate Order (Explosion).
    4. Verify Ingredient Stock deducted.
    """

    # 1. Setup Services
    inv_service = InventoryService(db_session)
    recipe_service = RecipeService(db_session)

    # 2. Create Ingredient (Level C)
    ingredient = Ingredient(
        id=uuid.uuid4(),
        company_id=test_company.id,
        name="Test Meat",
        sku="MEAT-001",
        base_unit="kg",
        current_cost=Decimal("10.00"),
        yield_factor=1.0
    )
    db_session.add(ingredient)
    await db_session.commit()

    # 3. Add Ingredient Stock
    # Initial: 10kg
    await inv_service.update_ingredient_stock(
        branch_id=test_branch.id,
        ingredient_id=ingredient.id,
        quantity_delta=Decimal("10.000"),
        transaction_type="IN"
    )

    # 4. Create Conversion (g -> kg) if not exists
    # Assuming seed_units ran, but let's ensure for test isolation
    conv = UnitConversion(
        id=uuid.uuid4(),
        from_unit="g",
        to_unit="kg",
        factor=0.001
    )
    db_session.add(conv)
    await db_session.commit()

    # 5. Create Recipe (Level B)
    # 1 Burger = 200g Meat
    items_data = [
        {
            "ingredient_id": ingredient.id,
            "gross_quantity": 200.0,
            "net_quantity": 180.0,
            "measure_unit": "g"
        }
    ]

    recipe = await recipe_service.create_recipe(
        product_id=test_product.id,
        company_id=test_company.id,
        name="Burger Recipe",
        items_data=items_data
    )

    # Link Recipe to Product (Level A -> B)
    test_product.active_recipe_id = recipe.id
    db_session.add(test_product)
    await db_session.commit()

    # 6. Simulate Sale (Explosion)
    # Sell 2 Burgers
    # Expected Deduction: 2 * 200g = 400g = 0.4kg
    await inv_service.process_recipe_deduction(
        branch_id=test_branch.id,
        product_id=test_product.id,
        quantity_sold=2,
        user_id=1, # Mock user
        reference_id="ORDER-123"
    )

    # 7. Verify Result
    stock_record = await inv_service.get_ingredient_stock(test_branch.id, ingredient.id)
    assert stock_record is not None
    # 10.0 - 0.4 = 9.6
    assert stock_record.stock == Decimal("9.600")
