import pytest
from httpx import AsyncClient
from app.models.product import Product
from app.models.ingredient import Ingredient, IngredientType
from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem
from app.models.order import OrderStatus
from decimal import Decimal
import uuid

@pytest.mark.asyncio
async def test_carril_b_flow(test_client, test_user, db_session, test_branch, auth_headers):
    """
    Verifies "Carril B" (Direct Consumption) + Live Audit Recommendation.
    Scenario: Salchipapa (Direct Consumption of 'Papa Francesa').
    1. Buy 'Papa' (Raw Material).
    2. Sell 'Salchipapa' -> Deducts recipe amount (Theoretical).
    3. Audit -> Found less stock than theoretical (Loss).
    4. Intelligence -> Suggests Calibration.
    """
    
    # 1. Setup Data
    # Create Ingredient: Papa Francesa (RAW)
    papa = Ingredient(
        company_id=test_user.company_id,
        name="Papa Francesa",
        sku="PAPA-001",
        type=IngredientType.RAW,
        base_unit="kg",
        current_cost=Decimal("2.00") # $2/kg
    )
    db_session.add(papa)
    await db_session.commit()
    await db_session.refresh(papa)

    # Add Stock (10kg Batch)
    from app.services.inventory_service import InventoryService
    inv_service = InventoryService(db_session)
    await inv_service.update_ingredient_stock(
        branch_id=test_branch.id,
        ingredient_id=papa.id,
        quantity_delta=Decimal("10.0"),
        transaction_type="BUY",
        cost_per_unit=Decimal("2.00"),
        supplier="Vegetable Vendor",
        user_id=test_user.id
    )

    # Create Product: Salchipapa
    salchipapa = Product(
        company_id=test_user.company_id,
        name="Salchipapa Clasica",
        price=Decimal("15.00"),
        is_active=True
    )
    db_session.add(salchipapa)
    await db_session.commit()
    await db_session.refresh(salchipapa)

    # Recipe: 0.2kg (200g) of Papa per Salchipapa
    recipe = Recipe(
        company_id=test_user.company_id,
        product_id=salchipapa.id,
        name="Receta Salchipapa"
    )
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)

    r_item = RecipeItem(
        recipe_id=recipe.id,
        company_id=test_user.company_id,
        ingredient_id=papa.id,
        gross_quantity=Decimal("0.200"), # 200g
        measure_unit="kg"
    )
    db_session.add(r_item)
    await db_session.commit()

    # 2. Sell Salchipapa (1 Unit)
    # Theoretical Consumption: 0.2kg
    # Theoretical Stock Remaining: 9.8kg
    order_payload = {
        "branch_id": test_branch.id,
        "delivery_type": "DINE_IN",
        "items": [
            {
                "product_id": salchipapa.id,
                "quantity": 1,
                "modifiers": [],
                "notes": "Bien frita"
            }
        ],
        "payments": []
    }
    resp = await test_client.post("/orders/", json=order_payload, headers=auth_headers)
    assert resp.status_code == 201
    
    # 3. Verify Stock (Theoretical)
    stock_record = await inv_service.get_ingredient_stock(test_branch.id, papa.id)
    assert abs(float(stock_record.stock) - 9.8) < 0.001

    # 4. "Momento de la Verdad" (Audit)
    # Cocinero says: "I actually used 300g because my hand is heavy". 
    # Or "I dropped some". 
    # Real Stock Count: 9.7kg (Loss of 0.1kg extra) -> Total Usage 0.3kg
    
    # User performs Audit Adjustment
    # System saw 9.8. User inputs 9.7.
    # Adjustment = -0.1kg.
    # update_ingredient_stock with 'ADJUST' takes NEW BALANCE as quantity_delta
    
    await inv_service.update_ingredient_stock(
        branch_id=test_branch.id,
        ingredient_id=papa.id,
        quantity_delta=Decimal("9.7"), # New Balance
        transaction_type="ADJUST",
        cost_per_unit=Decimal("0.00"),
        user_id=test_user.id
    )
    
    # 5. Intelligence Report
    # Theoretical: 0.2kg
    # Real: 0.2 Theo + 0.1 Loss = 0.3kg
    # Efficiency: 0.2 / 0.3 = 0.66
    
    resp_intel = await test_client.get(f"/intelligence/recipe-efficiency/{recipe.id}", headers=auth_headers)
    assert resp_intel.status_code == 200
    intel_data = resp_intel.json()
    
    rec = intel_data["recommendations"][0]
    assert rec["efficiency"] < 0.9
    
    # Check Text Generation or Message
    msg = rec["message"]
    # "Tu cocina usa 0.3kg reales vs 0.2kg teóricos."
    print(f"DEBUG Message: {msg}")
    assert "0.3kg reales" in msg or "0.3" in msg # Verify approximate message content
    assert "0.2kg teóricos" in msg or "0.2" in msg
