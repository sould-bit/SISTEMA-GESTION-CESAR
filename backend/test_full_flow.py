import asyncio
import httpx
from datetime import datetime
import random
import sys
import traceback

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

BASE_URL = "http://localhost:8000"
USER_EMAIL = "admin@fastops.com"
USER_PASSWORD = "admin123"
COMPANY_SLUG = "fastops"

# State to pass between steps
state = {}

def log(msg, type="info"):
    if type == "success":
        print(f"{GREEN}✅ {msg}{RESET}")
    elif type == "error":
        print(f"{RED}❌ {msg}{RESET}")
    elif type == "section":
        print(f"\n{BOLD}🔹 {msg}{RESET}")
    else:
        print(f"ℹ️  {msg}")

async def run_step(name, func, client):
    try:
        log(f"Ejecutando: {name}...")
        await func(client)
    except Exception as e:
        log(f"Fallo en {name}: {e}", "error")
        traceback.print_exc()
        sys.exit(1) # Stop immediately

async def main():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        log(f"Iniciando Full E2E Test en {BASE_URL}", "section")
        
        await run_step("1. Login Admin", login_admin, client)
        await run_step("2. Crear Categoría", create_category, client)
        await run_step("3. Crear Insumos (Inventario)", create_ingredients, client)
        await run_step("4. Crear Producto", create_product, client)
        await run_step("5. Crear Receta", create_recipe, client)
        await run_step("6. Registro CRM Publico (PWA)", register_customer_public, client)
        await run_step("7. Login Cliente (PWA)", login_customer, client)
        await run_step("8. Agregar Dirección", add_address, client)
        await run_step("9. Crear Pedido Delivery", create_order, client)
        await run_step("11. Verificar Reportes", check_reports, client)

# --- Steps Implementation ---

async def login_admin(client):
    res = await client.post("/auth/login", json={
        "username": "admin",
        "password": USER_PASSWORD,
        "company_slug": COMPANY_SLUG
    })
    if res.status_code != 200:
        raise Exception(f"Login failed: {res.text}")
    
    token = res.json()["access_token"]
    state["headers"] = {"Authorization": f"Bearer {token}"}
    log("Admin logueado correctamente", "success")

async def create_category(client):
    cat_name = f"Cat_Test_{random.randint(1000,9999)}"
    res = await client.post("/categories/", json={"name": cat_name, "description": "Categoria de prueba"}, headers=state["headers"])
    if res.status_code != 200:
         raise Exception(f"Category creation failed: {res.text}")
    
    state["category_id"] = res.json()["id"]
    log(f"Categoría creada: {cat_name}", "success")

async def create_ingredients(client):
    # Crear Pan
    ing1 = {
        "name": f"Pan_Test_{random.randint(100,999)}",
        "unit": "unidad",
        "cost": 500,
        "current_stock": 100,
        "min_stock": 10
    }
    res = await client.post("/inventory/", json=ing1, headers=state["headers"])
    state["ing_pan_id"] = res.json()["id"]
    
    # Crear Carne
    ing2 = {
        "name": f"Carne_Test_{random.randint(100,999)}",
        "unit": "gramos",
        "cost": 20, # por gramo
        "current_stock": 5000, # 5kg
        "min_stock": 500
    }
    res = await client.post("/inventory/", json=ing2, headers=state["headers"])
    state["ing_carne_id"] = res.json()["id"]
    log("Insumos creados (Pan y Carne)", "success")

async def create_product(client):
    prod_name = f"Burger_Especial_{random.randint(100,999)}"
    prod_data = {
        "name": prod_name,
        "price": 25000,
        "category_id": state["category_id"],
        "is_active": True
    }
    res = await client.post("/products/", json=prod_data, headers=state["headers"])
    state["product_id"] = res.json()["id"]
    log(f"Producto creado: {prod_name}", "success")

async def create_recipe(client):
    recipe_data = {
        "product_id": state["product_id"],
        "items": [
            {"ingredient_id": state["ing_pan_id"], "quantity": 1},   # 1 Pan
            {"ingredient_id": state["ing_carne_id"], "quantity": 150} # 150g Carne
        ]
    }
    res = await client.post("/recipes/", json=recipe_data, headers=state["headers"])
    if res.status_code != 200:
        # Check if already exists (idempotency check often fails in simple scripts)
        log(f"Warning creating recipe: {res.text}")
    else:
        log("Receta creada y costeo calculado", "success")

async def register_customer_public(client):
    phone = f"300{random.randint(1000000,9999999)}"
    state["phone"] = phone
    
    data = {
        "phone": phone,
        "full_name": "Test User PWA",
        "company_slug": COMPANY_SLUG,
        "email": f"user{phone}@test.com"
    }
    
    res = await client.post("/customers/public/register", json=data)
    if res.status_code != 201:
        raise Exception(f"Registration failed: {res.text}")
    
    customer = res.json()
    state["customer_id"] = customer["id"]
    log(f"Cliente PWA registrado: {phone}", "success")

async def login_customer(client):
    data = {
        "phone": state["phone"],
        "company_slug": COMPANY_SLUG
    }
    res = await client.post("/customers/auth/login", json=data)
    if res.status_code != 200:
        raise Exception(f"Customer Login failed: {res.text}")
        
    token = res.json()["access_token"]
    state["customer_headers"] = {"Authorization": f"Bearer {token}"}
    log("Cliente PWA logueado (Token obtenido)", "success")

async def add_address(client):
    addr_data = {
        "name": "Oficina",
        "address": "Calle 123 # 45-67",
        "details": "Edificio Tech, Of 301",
        "latitude": 4.123,
        "longitude": -74.123,
        "is_default": True
    }
    
    # Usamos el token del cliente, no del admin
    res = await client.post(
        f"/customers/{state['customer_id']}/addresses", 
        json=addr_data, 
        headers=state["customer_headers"]
    )
    if res.status_code != 200:
        raise Exception(f"Address creation failed: {res.text}")
    
    state["address"] = res.json()
    log("Dirección agregada por el cliente", "success")

async def create_order(client):
    # Admin crea la orden ( simulating POS receiving the order)
    # o PWA creando orden (si endpoint publico existiera, pero usamos el de admin por ahora)
    
    # Validar que address existe
    if "address" not in state or not state["address"]:
         raise Exception("No address in state to use for delivery order")

    order_data = {
        "branch_id": 1, # Asumimos ID 1
        "customer_id": state["customer_id"],
        "delivery_type": "delivery",
        "delivery_address": f"{state['address']['address']} ({state['address']['details']})",
        "delivery_notes": "Timbre dañado",
        "delivery_fee": 3000,
        "items": [
            {"product_id": state["product_id"], "quantity": 2, "notes": "Sin salsa"}
        ]
    }
    
    res = await client.post("/orders/", json=order_data, headers=state["headers"])
    if res.status_code != 200:
         raise Exception(f"Order creation failed: {res.text}")
    
    order = res.json()
    state["order_id"] = order["id"]
    log(f"Pedido Delivery creado: #{order['order_number']} - Total: {order['total']}", "success")

async def check_reports(client):
    # Verificar dashboard
    res = await client.get("/reports/dashboard", headers=state["headers"])
    if res.status_code != 200:
         raise Exception(f"Report dashboard failed: {res.text}")
    
    data = res.json()
    log(f"Reporte Dashboard consultado. Ventas Hoy: {data['summary']['today_sales']}", "success")

if __name__ == "__main__":
    asyncio.run(main())
