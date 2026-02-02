"""
Test Script para Flujo Completo de Recetas
Verifica: Listar, Ver Detalle, Editar Items
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Credenciales de test (admin del seed)
TEST_USER = {"email": "admin@elrincon.com", "password": "admin123"}


async def test_recipe_flow():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        print("=" * 60)
        print("🍳 TEST FLUJO COMPLETO DE RECETAS")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}\n")

        # 1. Autenticación
        print("1️⃣ AUTENTICACIÓN...")
        try:
            response = await client.post("/auth/login", data={
                "username": TEST_USER["email"],
                "password": TEST_USER["password"]
            })
            if response.status_code != 200:
                print(f"   ❌ Login fallido: {response.status_code} - {response.text}")
                return
            
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print(f"   ✅ Login exitoso. Token obtenido.")
        except Exception as e:
            print(f"   ❌ Error en login: {e}")
            return

        # 2. Listar Recetas
        print("\n2️⃣ LISTAR RECETAS...")
        try:
            response = await client.get("/recipes", headers=headers)
            if response.status_code != 200:
                print(f"   ❌ Error listando recetas: {response.status_code}")
                return
            
            recipes = response.json()
            print(f"   ✅ {len(recipes)} recetas encontradas")
            
            if not recipes:
                print("   ⚠️ No hay recetas para testear. Creando una de prueba...")
                # Necesitaríamos crear una receta primero
                return
            
            # Mostrar resumen de recetas
            for r in recipes[:3]:
                print(f"      - {r['name']} (ID: {r['id'][:8]}...) - ${r['total_cost']} - {r.get('items_count', 0)} items")
            
            test_recipe_id = recipes[0]["id"]
            test_recipe_name = recipes[0]["name"]
            print(f"\n   📋 Receta de prueba: {test_recipe_name}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return

        # 3. Ver Detalle de Receta
        print(f"\n3️⃣ VER DETALLE DE RECETA (ID: {test_recipe_id[:8]}...)...")
        try:
            response = await client.get(f"/recipes/{test_recipe_id}", headers=headers)
            if response.status_code != 200:
                print(f"   ❌ Error obteniendo detalle: {response.status_code} - {response.text}")
                return
            
            recipe_detail = response.json()
            print(f"   ✅ Detalle obtenido:")
            print(f"      Nombre: {recipe_detail['name']}")
            print(f"      Costo Total: ${recipe_detail['total_cost']}")
            print(f"      Producto: {recipe_detail.get('product_name', 'N/A')}")
            print(f"      Items: {len(recipe_detail.get('items', []))}")
            
            items = recipe_detail.get("items", [])
            if items:
                print(f"\n      📦 Ingredientes:")
                for item in items:
                    print(f"         - {item.get('ingredient_name', item['ingredient_id'][:8]+'...')}: {item['gross_quantity']} {item['measure_unit']}")
            else:
                print("   ⚠️ La receta no tiene ingredientes")
                return
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return

        # 4. Actualizar Items de Receta
        print(f"\n4️⃣ ACTUALIZAR ITEMS DE RECETA...")
        try:
            # Modificar la cantidad del primer item (incrementar en 10%)
            if items:
                original_qty = float(items[0]["gross_quantity"])
                new_qty = round(original_qty * 1.1, 2)  # Incrementar 10%
                
                updated_items = []
                for item in items:
                    updated_items.append({
                        "ingredient_id": item["ingredient_id"],
                        "gross_quantity": new_qty if item == items[0] else float(item["gross_quantity"]),
                        "measure_unit": item["measure_unit"]
                    })
                
                print(f"   Modificando cantidad del primer ingrediente: {original_qty} -> {new_qty}")
                
                response = await client.put(
                    f"/recipes/{test_recipe_id}/items",
                    headers=headers,
                    json={"items": updated_items}
                )
                
                if response.status_code == 200:
                    updated_recipe = response.json()
                    print(f"   ✅ Receta actualizada exitosamente!")
                    print(f"      Nuevo costo total: ${updated_recipe['total_cost']}")
                    
                    # Verificar que el cambio se aplicó
                    new_items = updated_recipe.get("items", [])
                    if new_items:
                        actual_qty = float(new_items[0]["gross_quantity"])
                        if abs(actual_qty - new_qty) < 0.01:
                            print(f"   ✅ Verificación: Cantidad actualizada correctamente ({actual_qty})")
                        else:
                            print(f"   ⚠️ Cantidad no coincide: esperada {new_qty}, actual {actual_qty}")
                elif response.status_code == 422:
                    print(f"   ❌ Error de validación (422): {response.json()}")
                else:
                    print(f"   ❌ Error actualizando: {response.status_code} - {response.text}")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return

        # 5. Verificar persistencia
        print(f"\n5️⃣ VERIFICAR PERSISTENCIA...")
        try:
            response = await client.get(f"/recipes/{test_recipe_id}", headers=headers)
            if response.status_code == 200:
                final_recipe = response.json()
                final_qty = float(final_recipe["items"][0]["gross_quantity"]) if final_recipe.get("items") else 0
                
                if abs(final_qty - new_qty) < 0.01:
                    print(f"   ✅ Persistencia verificada: Los cambios se guardaron correctamente")
                else:
                    print(f"   ❌ Los cambios no persistieron: {final_qty} != {new_qty}")
            else:
                print(f"   ❌ Error verificando: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        print("\n" + "=" * 60)
        print("✅ TEST COMPLETADO")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_recipe_flow())
