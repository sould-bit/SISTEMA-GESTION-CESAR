"""
Address Service - Refactored to Instance Pattern
=================================================
Alineado con el patrón dominante del proyecto.
"""
from typing import Optional, List
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.customer import Customer
from app.models.customer_address import CustomerAddress


class AddressService:
    """
    Servicio de Direcciones - Pattern Instance-based
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def add_address(
        self, 
        customer_id: int, 
        company_id: int,
        name: str, 
        address: str, 
        details: Optional[str] = None, 
        latitude: Optional[float] = None, 
        longitude: Optional[float] = None,
        is_default: bool = False
    ) -> Optional[CustomerAddress]:
        """Agrega una dirección a un cliente existente."""
        
        # 1. Validar que el cliente pertenezca a la empresa
        customer_query = select(Customer).where(
            Customer.id == customer_id, 
            Customer.company_id == company_id
        )
        result = await self.db.execute(customer_query)
        if not result.scalar_one_or_none():
            return None

        # 2. Si es default, quitar default a las otras
        if is_default:
            await self._clear_default_address(customer_id)

        new_address = CustomerAddress(
            customer_id=customer_id,
            name=name,
            address=address,
            details=details,
            latitude=latitude,
            longitude=longitude,
            is_default=is_default
        )
        self.db.add(new_address)
        await self.db.commit()
        await self.db.refresh(new_address)
        return new_address

    async def get_customer_addresses(
        self, 
        customer_id: int, 
        company_id: int
    ) -> List[CustomerAddress]:
        """Obtiene todas las direcciones de un cliente."""
        query = select(CustomerAddress).join(Customer).where(
            CustomerAddress.customer_id == customer_id,
            Customer.company_id == company_id
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _clear_default_address(self, customer_id: int):
        """Quita la marca de default a todas las direcciones del cliente."""
        query = select(CustomerAddress).where(
            CustomerAddress.customer_id == customer_id,
            CustomerAddress.is_default == True
        )
        result = await self.db.execute(query)
        defaults = result.scalars().all()
        for addr in defaults:
            addr.is_default = False
        # No commit here, let the caller commit
