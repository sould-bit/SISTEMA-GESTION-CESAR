import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.recipe import Recipe
from app.models.product import Product
from app.models.ingredient import Ingredient
from app.models.company import Company
from app.services.recipe_service import RecipeService
import uuid

@pytest.mark.asyncio
async def test_recipe_cost_calculation(db_session: AsyncSession):
    session = db_session
    uid = str(uuid.uuid4())[:8]

    # 1. Setup Data
    company = Company(name=f"Recipe Co {uid}", slug=f"recipe-co-{uid}", owner_name="Owner", owner_email=f"rec@{uid}.com")
    session.add(company)
    await session.commit()

    # Ingredient A (Meat) - $10
    ing_a = Ingredient(
        name=f"Meat {uid}", sku=f"meat-{uid}", base_unit="kg",
        current_cost=Decimal("10.00"), company_id=company.id, is_active=True
    )
    # Ingredient B (Bun) - $5
    ing_b = Ingredient(
        name=f"Bun {uid}", sku=f"bun-{uid}", base_unit="unit",
        current_cost=Decimal("5.00"), company_id=company.id, is_active=True
    )
    session.add(ing_a)
    session.add(ing_b)
    
    # Producto Final (Burger)
    final_prod = Product(name=f"Burger {uid}", company_id=company.id, price=Decimal("25.00"), stock=Decimal("0"), is_active=True)
    session.add(final_prod)
    
    await session.commit()
    await session.refresh(ing_a)
    await session.refresh(ing_b)
    
    service = RecipeService(session)

    # 2. Create Recipe (1 Meat kg + 2 Buns)
    # Costo esperado: (1 * 10) + (2 * 5) = 20.00
    items_data = [
        {"ingredient_id": ing_a.id, "gross_quantity": Decimal("1.000"), "measure_unit": "kg", "net_quantity": None},
        {"ingredient_id": ing_b.id, "gross_quantity": Decimal("2.000"), "measure_unit": "unit", "net_quantity": None}
    ]
    
    print("\n--- Creating Recipe ---")
    recipe = await service.create_recipe(
        product_id=final_prod.id,
        company_id=company.id,
        name=f"Standard Burger {uid}",
        items_data=items_data
    )
    
    assert recipe.total_cost == Decimal("20.00")
    print(f"Initial Cost Verified: {recipe.total_cost}")

    # 3. Update Ingredient Price
    # Meat sube a $12. Nuevo costo: (1 * 12) + (2 * 5) = 22.00
    print("\n--- Updating Ingredient Price ---")
    ing_a.current_cost = Decimal("12.00")
    session.add(ing_a)
    await session.commit()

    # Verificar que la receta NO cambia automáticamente (es snapshot)
    recipe_refetched = await service.get_recipe(recipe.id, company.id)
    assert recipe_refetched.total_cost == Decimal("20.00") 

    # 4. Recalculate
    print("\n--- Recalculating Cost ---")
    result = await service.recalculate_cost(recipe.id, company.id)
    
    assert result.new_total_cost == Decimal("22.00")
    assert result.difference == Decimal("2.00")
    
    # Verificar persistencia
    recipe_final = await service.get_recipe(recipe.id, company.id)
    assert recipe_final.total_cost == Decimal("22.00")
    
    print("Recipe Tests Passed!")
