
import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import select
from app.database import get_session
from app.models.product import Product
from app.models.category import Category
from app.models.ingredient import Ingredient, IngredientType
from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem

async def fix_beverage_categories():
    print("Starting beverage category fix...")
    async for session in get_session():
        # 1. Get or Create "Venta Directa" category
        stmt = select(Category).where(Category.name == "Venta Directa")
        result = await session.execute(stmt)
        category = result.scalar_one_or_none()
        
        if not category:
            print("Creating 'Venta Directa' category...")
            category = Category(
                name="Venta Directa",
                description="#BEBIDAS",
                is_active=True,
                company_id=1 # Assuming company_id 1 for now or we need to handle multi-tenant
            )
            session.add(category)
            await session.commit()
            await session.refresh(category)
        
        print(f"Target Category: {category.name} (ID: {category.id})")
        
        # 2. Find Products that should be beverages but have no category
        # Strategy: Find MERCHANDISE ingredients -> Recipe -> Product
        
        stmt = select(Ingredient).where(
            Ingredient.ingredient_type == IngredientType.MERCHANDISE
        )
        result = await session.execute(stmt)
        ingredients = result.scalars().all()
        
        print(f"Found {len(ingredients)} MERCHANDISE ingredients.")
        
        fixed_count = 0
        
        for ing in ingredients:
            # Find associated recipe item
            # We assume 1:1 relation as per BeverageService
            # Get recipe items for this ingredient
            stmt_ri = select(RecipeItem).where(RecipeItem.ingredient_id == ing.id)
            result_ri = await session.execute(stmt_ri)
            recipe_items = result_ri.scalars().all()
            
            for ri in recipe_items:
                 # Get Recipe
                 stmt_r = select(Recipe).where(Recipe.id == ri.recipe_id)
                 result_r = await session.execute(stmt_r)
                 recipe = result_r.scalar_one_or_none()
                 
                 if recipe and recipe.product_id:
                     # Get Product
                     stmt_p = select(Product).where(Product.id == recipe.product_id)
                     result_p = await session.execute(stmt_p)
                     product = result_p.scalar_one_or_none()
                     
                     if product and product.category_id is None:
                         print(f"Fixing Product: {product.name} (ID: {product.id})")
                         product.category_id = category.id
                         session.add(product)
                         fixed_count += 1
        
        if fixed_count > 0:
            await session.commit()
            print(f"Successfully fixed {fixed_count} products.")
        else:
            print("No products needed fixing.")
            
if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(fix_beverage_categories())
