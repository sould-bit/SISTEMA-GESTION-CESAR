import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.recipe import Recipe
from app.models.product import Product
from app.models.ingredient import Ingredient
from app.models.company import Company
from app.services.recipe_service import RecipeService
from app.services.ingredient_service import IngredientService
from app.services.cost_engine_service import CostEngineService
import uuid

@pytest.mark.asyncio
async def test_cost_propagation_flow(db_session: AsyncSession):
    session = db_session
    uid = str(uuid.uuid4())[:8]

    # 1. Setup Data
    company = Company(name=f"Prop Co {uid}", slug=f"prop-co-{uid}", owner_name="Owner", owner_email=f"prop@{uid}.com")
    session.add(company)
    await session.commit()

    # Ingredient A (Cheese) - $20
    ing_cheese = Ingredient(
        name=f"Cheese {uid}", sku=f"cheese-{uid}", base_unit="kg",
        current_cost=Decimal("20.00"), company_id=company.id, is_active=True
    )
    session.add(ing_cheese)
    await session.commit()
    
    # Product (Pizza)
    pizza = Product(name=f"Pizza {uid}", company_id=company.id, price=Decimal("100.00"), stock=Decimal("0"), is_active=True)
    session.add(pizza)
    await session.commit()

    # 2. Create Recipe (0.5 kg Cheese)
    # Expected Initial Cost: 0.5 * 20 = 10.00
    recipe_service = RecipeService(session)
    items_data = [
        {"ingredient_id": ing_cheese.id, "gross_quantity": Decimal("0.500"), "measure_unit": "kg", "net_quantity": None},
    ]
    
    recipe = await recipe_service.create_recipe(
        product_id=pizza.id,
        company_id=company.id,
        name=f"Salami Pizza {uid}",
        items_data=items_data
    )
    
    assert recipe.total_cost == Decimal("10.00")
    print(f"Initial Recipe Cost: {recipe.total_cost}")

    # 3. Update Ingredient Cost via Service (Simulating API call)
    # New Cost: $30. Expected Recipe Cost: 0.5 * 30 = 15.00
    print("\n--- Updating Ingredient Cost via Service ---")
    
    ing_service = IngredientService(session)
    # Update cost and trigger propagation
    # We simulate what the router does: Update Cost -> Recalculate All
    
    # Step A: Update the ingredient cost
    updated_ing = await ing_service.update_cost_from_purchase(
        ingredient_id=ing_cheese.id,
        new_cost=Decimal("30.00"),
        user_id=None,
        reason="Inflation"
    )
    assert updated_ing.current_cost == Decimal("30.00")
    
    # Step B: Trigger the propagation (The Router does this explicitly, so we test the Engine here)
    cost_engine = CostEngineService(session)
    await cost_engine.recalculate_all_recipes_for_ingredient(ing_cheese.id)

    # 4. Verify Recipe Updated
    # Need to refresh or fetch fresh
    result = await session.execute(select(Recipe).where(Recipe.id == recipe.id))
    recipe_updated = result.scalar_one()
    
    print(f"Updated Recipe Cost: {recipe_updated.total_cost}")
    assert recipe_updated.total_cost == Decimal("15.00")
    
    print("Cost Propagation Test Passed!")
