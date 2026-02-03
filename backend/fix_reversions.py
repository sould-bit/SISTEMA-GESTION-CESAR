import asyncio
import os
import sys

# Add backend directory to path so we can import app modules
# Assuming script is in backend/fix_reversions.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

# Import models
from app.models.ingredient_inventory import IngredientTransaction, IngredientInventory

# Get DB URL from env or use default
raw_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://admin:admin123456789@localhost:5432/bdfastops")
# Ensure asyncpg driver
if raw_url.startswith("postgresql://"):
    DATABASE_URL = raw_url.replace("postgresql://", "postgresql+asyncpg://")
else:
    DATABASE_URL = raw_url

engine = create_async_engine(DATABASE_URL, echo=False)

async def fix_duplicate_reversions():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print("🔍 Scanning for duplicate REVERT_ADJ transactions...")
        
        # 1. Fetch all REVERT_ADJ transactions ordered by creation date
        stmt = select(IngredientTransaction).where(IngredientTransaction.transaction_type == "REVERT_ADJ").order_by(IngredientTransaction.created_at)
        result = await session.execute(stmt)
        transactions = result.scalars().all()
        
        # 2. Group by reference_id (the ID of the original transaction being reverted)
        grouped = {}
        for txn in transactions:
            if not txn.reference_id:
                continue
            if txn.reference_id not in grouped:
                grouped[txn.reference_id] = []
            grouped[txn.reference_id].append(txn)
            
        duplicates = []
        
        for ref_id, txns in grouped.items():
            if len(txns) > 1:
                print(f"⚠️  Found {len(txns)} reversions for original transaction ID {ref_id}")
                # Keep the first one (already ordered by created_at)
                valid = txns[0]
                dups = txns[1:]
                
                print(f"   ✅ Keeping transaction {valid.id} ({valid.quantity} units, {valid.created_at})")
                
                for d in dups:
                    print(f"   ❌ Deleting duplicate {d.id} ({d.quantity} units, {d.created_at})")
                    duplicates.append(d)

        if not duplicates:
            print("✅ No duplicate reversions found.")
            return

        print(f"\nProcessing {len(duplicates)} duplicates...")
        
        # 3. Process deletions and stock updates
        for dup in duplicates:
            # Update inventory: Reverse the duplicate's effect.
            # If valid revert added 1, the duplicate also added 1. Resulting in +2.
            # We want total +1. So we subtract 1 (dup.quantity).
            
            stmt_inv = select(IngredientInventory).where(IngredientInventory.id == dup.inventory_id)
            res_inv = await session.execute(stmt_inv)
            inventory = res_inv.scalar_one_or_none()
            
            if inventory:
                old_stock = inventory.stock
                # Subtract the quantity of the duplicate transaction from the inventory
                inventory.stock -= dup.quantity
                print(f"   📉 Updating Stock for Inventory {inventory.id}: {old_stock} -> {inventory.stock}")
                session.add(inventory)
            else:
                print(f"   ⚠️  Inventory {dup.inventory_id} not found for transaction {dup.id}")
            
            # Delete transaction
            await session.delete(dup)
        
        # 4. Commit
        await session.commit()
        print("\n✨ Operations successfully committed.")

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(fix_duplicate_reversions())
    except Exception as e:
        print(f"💥 Error: {e}")
