"""
Company Service - Refactored to Instance Pattern
=================================================
Alineado con el patrón dominante del proyecto.
"""
from typing import Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Company


class CompanyService:
    """
    Servicio de Compañías - Pattern Instance-based
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_slug(self, slug: str) -> Optional[Company]:
        """Obtiene una compañía por su slug."""
        query = select(Company).where(
            Company.slug == slug, 
            Company.is_active == True
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_id(self, company_id: int) -> Optional[Company]:
        """Obtiene una compañía por su ID."""
        query = select(Company).where(Company.id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
