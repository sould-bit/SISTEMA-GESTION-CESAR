"""
Migration: Add recipe_type column to recipes table.

This migration adds a recipe_type column to differentiate between:
- REAL: Manual recipes with actual ingredients
- AUTO: Auto-generated recipes for beverages/merchandise
- PROCESSED: Recipes for processed ingredients
"""
import asyncio
import asyncpg


async def main():
    # Connect to database
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="admin",
        password="admin123",
        database="bdfastops"
    )

    try:
        # Step 1: Add the column if it doesn't exist
        print("Adding recipe_type column...")
        await conn.execute("""
            ALTER TABLE recipes 
            ADD COLUMN IF NOT EXISTS recipe_type VARCHAR(20) DEFAULT 'REAL';
        """)
        print("✅ Column added successfully")

        # Step 2: Update existing recipes based on name pattern
        print("\nUpdating existing recipes...")
        
        # Mark AUTO recipes (name starts with "Receta Auto:")
        result_auto = await conn.execute("""
            UPDATE recipes 
            SET recipe_type = 'AUTO' 
            WHERE name LIKE 'Receta Auto:%';
        """)
        print(f"✅ Marked AUTO recipes: {result_auto}")

        # Mark PROCESSED recipes (linked to processed ingredients)
        # These are auto-recipes for processed ingredients
        result_processed = await conn.execute("""
            UPDATE recipes 
            SET recipe_type = 'PROCESSED' 
            WHERE name LIKE 'Receta Auto:%'
            AND product_id IN (
                SELECT p.id FROM products p
                JOIN ingredients i ON i.name = p.name
                WHERE i.ingredient_type = 'PROCESSED'
            );
        """)
        print(f"✅ Marked PROCESSED recipes: {result_processed}")

        # Step 3: Verify the changes
        print("\n📊 Summary:")
        counts = await conn.fetch("""
            SELECT recipe_type, COUNT(*) as count 
            FROM recipes 
            GROUP BY recipe_type 
            ORDER BY recipe_type;
        """)
        for row in counts:
            print(f"  {row['recipe_type']}: {row['count']} recipes")

        print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
