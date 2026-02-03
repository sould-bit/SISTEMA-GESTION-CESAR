
import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.modifier import ProductModifier, ModifierRecipeItem
from app.models.ingredient import Ingredient
from app.core.config import settings

async def check_modifiers():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        stmt = select(ProductModifier).limit(5)
        result = await session.execute(stmt)
        modifiers = result.scalars().all()
        print(f"Found {len(modifiers)} modifiers")
        
        for mod in modifiers:
            print(f"\nModifier: {mod.name} (ID: {mod.id})")
            stmt_items = select(ModifierRecipeItem).where(ModifierRecipeItem.modifier_id == mod.id)
            result_items = await session.execute(stmt_items)
            items = result_items.scalars().all()
            print(f"  Recipe Items: {len(items)}")
            
            for item in items:
                print(f"    Item ID: {item.id}")
                print(f"      ingredient_product_id: {item.ingredient_product_id}")
                print(f"      ingredient_id: {item.ingredient_id}")
                
                if item.ingredient_id:
                    stmt_ing = select(Ingredient).where(Ingredient.id == item.ingredient_id)
                    res_ing = await session.execute(stmt_ing)
                    ing = res_ing.scalar_one_or_none()
                    if ing:
                        print(f"      Ingredient Ref Found: {ing.name} (Cost: {ing.current_cost})")
                    else:
                        print(f"      Ingredient Ref NOT FOUND in DB for UUID {item.ingredient_id}")
                
                if item.ingredient_product_id:
                    from app.models.product import Product
                    stmt_prod = select(Product).where(Product.id == item.ingredient_product_id)
                    res_prod = await session.execute(stmt_prod)
                    prod = res_prod.scalar_one_or_none()
                    if prod:
                        print(f"      Legacy Product Found: {prod.name} (Price: {prod.price})")
                    else:
                        print(f"      Legacy Product NOT FOUND in DB for ID {item.ingredient_product_id}")

if __name__ == "__main__":
    import os
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/el_rincon"
    asyncio.run(check_modifiers())
