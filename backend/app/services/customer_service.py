from typing import Optional, List
from sqlmodel import select, col
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer

class CustomerService:
    @staticmethod
    async def get_by_phone(db: AsyncSession, company_id: int, phone: str) -> Optional[Customer]:
        """Busca un cliente por teléfono dentro de una compañía (Multi-tenant)."""
        query = select(Customer).where(
            Customer.company_id == company_id,
            Customer.phone == phone
        ).options(selectinload(Customer.addresses))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_customer(db: AsyncSession, company_id: int, phone: str, full_name: str, email: Optional[str] = None, notes: Optional[str] = None) -> Customer:
        """Crea un nuevo cliente."""
        # Verificar duplicados
        existing = await CustomerService.get_by_phone(db, company_id, phone)
        if existing:
            return existing # Retorna el existente si ya está (Idempotencia)

        customer = Customer(
            company_id=company_id,
            phone=phone,
            full_name=full_name,
            email=email,
            notes=notes
        )
        db.add(customer)
        await db.commit()
        
        # Reload with relationship to satisfy Pydantic response model
        query = select(Customer).where(Customer.id == customer.id).options(selectinload(Customer.addresses))
        result = await db.execute(query)
        refreshed_customer = result.scalar_one()
        return refreshed_customer

    @staticmethod
    async def update_customer(db: AsyncSession, customer_id: int, company_id: int, **kwargs) -> Optional[Customer]:
        """Actualiza datos del cliente."""
        query = select(Customer).where(
            Customer.id == customer_id, 
            Customer.company_id == company_id
        )
        result = await db.execute(query)
        customer = result.scalar_one_or_none()
        
        if not customer:
            return None
            
        for key, value in kwargs.items():
            if hasattr(customer, key) and value is not None:
                setattr(customer, key, value)
                
        await db.commit()
        await db.refresh(customer)
        return customer
