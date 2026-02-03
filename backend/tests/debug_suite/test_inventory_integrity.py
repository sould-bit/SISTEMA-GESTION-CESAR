
import pytest
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.inventory_service import InventoryService
from app.models.ingredient import Ingredient
from app.models.ingredient_inventory import IngredientInventory, IngredientTransaction
from sqlmodel import select


@pytest.fixture
async def db_session(session: AsyncSession):
    yield session
    # Cleanup all entities created during test in this session
    # We will track created ingredients by ID in the test logic or just clean specifically
    await session.rollback()

@pytest.mark.asyncio
async def test_reversion_logic_integrity(session: AsyncSession, test_company, test_branch, test_user):
    """
    Test flow:
    1. Create distinct ingredient
    2. Add Stock (ADJUST +)
    3. Remove Stock (ADJUST -)
    4. Revert Removal -> Should restore Stock
    5. Attempt Revert Removal AGAIN -> Should Fail (Duplicate Protection)
    6. Verify History Trace
    """
    
    # Setup
    unique_id = uuid.uuid4().hex[:12]
    ingredient = Ingredient(
        name=f"Test Ingre {unique_id}",
        company_id=test_company.id, 
        current_cost=Decimal("10.00"),
        base_unit="KG",
        is_active=True
    )
    session.add(ingredient)
    await session.commit()
    await session.refresh(ingredient)
    
    try:
        service = InventoryService(session)
        user_id = test_user.id
        branch_id = test_branch.id
        
        # 1. Add Stock (+100)
        # Using 'ADJUST' effectively initializes or adds to stock without PO
        inv, _, _, _ = await service.update_ingredient_stock(
            branch_id=branch_id,
            ingredient_id=ingredient.id,
            quantity_delta=Decimal("100.00"),
            transaction_type="ADJUST",
            user_id=user_id,
            reason="Initial Load"
        )
        assert inv.stock == 100.00
        
        # 2. Consumption (-20)
        inv_after_consume, _, _, txn_consume = await service.update_ingredient_stock(
            branch_id=branch_id,
            ingredient_id=ingredient.id,
            quantity_delta=Decimal("-20.00"),
            transaction_type="ADJUST", # Using ADJUST for manual correction/waste simulation
            user_id=user_id,
            reason="Manual Reduction"
        )
        assert inv_after_consume.stock == 80.00
        
        # Capture the transaction to revert
        stmt = select(IngredientTransaction).where(IngredientTransaction.id == txn_consume.id)
        res = await session.execute(stmt)
        original_txn = res.scalar_one()
        
        print(f"\n[TEST] Original Transaction: {original_txn.id} | Qty: {original_txn.quantity}")

        # 3. Revert Consumption (Should be +20)
        print("reverting transaction...")
        reverted_inv, revert_txn = await service.revert_ingredient_transaction(
            transaction_id=original_txn.id,
            user_id=user_id,
            reason="Mistake in reduction"
        )
        
        print(f"[TEST] Reverted. New Stock: {reverted_inv.stock}")
        assert reverted_inv.stock == 100.00
        assert revert_txn.quantity == 20.00
        assert revert_txn.transaction_type == "REVERT_ADJ"
        
        # 4. Attempt Duplicate Reversion
        print("[TEST] Attempting duplicate reversion...")
        try:
            await service.revert_ingredient_transaction(
                transaction_id=original_txn.id,
                user_id=user_id,
                reason="Trying to cheat system"
            )
            assert False, "Should have raised HTTPException for duplicate reversion"
        except Exception as e:
            print(f"[TEST] Successfully caught expected error: {e}")
            assert "ya ha sido revertida" in str(e) or "400" in str(e) or "Bad Request" in str(e)

        # 5. Final Integrity Check
        stmt_final = select(IngredientInventory).where(IngredientInventory.ingredient_id == ingredient.id)
        res_final = await session.execute(stmt_final)
        final_inv = res_final.scalar_one()
        
        assert final_inv.stock == 100.00
        print("[TEST] Integrity Check Passed: Stock is back to 100.00 and duplicate prevented.")
    
    finally:
        # Cascade delete handling
        # Delete transactions first
        try:
             # Find inventory first
            stmt_inv = select(IngredientInventory).where(IngredientInventory.ingredient_id == ingredient.id)
            res_inv = await session.execute(stmt_inv)
            inventory = res_inv.scalar_one_or_none()
            
            if inventory:
                stmt_del_txns = select(IngredientTransaction).where(IngredientTransaction.inventory_id == inventory.id)
                res_txns = await session.execute(stmt_del_txns)
                txns = res_txns.scalars().all()
                for t in txns:
                    await session.delete(t)
                
                await session.delete(inventory)
            
            await session.delete(ingredient)
            await session.commit()
        except Exception as cleanup_error:
            print(f"Cleanup Error: {cleanup_error}")


@pytest.mark.asyncio
async def test_reversion_of_addition(session: AsyncSession, test_company, test_branch, test_user):
    """
    Test reversing an INPUT (+50). Should result in -50.
    """
    unique_id = uuid.uuid4().hex[:12]
    ingredient = Ingredient(
        name=f"Test Ingre Add {unique_id}",
        company_id=test_company.id, 
        current_cost=Decimal("5.00"),
        base_unit="L",
        is_active=True
    )
    session.add(ingredient)
    await session.commit()
    await session.refresh(ingredient)
    
    try:
        service = InventoryService(session)
        user_id = test_user.id
        branch_id = test_branch.id
        
        # Add +50
        inv, _, _, txn_add = await service.update_ingredient_stock(
            branch_id=branch_id,
            ingredient_id=ingredient.id,
            quantity_delta=Decimal("50.00"),
            transaction_type="ADJUST",
            user_id=user_id,
            reason="Wrong entry"
        )
        assert inv.stock == 50.00
        
        # Revert
        inv_after, txn_revert = await service.revert_ingredient_transaction(
            transaction_id=txn_add.id,
            user_id=user_id,
            reason="Undo addition"
        )
        
        assert inv_after.stock == 0.00
        assert txn_revert.quantity == -50.00
    
    finally:
        try:
             # Find inventory first
            stmt_inv = select(IngredientInventory).where(IngredientInventory.ingredient_id == ingredient.id)
            res_inv = await session.execute(stmt_inv)
            inventory = res_inv.scalar_one_or_none()
            
            if inventory:
                stmt_del_txns = select(IngredientTransaction).where(IngredientTransaction.inventory_id == inventory.id)
                res_txns = await session.execute(stmt_del_txns)
                txns = res_txns.scalars().all()
                for t in txns:
                    await session.delete(t)
                
                await session.delete(inventory)
            
            await session.delete(ingredient)
            await session.commit()
        except Exception as cleanup_error:
            print(f"Cleanup Error: {cleanup_error}")
