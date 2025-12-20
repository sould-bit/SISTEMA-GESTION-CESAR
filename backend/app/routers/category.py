"""
🗂️ ROUTER DE CATEGORÍAS - Gestión del Catálogo de Productos

Este módulo maneja las categorías de productos con aislamiento multi-tenant.
Todas las operaciones están filtradas por company_id.

Conceptos clave:
- Multi-tenant: Cada empresa ve solo sus categorías
- Async/Await: Operaciones no-bloqueantes
- Validation: Schemas Pydantic para entrada/salida
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_session
from app.models.user import User
from app.dependencies import (
    get_current_user,
    verify_current_user_company,  # ✅ Nueva: retorna company_id del usuario
    verify_company_access         # ✅ Original: valida acceso específico
)
from app.schemas.category import CategoryRead, CategoryCreate, CategoryUpdate
from app.services import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])

# ============================================
# DEPENDENCIAS DE SERVICIOS
# ============================================
def get_category_service(session: AsyncSession = Depends(get_session)) -> CategoryService:
    """
    🛠️ DEPENDENCIA: INYECTAR CATEGORY SERVICE

    Proporciona una instancia del CategoryService con la sesión de BD.
    """
    return CategoryService(session)

# ============================================
# ENDPOINT: LISTAR CATEGORÍAS
# ============================================
@router.get("/", response_model=List[CategoryRead])
async def get_categories(
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    📋 LISTAR TODAS LAS CATEGORÍAS DE LA EMPRESA

    Retorna todas las categorías activas de la empresa del usuario.
    Filtrado automático por company_id.

    Args:
        current_user: Usuario autenticado (inyectado por dependencia)
        category_service: Servicio de categorías

    Returns:
        List[CategoryRead]: Lista de categorías
    """
    return await category_service.get_categories(current_user.company_id)

# ============================================
# ENDPOINT: CREAR CATEGORÍA
# ============================================
@router.post("/", response_model=CategoryRead)
async def create_category(
    category_data: CategoryCreate,
    company_id: int = Depends(verify_current_user_company),  # ✅ Retorna int del usuario
    category_service: CategoryService = Depends(get_category_service)
):
    """
    ➕ CREAR NUEVA CATEGORÍA CON SEGURIDAD MULTI-TENANT

    Crea una categoría para la empresa del usuario autenticado.
    El company_id se obtiene automáticamente del usuario (NO del body)
    para prevenir que usuarios creen categorías en empresas ajenas.

    SEGURIDAD: Tres capas de protección
    1. ✅ Autenticación: Usuario debe estar logueado
    2. ✅ Multi-tenant: company_id viene del contexto del usuario
    3. ✅ Asignación automática: No se puede manipular desde el cliente

    Args:
        category_data: Datos de la nueva categoría (name, description, is_active)
        company_id: ID de empresa obtenido del usuario autenticado (automático)
        category_service: Servicio de categorías

    Returns:
        CategoryRead: Categoría creada con ID asignado

    Raises:
        HTTPException 400: Si ya existe una categoría con el mismo nombre
        HTTPException 401: Si el usuario no está autenticado
        HTTPException 500: Si hay errores internos del servidor
    """
    return await category_service.create_category(category_data, company_id)

# ============================================
# ENDPOINT: OBTENER CATEGORÍA POR ID
# ============================================
@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    🔍 OBTENER CATEGORÍA ESPECÍFICA

    Busca una categoría por ID, verificando que pertenezca a la empresa.

    Args:
        category_id: ID de la categoría
        current_user: Usuario autenticado
        category_service: Servicio de categorías

    Returns:
        CategoryRead: Datos de la categoría

    Raises:
        HTTPException 404: Si no se encuentra o no pertenece a la empresa
    """
    return await category_service.get_category_by_id(category_id, current_user.company_id)

# ============================================
# ENDPOINT: ACTUALIZAR CATEGORÍA
# ============================================
@router.put("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    ✏️ ACTUALIZAR CATEGORÍA

    Actualiza los datos de una categoría existente.
    Solo campos proporcionados serán actualizados.

    Args:
        category_id: ID de la categoría
        category_data: Datos a actualizar (campos opcionales)
        current_user: Usuario autenticado
        category_service: Servicio de categorías

    Returns:
        CategoryRead: Categoría actualizada

    Raises:
        HTTPException 404: Si no se encuentra o no pertenece a la empresa
    """
    return await category_service.update_category(
        category_id,
        category_data,
        current_user.company_id
    )

# ============================================
# ENDPOINT: ELIMINAR CATEGORÍA (SOFT DELETE)
# ============================================
@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    🗑️ ELIMINAR CATEGORÍA (Soft Delete)

    Marca la categoría como inactiva en lugar de eliminarla.
    Esto preserva la integridad referencial.

    Args:
        category_id: ID de la categoría
        current_user: Usuario autenticado
        category_service: Servicio de categorías

    Returns:
        dict: Confirmación de eliminación

    Raises:
        HTTPException 404: Si no se encuentra o no pertenece a la empresa
    """
    return await category_service.delete_category(category_id, current_user.company_id)
