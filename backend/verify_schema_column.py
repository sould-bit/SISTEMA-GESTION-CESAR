import asyncio
import sys
import os
from sqlalchemy import text

sys.path.append(os.getcwd())
from app.database import async_session

async def verify_column():
    async with async_session() as session:
        print("Checking column output_batch_id in production_events...")
        try:
            # Query information_schema
            stmt = text("SELECT column_name FROM information_schema.columns WHERE table_name='production_events' AND column_name='output_batch_id'")
            result = await session.execute(stmt)
            col = result.scalar()
            if col:
                print(f"SUCCESS: Column '{col}' exists.")
            else:
                print("FAILURE: Column 'output_batch_id' NOT FOUND.")
        except Exception as e:
            print(f"Error checking column: {e}")

if __name__ == "__main__":
    asyncio.run(verify_column())
