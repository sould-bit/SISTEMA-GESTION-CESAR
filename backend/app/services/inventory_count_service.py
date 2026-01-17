from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid
from sqlmodel import select, col
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.inventory_count import InventoryCount, InventoryCountItem, InventoryCountStatus
from app.models.ingredient import Ingredient
from app.models.ingredient_inventory import IngredientInventory
from app.services.inventory_service import InventoryService

class InventoryCountService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.inventory_service = InventoryService(db)

    async def create_count(self, company_id: int, branch_id: int, user_id: int, notes: str = None) -> InventoryCount:
        """
        Inicia una toma de inventario.
        Genera items para TODOS los ingredientes activos de la compañía (o sucursal?).
        Típicamente los ingredientes son globales, el stock es por sucursal.
        Si no hay stock record, expected=0.
        """
        # 1. Crear Header
        count = InventoryCount(
            company_id=company_id,
            branch_id=branch_id,
            user_id=user_id,
            status=InventoryCountStatus.OPEN,
            created_at=datetime.utcnow(),
            notes=notes
        )
        self.db.add(count)
        await self.db.flush() # Para tener ID
        
        # 2. Snapshot de Inventario
        # Obtener todos los ingredientes de la empresa
        stmt = select(Ingredient).where(Ingredient.company_id == company_id, Ingredient.is_active == True)
        res = await self.db.execute(stmt)
        ingredients = res.scalars().all()
        
        # Obtener stock actual para esta sucursal (en bulk)
        # Podriamos hacerlo uno por uno o query mas optimizada.
        # Por simplicidad ahora: iterar.
        
        for ing in ingredients:
            # Obtener stock actual
            inventory = await self.inventory_service.get_ingredient_stock(branch_id, ing.id)
            current_stock = inventory.stock if inventory else Decimal(0)
            
            # TODO: Snapshot del Costo Promedio o Ultimo?
            # Usaremos current_cost del ingrediente o costo ponderado si estuviera disponible.
            # Por ahora ingredient.current_cost o last_cost.
            cost = ing.current_cost or Decimal(0)
            
            item = InventoryCountItem(
                count_id=count.id,
                ingredient_id=ing.id,
                expected_quantity=current_stock,
                counted_quantity=None, # Aun no contado
                cost_per_unit=cost
            )
            self.db.add(item)
            
        await self.db.commit()
        await self.db.refresh(count)
        return count

    async def update_count_item(self, count_id: uuid.UUID, ingredient_id: uuid.UUID, counted_qty: Decimal):
        """Actualiza el conteo físico de un ítem."""
        stmt = select(InventoryCountItem).where(
            InventoryCountItem.count_id == count_id,
            InventoryCountItem.ingredient_id == ingredient_id
        )
        res = await self.db.execute(stmt)
        item = res.scalar_one_or_none()
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found in this count")
            
        item.counted_quantity = counted_qty
        self.db.add(item)
        await self.db.commit()
        return item

    async def close_count(self, count_id: uuid.UUID):
        """Cierra el conteo. Ya no se pueden editar cantidades."""
        count = await self.db.get(InventoryCount, count_id)
        if not count:
            raise HTTPException(status_code=404, detail="Count not found")
            
        if count.status != InventoryCountStatus.OPEN:
            raise HTTPException(status_code=400, detail="Count is not OPEN")
            
        count.status = InventoryCountStatus.CLOSED
        count.closed_at = datetime.utcnow()
        self.db.add(count)
        await self.db.commit()
        return count

    async def apply_adjustments(self, count_id: uuid.UUID, user_id: int):
        """
        Aplica las diferencias al inventario real.
        Genera movimientos de tipo "AUDIT_ADJUST".
        """
        count = await self.db.get(InventoryCount, count_id)
        if not count:
            raise HTTPException(status_code=404, detail="Count not found")
            
        if count.status != InventoryCountStatus.CLOSED:
             # Permitir aplicar solo si está CERRADO (Revisado)
            raise HTTPException(status_code=400, detail="Count must be CLOSED to apply")

        # Cargar items
        stmt = select(InventoryCountItem).where(InventoryCountItem.count_id == count_id)
        res = await self.db.execute(stmt)
        items = res.scalars().all()
        
        for item in items:
            if item.counted_quantity is None:
                continue # No contado, ignorar o asumir 0? Mejor ignorar para no destruir stock no contado.
                
            diff = item.counted_quantity - item.expected_quantity
            
            if diff != 0:
                # Ajustar Stock
                # Si diff > 0: Sobra (Entrada)
                # Si diff < 0: Falta (Salida/Merma)
                
                # Usamos update_ingredient_stock con TransactionType="ADJUST"
                # Pero InventoryService.update logic for ADJUST: expected absolute quantity? 
                # Revisitamos InventoryService:
                # if transaction_type == "ADJUST": new_balance = quantity_delta (Passed as absolute?)
                # Checks: "if transaction_type == "ADJUST": new_balance = quantity_delta; actual_delta = new_balance - inventory.stock"
                # YES. So we pass the NEW absolute quantity (counted_quantity).
                
                await self.inventory_service.update_ingredient_stock(
                    branch_id=count.branch_id,
                    ingredient_id=item.ingredient_id,
                    quantity_delta=item.counted_quantity, # Pass ABSOLUTE value for ADJUST
                    transaction_type="ADJUST",
                    user_id=user_id,
                    reference_id=str(count.id),
                    reason="Audit Adjustment",
                    cost_per_unit=item.cost_per_unit # Use snapshot cost for adjustments
                )
        
        count.status = InventoryCountStatus.APPLIED
        count.applied_at = datetime.utcnow()
        self.db.add(count)
        await self.db.commit()
        return count
