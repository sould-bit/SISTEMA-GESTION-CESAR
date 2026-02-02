
import sys
import os
import asyncio
from decimal import Decimal

# Setup path to include backend
current_dir = os.getcwd()
backend_dir = os.path.join(current_dir, 'backend')
sys.path.append(backend_dir)

from app.database import async_session, engine
from app.services.production_service import ProductionService
from app.services.inventory_service import InventoryService
from app.services.ingredient_service import IngredientService
from app.models.ingredient import Ingredient, IngredientType
from app.models.user import User
from sqlmodel import select

async def test_undo_isolation():
    async with async_session() as session:
        print("--- INICIO DE PRUEBA DE AISLAMIENTO DE DESHACER ---")
        
        # 1. Setup Simplificado (Supone DB ya sembrada con usuario/branch/company)
        # Usaremos IDs hardcodeados o buscaremos los primeros disponibles para no complicar el setup
        # PRECAUCION: Esto modifica la DB real. Idealmente usar DB de test, pero para este diagnóstico rápido usaremos datos reales controlados.
        
        # Buscar usuario admin
        stmt = select(User).limit(1)
        user = (await session.execute(stmt)).scalar_one()
        company_id = user.company_id
        
        # 2. Crear Insumo Materia Prima (Tomate Test)
        ing_service = IngredientService(session)
        inv_service = InventoryService(session)
        prod_service = ProductionService(session)
        
        tomate = await ing_service.create(
            company_id=company_id,
            name="Tomate Test Isolation",
            sku="TEST-TOM-ISO",
            base_unit="kg",
            ingredient_type=IngredientType.RAW,
            current_cost=1000
        )
        print(f"1. Creado Materia Prima: {tomate.name}")
        
        # Agregar stock
        await inv_service.update_ingredient_stock(
            branch_id=1, # Asumiendo branch 1
            ingredient_id=tomate.id,
            quantity_delta=Decimal(100),
            transaction_type="IN",
            user_id=user.id,
            cost_per_unit=Decimal(1000),
            supplier="Test Setup"
        )
        
        # 3. Crear Producto Procesado (Salsa Test)
        salsa = await ing_service.create(
            company_id=company_id,
            name="Salsa Test Isolation",
            sku="TEST-SALSA-ISO",
            base_unit="kg",
            ingredient_type=IngredientType.PROCESSED,
            current_cost=0
        )
        print(f"2. Creado Producto Final: {salsa.name}")
        
        # 4. PRODUCCIÓN 1 (Lote A)
        print("3. Ejecutando Producción 1...")
        event1 = await prod_service.register_production_event(
            company_id=company_id,
            branch_id=1,
            user_id=user.id,
            inputs=[{"ingredient_id": tomate.id, "quantity": 10}],
            output={"ingredient_id": salsa.id},
            output_quantity=10,
            notes="Batch 1"
        )
        batch1_id = event1.output_batch_id
        print(f"   -> Lote 1 Creado: {batch1_id}")

        # 5. PRODUCCIÓN 2 (Lote B)
        print("4. Ejecutando Producción 2...")
        event2 = await prod_service.register_production_event(
            company_id=company_id,
            branch_id=1,
            user_id=user.id,
            inputs=[{"ingredient_id": tomate.id, "quantity": 10}],
            output={"ingredient_id": salsa.id},
            output_quantity=10,
            notes="Batch 2"
        )
        batch2_id = event2.output_batch_id
        print(f"   -> Lote 2 Creado: {batch2_id}")
        
        # Verificar ambos existen
        b1 = await ing_service.get_batch_by_id(batch1_id)
        b2 = await ing_service.get_batch_by_id(batch2_id)
        if b1 and b2:
            print("   -> Confirmado: Ambos lotes existen.")
        else:
            print("   -> ERROR: Alguno no se creó correctamente.")
            return

        # 6. DESHACER LOTE 2
        print("5. Deshaciendo SOLO Lote 2...")
        await ing_service.delete_batch(batch2_id) # Esto llama internamente a revert_production
        
        # 7. VERIFICACIÓN FINAL
        b1_after = await ing_service.get_batch_by_id(batch1_id)
        b2_after = await ing_service.get_batch_by_id(batch2_id)
        
        if b1_after and not b2_after:
            print("SUCCESS: Lote 1 sigue vivo, Lote 2 eliminado.")
        elif not b1_after:
            print("FAIL: ¡EL LOTE 1 TAMBIÉN FUE ELIMINADO! (Bug confirmado)")
        elif b2_after:
            print("FAIL: El Lote 2 no se eliminó.")
            
        # Limpieza (opcional, dejamos basura de test por ahora o la borramos)
        # cleanup...

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(test_undo_isolation())
    except Exception as e:
        print(f"CRASH: {e}")
