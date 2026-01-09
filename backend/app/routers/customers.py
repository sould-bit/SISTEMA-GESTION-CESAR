from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, Field

from app.database import get_session
from app.auth_deps import get_current_user
from app.models.user import User
from app.services.customer_service import CustomerService
from app.services.address_service import AddressService
from app.models.customer import Customer
from app.models.customer_address import CustomerAddress
from app.core.permissions import require_permission
from app.services.company_service import CompanyService
from app.utils.security import create_access_token
from datetime import timedelta
from app.config import settings

router = APIRouter(prefix="/customers", tags=["CRM"])

# --- Schemas internos para Requests/Responses ---

class CustomerCreate(SQLModel):
    phone: str
    full_name: str
    email: Optional[str] = None
    notes: Optional[str] = None

class CustomerCreatePublic(SQLModel):
    phone: str
    full_name: str
    email: Optional[str] = None
    company_slug: str

class CustomerLogin(SQLModel):
    phone: str
    company_slug: str

class CustomerRead(SQLModel):
    id: int
    phone: str
    full_name: str
    addresses: List[CustomerAddress] = []

class Token(SQLModel):
    access_token: str
    token_type: str
    customer: CustomerRead

class AddressCreate(SQLModel):
    name: str = Field(description="Alias (ej. Casa)")
    address: str
    details: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool = False

# --- Endpoints ---

@router.get("/search", response_model=Optional[CustomerRead])
async def search_customer(
    phone: str = Query(..., min_length=7),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Busca un cliente por teléfono para el POS/Call Center.
    Si no existe, retorna null (200 OK con body null) o 404 según preferencia. 
    Aquí retornaremos null si no existe para facilitar al frontend.
    """
    customer = await CustomerService.get_by_phone(db, current_user.company_id, phone)
    if not customer:
        return None # Frontend debe manejar esto como "Prompt to create"
        
    return customer


@router.post("/", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_in: CustomerCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Registra un nuevo cliente.
    """
    # Lógica de servicio
    customer = await CustomerService.create_customer(
        db, 
        current_user.company_id, 
        customer_in.phone, 
        customer_in.full_name, 
        customer_in.email, 
        customer_in.notes
    )
    return customer


@router.get("/{customer_id}/addresses", response_model=List[CustomerAddress])
async def get_addresses(
    customer_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Obtiene todas las direcciones de un cliente."""
    return await AddressService.get_customer_addresses(db, customer_id, current_user.company_id)


@router.post("/{customer_id}/addresses", response_model=CustomerAddress)
async def add_address(
    customer_id: int,
    address_in: AddressCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Agrega una nueva dirección a un cliente."""
    address = await AddressService.add_address(
        db,
        customer_id,
        current_user.company_id,
        name=address_in.name,
        address=address_in.address,
        details=address_in.details,
        latitude=address_in.latitude,
        longitude=address_in.longitude,
        is_default=address_in.is_default
    )
    
    if not address:
        raise HTTPException(status_code=404, detail="Cliente no encontrado o no pertenece a su empresa")
        
    return address

# --- Public Endpoints (PWA) ---

@router.post("/public/register", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def register_public(
    customer_in: CustomerCreatePublic,
    db: AsyncSession = Depends(get_session)
):
    """
    Registro público desde la PWA.
    Requiere el slug del negocio para asociar el cliente a la empresa correcta.
    """
    # 1. Resolver Company ID
    company = await CompanyService.get_by_slug(db, customer_in.company_slug)
    if not company:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    # 2. Crear Cliente
    customer = await CustomerService.create_customer(
        db, 
        company.id, 
        customer_in.phone, 
        customer_in.full_name, 
        customer_in.email,
        notes="Registro desde App Móvil"
    )
    return customer


@router.post("/auth/login", response_model=Token)
async def login_public(
    login_data: CustomerLogin,
    db: AsyncSession = Depends(get_session)
):
    """
    Login simplificado por teléfono para clientes.
    Genera un token JWT con scope de cliente.
    """
    # 1. Resolver Company
    company = await CompanyService.get_by_slug(db, login_data.company_slug)
    if not company:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    # 2. Buscar Cliente
    customer = await CustomerService.get_by_phone(db, company.id, login_data.phone)
    if not customer:
        raise HTTPException(status_code=401, detail="Número no registrado")

    # 3. Generar Token (Simulado por ahora, podríamos validar OTP aquí)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Payload custom para clientes
    token_payload = {
        "sub": f"customer:{customer.id}:{company.id}", # Subject especial
        "type": "customer",
        "company_id": company.id,
        "customer_id": customer.id
    }
    
    access_token = create_access_token(
        data=token_payload, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "customer": customer
    }
