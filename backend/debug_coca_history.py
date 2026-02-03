
import asyncio
import uuid
from sqlalchemy import select, func
from app.database import async_session
from app.models.ingredient import Ingredient
from app.models.ingredient_inventory import IngredientInventory, IngredientTransaction

async def check_coca_history():
    async with async_session() as session:
        # 1. Buscar ingrediente coca
        stmt = select(Ingredient).where(Ingredient.name.ilike("%coca%"))
        result = await session.execute(stmt)
        ingredients = result.scalars().all()
        
        if not ingredients:
            print("No se encontró el ingrediente 'coca'")
            return

        for ing in ingredients:
            print(f"\n--- Ingrediente: {ing.name} (ID: {ing.id}) SKU: {ing.sku} ---")
            
            # 2. Buscar registros de inventario (sucursales)
            stmt_inv = select(IngredientInventory).where(IngredientInventory.ingredient_id == ing.id)
            res_inv = await session.execute(stmt_inv)
            inventories = res_inv.scalars().all()
            
            if not inventories:
                print("No hay registros en ingredient_inventory para este ingrediente.")
                continue
                
            for inv in inventories:
                print(f"  Sucursal ID: {inv.branch_id}, Stock Actual: {inv.stock}, Inv ID: {inv.id}")
                
                # 3. Buscar transacciones para este inventario
                stmt_txn = select(IngredientTransaction).where(IngredientTransaction.inventory_id == inv.id).order_by(IngredientTransaction.created_at.desc())
                res_txn = await session.execute(stmt_txn)
                transactions = res_txn.scalars().all()
                
                if not transactions:
                    print("    No hay transacciones registradas.")
                else:
                    print(f"    Encontradas {len(transactions)} transacciones:")
                    for txn in transactions:
                        print(f"      [{txn.created_at}] Tipo: {txn.transaction_type}, Cantidad: {txn.quantity}, Resultante: {txn.balance_after}, Motivo: {txn.reason}")

if __name__ == "__main__":
    asyncio.run(check_coca_history())
