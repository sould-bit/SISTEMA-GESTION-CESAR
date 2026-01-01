import pytest
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Product, Recipe, RecipeItem, Category
from app.services.recipe_service import RecipeService
from app.schemas.recipes import RecipeCreate, RecipeItemCreate, RecipeUpdate, RecipeItemAddOrUpdate

@pytest.mark.asyncio
async def test_create_recipe_flow(db_session, test_company, test_category):
    """
    Test completo del flujo de creación de recetas:
    1. Crear ingredientes
    2. Crear producto final
    3. Crear receta
    4. Verificar cálculo de costos
    """
    service = RecipeService(db_session)

    # 1. Crear ingredientes
    ingredient_1 = Product(
        name="Carne Molida",
        price=Decimal("5000.00"),  # Precio por unidad (ej. kg)
        company_id=test_company.id,
        category_id=test_category.id,
        is_active=True
    )
    ingredient_2 = Product(
        name="Pan Hamburguesa",
        price=Decimal("1000.00"),
        company_id=test_company.id,
        category_id=test_category.id,
        is_active=True
    )
    db_session.add_all([ingredient_1, ingredient_2])
    await db_session.commit()
    await db_session.refresh(ingredient_1)
    await db_session.refresh(ingredient_2)

    # 2. Crear producto final (Hamburguesa)
    final_product = Product(
        name="Hamburguesa Especial",
        price=Decimal("15000.00"),
        company_id=test_company.id,
        category_id=test_category.id,
        is_active=True
    )
    db_session.add(final_product)
    await db_session.commit()
    await db_session.refresh(final_product)

    # 3. Crear receta
    # 200g de carne, 1 pan
    recipe_data = RecipeCreate(
        name="Receta Hamburguesa Especial",
        description="Receta estandar",
        product_id=final_product.id,
        items=[
            RecipeItemCreate(
                ingredient_product_id=ingredient_1.id,
                quantity=Decimal("0.2"),  # 200g
                unit="kg"
            ),
            RecipeItemCreate(
                ingredient_product_id=ingredient_2.id,
                quantity=Decimal("1"),
                unit="unidad"
            )
        ]
    )

    recipe = await service.create_recipe(recipe_data, test_company.id)

    # 4. Verificar creación
    assert recipe.id is not None
    assert recipe.product_id == final_product.id
    assert len(recipe.items) == 2
    
    # 5. Verificar Costos
    # Carne: 0.2 * 5000 = 1000
    # Pan: 1 * 1000 = 1000
    # Total esperando: 2000
    expected_cost = Decimal("2000.00")
    assert recipe.total_cost == expected_cost

@pytest.mark.asyncio
async def test_update_recipe_items(db_session, test_company, test_category):
    """Test actualización de items y recálculo"""
    service = RecipeService(db_session)

    # Setup básico (Ingrediente y Producto)
    ingrediente = Product(name="Queso", price=Decimal("2000.00"), company_id=test_company.id, category_id=test_category.id)
    producto = Product(name="Sandwich Queso", price=Decimal("5000.00"), company_id=test_company.id, category_id=test_category.id)
    db_session.add_all([ingrediente, producto])
    await db_session.commit()

    # Receta inicial
    recipe_data = RecipeCreate(
        name="Sandwich Base",
        product_id=producto.id,
        items=[
            RecipeItemCreate(ingredient_product_id=ingrediente.id, quantity=Decimal("1"), unit="loncha")
        ]
    )
    recipe = await service.create_recipe(recipe_data, test_company.id)
    assert recipe.total_cost == Decimal("2000.00")

    # Actualizar items (Doble queso)
    new_items = [
        RecipeItemCreate(ingredient_product_id=ingrediente.id, quantity=Decimal("2"), unit="loncha")
    ]
    
    updated_recipe = await service.update_recipe_items(recipe.id, test_company.id, new_items)
    
    # Verificar nuevo costo (2 * 2000 = 4000)
    assert updated_recipe.total_cost == Decimal("4000.00")
    assert len(updated_recipe.items) == 1
    assert updated_recipe.items[0].quantity == Decimal("2")

@pytest.mark.asyncio
async def test_recalculate_cost(db_session, test_company, test_category):
    """Test recálculo de costos cuando cambia el precio del insumo"""
    service = RecipeService(db_session)

    # 1. Crear insumo y receta
    insumo = Product(name="Aguacate", price=Decimal("100.00"), company_id=test_company.id, category_id=test_category.id)
    plato = Product(name="Tostada Aguacate", price=Decimal("500.00"), company_id=test_company.id, category_id=test_category.id)
    db_session.add_all([insumo, plato])
    await db_session.commit()

    recipe = await service.create_recipe(
        RecipeCreate(
            name="Receta Tostada", 
            product_id=plato.id, 
            items=[RecipeItemCreate(ingredient_product_id=insumo.id, quantity=Decimal("2"), unit="unidad")]
        ),
        test_company.id
    ) # Costo inicial: 2 * 100 = 200

    assert recipe.total_cost == Decimal("200.00")

    # 2. Cambiar precio del insumo (Inflación!)
    insumo.price = Decimal("150.00")
    await db_session.commit()

    # 3. Recalcular
    result = await service.recalculate_cost(recipe.id, test_company.id)

    # 4. Verificar
    assert result.old_total_cost == Decimal("200.00")
    assert result.new_total_cost == Decimal("300.00") # 2 * 150
    assert result.difference == Decimal("100.00")

