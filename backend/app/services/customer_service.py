"""
Customer Service - Refactored to Instance Pattern
=================================================
Alineado con el patrón dominante del proyecto (ProductService, OrderService).
"""
from typing import Optional, List
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.models.customer import Customer


# --- Pydantic Schemas (para respuestas limpias) ---

class CustomerRead(BaseModel):
    id: int
    company_id: int
    phone: str
    full_name: str
    email: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True


class CustomerService:
    """
    Servicio de Clientes - Pattern Instance-based
    
    Gestiona operaciones CRUD para clientes del CRM.
    Inyección de dependencias via constructor para testing.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_phone(self, company_id: int, phone: str) -> Optional[Customer]:
        """Busca un cliente por teléfono dentro de una compañía (Multi-tenant)."""
        query = select(Customer).where(
            Customer.company_id == company_id,
            Customer.phone == phone
        ).options(selectinload(Customer.addresses))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_id(self, customer_id: int, company_id: int) -> Optional[Customer]:
        """Obtiene un cliente por ID."""
        query = select(Customer).where(
            Customer.id == customer_id,
            Customer.company_id == company_id
        ).options(selectinload(Customer.addresses))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_customer(
        self, 
        company_id: int, 
        phone: str, 
        full_name: str, 
        email: Optional[str] = None, 
        notes: Optional[str] = None
    ) -> Customer:
        """
        Crea un nuevo cliente.
        
        Si ya existe (mismo phone + company), retorna el existente (idempotencia).
        """
        # Verificar duplicados
        existing = await self.get_by_phone(company_id, phone)
        if existing:
            return existing

        customer = Customer(
            company_id=company_id,
            phone=phone,
            full_name=full_name,
            email=email,
            notes=notes
        )
        self.db.add(customer)
        await self.db.commit()
        
        # Reload con relaciones usando refresh (evita f405)
        await self.db.refresh(customer, attribute_names=["addresses"])
        return customer

    async def update_customer(
        self, 
        customer_id: int, 
        company_id: int, 
        **kwargs
    ) -> Optional[Customer]:
        """Actualiza datos del cliente."""
        customer = await self.get_by_id(customer_id, company_id)
        
        if not customer:
            return None
            
        for key, value in kwargs.items():
            if hasattr(customer, key) and value is not None:
                setattr(customer, key, value)
                
        await self.db.commit()
        await self.db.refresh(customer)
        return customer
    
    async def search_customers(
        self, 
        company_id: int, 
        query_str: Optional[str] = None,
        limit: int = 20
    ) -> List[Customer]:
        """Busca clientes por nombre o teléfono."""
        query = select(Customer).where(Customer.company_id == company_id)
        
        if query_str:
            search_pattern = f"%{query_str}%"
            query = query.where(
                (Customer.full_name.ilike(search_pattern)) |
                (Customer.phone.ilike(search_pattern))
            )
        
        query = query.limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
