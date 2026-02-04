
import pytest
from httpx import AsyncClient
from app.main import app
from app.services.inventory_service import inventory_service
from app.models.product import Product
from decimal import Decimal

# Helper to creates dummy data
async def create_dummy_product_with_recipe(async_client, branch_id):
    # 1. Create Ingredients
    ing1_res = await async_client.post("/products/", json={
        "name": "Ingrediente Test 1",
        "price": 0,
        "stock": 100,
        "is_active": True,
        "category_id": 1
    })
    ing2_res = await async_client.post("/products/", json={
        "name": "Ingrediente Test 2",
        "price": 0,
        "stock": 100,
        "is_active": True,
        "category_id": 1
    })
    
    ing1 = ing1_res.json()
    ing2 = ing2_res.json()
    
    # 2. Add Stock to Ingredients (via InventoryService backdoor or API if needed)
    # We need them to have stock to deduct.
    # Assuming initial stock 100 is raw, but inventory service needs batches?
    # Let's use the explicit adjustment endpoint or rely on initial stock if handled (likely not)
    
    await inventory_service.update_ingredient_stock(branch_id, ing1["id"], 50, "ADJUST", "Setup")
    await inventory_service.update_ingredient_stock(branch_id, ing2["id"], 50, "ADJUST", "Setup")
    
    # 3. Create Product
    prod_res = await async_client.post("/products/", json={
        "name": "Producto Receta Test",
        "price": 10000,
        "stock": 0,
        "is_active": True,
        "category_id": 2
    })
    prod = prod_res.json()
    
    # 4. Create Recipe
    recipe_payload = {
        "product_id": prod["id"],
        "name": "Receta Test",
        "items": [
            {"ingredient_product_id": ing1["id"], "quantity": 2, "unit": "UN"}, # 2 units of Ing1
            {"ingredient_product_id": ing2["id"], "quantity": 1, "unit": "UN"}  # 1 unit of Ing2
        ]
    }
    await async_client.post("/recipes/", json=recipe_payload)
    
    return prod, ing1, ing2

@pytest.mark.asyncio
async def test_order_removed_ingredients_logic(async_client: AsyncClient):
    # Setup
    branch_id = 1
    prod, ing1, ing2 = await create_dummy_product_with_recipe(async_client, branch_id)
    
    # Get initial stock
    stock1_before = await inventory_service.get_stock(branch_id, ing1["id"])
    stock2_before = await inventory_service.get_stock(branch_id, ing2["id"])
    
    # Create Order removing Ing1
    order_payload = {
        "branch_id": branch_id,
        "table_id": None,
        "delivery_type": "dine_in",
        "items": [
            {
                "product_id": prod["id"],
                "quantity": 1,
                "modifiers": [],
                "removed_ingredients": [str(ing1["id"])] # Removing Ing1
            }
        ]
    }
    
    res = await async_client.post("/orders/", json=order_payload)
    assert res.status_code == 200
    
    # Verify Stock
    stock1_after = await inventory_service.get_stock(branch_id, ing1["id"])
    stock2_after = await inventory_service.get_stock(branch_id, ing2["id"])
    
    # Ing1 should NOT change (Removed)
    assert stock1_after == stock1_before, f"Ing1 stock changed! Before: {stock1_before}, After: {stock1_after}"
    
    # Ing2 SHOULD decrease by 1
    assert stock2_after == stock2_before - 1, f"Ing2 stock failed to deduct! Before: {stock2_before}, After: {stock2_after}"
    
    print("\n✅ Test Passed: Removed ingredient stock was preserved, other ingredient deducted correctly.")
