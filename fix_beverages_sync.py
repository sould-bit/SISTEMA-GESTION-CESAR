
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlmodel import Session, create_engine, select
from app.models.product import Product
from app.models.category import Category
from app.models.ingredient import Ingredient, IngredientType
from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem
from app.config import settings

def fix_beverages_sync():
    print("Starting beverage category fix (SYNC)...")
    
    # Create sync engine
    # We use settings.DATABASE_URL which defaults to postgresql:// (sync)
    url = settings.DATABASE_URL
    print(f"Connecting to: {url}")
    engine = create_engine(
        url,
        connect_args={"client_encoding": "utf8"}
    )
    
    with Session(engine) as session:
        # 1. Get or Create "Venta Directa" category
        stmt = select(Category).where(Category.name == "Venta Directa")
        result = session.exec(stmt)
        category = result.first()
        
        if not category:
            print("Creating 'Venta Directa' category...")
            category = Category(
                name="Venta Directa",
                description="#BEBIDAS",
                is_active=True,
                company_id=1
            )
            session.add(category)
            session.commit()
            session.refresh(category)
        
        print(f"Target Category: {category.name} (ID: {category.id})")
        
        # 2. Find Products
        stmt = select(Ingredient).where(
            Ingredient.ingredient_type == IngredientType.MERCHANDISE
        )
        result = session.exec(stmt)
        ingredients = result.all()
        
        print(f"Found {len(ingredients)} MERCHANDISE ingredients.")
        
        fixed_count = 0
        
        for ing in ingredients:
            stmt_ri = select(RecipeItem).where(RecipeItem.ingredient_id == ing.id)
            recipe_items = session.exec(stmt_ri).all()
            
            for ri in recipe_items:
                 stmt_r = select(Recipe).where(Recipe.id == ri.recipe_id)
                 recipe = session.exec(stmt_r).first()
                 
                 if recipe and recipe.product_id:
                     stmt_p = select(Product).where(Product.id == recipe.product_id)
                     product = session.exec(stmt_p).first()
                     
                     if product and product.category_id is None:
                         # print(f"Fixing Product: {product.name} (ID: {product.id})")
                         print(f"Fixing Product ID: {product.id}")
                         product.category_id = category.id
                         session.add(product)
                         fixed_count += 1
        
        if fixed_count > 0:
            session.commit()
            print(f"Successfully fixed {fixed_count} products.")
        else:
            print("No products needed fixing.")
            
if __name__ == "__main__":
    fix_beverages_sync()
