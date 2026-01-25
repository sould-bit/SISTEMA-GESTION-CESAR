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
from sqlalchemy.exc import IntegrityError
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
from app.services.beverage_service import BeverageService
from pydantic import BaseModel


router = APIRouter(prefix="/products", tags=["products"])


# Schema for Beverage creation
class BeverageCreate(BaseModel):
    name: str
    cost: Decimal
    sale_price: Decimal
    initial_stock: Decimal = Decimal("0")
    unit: str = "unidad"
    sku: Optional[str] = None
    supplier: Optional[str] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None # For inline creation
    description: Optional[str] = None


def get_product_service(session: AsyncSession = Depends(get_session)) -> ProductService:
    """🛠️ Inyección de dependencia: ProductService"""
    return ProductService(session)


def get_beverage_service(session: AsyncSession = Depends(get_session)) -> BeverageService:
    """🛠️ Inyección de dependencia: BeverageService"""
    return BeverageService(session)


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


# ============================================
# 🍺 CREAR BEBIDA / MERCADERÍA (ATOMIC 1:1)
# ============================================
@router.post("/beverage", status_code=status.HTTP_201_CREATED)
@require_permission("products.create")
async def create_beverage(
    payload: BeverageCreate,
    branch_id: int = Query(..., description="Branch ID para stock inicial"),
    current_user: User = Depends(get_current_user),
    beverage_service: BeverageService = Depends(get_beverage_service)
):
    """
    🍺 CREAR PRODUCTO TIPO BEBIDA/MERCADERÍA
    
    Implementa el patrón "Puente 1:1":
    - Crea Ingredient (MERCHANDISE) para inventario
    - Crea Product para ventas/POS  
    - Crea Recipe 1:1 para unificar lógica de deducción de stock
    
    Todo en una sola transacción atómica.
    
    Args:
        payload: Datos de la bebida (nombre, costo, precio venta, stock inicial)
        branch_id: Sucursal donde se registrará el stock inicial
        
    Returns:
        dict con product, ingredient, recipe creados
    """
    try:
        return await beverage_service.create_beverage(
            name=payload.name,
            cost=payload.cost,
            sale_price=payload.sale_price,
            initial_stock=payload.initial_stock,
            unit=payload.unit,
            branch_id=branch_id,
            company_id=current_user.company_id,
            user_id=current_user.id,
            image_url=payload.image_url,
            category_id=payload.category_id,
            category_name=payload.category_name,
            description=payload.description
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una bebida con el nombre '{payload.name}'"
        )


# Schema for Beverage update
class BeverageUpdate(BaseModel):
    name: Optional[str] = None
    cost: Optional[Decimal] = None
    sale_price: Optional[Decimal] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    sku: Optional[str] = None
    additional_stock: Optional[Decimal] = None
    supplier: Optional[str] = None


# ============================================
# ✏️ ACTUALIZAR BEBIDA / MERCADERÍA (ATOMIC 1:1)
# ============================================
@router.put("/beverage/{product_id}")
@require_permission("products.update")
async def update_beverage(
    product_id: int,
    payload: BeverageUpdate,
    branch_id: Optional[int] = Query(None, description="Branch ID para stock adicional"),
    current_user: User = Depends(get_current_user),
    beverage_service: BeverageService = Depends(get_beverage_service)
):
    """
    ✏️ ACTUALIZAR PRODUCTO TIPO BEBIDA/MERCADERÍA
    
    Actualiza Product + Ingredient vinculado (cascada 1:1).
    Opcionalmente agrega stock adicional si se proporciona.
    
    Args:
        product_id: ID del producto a actualizar
        payload: Campos a actualizar
        branch_id: Requerido si se agrega stock adicional
        
    Returns:
        dict con product, ingredient actualizados
    """
    try:
        return await beverage_service.update_beverage(
            product_id=product_id,
            name=payload.name,
            cost=payload.cost,
            sale_price=payload.sale_price,
            image_url=payload.image_url,
            category_id=payload.category_id,
            sku=payload.sku,
            additional_stock=payload.additional_stock,
            branch_id=branch_id,
            user_id=current_user.id,
            supplier=payload.supplier
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error de integridad al actualizar"
        )


# ============================================
# 🗑️ ELIMINAR BEBIDA / MERCADERÍA (SOFT DELETE CASCADE)
# ============================================
@router.delete("/beverage/{product_id}")
@require_permission("products.delete")
async def delete_beverage(
    product_id: int,
    current_user: User = Depends(get_current_user),
    beverage_service: BeverageService = Depends(get_beverage_service)
):
    """
    🗑️ ELIMINAR PRODUCTO TIPO BEBIDA/MERCADERÍA
    
    Soft-delete con cascada:
    - Product.is_active = False
    - Ingredient.is_active = False
    - Batches.is_active = False
    - Recipe.is_active = False
    
    Args:
        product_id: ID del producto a eliminar
        
    Returns:
        dict con mensaje de confirmación
    """
    try:
        return await beverage_service.delete_beverage(product_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )