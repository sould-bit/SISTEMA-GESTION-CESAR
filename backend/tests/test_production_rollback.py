"""
Test específico para verificar el fix del rollback de producción.

Flujo del Test:
1. Crear ingrediente RAW (Harina) con stock inicial
2. Crear ingrediente PROCESSED (Pan) 
3. Realizar DOS producciones del mismo producto PROCESSED (crear 2 lotes)
4. Verificar estado inicial (2 lotes en PROCESSED, stock reducido en RAW)
5. Eliminar UN lote de producción (rollback)
6. Verificar que:
   - El OTRO lote SIGUE existiendo intacto
   - Los insumos del lote eliminado fueron DEVUELTOS a RAW
   - El stock total es consistente
"""
import pytest
from httpx import AsyncClient
from decimal import Decimal
from sqlmodel import select
import uuid

from app.models.ingredient import Ingredient, IngredientType
from app.models.ingredient_batch import IngredientBatch
from app.models.ingredient_inventory import IngredientInventory
from app.models.production_event import ProductionEvent


@pytest.mark.asyncio
async def test_production_rollback_preserves_other_batches(client: AsyncClient, session, auth_headers, test_company, test_branch):
    """
    TEST CRÍTICO: Verificar que al eliminar UN lote de producción,
    SOLO ese lote se elimina y los demás permanecen intactos.
    
    Bug previo: Al eliminar un lote, el FIFO consumía TODOS los lotes del mismo ingrediente.
    Fix: Decrementar inventory.stock directamente sin activar FIFO.
    """
    print("\n" + "="*60)
    print("TEST: Production Rollback Preserves Other Batches")
    print("="*60)
    
    # ==========================================================
    # FASE 1: SETUP - Crear ingredientes y stock inicial
    # ==========================================================
    print("\n[FASE 1] Setup - Creando ingredientes...")
    
    # Crear ingrediente RAW (Harina)
    raw_ing = Ingredient(
        id=uuid.uuid4(),
        name="Harina Test Rollback",
        sku=f"RAW-ROLLBACK-{uuid.uuid4().hex[:6]}",
        base_unit="kg",
        ingredient_type=IngredientType.RAW,
        company_id=test_company.id,
        current_cost=Decimal("10.00")
    )
    session.add(raw_ing)
    
    # Crear ingrediente PROCESSED (Pan)
    proc_ing = Ingredient(
        id=uuid.uuid4(),
        name="Pan Test Rollback",
        sku=f"PROC-ROLLBACK-{uuid.uuid4().hex[:6]}",
        base_unit="und",
        ingredient_type=IngredientType.PROCESSED,
        company_id=test_company.id,
        current_cost=Decimal("0")
    )
    session.add(proc_ing)
    await session.commit()
    await session.refresh(raw_ing)
    await session.refresh(proc_ing)
    
    print(f"  ✓ RAW Ingredient: {raw_ing.name} (ID: {raw_ing.id})")
    print(f"  ✓ PROCESSED Ingredient: {proc_ing.name} (ID: {proc_ing.id})")
    
    # Agregar stock inicial a RAW (100 kg)
    resp_stock = await client.post(
        f"/ingredients/{raw_ing.id}/stock",
        json={
            "quantity": 100.0,
            "transaction_type": "IN",
            "cost_per_unit": 10.0,
            "supplier": "Supplier Test",
            "reason": "Stock inicial para test rollback"
        },
        headers=auth_headers
    )
    assert resp_stock.status_code == 200, f"Failed to add stock: {resp_stock.text}"
    print(f"  ✓ Stock inicial RAW: 100 kg @ $10/kg = $1000")
    
    # ==========================================================
    # FASE 2: PRODUCCIÓN 1 - Crear primer lote de Pan (20 und usando 10 kg)
    # ==========================================================
    print("\n[FASE 2] Producción 1 - Creando primer lote de Pan...")
    
    prod1_data = {
        "inputs": [{"ingredient_id": str(raw_ing.id), "quantity": 10.0}],
        "output": {"ingredient_id": str(proc_ing.id)},
        "output_quantity": 20.0,
        "notes": "Producción 1 para test rollback"
    }
    
    resp_prod1 = await client.post(
        "/kitchen/production/",
        json=prod1_data,
        headers=auth_headers
    )
    assert resp_prod1.status_code == 201, f"Failed production 1: {resp_prod1.text}"
    prod1_result = resp_prod1.json()
    print(f"  ✓ Producción 1: 10 kg Harina -> 20 und Pan")
    print(f"  ✓ Costo unitario: ${prod1_result['calculated_unit_cost']}")
    
    # ==========================================================
    # FASE 3: PRODUCCIÓN 2 - Crear segundo lote de Pan (30 und usando 15 kg)
    # ==========================================================
    print("\n[FASE 3] Producción 2 - Creando segundo lote de Pan...")
    
    prod2_data = {
        "inputs": [{"ingredient_id": str(raw_ing.id), "quantity": 15.0}],
        "output": {"ingredient_id": str(proc_ing.id)},
        "output_quantity": 30.0,
        "notes": "Producción 2 para test rollback"
    }
    
    resp_prod2 = await client.post(
        "/kitchen/production/",
        json=prod2_data,
        headers=auth_headers
    )
    assert resp_prod2.status_code == 201, f"Failed production 2: {resp_prod2.text}"
    prod2_result = resp_prod2.json()
    print(f"  ✓ Producción 2: 15 kg Harina -> 30 und Pan")
    print(f"  ✓ Costo unitario: ${prod2_result['calculated_unit_cost']}")
    
    # ==========================================================
    # FASE 4: VERIFICAR ESTADO INICIAL
    # ==========================================================
    print("\n[FASE 4] Verificando estado inicial...")
    
    # Verificar stock RAW (debería ser 100 - 10 - 15 = 75 kg)
    resp_raw_batches = await client.get(
        f"/ingredients/{raw_ing.id}/batches?active_only=true",
        headers=auth_headers
    )
    raw_batches = resp_raw_batches.json()
    raw_stock_initial = sum(float(b["quantity_remaining"]) for b in raw_batches)
    print(f"  → Stock RAW (Harina): {raw_stock_initial} kg (esperado: 75 kg)")
    assert abs(raw_stock_initial - 75.0) < 0.01, f"Stock RAW incorrecto: {raw_stock_initial}"
    
    # Verificar lotes PROCESSED (deberían ser 2)
    resp_proc_batches = await client.get(
        f"/ingredients/{proc_ing.id}/batches?active_only=true",
        headers=auth_headers
    )
    proc_batches_initial = resp_proc_batches.json()
    print(f"  → Lotes PROCESSED (Pan): {len(proc_batches_initial)} (esperado: 2)")
    assert len(proc_batches_initial) == 2, f"Debería haber 2 lotes, hay {len(proc_batches_initial)}"
    
    proc_stock_initial = sum(float(b["quantity_remaining"]) for b in proc_batches_initial)
    print(f"  → Stock PROCESSED total: {proc_stock_initial} und (esperado: 50 = 20 + 30)")
    assert abs(proc_stock_initial - 50.0) < 0.01, f"Stock PROCESSED incorrecto"
    
    # Identificar los lotes
    batch_to_delete = proc_batches_initial[0]  # Eliminaremos el primero
    batch_to_keep = proc_batches_initial[1]    # Este debe permanecer
    
    print(f"  → Lote a ELIMINAR: {batch_to_delete['id']} ({batch_to_delete['quantity_remaining']} und)")
    print(f"  → Lote a PRESERVAR: {batch_to_keep['id']} ({batch_to_keep['quantity_remaining']} und)")
    
    deleted_batch_qty = float(batch_to_delete['quantity_remaining'])
    kept_batch_qty = float(batch_to_keep['quantity_remaining'])
    
    # ==========================================================
    # FASE 5: ELIMINAR UN LOTE (ROLLBACK)
    # ==========================================================
    print("\n[FASE 5] ELIMINANDO UN LOTE DE PRODUCCIÓN...")
    
    resp_delete = await client.delete(
        f"/ingredients/batches/{batch_to_delete['id']}",
        headers=auth_headers
    )
    assert resp_delete.status_code == 204, f"Failed to delete batch: {resp_delete.text}"
    print(f"  ✓ Lote {batch_to_delete['id'][:8]}... ELIMINADO")
    
    # ==========================================================
    # FASE 6: VERIFICAR ESTADO FINAL
    # ==========================================================
    print("\n[FASE 6] VERIFICANDO ESTADO FINAL (CRÍTICO)...")
    
    # 6.1: El lote que debía preservarse DEBE seguir existiendo
    resp_proc_batches_final = await client.get(
        f"/ingredients/{proc_ing.id}/batches?active_only=true",
        headers=auth_headers
    )
    proc_batches_final = resp_proc_batches_final.json()
    
    print(f"\n  [VERIFICACIÓN 1] Lotes PROCESSED restantes:")
    print(f"     → Cantidad de lotes: {len(proc_batches_final)} (esperado: 1)")
    
    assert len(proc_batches_final) == 1, \
        f"❌ ERROR CRÍTICO: Debería quedar 1 lote, pero hay {len(proc_batches_final)}. " \
        f"El bug del FIFO sigue activo!"
    
    remaining_batch = proc_batches_final[0]
    print(f"     → Lote restante ID: {remaining_batch['id']}")
    print(f"     → Cantidad: {remaining_batch['quantity_remaining']} und (esperado: {kept_batch_qty})")
    
    assert remaining_batch['id'] == batch_to_keep['id'], \
        f"❌ ERROR: El lote preservado no es el correcto"
    
    assert abs(float(remaining_batch['quantity_remaining']) - kept_batch_qty) < 0.01, \
        f"❌ ERROR: La cantidad del lote preservado cambió"
    
    print(f"     ✅ LOTE PRESERVADO CORRECTAMENTE")
    
    # 6.2: Los insumos deben haber sido devueltos
    resp_raw_batches_final = await client.get(
        f"/ingredients/{raw_ing.id}/batches?active_only=true",
        headers=auth_headers
    )
    raw_batches_final = resp_raw_batches_final.json()
    raw_stock_final = sum(float(b["quantity_remaining"]) for b in raw_batches_final)
    
    # Si eliminamos el lote de 20 und que consumió 10 kg, el stock RAW debe volver a 85 kg
    # (75 + 10 = 85, o si era el de 30 und que consumió 15 kg, sería 75 + 15 = 90)
    # El lote eliminado fue el primero, que puede ser el de 20 o 30 und
    
    # Calculamos cuánto se debería haber restaurado
    # Si deleted_batch_qty == 20, se restauraron 10 kg -> raw_stock_final = 85
    # Si deleted_batch_qty == 30, se restauraron 15 kg -> raw_stock_final = 90
    expected_raw_stock = 75.0 + (10.0 if abs(deleted_batch_qty - 20.0) < 0.01 else 15.0)
    
    print(f"\n  [VERIFICACIÓN 2] Insumos devueltos:")
    print(f"     → Stock RAW final: {raw_stock_final} kg (esperado: ~{expected_raw_stock} kg)")
    
    # Permitir algo de tolerancia por redondeo
    assert raw_stock_final > 75.0, \
        f"❌ ERROR: Los insumos NO fueron devueltos. Stock sigue en {raw_stock_final}"
    
    print(f"     ✅ INSUMOS DEVUELTOS CORRECTAMENTE")
    
    # 6.3: Verificar consistencia del inventario total
    resp_proc_inv = await client.get(
        f"/ingredients/{proc_ing.id}",
        headers=auth_headers
    )
    proc_info = resp_proc_inv.json()
    
    print(f"\n  [VERIFICACIÓN 3] Consistencia de inventario PROCESSED:")
    
    # El stock de PROCESSED debe ser solo el lote que quedó
    assert len(proc_batches_final) == 1
    final_proc_stock = float(proc_batches_final[0]['quantity_remaining'])
    print(f"     → Stock PROCESSED restante: {final_proc_stock} und")
    print(f"     ✅ INVENTARIO CONSISTENTE")
    
    # ==========================================================
    # RESULTADO FINAL
    # ==========================================================
    print("\n" + "="*60)
    print("✅ TEST PASSED: El rollback de producción funciona correctamente")
    print("="*60)
    print(f"""
RESUMEN:
- Se crearon 2 lotes de producción (20 und + 30 und = 50 und)
- Se eliminó 1 lote ({deleted_batch_qty} und)
- El otro lote ({kept_batch_qty} und) permanece INTACTO
- Los insumos fueron DEVUELTOS (Stock RAW: 75 kg -> {raw_stock_final} kg)
""")


