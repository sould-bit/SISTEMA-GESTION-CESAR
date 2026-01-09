from typing import Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Company

class CompanyService:
    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Optional[Company]:
        """Obtiene una compañía por su slug."""
        query = select(Company).where(Company.slug == slug, Company.is_active == True)
        result = await db.execute(query)
        return result.scalar_one_or_none()
