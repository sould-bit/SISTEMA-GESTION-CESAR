"""
🛒 ROUTER DE PRODUCTOS - API REST Optimizada

Endpoints actualizados para usar arquitectura híbrida:
- GET /products/ → ProductListRead (schema ligero)
- GET /products/{id} → ProductDetailRead (schema completo)
- POST/PUT/DELETE → ProductDetailRead con invalidación de caché

Evita error MissingGreenlet usando schemas apropiados.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from decimal import Decimal

from app.database import get_session
from app.models.user import User
from app.dependencies import get_current_user
from app.core.permissions import require_permission
from app.schemas.products import (
    ProductListRead, 
    ProductDetailRead, 
    ProductCreate, 
    ProductUpdate
)
from app.services import ProductService


router = APIRouter(prefix="/products", tags=["products"])


def get_product_service(session: AsyncSession = Depends(get_session)) -> ProductService:
    """🛠️ Inyección de dependencia: ProductService"""
    return ProductService(session)


# ============================================
# 📋 LISTADO OPTIMIZADO
# ============================================
@router.get("/", response_model=List[ProductListRead])
@require_permission("products.read")
async def get_products(
    category_id: Optional[int] = Query(None, description="Filtrar por categoría"),
    search: Optional[str] = Query(None, description="Buscar por nombre"),
    active_only: bool = Query(True, description="Solo productos activos"),
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    📋 LISTAR PRODUCTOS CON FILTROS
    
    Devuelve ProductListRead (schema ligero) con category_name.
    Evita MissingGreenlet al no cargar relaciones completas.
    
    Returns:
        List[ProductListRead]: Productos con category_name
    """
    return await product_service.get_products_for_list(
        company_id=current_user.company_id,
        category_id=category_id,
        search=search,
        active_only=active_only
    )


# ============================================
# ➕ CREAR PRODUCTO
# ============================================
@router.post("/", response_model=ProductDetailRead, status_code=status.HTTP_201_CREATED)
@require_permission("products.create")
async def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    ➕ CREAR NUEVO PRODUCTO
    
    Crea producto con validaciones y devuelve ProductDetailRead.
    Invalida caché automáticamente.
    """
    return await product_service.create_product(product, current_user.company_id)


# ============================================
# 🔍 DETALLE DE PRODUCTO
# ============================================
@router.get("/{product_id}", response_model=ProductDetailRead)
@require_permission("products.read")
async def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    🔍 OBTENER DETALLE DE PRODUCTO
    
    Devuelve ProductDetailRead con relación Category completa.
    Usa selectinload para cargar la relación de forma segura.
    """
    return await product_service.get_product_detail(
        product_id, 
        current_user.company_id
    )


# ============================================
# ✏️ ACTUALIZAR PRODUCTO
# ============================================
@router.put("/{product_id}", response_model=ProductDetailRead)
@require_permission("products.update")
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    ✏️ ACTUALIZAR PRODUCTO
    
    Actualiza producto y devuelve ProductDetailRead.
    Invalida caché automáticamente.
    """
    return await product_service.update_product(
        product_id, 
        product_update, 
        current_user.company_id
    )


# ============================================
# 🗑️ ELIMINAR PRODUCTO
# ============================================
@router.delete("/{product_id}")
@require_permission("products.delete")
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    🗑️ ELIMINAR PRODUCTO (SOFT DELETE)
    
    Marca como inactivo e invalida caché.
    """
    return await product_service.delete_product(
        product_id, 
        current_user.company_id
    )


# ============================================
# 📉 PRODUCTOS CON STOCK BAJO
# ============================================
@router.get("/inventory/low-stock", response_model=List[ProductListRead])
@require_permission("products.read")
async def get_low_stock_products(
    threshold: Decimal = Query(Decimal('10'), description="Umbral de stock bajo"),
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    📉 PRODUCTOS CON STOCK BAJO
    
    Lista productos con stock bajo usando ProductListRead.
    """
    return await product_service.get_low_stock_products(
        current_user.company_id, 
        threshold
    )


# ============================================
# 🔍 BUSCAR PRODUCTOS
# ============================================
@router.get("/search/", response_model=List[ProductListRead])
@require_permission("products.read")
async def search_products(
    q: str = Query(..., min_length=1, description="Texto de búsqueda"),
    limit: int = Query(50, ge=1, le=100, description="Máximo resultados"),
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    🔍 BUSCAR PRODUCTOS POR NOMBRE
    
    Búsqueda case-insensitive usando ProductListRead.
    """
    return await product_service.get_products_for_list(
        company_id=current_user.company_id,
        search=q,
        active_only=True
    )