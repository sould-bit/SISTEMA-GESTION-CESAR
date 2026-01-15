import pytest
import uuid
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_ingredient_batches_fifo(client: AsyncClient, auth_headers):
    # 1. Create Ingredient
    create_payload = {
        "name": f"Batch Testing Ingredient {uuid.uuid4()}",
        "sku": f"BATCH-{uuid.uuid4()}",
        "base_unit": "kg",
        "current_cost": 0,
        "yield_factor": 1.0,
        "category_id": None
    }
    response = await client.post("/ingredients/", json=create_payload, headers=auth_headers)
    assert response.status_code == 201
    ingredient_id = response.json()["id"]

    # 2. Add Batch 1 (Purchase): 10 units @ 100
    batch1_payload = {
        "quantity": 10,
        "transaction_type": "PURCHASE",
        "cost_per_unit": 100,
        "supplier": "Supplier A"
    }
    response = await client.post(f"/ingredients/{ingredient_id}/stock", json=batch1_payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert float(data["new_stock"]) == 10.0

    # Verify Batch 1 Created
    response = await client.get(f"/ingredients/{ingredient_id}/batches", headers=auth_headers)
    assert response.status_code == 200
    batches = response.json()
    assert len(batches) == 1
    assert float(batches[0]["quantity_remaining"]) == 10.0
    assert float(batches[0]["cost_per_unit"]) == 100.0
    assert batches[0]["supplier"] == "Supplier A"
    assert batches[0]["is_active"] == True

    # 3. Add Batch 2 (Purchase): 5 units @ 200
    batch2_payload = {
        "quantity": 5,
        "transaction_type": "PURCHASE",
        "cost_per_unit": 200,
        "supplier": "Supplier B"
    }
    response = await client.post(f"/ingredients/{ingredient_id}/stock", json=batch2_payload, headers=auth_headers)
    assert response.status_code == 200
    assert float(response.json()["new_stock"]) == 15.0

    # Verify 2 Batches
    response = await client.get(f"/ingredients/{ingredient_id}/batches", headers=auth_headers)
    batches = response.json()
    assert len(batches) == 2
    # Ensure order (Newest first in GET, but FIFO consumption logic uses OLDEST)
    # The GET endpoint orders by acquired_at DESC (Newest first)
    # So batches[0] is Batch 2, batches[1] is Batch 1
    # Check acquired_at logic roughly or just ID
    
    # 4. Consume Stock (FIFO): Consume 12 units
    # - Should consume all 10 from Batch 1
    # - Should consume 2 from Batch 2
    # - Remaining Total: 3
    # - Remaining Batch 2: 3
    consume_payload = {
        "quantity": 12,
        "transaction_type": "OUT",
        "reason": "Production"
    }
    response = await client.post(f"/ingredients/{ingredient_id}/stock", json=consume_payload, headers=auth_headers)
    assert response.status_code == 200
    assert float(response.json()["new_stock"]) == 3.0

    # 5. Verify Batches After Consumption
    response = await client.get(f"/ingredients/{ingredient_id}/batches?active_only=false", headers=auth_headers)
    batches = response.json()
    
    # We expect 2 batches total history
    assert len(batches) == 2
    
    # Sort by acquired ASC (Oldest first) to identify easier
    batches_sorted = sorted(batches, key=lambda b: b["acquired_at"])
    batch1 = batches_sorted[0]
    batch2 = batches_sorted[1]
    
    # Verify Batch 1 (Oldest, Cost 100) -> Exhausted
    assert float(batch1["cost_per_unit"]) == 100.0
    assert float(batch1["quantity_remaining"]) == 0.0
    assert batch1["is_active"] == False
    
    # Verify Batch 2 (Newest, Cost 200) -> Partially Consumed (5 - 2 = 3 remaining)
    assert float(batch2["cost_per_unit"]) == 200.0
    assert float(batch2["quantity_remaining"]) == 3.0
    assert batch2["is_active"] == True
