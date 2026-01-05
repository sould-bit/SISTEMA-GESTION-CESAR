
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models.user import User
from app.auth_deps import get_current_user
from app.services.cash_service import CashService
from app.schemas.cash import CashOpen, CashClose, CashClosureRead

router = APIRouter(prefix="/cash", tags=["cash"])

def get_cash_service(session: AsyncSession = Depends(get_session)) -> CashService:
    return CashService(session)

@router.post("/open", response_model=CashClosureRead)
async def open_register(
    data: CashOpen,
    current_user: User = Depends(get_current_user),
    service: CashService = Depends(get_cash_service)
):
    """Abre un nuevo turno de caja."""
    return await service.open_register(current_user, data.initial_cash)

@router.get("/current", response_model=CashClosureRead)
async def get_current_status(
    current_user: User = Depends(get_current_user),
    service: CashService = Depends(get_cash_service)
):
    """Ver estado actual de la caja abierta (con totales calculados al momento)."""
    closure = await service.get_active_closure(current_user.id)
    if not closure:
        raise HTTPException(status_code=404, detail="No hay caja abierta")
    
    # Calcular totales on-the-flight para mostrar al usuario
    totals = await service.calculate_current_totals(closure)
    
    # Actualizar objeto en memoria para la respuesta (sin guardar en BD aun)
    closure.expected_cash = totals["cash"]
    closure.expected_card = totals["card"]
    closure.expected_transfer = totals["transfer"]
    closure.expected_total = closure.initial_cash + sum(totals.values())
    
    return closure

@router.post("/{closure_id}/close", response_model=CashClosureRead)
async def close_register(
    closure_id: int,
    data: CashClose,
    service: CashService = Depends(get_cash_service),
    current_user: User = Depends(get_current_user)
):
    """Cierra la caja reportando montos reales."""
    return await service.close_register(
        closure_id=closure_id,
        real_cash=data.real_cash,
        real_card=data.real_card,
        real_transfer=data.real_transfer,
        notes=data.notes
    )
