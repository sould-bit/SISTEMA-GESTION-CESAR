from decimal import Decimal
from typing import List, Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.inventory import Inventory, InventoryTransaction

class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stock(self, branch_id: int, product_id: int, for_update: bool = False) -> Optional[Inventory]:
        """Obtener registro de inventario para un producto en una sucursal"""
        statement = select(Inventory).where(
            Inventory.branch_id == branch_id,
            Inventory.product_id == product_id
        )
        if for_update:
            statement = statement.with_for_update()
            
        result = await self.db.execute(statement)
        return result.scalars().one_or_none()

    async def initialize_stock(self, branch_id: int, product_id: int) -> Inventory:
        """Crear registro de inventario inicial (en 0)"""
        inventory = Inventory(
            branch_id=branch_id,
            product_id=product_id,
            stock=Decimal("0.000")
        )
        self.db.add(inventory)
        await self.db.commit()
        await self.db.refresh(inventory)
        return inventory

    async def update_stock(
        self, 
        branch_id: int, 
        product_id: int, 
        quantity_delta: Decimal, 
        transaction_type: str,
        user_id: int,
        reference_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Inventory:
        """
        Actualizar stock de manera transaccional.
        - quantity_delta: Positivo para entrada, Negativo para salida/venta
        """
        # 1. Obtener o crear inventario
        inventory = await self.get_stock(branch_id, product_id, for_update=True)
        if not inventory:
            inventory = await self.initialize_stock(branch_id, product_id)

        # 2. Calcular nuevo balance
        new_balance = inventory.stock + quantity_delta
        
        # 3. Validación: No permitir stock negativo (opcional, por ahora soft-check)
        if new_balance < 0 and transaction_type in ["SALE", "OUT"]:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente. Disponible: {inventory.stock}, Solicitado: {abs(quantity_delta)}"
            ) 

        # 4. Actualizar Inventario
        inventory.stock = new_balance
        self.db.add(inventory)

        # 5. Registrar Transacción (Kardex)
        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type=transaction_type,
            quantity=quantity_delta,
            balance_after=new_balance,
            reference_id=reference_id,
            reason=reason,
            user_id=user_id
        )
        self.db.add(transaction)
        
        await self.db.commit()
        await self.db.refresh(inventory)
        
        return inventory

    async def get_low_stock_alerts(self, branch_id: int) -> List[Inventory]:
        """Listar productos con stock debajo del mínimo"""
        statement = select(Inventory).where(
            Inventory.branch_id == branch_id,
            Inventory.stock <= Inventory.min_stock
        )
        result = await self.db.execute(statement)
        return result.scalars().all()
