
import sys
import os
import asyncio
from uuid import UUID

current_dir = os.getcwd()
backend_dir = os.path.join(current_dir, 'backend')
sys.path.append(backend_dir)

from app.database import async_session, engine
from app.models.ingredient_batch import IngredientBatch
from sqlmodel import select

async def inspect():
    target_ing_id = UUID("893d4de3-f0d2-40e5-ba6f-d21b17699155")
    async with async_session() as session:
        print(f"--- INSPECTING INGREDIENT {target_ing_id} ---")
        stmt = select(IngredientBatch).where(IngredientBatch.ingredient_id == target_ing_id)
        result = await session.execute(stmt)
        batches = result.scalars().all()
        
        print(f"Total Batches Found: {len(batches)}")
        for b in batches:
            print(f"ID: {b.id} | Active: {b.is_active} | Qty Remaining: {b.quantity_remaining} | Initial: {b.quantity_initial} | Supplier: {b.supplier}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(inspect())
