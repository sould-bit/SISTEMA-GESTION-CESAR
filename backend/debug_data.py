import asyncio
import sys
import os

# Ensure backend directory is in python path
sys.path.append(os.getcwd())

from app.database import engine
from app.models.ingredient import Ingredient
from app.models.category import Category
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

async def check():
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        print("\n--- INGREDIENTS DUMP ---")
        stmt = select(Ingredient.name, Ingredient.category_id, Ingredient.ingredient_type).limit(20)
        result = await session.execute(stmt)
        for row in result.all():
            print(f"Name: {row.name} | CatID: {row.category_id} | Type: {row.ingredient_type}")

        print("\n--- CATEGORIES DUMP ---")
        stmt2 = select(Category.id, Category.name)
        result2 = await session.execute(stmt2)
        for row in result2.all():
            print(f"ID: {row.id} | Name: {row.name}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check())
