"""
Test Script: Customer (PWA) Flow via Storefront API
Ejecutar DESPUÉS de test_admin_flow.py

Flujo:
1. Registro Público (sin login)
2. Login por Teléfono
3. Ver Sucursales Disponibles
4. Ver Menú de Sucursal
5. Agregar Dirección (con token customer)
6. Crear Pedido Delivery (con token customer)
"""
import asyncio
import httpx
import random
import sys
import traceback
import json

# Config
BASE_URL = "http://localhost:8000"
COMPANY_SLUG = "fastops"

state = {}

GREEN, RED, RESET, BOLD = "\033[92m", "\033[91m", "\033[0m", "\033[1m"

def log(msg, type="info"):
    prefix = {"success": f"{GREEN}✅", "error": f"{RED}❌", "section": f"\n{BOLD}🔹"}.get(type, "ℹ️ ")
    print(f"{prefix} {msg}{RESET}")

async def run_step(name, func, client):
    try:
        log(f"Ejecutando: {name}...")
        await func(client)
    except Exception as e:
        log(f"Fallo en {name}: {e}", "error")
        traceback.print_exc()
        sys.exit(1)

async def main():
    # Cargar state del admin flow
    try:
        with open("test_state.json", "r") as f:
            admin_state = json.load(f)
            state["product_id"] = admin_state["product_id"]
            state["branch_id"] = admin_state["branch_id"]
    except FileNotFoundError:
        log("⚠️  Ejecuta primero test_admin_flow.py para crear datos base", "error")
        state["branch_id"] = 1  # Fallback a sucursal 1
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        log("FLUJO CUSTOMER (PWA) - Experiencia del Usuario Final", "section")
        
        await run_step("1. Registro Público", register_public, client)
        await run_step("2. Login por Teléfono", login_phone, client)
        await run_step("3. Ver Sucursales", browse_branches, client)
        await run_step("4. Ver Menú", browse_menu, client)
        await run_step("5. Agregar Dirección", add_address, client)
        await run_step("6. Crear Pedido Delivery", create_delivery_order, client)
        
        log("\n✅ FLUJO CUSTOMER COMPLETO - Todos los endpoints funcionando", "success")

# --- Steps ---

async def register_public(client):
    phone = f"300{random.randint(1000000, 9999999)}"
    state["phone"] = phone
    
    res = await client.post("/customers/public/register", json={
        "phone": phone,
        "full_name": f"Usuario Test {random.randint(100,999)}",
        "email": f"test{phone}@example.com",
        "company_slug": COMPANY_SLUG
    })
    if res.status_code != 201:
        raise Exception(f"Register failed: {res.text}")
    
    customer = res.json()
    state["customer_id"] = customer["id"]
    log(f"Registrado: {phone}", "success")

async def login_phone(client):
    res = await client.post("/customers/auth/login", json={
        "phone": state["phone"],
        "company_slug": COMPANY_SLUG
    })
    if res.status_code != 200:
        raise Exception(f"Login failed: {res.text}")
    
    token = res.json()["access_token"]
    state["headers"] = {"Authorization": f"Bearer {token}"}
    log("Logueado con token customer", "success")

async def browse_branches(client):
    """Ver sucursales disponibles (público)."""
    res = await client.get(f"/storefront/{COMPANY_SLUG}/branches")
    if res.status_code != 200:
        raise Exception(f"Branches failed: {res.text}")
    
    branches = res.json()
    log(f"Sucursales disponibles: {len(branches)}", "success")
    
    # Usar la primera sucursal si no tenemos una del admin flow
    if branches and not state.get("branch_id"):
        state["branch_id"] = branches[0]["id"]

async def browse_menu(client):
    """Ver menú de la sucursal (público)."""
    branch_id = state.get("branch_id", 1)
    res = await client.get(f"/storefront/{COMPANY_SLUG}/branches/{branch_id}/menu")
    if res.status_code != 200:
        raise Exception(f"Menu failed: {res.text}")
    
    menu = res.json()
    total_products = sum(len(cat.get("products", [])) for cat in menu.get("categories", []))
    log(f"Menú: {len(menu.get('categories', []))} categorías, {total_products} productos", "success")
    
    # Obtener un producto disponible
    for cat in menu.get("categories", []):
        for prod in cat.get("products", []):
            if prod.get("available"):
                state["product_id"] = prod["id"]
                log(f"Producto seleccionado: {prod['name']} (${prod['price']})", "success")
                return
    
    # Si no hay disponible, usar el del admin flow o primero de la lista
    if not state.get("product_id"):
        for cat in menu.get("categories", []):
            for prod in cat.get("products", []):
                state["product_id"] = prod["id"]
                log(f"Producto (sin stock): {prod['name']}", "success")
                return

async def add_address(client):
    """Agregar dirección usando storefront/me/addresses."""
    res = await client.post("/storefront/me/addresses", json={
        "name": "Casa",
        "address": f"Calle {random.randint(1,100)} # {random.randint(1,50)}-{random.randint(1,99)}",
        "details": f"Apto {random.randint(100,999)}",
        "latitude": 4.60 + random.random() * 0.1,
        "longitude": -74.08 + random.random() * 0.1,
        "is_default": True
    }, headers=state["headers"])
    
    if res.status_code not in [200, 201]:
        raise Exception(f"Address failed: {res.text}")
    
    state["address"] = res.json()
    log(f"Dirección guardada: {state['address']['address']}", "success")

async def create_delivery_order(client):
    """Crear pedido usando storefront/me/orders."""
    res = await client.post("/storefront/me/orders", json={
        "branch_id": state["branch_id"],
        "delivery_address": f"{state['address']['address']} - {state['address'].get('details', '')}",
        "delivery_notes": "Llamar al llegar",
        "items": [
            {"product_id": state["product_id"], "quantity": 1, "notes": "Sin cebolla"}
        ]
    }, headers=state["headers"])
    
    if res.status_code not in [200, 201]:
        raise Exception(f"Order failed: {res.text}")
    
    order = res.json()
    log(f"Pedido Delivery #{order['order_number']} - Total: ${order['total']}", "success")

if __name__ == "__main__":
    asyncio.run(main())
