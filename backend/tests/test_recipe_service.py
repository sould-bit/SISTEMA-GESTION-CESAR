import pytest
from decimal import Decimal
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.recipe import Recipe, RecipeItem
from app.models.product import Product
from app.services.recipe_service import RecipeService
from app.schemas.recipes import RecipeCreate, RecipeItemCreate
from app.models.company import Company
import uuid

@pytest.mark.asyncio
async def test_recipe_cost_calculation(db_session: AsyncSession):
    """
    Test de flujo de Recetas:
    1. Setup: Crear Company y Productos (Ingredientes + Producto Final).
    2. Create Recipe: Crear receta con ingredientes.
    3. Verify Cost: Verificar costo total inicial.
    4. Update Price: Cambiar precio de ingrediente.
    5. Recalculate: Recalcular y verificar nuevo costo.
    """
    session = db_session
    uid = str(uuid.uuid4())[:8]

    # 1. Setup Data
    company = Company(name=f"Recipe Co {uid}", slug=f"recipe-co-{uid}", owner_name="Owner", owner_email=f"rec@{uid}.com")
    session.add(company)
    await session.commit()

    # Ingrediente A (Meat) - $10
    ing_a = Product(name=f"Meat {uid}", company_id=company.id, price=Decimal("10.00"), stock=Decimal("100"), is_active=True)
    session.add(ing_a)
    
    # Ingrediente B (Bun) - $5
    ing_b = Product(name=f"Bun {uid}", company_id=company.id, price=Decimal("5.00"), stock=Decimal("100"), is_active=True)
    session.add(ing_b)
    
    # Producto Final (Burger)
    final_prod = Product(name=f"Burger {uid}", company_id=company.id, price=Decimal("25.00"), stock=Decimal("0"), is_active=True)
    session.add(final_prod)
    
    await session.commit()
    
    service = RecipeService(session)

    # 2. Create Recipe (1 Meat + 2 Buns)
    # Costo esperado: (1 * 10) + (2 * 5) = 20.00
    items = [
        RecipeItemCreate(ingredient_product_id=ing_a.id, quantity=Decimal("1.000"), unit="unit"),
        RecipeItemCreate(ingredient_product_id=ing_b.id, quantity=Decimal("2.000"), unit="unit")
    ]
    
    recipe_data = RecipeCreate(
        product_id=final_prod.id,
        name=f"Standard Burger {uid}",
        description="Classic",
        items=items
    )

    print("\n--- Creating Recipe ---")
    recipe = await service.create_recipe(recipe_data, company_id=company.id)
    
    assert recipe.total_cost == Decimal("20.00")
    print(f"Initial Cost Verified: {recipe.total_cost}")

    # 3. Update Ingredient Price
    # Meat sube a $12. Nuevo costo debería ser: (1 * 12) + (2 * 5) = 22.00
    print("\n--- Updating Ingredient Price ---")
    ing_a.price = Decimal("12.00")
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