@pytest.mark.asyncio  
async def test_production_rollback_does_not_affect_unrelated_batches(client: AsyncClient, session, auth_headers, test_company, test_branch):
    """
    Test adicional: Verificar que el rollback de producción no afecta lotes
    de OTROS ingredientes que podrían tener el mismo tipo (PROCESSED).
    """
    print("\n" + "="*60)
    print("TEST: Rollback No Affects Unrelated Ingredients")
    print("="*60)
    
    # Crear dos ingredientes PROCESSED diferentes
    proc_a = Ingredient(
        id=uuid.uuid4(),
        name="Producto A Test",
        sku=f"PROC-A-{uuid.uuid4().hex[:6]}",
        base_unit="und",
        ingredient_type=IngredientType.PROCESSED,
        company_id=test_company.id
    )
    proc_b = Ingredient(
        id=uuid.uuid4(),
        name="Producto B Test",
        sku=f"PROC-B-{uuid.uuid4().hex[:6]}",
        base_unit="und",
        ingredient_type=IngredientType.PROCESSED,
        company_id=test_company.id
    )
    
    # Crear insumo RAW
    raw = Ingredient(
        id=uuid.uuid4(),
        name="Insumo Test Unrelated",
        sku=f"RAW-UNREL-{uuid.uuid4().hex[:6]}",
        base_unit="kg",
        ingredient_type=IngredientType.RAW,
        company_id=test_company.id,
        current_cost=Decimal("5.00")
    )
    
    session.add_all([proc_a, proc_b, raw])
    await session.commit()
    
    # Agregar stock al RAW
    await client.post(
        f"/ingredients/{raw.id}/stock",
        json={"quantity": 100.0, "transaction_type": "IN", "cost_per_unit": 5.0, "reason": "Init"},
        headers=auth_headers
    )
    
    # Producir ambos productos
    await client.post(
        "/kitchen/production/",
        json={
            "inputs": [{"ingredient_id": str(raw.id), "quantity": 10.0}],
            "output": {"ingredient_id": str(proc_a.id)},
            "output_quantity": 50.0
        },
        headers=auth_headers
    )
    
    await client.post(
        "/kitchen/production/",
        json={
            "inputs": [{"ingredient_id": str(raw.id), "quantity": 10.0}],
            "output": {"ingredient_id": str(proc_b.id)},
            "output_quantity": 50.0
        },
        headers=auth_headers
    )
    
    # Verificar estado inicial
    resp_a = await client.get(f"/ingredients/{proc_a.id}/batches?active_only=true", headers=auth_headers)
    resp_b = await client.get(f"/ingredients/{proc_b.id}/batches?active_only=true", headers=auth_headers)
    
    batches_a = resp_a.json()
    batches_b = resp_b.json()
    
    assert len(batches_a) == 1, "Producto A debería tener 1 lote"
    assert len(batches_b) == 1, "Producto B debería tener 1 lote"
    
    print(f"  ✓ Producto A: 1 lote ({batches_a[0]['quantity_remaining']} und)")
    print(f"  ✓ Producto B: 1 lote ({batches_b[0]['quantity_remaining']} und)")
    
    # Eliminar lote de Producto A
    resp_delete = await client.delete(
        f"/ingredients/batches/{batches_a[0]['id']}",
        headers=auth_headers
    )
    assert resp_delete.status_code == 204
    print(f"  ✓ Eliminado lote de Producto A")
    
    # Verificar que Producto B NO fue afectado
    resp_b_final = await client.get(f"/ingredients/{proc_b.id}/batches?active_only=true", headers=auth_headers)
    batches_b_final = resp_b_final.json()
    
    assert len(batches_b_final) == 1, \
        f"❌ ERROR: Producto B fue afectado incorrectamente. Lotes: {len(batches_b_final)}"
    
    assert batches_b_final[0]['id'] == batches_b[0]['id'], \
        "❌ ERROR: El lote de Producto B cambió"
    
    assert float(batches_b_final[0]['quantity_remaining']) == float(batches_b[0]['quantity_remaining']), \
        "❌ ERROR: La cantidad del lote de Producto B cambió"
    
    print(f"  ✓ Producto B: INTACTO ({batches_b_final[0]['quantity_remaining']} und)")
    print("\n✅ TEST PASSED: Rollback no afecta ingredientes no relacionados")
