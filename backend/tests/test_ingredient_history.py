import pytest
from httpx import AsyncClient
from app.models.ingredient import Ingredient
from app.models.user import User

@pytest.mark.asyncio
async def test_ingredient_cost_history_flow(client: AsyncClient, auth_headers: dict):
    # 1. Create Ingredient
    create_payload = {
        "name": "Harina Test History",
        "sku": "HAR-HIST-001",
        "base_unit": "kg",
        "current_cost": 5000,
        "yield_factor": 1.0,
        "category_id": None
    }
    response = await client.post("/ingredients/", json=create_payload, headers=auth_headers)
    assert response.status_code == 201
    ingredient = response.json()
    ingredient_id = ingredient["id"]
    
    # 2. Update Cost (First Update)
    update_payload_1 = {
        "new_cost": 6000,
        "use_weighted_average": False,
        "reason": "Inflation adjustment"
    }
    response = await client.post(f"/ingredients/{ingredient_id}/update-cost", json=update_payload_1, headers=auth_headers)
    assert response.status_code == 200
    data_1 = response.json()
    assert float(data_1["current_cost"]) == 6000.0
    assert float(data_1["last_cost"]) == 5000.0
    
    # 3. Update Cost (Second Update)
    update_payload_2 = {
        "new_cost": 5500,
        "use_weighted_average": False,
        "reason": "Supplier discount"
    }
    response = await client.post(f"/ingredients/{ingredient_id}/update-cost", json=update_payload_2, headers=auth_headers)
    assert response.status_code == 200
    data_2 = response.json()
    assert float(data_2["current_cost"]) == 5500.0
    
    # 4. Get History
    response = await client.get(f"/ingredients/{ingredient_id}/history", headers=auth_headers)
    assert response.status_code == 200
    history = response.json()
    
    # Verify History Entries
    assert len(history) == 2
    
    # Most recent first
    assert float(history[0]["new_cost"]) == 5500.0
    assert float(history[0]["previous_cost"]) == 6000.0
    assert history[0]["reason"] == "Supplier discount"
    
    # Oldest
    assert float(history[1]["new_cost"]) == 6000.0
    assert float(history[1]["previous_cost"]) == 5000.0
    assert history[1]["reason"] == "Inflation adjustment"
