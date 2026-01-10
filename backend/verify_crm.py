
import asyncio
import httpx
from datetime import datetime

# Config
BASE_URL = "http://localhost:8000"
USER_EMAIL = "admin@fastops.com" 
USER_PASSWORD = "admin123" 

async def verify_crm():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Login
        print("🔐 Iniciando sesión...")
        login_res = await client.post("/auth/login", json={
            "username": "admin",
            "password": USER_PASSWORD,
            "company_slug": "fastops"
        })
        if login_res.status_code != 200:
            print(f"❌ Error Login: {login_res.text}")
            return
        
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login exitoso")

        # 2. Registrar Cliente
        print("\n👤 Registrando cliente...")
        phone = f"300{int(datetime.now().timestamp())}" # Teléfono único
        customer_data = {
            "phone": phone,
            "full_name": "Test Customer CRM",
            "email": "crm@test.com",
            "notes": "Cliente VIP"
        }
        
        res = await client.post("/customers/", json=customer_data, headers=headers)
        if res.status_code != 201:
            print(f"❌ Error Customer: {res.text}")
            return
        customer = res.json()
        print(f"✅ Cliente creado: ID={customer['id']}, Phone={customer['phone']}")

        # 3. Agregar Dirección
        print("\n🏠 Agregando dirección...")
        address_data = {
            "name": "Casa",
            "address": "Calle Falsa 123",
            "details": "Apto 505",
            "latitude": 4.60971,
            "longitude": -74.08175,
            "is_default": True
        }
        
        res = await client.post(f"/customers/{customer['id']}/addresses", json=address_data, headers=headers)
        if res.status_code != 200:
            print(f"❌ Error Address: {res.text}")
            return
        address = res.json()
        print(f"✅ Dirección creada: ID={address['id']}, Lat/Lng={address['latitude']}/{address['longitude']}")

        # 4. Crear Orden de Delivery
        # Necesitamos una sucursal activa y producto. Asumimos Branch ID 1 y Product ID existente (o buscamos)
        branch_id = 1
        
        print("\n📦 Creando pedido delivery...")
        # Buscar un producto primero
        prod_res = await client.get("/products/?skip=0&limit=1", headers=headers)
        products = prod_res.json()
        if not products:
            print("⚠️ No hay productos, saltando creación de orden")
            return
        
        product_id = products[0]["id"]
        
        order_data = {
            "branch_id": branch_id,
            "items": [
                {"product_id": product_id, "quantity": 1, "notes": "Sin cebolla"}
            ],
            # CRM Fields
            "customer_id": customer['id'],
            "delivery_type": "delivery",
            "delivery_address": f"{address['address']} {address['details']}",
            "delivery_notes": "Tocar timbre fuerte",
            "delivery_fee": 5000
        }
        
        res = await client.post("/orders/", json=order_data, headers=headers)
        if res.status_code != 200:
             print(f"❌ Error Pedido: {res.text}")
             return
        
        order = res.json()
        print(f"✅ Pedido Delivery Creado: #{order['order_number']}")
        print(f"   Destino Snapshot: {order['delivery_address']}")
        print(f"   Cliente ID vinculado: {order['customer_id']}")

if __name__ == "__main__":
    asyncio.run(verify_crm())
