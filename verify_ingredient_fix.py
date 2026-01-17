import requests
import uuid
import json

BASE_URL = "http://localhost:8000"

def test_ingredient_operations():
    # 0. Authenticate
    print("Authenticating...")
    token = None
    try:
        login_payload = {
            "username": "admin",
            "password": "admin123", # Assuming default seed password
            "company_slug": "fastops" # Assuming default seed company
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
        if response.status_code == 200:
            token = response.json().get("access_token")
            print("SUCCESS: Authenticated.")
        else:
            print(f"FAILURE: Authentication failed. Status: {response.status_code}")
            print(response.text)
            # Try with 'salchipapa-burguer' if fastops fails
            login_payload["company_slug"] = "salchipapa-burguer"
            print("Retrying with 'salchipapa-burguer'...")
            response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
            if response.status_code == 200:
                token = response.json().get("access_token")
                print("SUCCESS: Authenticated with 'salchipapa-burguer'.")
            else:
                print(f"FAILURE: Authentication failed again. Status: {response.status_code}")
                print(response.text)
                return

    except Exception as e:
        print(f"ERROR: Failed to connect to {BASE_URL} during login. {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test Listing Ingredients (GET)
    print("\nTesting GET /ingredients/...")
    try:
        response = requests.get(f"{BASE_URL}/ingredients/", headers=headers)
        if response.status_code == 200:
            print("SUCCESS: Retrieved ingredients list.")
            print(f"Count: {len(response.json())}")
        else:
            print(f"FAILURE: Could not retrieve ingredients. Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"ERROR: Failed to connect to {BASE_URL}. Is the backend running? {e}")
        return

    # 2. Test Creating Ingredient (POST)
    print("\nTesting POST /ingredients/...")
    new_sku = f"TEST-SKU-{uuid.uuid4().hex[:6]}"
    payload = {
        "name": f"Test Ingredient {new_sku}",
        "sku": new_sku,
        "base_unit": "KG",
        "current_cost": 10.50,
        "yield_factor": 0.95,
        "company_id": 1, # Assuming company 1 exists
        "ingredient_type": "RAW"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ingredients/", json=payload, headers=headers)
        if response.status_code == 200 or response.status_code == 201:
            print("SUCCESS: Created new ingredient.")
            print(response.json())
        else:
            print(f"FAILURE: Could not create ingredient. Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"ERROR: Failed to POST to {BASE_URL}. {e}")

if __name__ == "__main__":
    test_ingredient_operations()
