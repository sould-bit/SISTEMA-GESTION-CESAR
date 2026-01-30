
import asyncio
import sys
import os
from dotenv import load_dotenv

# Add backend directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Load env vars manually to ensure DB connection works
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Windows Asyncio Fix
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.database import get_session
from app.models.ingredient import Ingredient, IngredientType
from sqlalchemy import select, or_, and_

async def cleanup_zombies():
    print("Iniciando limpieza de insumos zombie...")
    async for session in get_session():
        # Terms identified from user screenshot and request
        terms = ["jugo", "magua", "test"]
        
        conditions = [Ingredient.name.ilike(f"%{term}%") for term in terms]
        
        stmt = select(Ingredient).where(
            or_(*conditions),
            Ingredient.is_active == True,
            Ingredient.ingredient_type == IngredientType.MERCHANDISE
        )
        
        result = await session.execute(stmt)
        ingredients = result.scalars().all()
        
        if not ingredients:
            print("No se encontraron insumos activos que coincidan con los criterios.")
            return

        print(f"Se encontraron {len(ingredients)} insumos candidatos:")
        for ing in ingredients:
            print(f" - [{ing.id}] {ing.name} ({ing.sku}) - {ing.ingredient_type}")
        
        # Proceed to deactivate
        print("\nDesactivando insumos...")
        count = 0
        for ing in ingredients:
            ing.is_active = False
            session.add(ing)
            count += 1
            
        await session.commit()
        print(f"✅ Se desactivaron correctamente {count} insumos.")
        break

if __name__ == "__main__":
    asyncio.run(cleanup_zombies())
