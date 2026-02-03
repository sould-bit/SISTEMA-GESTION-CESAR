import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.inventory_service import InventoryService
from app.schemas.ingredients import IngredientStockMovementResponse
from pydantic import TypeAdapter
from typing import List
import os

# Database URL from environment or default
DATABASE_URL = "postgresql+asyncpg://admin:admin@localhost:5432/bdfastops"

async def test():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        service = InventoryService(session)
        print("Fetching global audit history...")
        history = await service.get_global_audit_history(limit=5)
        print(f"Found {len(history)} entries.")
        
        # Try to validate with Pydantic
        try:
            adapter = TypeAdapter(List[IngredientStockMovementResponse])
            validated = adapter.validate_python(history)
            print("Successfully validated with Pydantic!")
            for item in validated[:2]:
                print(f"- {item.ingredient_name}: {item.quantity_change} {item.ingredient_unit}")
        except Exception as e:
            print(f"Pydantic Validation Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
