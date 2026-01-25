import pytest
from httpx import AsyncClient
from app.models.ingredient import Ingredient, IngredientType
from decimal import Decimal

@pytest.mark.asyncio
async def test_audit_flow(client: AsyncClient, session, auth_headers, test_company, test_branch):
    # 1. Setup: Create Ingredient
    ing = Ingredient(
        name="Soda Test 2",
        sku="SODA-002",
        base_unit="und",
        type=IngredientType.RAW,
        company_id=test_company.id,
        current_cost=Decimal("1.50")
    )
    session.add(ing)
    await session.commit()
    await session.refresh(ing)
    
    # 2. Add Stock (10 units)
    await client.post(
        f"/ingredients/{ing.id}/stock",
        json={
            "quantity": 10.0,
            "transaction_type": "IN",
            "cost_per_unit": 1.50,
            "supplier": "Test Supplier",
            "reason": "Initial"
        },
        headers=auth_headers
    )
    
    # 3. Start Count
    resp_start = await client.post(
        "/inventory-counts/",
        json={"branch_id": test_branch.id, "notes": "Audit Test"},
        headers=auth_headers
    )
    assert resp_start.status_code == 201
    count = resp_start.json()
    count_id = count["id"]
    
    # 4. Update Item -> Counted 8 (Missing 2)
    resp_update = await client.post(
        f"/inventory-counts/{count_id}/items",
        json=[
            {
                "ingredient_id": str(ing.id),
                "counted_quantity": 8.0
            }
        ],
        headers=auth_headers
    )
    assert resp_update.status_code == 200
    
    # Verify Detail
    resp_detail = await client.get(f"/inventory-counts/{count_id}", headers=auth_headers)
    detail = resp_detail.json()
    item = next(i for i in detail["items"] if i["ingredient_id"] == str(ing.id))
    assert item["expected_quantity"] == 10.0
    assert item["counted_quantity"] == 8.0
    assert item["discrepancy"] == -2.0
    
    # 5. Close Count
    resp_close = await client.post(f"/inventory-counts/{count_id}/close", headers=auth_headers)
    assert resp_close.status_code == 200
    
    # 6. Apply Count
    resp_apply = await client.post(f"/inventory-counts/{count_id}/apply", headers=auth_headers)
    assert resp_apply.status_code == 200
    
    # 7. Verify Live Stock is now 8
    # Fetch stock (via batches or inventory endpoint)
    # Using inventory service logic (get_ingredient_stock) equivalent
    # Or just check batches remaining.
    resp_batches = await client.get(f"/ingredients/{ing.id}/batches", headers=auth_headers)
    batches = resp_batches.json()
    
    active_batches = [b for b in batches if b["is_active"]]
    # Note: FIFO consumption logic handles negative delta (consumption)
    # If we consumed 2, remaining should be 8.
    
    total_qty = sum(float(b["quantity_remaining"]) for b in active_batches)
    assert total_qty == 8.0
