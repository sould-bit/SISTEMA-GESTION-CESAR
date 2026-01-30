import os
import sys
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

# Path setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Force sync driver
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("❌ ERROR: DATABASE_URL not found in .env")
    sys.exit(1)

# Replace async driver with sync driver
sync_url = db_url.replace("postgresql+asyncpg", "postgresql")

def check():
    print("Checking database columns...")
    try:
        engine = create_engine(sync_url)
        insp = inspect(engine)
        
        print("\nTable: RECIPES")
        print("-" * 30)
        cols = insp.get_columns("recipes")
        for c in cols:
            print(f"{c['name']:<15} | {c['type']}")
            
        print("\nTable: RECIPE_ITEMS")
        print("-" * 30)
        cols_items = insp.get_columns("recipe_items")
        for c in cols_items:
            print(f"{c['name']:<15} | {c['type']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check()
