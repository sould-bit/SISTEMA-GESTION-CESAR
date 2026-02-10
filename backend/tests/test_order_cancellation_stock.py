import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Product, Company, Branch, User, Ingredient
from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem
from app.models.order import OrderStatus
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order_service import OrderService
from app.services.inventory_service import InventoryService
from app.services.notification_service import NotificationService
from unittest.mock import AsyncMock
import uuid

@pytest.mark.asyncio
async def test_order_cancellation_stock_return(
    db_session: AsyncSession,
    test_company: Company,
    test_branch: Branch,
    test_user: User
):
    """
    Test: Al cancelar un pedido, los insumos deben volver al inventario.
    Incluso si el pedido estaba 'en preparación'.
    """
    # Mock NotificationService to avoid WS issues in tests
    NotificationService.notify_order_status = AsyncMock()
    NotificationService.notify_order_created = AsyncMock()
    
    session = db_session
    uid = str(uuid.uuid4())[:8]

    # Insumo (Ingrediente)
    ing_meat = Ingredient(
        name=f"Meat {uid}", 
        sku=f"SKU-M-{uid}",
        company_id=test_company.id, 
        base_unit="gr", 
        current_cost=Decimal("0.05"),
        is_active=True
    )
    session.add(ing_meat)
    await session.commit()
    
    # Producto con Receta
    prod_burger = Product(
        name=f"Burger {uid}", 
        company_id=test_company.id, 
        price=Decimal("15.00"), 
        is_active=True
    )
    session.add(prod_burger)
    await session.commit()
    
    # Receta (100gr de carne)
    recipe = Recipe(
        company_id=test_company.id, 
        product_id=prod_burger.id, 
        name="Std Burger",
        is_active=True
    )
    session.add(recipe)
    await session.commit()
    
    r_item = RecipeItem(
        recipe_id=recipe.id, 
        ingredient_id=ing_meat.id, 
        company_id=test_company.id,
        gross_quantity=Decimal("100.00"), 
        measure_unit="gr",
        calculated_cost=Decimal("5.00")
    )
    session.add(r_item)
    
    # Asociar receta al producto
    prod_burger.active_recipe_id = recipe.id
    session.add(prod_burger)
    await session.commit()
    
    # 2. Inicializar Inventario (500gr de carne)
    inv_service = InventoryService(session)
    await inv_service.update_ingredient_stock(
        branch_id=test_branch.id, 
        ingredient_id=ing_meat.id, 
        quantity_delta=Decimal("500.00"), 
        transaction_type="IN", 
        user_id=test_user.id,
        cost_per_unit=Decimal("0.05"),
        reason="Initial Stock"
    )
    
    # Verificar stock inicial
    inv_meat = await inv_service.get_ingredient_stock(test_branch.id, ing_meat.id)
    assert inv_meat.stock == Decimal("500.00")
    
    # 3. Crear Pedido (1 Burger -> consume 100gr)
    print("\n[STEP 1] Creating order...")
    order_service = OrderService(session)
    order_data = OrderCreate(
        branch_id=test_branch.id,
        items=[OrderItemCreate(product_id=prod_burger.id, quantity=Decimal("1.00"))]
    )
    
    try:
        order = await order_service.create_order(order_data, test_company.id, user_id=test_user.id)
    except Exception as e:
        print(f"Error creating order: {e}")
        import traceback
        traceback.print_exc()
        raise e
    
    # Refresh inv_meat to verify deduction
    inv_meat = await inv_service.get_ingredient_stock(test_branch.id, ing_meat.id)
    assert inv_meat.stock == Decimal("400.00")
    print(f"\n[STEP 1] Order created. Stock: {inv_meat.stock} (Expected 400)")

    # 4. Cambiar a 'en preparación'
    await order_service.update_status(order.id, OrderStatus.PREPARING, test_company.id, user=test_user)
    
    # Verify stock remains 400
    inv_meat = await inv_service.get_ingredient_stock(test_branch.id, ing_meat.id)
    assert inv_meat.stock == Decimal("400.00")
    print(f"[STEP 2] Status changed to PREPARING. Stock: {inv_meat.stock} (Expected 400)")

    # 5. CANCELAR Pedido
    print("[STEP 3] Cancelling order...")
    # Change user role to allow cancellation from PREPARING (requires manager/admin)
    test_user.role = "admin"
    
    try:
        await order_service.update_status(order.id, OrderStatus.CANCELLED, test_company.id, user=test_user)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e
    
    # 6. VERIFICAR RETORNO DE STOCK
    # Re-consultar para asegurar que vemos los datos actualizados post-commit
    inv_meat = await inv_service.get_ingredient_stock(test_branch.id, ing_meat.id)
    
    print(f"[FINAL] Order CANCELLED. Stock: {inv_meat.stock} (Expected 500)")
    
    assert inv_meat.stock == Decimal("500.00"), f"Stock should be 500 after cancellation, but got {inv_meat.stock}"
    
    # 7. Verificar Kardex (Audit Log)
    history = await inv_service.get_ingredient_history(ing_meat.id)
    print(f"History: {[h['transaction_type'] for h in history]}")
    
    print("Test passed: Stock returned correctly on cancellation.")
