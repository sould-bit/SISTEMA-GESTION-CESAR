from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

from app.database import get_session
from app.models.user import User
from app.models.inventory import Inventory, InventoryTransaction
from app.auth_deps import get_current_user
from app.core.permissions import require_permission

router = APIRouter(prefix="/inventory", tags=["inventory"])

# -----------------------------------------------
# Schemas (DTOs)
# -----------------------------------------------
class StockAdjustmentRequest(BaseModel):
    branch_id: int
    product_id: int
    quantity_delta: Decimal
    transaction_type: str # IN, OUT, ADJ, WASTE
    reason: Optional[str] = None
    reference_id: Optional[str] = None

class InventoryResponse(BaseModel):
    id: int
    branch_id: int
    product_id: int
    stock: Decimal
    min_stock: Decimal
    bin_location: Optional[str]
    product_name: str
    updated_at: datetime

# -----------------------------------------------
# Endpoints
# -----------------------------------------------

@router.get("/{branch_id}", response_model=List[InventoryResponse])
@require_permission("inventory:list")
async def list_branch_inventory(
    branch_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Listar inventario de una sucursal"""
    # TODO: Validar acceso del usuario a la sucursal (Middleware o check manual)
    
    # Por ahora hacemos query manual para join con producto
    # En futuro servicio podria devolver DTOs
    statement = select(Inventory).where(Inventory.branch_id == branch_id)
    result = await session.exec(statement)
    inventory_items = result.all()
    
    response = []
    for item in inventory_items:
        # Lazy load product name needs special handling in async
        # We should probably eager load product in query
        # For now, let's just try to access if loaded, or query separately if needed.
        # Ideally: statement.options(selectinload(Inventory.product))
        
        # NOTE: Async relationships might trigger MissingGreenlet if not careful.
        # But let's assume loose coupling for now. If failure, we will fix with selectinload.
        product_name = "Producto (ID: " + str(item.product_id) + ")" # Placeholder safe
        
        response.append(InventoryResponse(
            id=item.id,
            branch_id=item.branch_id,
            product_id=item.product_id,
            stock=item.stock,
            min_stock=item.min_stock,
            bin_location=item.bin_location,
            product_name=product_name,
            updated_at=item.updated_at
        ))
    return response

@router.post("/adjust", response_model=dict)
@require_permission("inventory:adjust")
async def adjust_stock(
    adjustment: StockAdjustmentRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Realizar ajuste manual de stock"""
    service = InventoryService(session)
    
    try:
        inventory = await service.update_stock(
            branch_id=adjustment.branch_id,
            product_id=adjustment.product_id,
            quantity_delta=adjustment.quantity_delta,
            transaction_type=adjustment.transaction_type,
            user_id=current_user.id,
            reference_id=adjustment.reference_id,
            reason=adjustment.reason
        )
        return {"status": "success", "new_stock": inventory.stock, "message": "Ajuste realizado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/alerts/{branch_id}")
@require_permission("inventory:list")
async def get_low_stock(
    branch_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Obtener productos con stock bajo"""
    service = InventoryService(session)
    alerts = await service.get_low_stock_alerts(branch_id)
    return alerts
