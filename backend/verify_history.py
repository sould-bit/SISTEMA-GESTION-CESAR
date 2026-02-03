
import asyncio
import uuid
from sqlalchemy import select
from app.database import async_session
from app.models.ingredient import Ingredient
from app.services.inventory_service import InventoryService

async def verify():
    async with async_session() as session:
        # 1. Get coca
        stmt = select(Ingredient).where(Ingredient.name.ilike("%coca%"))
        res = await session.execute(stmt)
        ing = res.scalars().first()
        
        if not ing:
            print("Coca not found")
            return
            
        print(f"Found {ing.name} with ID {ing.id}")
        
        # 2. Call service
        service = InventoryService(session)
        history = await service.get_ingredient_history(ing.id)
        
        print(f"Found {len(history)} history entries:")
        for entry in history:
            print(f"- {entry['created_at']} | {entry['transaction_type']} | {entry['quantity']} | {entry['reason']} | {entry['user_name']}")

if __name__ == "__main__":
    asyncio.run(verify())
