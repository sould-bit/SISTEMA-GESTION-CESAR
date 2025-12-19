"""
🗂️ ROUTER DE CATEGORÍAS - Gestión del Catálogo de Productos

Este módulo maneja las categorías de productos con aislamiento multi-tenant.
Todas las operaciones están filtradas por company_id.

Conceptos clave:
- Multi-tenant: Cada empresa ve solo sus categorías
- Async/Await: Operaciones no-bloqueantes
- Validation: Schemas Pydantic para entrada/salida
"""

from unicodedata import category
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_session
from app.models.category import Category
from app.models.user import User
from app.dependencies import (
    get_current_user,
    verify_current_user_company,  # ✅ Nueva: retorna company_id del usuario
    verify_company_access         # ✅ Original: valida acceso específico
) 
from app.schemas.category import CategoryRead, CategoryCreate, CategoryUpdate 

router = APIRouter(prefix="/categories", tags=["categories"])

# ============================================
# ENDPOINT: LISTAR CATEGORÍAS
# ============================================
@router.get("/", response_model=List[CategoryRead])
async def get_categories(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    📋 LISTAR TODAS LAS CATEGORÍAS DE LA EMPRESA

    Retorna todas las categorías activas de la empresa del usuario.
    Filtrado automático por company_id.

    Args:
        session: Sesión de BD asíncrona
        current_user: Usuario autenticado (inyectado por dependencia)

    Returns:
        List[CategoryRead]: Lista de categorías
    """
    # Query filtrada por empresa
    statement = select(Category).where(
        Category.company_id == current_user.company_id,
        Category.is_active == True
    )

    result = await session.execute(statement)
    categories = result.scalars().all()

    return categories

# ============================================
# ENDPOINT: CREAR CATEGORÍA
# ============================================
@router.post("/", response_model=CategoryRead)
async def create_category(
    category_data: CategoryCreate,
    company_id: int = Depends(verify_current_user_company),  # ✅ Retorna int del usuario
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
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
        current_user: Usuario autenticado (automático)
        session: Sesión de BD asíncrona (automática)

    Returns:
        CategoryRead: Categoría creada con ID asignado

    Raises:
        HTTPException 401: Si el usuario no está autenticado
        SQLAlchemyError: Si hay problemas con la base de datos
    """

    # ✅ SEGURIDAD: company_id viene de verify_current_user_company()
    # No hay verificación manual porque company_id ya es confiable
    # (viene del usuario autenticado, no del body del request)

    # Crear instancia del modelo con company_id seguro
    category = Category(
        name=category_data.name,
        description=category_data.description,
        is_active=category_data.is_active,
        company_id=company_id  # ✅ Viene de verify_current_user_company() (seguro)
    )

    # Guardar en BD
    session.add(category)
    await session.commit()
    await session.refresh(category)

    return category

# ============================================
# ENDPOINT: OBTENER CATEGORÍA POR ID
# ============================================
@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    🔍 OBTENER CATEGORÍA ESPECÍFICA

    Busca una categoría por ID, verificando que pertenezca a la empresa.

    Args:
        category_id: ID de la categoría
        session: Sesión de BD asíncrona
        current_user: Usuario autenticado

    Returns:
        CategoryRead: Datos de la categoría

    Raises:
        HTTPException 404: Si no se encuentra o no pertenece a la empresa
    """
    # Buscar categoría filtrada por empresa
    result = await session.execute(
        select(Category).where(
            Category.id == category_id,
            Category.company_id == current_user.company_id
        )
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    return category

# ============================================
# ENDPOINT: ACTUALIZAR CATEGORÍA
# ============================================
@router.put("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    ✏️ ACTUALIZAR CATEGORÍA

    Actualiza los datos de una categoría existente.
    Solo campos proporcionados serán actualizados.

    Args:
        category_id: ID de la categoría
        category_data: Datos a actualizar (campos opcionales)
        session: Sesión de BD asíncrona
        current_user: Usuario autenticado

    Returns:
        CategoryRead: Categoría actualizada

    Raises:
        HTTPException 404: Si no se encuentra o no pertenece a la empresa
    """
    # Buscar categoría
    result = await session.execute(
        select(Category).where(
            Category.id == category_id,
            Category.company_id == current_user.company_id
        )
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    # Actualizar solo campos proporcionados
    update_data = category_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    # Guardar cambios
    await session.commit()
    await session.refresh(category)

    return category

# ============================================
# ENDPOINT: ELIMINAR CATEGORÍA (SOFT DELETE)
# ============================================
@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    🗑️ ELIMINAR CATEGORÍA (Soft Delete)

    Marca la categoría como inactiva en lugar de eliminarla.
    Esto preserva la integridad referencial.

    Args:
        category_id: ID de la categoría
        session: Sesión de BD asíncrona
        current_user: Usuario autenticado

    Returns:
        dict: Confirmación de eliminación

    Raises:
        HTTPException 404: Si no se encuentra o no pertenece a la empresa
    """
    # Buscar categoría
    result = await session.execute(
        select(Category).where(
            Category.id == category_id,
            Category.company_id == current_user.company_id
        )
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    # Soft delete: marcar como inactiva
    category.is_active = False

    # Guardar cambios
    await session.commit()

    return {"message": f"Categoría '{category.name}' eliminada correctamente"}
