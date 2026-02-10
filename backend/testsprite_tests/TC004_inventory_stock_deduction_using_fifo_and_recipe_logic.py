import requests
import uuid

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}

def test_inventory_stock_deduction_using_fifo_and_recipe_logic():
    # Step 1: Setup - Create ingredient batches with different quantities and batch dates (FIFO)
    ingredient_id = str(uuid.uuid4())
    batch_1 = {
        "ingredient_id": ingredient_id,
        "quantity": 100,
        "batch_date": "2026-01-01T00:00:00Z"
    }
    batch_2 = {
        "ingredient_id": ingredient_id,
        "quantity": 50,
        "batch_date": "2026-01-10T00:00:00Z"
    }
    created_batches = []

    try:
        # Create batch 1
        resp = requests.post(f"{BASE_URL}/inventory/ingredient_batches", json=batch_1, headers=HEADERS, timeout=TIMEOUT)
        assert resp.status_code == 201, f"Failed to create batch 1: {resp.text}"
        batch_1_resp = resp.json()
        created_batches.append(batch_1_resp)

        # Create batch 2
        resp = requests.post(f"{BASE_URL}/inventory/ingredient_batches", json=batch_2, headers=HEADERS, timeout=TIMEOUT)
        assert resp.status_code == 201, f"Failed to create batch 2: {resp.text}"
        batch_2_resp = resp.json()
        created_batches.append(batch_2_resp)

        # Step 2: Setup - Create a recipe using the ingredient with required quantity 120 (to trigger FIFO usage)
        recipe_id = str(uuid.uuid4())
        recipe_payload = {
            "id": recipe_id,
            "name": "Test Recipe",
            "ingredients": [
                {
                    "ingredient_id": ingredient_id,
                    "quantity": 120
                }
            ],
            "modifiers": []
        }
        resp = requests.post(f"{BASE_URL}/recipes", json=recipe_payload, headers=HEADERS, timeout=TIMEOUT)
        assert resp.status_code == 201, f"Failed to create recipe: {resp.text}"

        # Step 3: Create an order including this recipe and complete the sale that triggers inventory deduction
        order_payload = {
            "customer_id": str(uuid.uuid4()),
            "items": [
                {
                    "recipe_id": recipe_id,
                    "quantity": 1,
                    "modifiers": []
                }
            ],
            "delivery_type": "dine-in",
            "status": "completed"
        }
        resp = requests.post(f"{BASE_URL}/orders", json=order_payload, headers=HEADERS, timeout=TIMEOUT)
        assert resp.status_code == 201, f"Failed to create order: {resp.text}"
        order_resp = resp.json()
        order_id = order_resp.get("id")
        assert order_id, "Order ID not returned"

        # Step 4: Verify inventory deduction using FIFO method:
        # Query the ingredient batches after order completion to check proper quantity deductions (FIFO)
        resp = requests.get(f"{BASE_URL}/inventory/ingredient_batches?ingredient_id={ingredient_id}", headers=HEADERS, timeout=TIMEOUT)
        assert resp.status_code == 200, f"Failed to get ingredient batches after order: {resp.text}"
        batches = resp.json()
        # Sort batches by batch_date ascending to verify FIFO deduction
        batches_sorted = sorted(batches, key=lambda b: b["batch_date"])

        # Expected: batch_1 reduced from 100 to 0, batch_2 reduced from 50 to 30 (120 total deducted)
        batch1_after = next((b for b in batches_sorted if b["id"] == batch_1_resp["id"]), None)
        batch2_after = next((b for b in batches_sorted if b["id"] == batch_2_resp["id"]), None)
        assert batch1_after is not None, "Batch 1 missing after deduction"
        assert batch2_after is not None, "Batch 2 missing after deduction"

        assert batch1_after["quantity"] == 0, f"Batch 1 quantity expected 0 but got {batch1_after['quantity']}"
        assert batch2_after["quantity"] == 30, f"Batch 2 quantity expected 30 but got {batch2_after['quantity']}"

    finally:
        # Cleanup: delete order, recipe, and ingredient batches
        if 'order_id' in locals():
            requests.delete(f"{BASE_URL}/orders/{order_id}", headers=HEADERS, timeout=TIMEOUT)
        if 'recipe_id' in locals():
            requests.delete(f"{BASE_URL}/recipes/{recipe_id}", headers=HEADERS, timeout=TIMEOUT)
        for batch in created_batches:
            requests.delete(f"{BASE_URL}/inventory/ingredient_batches/{batch['id']}", headers=HEADERS, timeout=TIMEOUT)

test_inventory_stock_deduction_using_fifo_and_recipe_logic()
