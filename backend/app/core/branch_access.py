"""
📍 BRANCH ACCESS - Dependencias para Control de Acceso a Sucursales

Dependencias y decoradores para validar que el usuario tiene acceso
a la sucursal que está intentando acceder/modificar.
"""
from typing import Optional, Callable
from functools import wraps
from fastapi import Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.models.branch import Branch
from app.auth_deps import get_current_user
from sqlmodel import select, and_

from logging import getLogger

logger = getLogger(__name__)


class BranchAccessError(HTTPException):
    """Excepción específica para errores de acceso a sucursal."""
    def __init__(self, branch_id: int, message: str = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message or f"No tienes acceso a la sucursal {branch_id}"
        )


async def validate_branch_access(
    branch_id: int,
    user: User,
    session: AsyncSession,
    require_active: bool = True
) -> Branch:
    """
    Valida que el usuario puede acceder a una sucursal específica.
    
    Args:
        branch_id: ID de la sucursal a acceder
        user: Usuario actual
        session: Sesión de BD
        require_active: Si la sucursal debe estar activa
        
    Returns:
        Branch: La sucursal si tiene acceso
        
    Raises:
        HTTPException: 403 si no tiene acceso, 404 si no existe
    """
    # Buscar la sucursal
    conditions = [
        Branch.id == branch_id,
        Branch.company_id == user.company_id  # Debe pertenecer a su empresa
    ]
    if require_active:
        conditions.append(Branch.is_active == True)
    
    stmt = select(Branch).where(and_(*conditions))
    result = await session.execute(stmt)
    branch = result.scalar_one_or_none()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sucursal {branch_id} no encontrada o inactiva"
        )
    
    # Validar acceso del usuario
    if not user.can_access_branch(branch_id):
        logger.warning(
            f"🚫 Acceso denegado: Usuario {user.username} intentó acceder a sucursal {branch_id} "
            f"(asignado a {user.branch_id})"
        )
        raise BranchAccessError(branch_id)
    
    return branch


async def get_validated_branch(
    branch_id: int = Path(..., description="ID de la sucursal"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> Branch:
    """
    Dependencia que valida acceso a sucursal en path parameter.
    
    Uso:
        @router.get("/{branch_id}/items")
        async def get_items(
            branch: Branch = Depends(get_validated_branch)
        ):
    """
    return await validate_branch_access(branch_id, current_user, session)


async def get_optional_validated_branch(
    branch_id: Optional[int] = Query(None, description="ID de sucursal (opcional)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> Optional[Branch]:
    """
    Dependencia para branch_id opcional en query params.
    
    Si no se especifica y el usuario tiene branch asignado, usa ese.
    Si no se especifica y el usuario NO tiene branch (acceso global), retorna None (todas).
    
    Uso:
        @router.get("/items")
        async def list_items(
            branch: Optional[Branch] = Depends(get_optional_validated_branch)
        ):
    """
    if branch_id is not None:
        return await validate_branch_access(branch_id, current_user, session)
    
    # Si el usuario tiene branch asignado, usar ese
    if current_user.branch_id:
        return await validate_branch_access(current_user.branch_id, current_user, session)
    
    # Usuario con acceso global (None = todas las sucursales)
    return None


def get_effective_branch_id(
    branch: Optional[Branch],
    user: User
) -> Optional[int]:
    """
    Obtiene el branch_id efectivo basado en el contexto.
    
    Args:
        branch: Sucursal validada (puede ser None para acceso global)
        user: Usuario actual
        
    Returns:
        branch_id efectivo o None si debe consultar todas
    """
    if branch:
        return branch.id
    if user.branch_id:
        return user.branch_id
    return None  # Consultar todas


def require_branch_access(func: Callable) -> Callable:
    """
    Decorador que inyecta validación de acceso a sucursal.
    
    El endpoint debe tener un parámetro `branch_id` (path o body).
    
    Uso:
        @router.post("/{branch_id}/orders")
        @require_branch_access
        async def create_order(
            branch_id: int,
            current_user: User = Depends(get_current_user),
            session: AsyncSession = Depends(get_session)
        ):
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extraer dependencias del contexto
        branch_id = kwargs.get('branch_id')
        current_user = kwargs.get('current_user')
        session = kwargs.get('session') or kwargs.get('db')
        
        if branch_id and current_user and session:
            # Validar acceso
            await validate_branch_access(branch_id, current_user, session)
        
        return await func(*args, **kwargs)
    
    return wrapper
