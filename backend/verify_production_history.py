import asyncio
import uuid
import sys
import os

# Add backend directory to path
sys.path.append(os.getcwd())

from app.database import async_session
from app.services.production_service import ProductionService
from app.services.inventory_service import InventoryService
from app.services.ingredient_service import IngredientService
from app.models.ingredient import Ingredient, IngredientType
from app.models.permission import Permission
from app.models.user import User

async def verify_production_history():
    async with async_session() as session:
        print("Starting Verification...")
        
        # 0. Setup Services
        prod_service = ProductionService(session)
        inv_service = InventoryService(session)
        ing_service = IngredientService(session)

        # 1. Create Test Ingredients
        print("Creating Ingredients...")
        try:
            input1 = await ing_service.create(
                company_id=1, name=f"Test Input 1 {uuid.uuid4().hex[:4]}", sku=f"TEST-IN-1-{uuid.uuid4().hex[:4]}", base_unit="g", current_cost=10.0, ingredient_type=IngredientType.RAW
            )
            print(f"Input 1 Created: {input1.id}")
            input2 = await ing_service.create(
                company_id=1, name=f"Test Input 2 {uuid.uuid4().hex[:4]}", sku=f"TEST-IN-2-{uuid.uuid4().hex[:4]}", base_unit="ml", current_cost=5.0, ingredient_type=IngredientType.RAW
            )
            print(f"Input 2 Created: {input2.id}")
            output_ing = await ing_service.create(
                company_id=1, name=f"Test Output {uuid.uuid4().hex[:4]}", sku=f"TEST-OUT-{uuid.uuid4().hex[:4]}", base_unit="und", current_cost=0.0, ingredient_type=IngredientType.PROCESSED
            )
            print(f"Output Created: {output_ing.id}")
        except Exception as e:
            print(f"Error creating ingredients: {e}")
            import traceback
            traceback.print_exc()
            return

        # 2. Add Stock for Inputs
        print(f"Adding Stock for {input1.id} and {input2.id}...")
        try:
            await inv_service.update_ingredient_stock(branch_id=1, ingredient_id=input1.id, quantity_delta=1000, transaction_type="IN", user_id=1, cost_per_unit=10.0)
            await inv_service.update_ingredient_stock(branch_id=1, ingredient_id=input2.id, quantity_delta=500, transaction_type="IN", user_id=1, cost_per_unit=5.0)
            print("Stock Added.")
        except Exception as e:
            print(f"Error adding stock: {e}")
            import traceback
            traceback.print_exc()
            return

        # 3. Register Production
        print("Registering Production...")
        inputs_payload = [
            {"ingredient_id": input1.id, "quantity": 100},
            {"ingredient_id": input2.id, "quantity": 50}
        ]
        output_payload = {"ingredient_id": output_ing.id} 

        try:
            event = await prod_service.register_production_event(
                company_id=1,
                branch_id=1,
                user_id=1,
                inputs=inputs_payload,
                output=output_payload,
                output_quantity=10,
                notes="Verification Test"
            )
            print(f"Production Event Created: {event.id}")
        except Exception as e:
            print(f"Error registering production: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 4. Verify output_batch_id
        print(f"Output Batch ID: {event.output_batch_id}")
        if not event.output_batch_id:
            print("FAILURE: output_batch_id is None!")
        else:
            print("SUCCESS: output_batch_id is set.")
            
            # 5. Simulate Fetching Details
            from sqlmodel import select
            from app.models.production_event_input import ProductionEventInput
            
            stmt = select(ProductionEventInput, Ingredient.name, Ingredient.base_unit)\
                .join(Ingredient, ProductionEventInput.ingredient_id == Ingredient.id)\
                .where(ProductionEventInput.production_event_id == event.id)
            
            res = await session.execute(stmt)
            inputs_data = res.all()
            
            print("Fetched Inputs for Batch:")
            for inp, name, unit in inputs_data:
                print(f" - {name}: {inp.quantity} {unit}")
                
            if len(inputs_data) == 2:
                 print("SUCCESS: Correct number of inputs linked.")
            else:
                 print(f"FAILURE: Expected 2 inputs, got {len(inputs_data)}.")

if __name__ == "__main__":
    asyncio.run(verify_production_history())
