import pytest
from httpx import AsyncClient
from decimal import Decimal
from sqlmodel import select
from app.models.ingredient import Ingredient, IngredientType
from app.models.ingredient_batch import IngredientBatch
from app.models.production_event import ProductionEvent

@pytest.mark.asyncio
async def test_production_flow(client: AsyncClient, session, auth_headers, test_company):
    # 1. Setup: Crear Ingrediente RAW (Carne Molida) y PROCESSED (Carne Burger)
    # -----------------------------------------------------------------------
    raw_ing = Ingredient(
        name="Carne Molida Test",
        sku="RAW-001",
        base_unit="kg",
        type=IngredientType.RAW,
        company_id=test_company.id
    )
    session.add(raw_ing)
    
    proc_ing = Ingredient(
        name="Carne Burger Test",
        sku="PROC-001",
        base_unit="und",
        type=IngredientType.PROCESSED,
        company_id=test_company.id
    )
    session.add(proc_ing)
    await session.commit()
    await session.refresh(raw_ing)
    await session.refresh(proc_ing)
    
    # 2. Setup: Añadir Stock Inicial (Lotes) para RAW
    # -----------------------------------------------------------------------
    # Lote 1: 10kg a $100/kg
    # Lote 2: 10kg a $120/kg
    # Total stock: 20kg
    
    # Usamos el endpoint de stock para crear lotes via "purchase" simulation
    # O directamente en BD para ser mas rapido. Usaremos DB direct para test unitario logica
    # Pero aqui estamos testing integration "flow", asi que mejor usar endpoint o servicio.
    # Usaremos el endpoint /stock update que ya soporta lotes. (Simulando compras)
    
    # Compra 1
    resp1 = await client.post(
        f"/ingredients/{raw_ing.id}/stock",
        json={
            "quantity": 10.0,
            "transaction_type": "IN",
            "cost_per_unit": 100.0,
            "supplier": "Supplier A",
            "reason": "Initial Purchase 1"
        },
        headers=auth_headers
    )
    assert resp1.status_code == 200
    
    # Compra 2
    resp2 = await client.post(
        f"/ingredients/{raw_ing.id}/stock",
        json={
            "quantity": 10.0,
            "transaction_type": "IN",
            "cost_per_unit": 120.0,
            "supplier": "Supplier B",
            "reason": "Initial Purchase 2"
        },
        headers=auth_headers
    )
    assert resp2.status_code == 200

    # 3. Ejecutar Producción
    # -----------------------------------------------------------------------
    # Vamos a producir 100 hamburguesas usando 15kg de carne.
    # Consumo esperado: 
    # - 10kg del Lote 1 ($100 * 10 = $1000)
    # - 5kg del Lote 2 ($120 * 5 = $600)
    # Total Costo Insumo = $1600
    # Cantidad Output = 100 unds
    # Costo Unitario Output = $1600 / 100 = $16.0
    
    prod_data = {
        "input_ingredient_id": str(raw_ing.id),
        "input_quantity": 15.0,
        "output_ingredient_id": str(proc_ing.id),
        "output_quantity": 100.0
    }
    
    resp_prod = await client.post(
        "/kitchen/production/",
        json=prod_data,
        headers=auth_headers
    )
    
    assert resp_prod.status_code == 201, resp_prod.text
    data = resp_prod.json()
    
    assert data["input_cost_total"] == 1600.0
    assert data["calculated_unit_cost"] == 16.0
    
    # 4. Verificar Estado Final en BD
    # -----------------------------------------------------------------------
    
    # Verificar Stock RAW (Debería quedar 5kg del Lote 2)
    qty_raw = await client.get(f"/ingredients/{raw_ing.id}", headers=auth_headers)
    # Wait, fetching ingredient doesn't return stock directly in main model typically, only cost/info
    # We should verify via the batches endpoint or inventory check.
    # The /ingredients endpoint calls get_stock? No, usually in separate call. 
    # But let's check batches for RAW.
    
    resp_batches = await client.get(f"/ingredients/{raw_ing.id}/batches", headers=auth_headers)
    batches = resp_batches.json()
    
    # Deben haber 2 lotes
    # Lote 1: Quantity Remaining 0, is_active False
    # Lote 2: Quantity Remaining 5, is_active True
    
    # Note: API might filter active_only=True by default.
    active_batches = [b for b in batches if b["is_active"]]
    assert len(active_batches) == 1
    assert float(active_batches[0]["quantity_remaining"]) == 5.0
    assert float(active_batches[0]["cost_per_unit"]) == 120.0
    
    # Verificar Batch Generado para PROCESSED
    resp_proc_batches = await client.get(f"/ingredients/{proc_ing.id}/batches", headers=auth_headers)
    proc_batches = resp_proc_batches.json()
    
    assert len(proc_batches) == 1
    new_batch = proc_batches[0]
    assert float(new_batch["quantity_initial"]) == 100.0
    assert float(new_batch["quantity_remaining"]) == 100.0
    assert float(new_batch["cost_per_unit"]) == 16.0
    assert new_batch["supplier"] == "Internal Production"
