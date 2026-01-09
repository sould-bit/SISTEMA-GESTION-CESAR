"""
Storefront Router (PWA)
========================
Endpoints públicos y de cliente para la aplicación móvil.
Separado del backoffice para seguridad B2B2C.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from pydantic import BaseModel
from decimal import Decimal

from app.database import get_session
from app.auth_deps_customer import get_current_customer, get_optional_customer, CustomerContext
from app.models.company import Company
from app.models.branch import Branch
from app.models.product import Product
from app.models.category import Category
from app.models.inventory import Inventory
from app.models.customer_address import CustomerAddress
from app.models.order import Order
from app.services.customer_service import CustomerService
from app.services.address_service import AddressService
from app.services.order_service import OrderService

router = APIRouter(prefix="/storefront", tags=["Storefront (PWA)"])


# --- Schemas ---

class BranchPublic(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None

class ProductPublic(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    image_url: Optional[str] = None
    category_name: Optional[str] = None
    available: bool = True

class MenuResponse(BaseModel):
    branch_id: int
    branch_name: str
    categories: List[dict]

class AddressCreate(BaseModel):
    name: str
    address: str
    details: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool = False

class AddressRead(BaseModel):
    id: int
    name: str
    address: str
    details: Optional[str] = None
    is_default: bool

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    notes: Optional[str] = None

class OrderCreate(BaseModel):
    branch_id: int
    delivery_address: str
    delivery_notes: Optional[str] = None
    items: List[OrderItemCreate]

class OrderRead(BaseModel):
    id: int
    order_number: str
    status: str
    total: Decimal
    delivery_address: str
    created_at: str


# --- Public Endpoints (No Auth) ---

@router.get("/{slug}/branches", response_model=List[BranchPublic])
async def list_branches(
    slug: str,
    db: AsyncSession = Depends(get_session)
):
    """Lista las sucursales activas de una empresa."""
    # Buscar empresa por slug
    result = await db.execute(
        select(Company).where(Company.slug == slug, Company.is_active == True)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Obtener sucursales
    result = await db.execute(
        select(Branch).where(Branch.company_id == company.id, Branch.is_active == True)
    )
    branches = result.scalars().all()
    
    return [BranchPublic(
        id=b.id,
        name=b.name,
        address=b.address,
        phone=b.phone
    ) for b in branches]


@router.get("/{slug}/branches/{branch_id}/menu", response_model=MenuResponse)
async def get_menu(
    slug: str,
    branch_id: int,
    db: AsyncSession = Depends(get_session)
):
    """Obtiene el menú de una sucursal con disponibilidad en tiempo real."""
    # Validar empresa
    result = await db.execute(
        select(Company).where(Company.slug == slug, Company.is_active == True)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Validar sucursal
    result = await db.execute(
        select(Branch).where(
            Branch.id == branch_id,
            Branch.company_id == company.id,
            Branch.is_active == True
        )
    )
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    
    # Obtener productos con categorías
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.company_id == company.id, Product.is_active == True)
    )
    products = result.scalars().all()
    
    # Obtener inventario de la sucursal
    result = await db.execute(
        select(Inventory).where(Inventory.branch_id == branch_id)
    )
    inventory_map = {inv.product_id: inv.stock for inv in result.scalars().all()}
    
    # Agrupar por categoría
    categories_dict = {}
    for product in products:
        cat_name = product.category.name if product.category else "Otros"
        if cat_name not in categories_dict:
            categories_dict[cat_name] = []
        
        stock = inventory_map.get(product.id, Decimal("0"))
        categories_dict[cat_name].append({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "image_url": product.image_url,
            "available": stock > 0
        })
    
    return MenuResponse(
        branch_id=branch.id,
        branch_name=branch.name,
        categories=[
            {"name": name, "products": prods}
            for name, prods in categories_dict.items()
        ]
    )


# --- Customer Endpoints (Require Customer Token) ---

@router.get("/me/addresses", response_model=List[AddressRead])
async def list_my_addresses(
    ctx: CustomerContext = Depends(get_current_customer),
    db: AsyncSession = Depends(get_session)
):
    """Lista las direcciones del cliente autenticado."""
    addresses = await AddressService.get_customer_addresses(
        db, ctx.customer_id, ctx.company_id
    )
    return [AddressRead(
        id=a.id,
        name=a.name,
        address=a.address,
        details=a.details,
        is_default=a.is_default
    ) for a in addresses]


@router.post("/me/addresses", response_model=AddressRead, status_code=status.HTTP_201_CREATED)
async def add_my_address(
    address_in: AddressCreate,
    ctx: CustomerContext = Depends(get_current_customer),
    db: AsyncSession = Depends(get_session)
):
    """Agrega una dirección para el cliente autenticado."""
    address = await AddressService.add_address(
        db,
        customer_id=ctx.customer_id,
        company_id=ctx.company_id,
        name=address_in.name,
        address=address_in.address,
        details=address_in.details,
        latitude=address_in.latitude,
        longitude=address_in.longitude,
        is_default=address_in.is_default
    )
    
    if not address:
        raise HTTPException(status_code=400, detail="No se pudo crear la dirección")
    
    return AddressRead(
        id=address.id,
        name=address.name,
        address=address.address,
        details=address.details,
        is_default=address.is_default
    )


@router.post("/me/orders", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_my_order(
    order_in: OrderCreate,
    ctx: CustomerContext = Depends(get_current_customer),
    db: AsyncSession = Depends(get_session)
):
    """Crea un pedido delivery para el cliente autenticado."""
    from app.schemas.order import OrderCreate as OrderCreateSchema, OrderItemCreate as OrderItemSchema
    
    # Construir el schema de orden
    order_data = OrderCreateSchema(
        branch_id=order_in.branch_id,
        customer_id=ctx.customer_id,
        delivery_type="delivery",
        delivery_address=order_in.delivery_address,
        delivery_notes=order_in.delivery_notes,
        delivery_fee=Decimal("5000"),  # TODO: Calcular dinámicamente
        items=[OrderItemSchema(
            product_id=item.product_id,
            quantity=item.quantity,
            notes=item.notes
        ) for item in order_in.items]
    )
    
    order_service = OrderService(db)
    
    try:
        # For customer self-service orders, user_id is None (no staff member)
        order = await order_service.create_order(order_data, ctx.company_id, user_id=None)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return OrderRead(
        id=order.id,
        order_number=order.order_number,
        status=order.status.value if hasattr(order.status, 'value') else str(order.status),
        total=order.total,
        delivery_address=order.delivery_address or "",
        created_at=order.created_at.isoformat()
    )


@router.get("/me/orders", response_model=List[OrderRead])
async def list_my_orders(
    ctx: CustomerContext = Depends(get_current_customer),
    db: AsyncSession = Depends(get_session)
):
    """Lista el historial de pedidos del cliente."""
    result = await db.execute(
        select(Order)
        .where(Order.customer_id == ctx.customer_id)
        .order_by(Order.created_at.desc())
        .limit(20)
    )
    orders = result.scalars().all()
    
    return [OrderRead(
        id=o.id,
        order_number=o.order_number,
        status=o.status.value if hasattr(o.status, 'value') else str(o.status),
        total=o.total,
        delivery_address=o.delivery_address or "",
        created_at=o.created_at.isoformat()
    ) for o in orders]
