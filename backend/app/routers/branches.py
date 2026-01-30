"""
📍 ROUTER DE SUCURSALES (BRANCHES)

Endpoints para gestión de sucursales.
Todos los endpoints requieren autenticación y permisos RBAC.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.auth_deps import get_current_user
from app.services.branch_service import BranchService
from app.schemas.branch import (
    BranchCreate,
    BranchUpdate,
    BranchResponse,
    BranchList
)
from app.core.permissions import require_permission

from logging import getLogger

logger = getLogger(__name__)

router = APIRouter(prefix="/branches", tags=["Sucursales"])


# ============================================================================
# DEPENDENCIAS
# ============================================================================
def get_branch_service(session: AsyncSession = Depends(get_session)) -> BranchService:
    """Inyecta el servicio de sucursales."""
    return BranchService(session)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("", response_model=BranchList)
@require_permission("branches.read")
async def list_branches(
    include_inactive: bool = Query(False, description="Incluir sucursales inactivas"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    branch_service: BranchService = Depends(get_branch_service)
):
    """
    📋 Lista todas las sucursales de la empresa.
    
    Permisos requeridos: `branches.read`
    
    Retorna lista paginada con estadísticas opcionales.
    """
    branches, total = await branch_service.list_branches(
        company_id=current_user.company_id,
        include_inactive=include_inactive,
        page=page,
        size=size
    )
    
    # Agregar conteo de usuarios a cada sucursal
    items = []
    for branch in branches:
        response = BranchResponse.model_validate(branch)
        response.user_count = await branch_service.get_user_count(branch.id)
        items.append(response)
    
    return BranchList(
        items=items,
        total=total,
        page=page,
        size=size
    )


@router.get("/{branch_id}", response_model=BranchResponse)
@require_permission("branches.read")
async def get_branch(
    branch_id: int,
    current_user: User = Depends(get_current_user),
    branch_service: BranchService = Depends(get_branch_service)
):
    """
    🔍 Obtiene una sucursal por ID.
    
    Permisos requeridos: `branches.read`
    """
    branch = await branch_service.get_branch_or_404(branch_id, current_user.company_id)
    response = BranchResponse.model_validate(branch)
    response.user_count = await branch_service.get_user_count(branch.id)
    return response


@router.post("", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
@require_permission("branches.create")
async def create_branch(
    branch_data: BranchCreate,
    current_user: User = Depends(get_current_user),
    branch_service: BranchService = Depends(get_branch_service)
):
    """
    ➕ Crea una nueva sucursal.
    
    Permisos requeridos: `branches.create`
    
    Validaciones:
    - El código debe ser único por empresa
    - Si es la primera sucursal, se marca automáticamente como principal
    """
    branch = await branch_service.create_branch(
        company_id=current_user.company_id,
        data=branch_data
    )
    
    response = BranchResponse.model_validate(branch)
    response.user_count = 0
    return response


@router.put("/{branch_id}", response_model=BranchResponse)
@require_permission("branches.update")
async def update_branch(
    branch_id: int,
    branch_data: BranchUpdate,
    current_user: User = Depends(get_current_user),
    branch_service: BranchService = Depends(get_branch_service)
):
    """
    ✏️ Actualiza una sucursal existente.
    
    Permisos requeridos: `branches.update`
    
    Validaciones:
    - Si cambia el código, debe ser único
    - Si se marca como principal, desmarca las otras
    """
    branch = await branch_service.update_branch(
        branch_id=branch_id,
        company_id=current_user.company_id,
        data=branch_data
    )
    
    response = BranchResponse.model_validate(branch)
    response.user_count = await branch_service.get_user_count(branch.id)
    return response


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("branches.delete")
async def delete_branch(
    branch_id: int,
    current_user: User = Depends(get_current_user),
    branch_service: BranchService = Depends(get_branch_service)
):
    """
    🗑️ Elimina (desactiva) una sucursal.
    
    Permisos requeridos: `branches.delete`
    
    Validaciones:
    - No se puede eliminar la sucursal principal si hay otras activas
    - No se puede eliminar si tiene usuarios asignados
    
    Nota: Es un soft-delete, la sucursal se marca como inactiva.
    """
    await branch_service.delete_branch(
        branch_id=branch_id,
        company_id=current_user.company_id
    )
    return None


@router.post("/{branch_id}/set-main", response_model=BranchResponse)
@require_permission("branches.update")
async def set_main_branch(
    branch_id: int,
    current_user: User = Depends(get_current_user),
    branch_service: BranchService = Depends(get_branch_service)
):
    """
    ⭐ Establece una sucursal como principal.
    
    Permisos requeridos: `branches.update`
    
    Desmarca automáticamente la sucursal principal anterior.
    """
    from app.schemas.branch import BranchUpdate
    
    branch = await branch_service.update_branch(
        branch_id=branch_id,
        company_id=current_user.company_id,
        data=BranchUpdate(is_main=True)
    )
    
    response = BranchResponse.model_validate(branch)
    response.user_count = await branch_service.get_user_count(branch.id)
    return response
