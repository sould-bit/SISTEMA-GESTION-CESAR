"""
🔐 RBAC ROUTER - Gestión de Roles y Permisos

Este router centraliza la administración de:
1. Roles personalizados y del sistema
2. Permisos y asignación a roles
3. Categorías de permisos dinámicas

Aislamiento Multi-tenant: Todas las operaciones están protegidas por company_id.
Seguridad: Protegido por decoradores @require_permission.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.dependencies import get_current_user, verify_current_user_company
from app.services.role_service import RoleService
from app.services.permission_service import PermissionService
from app.services.permission_category_service import PermissionCategoryService
from app.schemas.rbac import (
    RoleRead, RoleCreate, RoleUpdate, RoleWithPermissions,
    PermissionRead, PermissionCreate, PermissionUpdate,
    PermissionCategoryRead, PermissionCategoryCreate, PermissionCategoryUpdate
)
from app.core.permissions import require_permission


router = APIRouter(prefix="/rbac", tags=["RBAC"])


# ============================================================================
# DEPENDENCIAS DE SERVICIOS
# ============================================================================

def get_role_service(session: AsyncSession = Depends(get_session)) -> RoleService:
    return RoleService(session)

def get_permission_service(session: AsyncSession = Depends(get_session)) -> PermissionService:
    return PermissionService(session)

def get_category_service(session: AsyncSession = Depends(get_session)) -> PermissionCategoryService:
    return PermissionCategoryService(session)


# ============================================================================
# ROLES ENDPOINTS
# ============================================================================

@router.get("/roles", response_model=List[RoleRead])
@require_permission("admin.roles.read")
async def list_roles(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    role_service: RoleService = Depends(get_role_service)
):
    """Lista todos los roles de la empresa."""
    return await role_service.list_roles(current_user.company_id)


@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
@require_permission("admin.roles.create")
async def create_role(
    role_data: RoleCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    role_service: RoleService = Depends(get_role_service)
):
    """Crea un nuevo rol personalizado."""
    try:
        return await role_service.create_role(
            company_id=current_user.company_id,
            name=role_data.name,
            code=role_data.code,
            description=role_data.description,
            hierarchy_level=role_data.hierarchy_level,
            permission_ids=role_data.permission_ids
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/roles/{role_id}", response_model=RoleWithPermissions)
@require_permission("admin.roles.read")
async def get_role(
    role_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    role_service: RoleService = Depends(get_role_service)
):
    """Obtiene un rol con todos sus permisos."""
    role = await role_service.get_role(role_id, current_user.company_id, include_permissions=True)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")
    
    # Transformar RolePermission relations a lista de PermissionRead
    permissions = [rp.permission for rp in role.role_permissions if rp.permission]
    
    role_dict = role.model_dump()
    role_dict["permissions"] = permissions
    return role_dict


@router.put("/roles/{role_id}", response_model=RoleRead)
@require_permission("admin.roles.update")
async def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    role_service: RoleService = Depends(get_role_service)
):
    """Actualiza la información de un rol."""
    try:
        return await role_service.update_role(
            role_id=role_id,
            company_id=current_user.company_id,
            **role_data.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/roles/{role_id}")
@require_permission("admin.roles.delete")
async def delete_role(
    role_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    role_service: RoleService = Depends(get_role_service)
):
    """Elimina (soft delete) un rol."""
    try:
        success = await role_service.delete_role(role_id, current_user.company_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")
        return {"message": "Rol eliminado exitosamente"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# PERMISSIONS ENDPOINTS
# ============================================================================

@router.get("/permissions", response_model=List[PermissionRead])
@require_permission("admin.permissions.read")
async def list_permissions(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """Lista todos los permisos disponibles en la empresa."""
    return await permission_service.list_permissions(current_user.company_id)


@router.post("/roles/{role_id}/permissions/{permission_id}")
@require_permission("admin.roles.update")
async def grant_permission(
    role_id: UUID,
    permission_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """Asigna un permiso a un rol."""
    try:
        await permission_service.grant_permission_to_role(
            role_id=role_id,
            permission_id=permission_id,
            granted_by=current_user.id
        )
        return {"message": "Permiso asignado exitosamente"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/roles/{role_id}/permissions/{permission_id}")
@require_permission("admin.roles.update")
async def revoke_permission(
    role_id: UUID,
    permission_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """Revoca un permiso de un rol."""
    success = await permission_service.revoke_permission_from_role(role_id, permission_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada")
    return {"message": "Permiso revocado exitosamente"}


# ============================================================================
# CATEGORIES ENDPOINTS
# ============================================================================

@router.get("/categories", response_model=List[PermissionCategoryRead])
@require_permission("admin.categories.read")
async def list_categories(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    category_service: PermissionCategoryService = Depends(get_category_service)
):
    """Lista todas las categorías de permisos."""
    return await category_service.list_categories(current_user.company_id)


@router.post("/categories", response_model=PermissionCategoryRead, status_code=status.HTTP_201_CREATED)
@require_permission("admin.categories.create")
async def create_category(
    category_data: PermissionCategoryCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    category_service: PermissionCategoryService = Depends(get_category_service)
):
    """Crea una nueva categoría de permisos."""
    try:
        return await category_service.create_category(
            company_id=current_user.company_id,
            name=category_data.name,
            code=category_data.code,
            description=category_data.description,
            icon=category_data.icon,
            color=category_data.color
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
