"""
Servicio de Gestión de Categorías de Permisos

Este servicio maneja:
1. CRUD de categorías dinámicas de permisos
2. Validación de categorías antes de eliminar
3. Seed de categorías del sistema

NOTA: Este servicio es diferente de category_service.py (categorías de productos)
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models import PermissionCategory, Permission


class PermissionCategoryService:
    """Servicio para gestión de categorías de permisos."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_category(
        self,
        company_id: int,
        name: str,
        code: str,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None
    ) -> PermissionCategory:
        """Crea una nueva categoría de permisos."""
        # Verificar que el código no exista
        result = await self.session.execute(
            select(PermissionCategory)
            .where(and_(
                PermissionCategory.company_id == company_id,
                PermissionCategory.code == code
            ))
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise ValueError(f"Ya existe una categoría con el código '{code}'")
        
        category = PermissionCategory(
            company_id=company_id,
            name=name,
            code=code,
            description=description,
            icon=icon,
            color=color,
            is_system=False,
            is_active=True
        )
        
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        
        return category
    
    async def update_category(
        self,
        category_id: UUID,
        company_id: int,
        **kwargs
    ) -> PermissionCategory:
        """Actualiza una categoría existente."""
        result = await self.session.execute(
            select(PermissionCategory)
            .where(and_(
                PermissionCategory.id == category_id,
                PermissionCategory.company_id == company_id
            ))
        )
        category = result.scalar_one_or_none()
        
        if not category:
            raise ValueError("Categoría no encontrada")
        
        if category.is_system:
            raise ValueError("No se pueden modificar categorías del sistema")
        
        allowed_fields = ['name', 'description', 'icon', 'color', 'is_active']
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(category, field, value)
        
        category.updated_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        await self.session.refresh(category)
        
        return category
    
    async def delete_category(
        self,
        category_id: UUID,
        company_id: int
    ) -> bool:
        """Elimina (soft delete) una categoría personalizada."""
        result = await self.session.execute(
            select(PermissionCategory)
            .where(and_(
                PermissionCategory.id == category_id,
                PermissionCategory.company_id == company_id
            ))
        )
        category = result.scalar_one_or_none()
        
        if not category:
            return False
        
        if category.is_system:
            raise ValueError("No se pueden eliminar categorías del sistema")
        
        # Verificar que no tenga permisos activos
        result = await self.session.execute(
            select(func.count(Permission.id))
            .where(and_(
                Permission.category_id == category_id,
                Permission.is_active == True
            ))
        )
        permission_count = result.scalar()
        
        if permission_count > 0:
            raise ValueError(
                f"No se puede eliminar la categoría. Tiene {permission_count} permiso(s) activo(s)"
            )
        
        category.is_active = False
        category.updated_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        
        return True
    
    async def list_categories(
        self,
        company_id: int,
        include_system: bool = True,
        only_active: bool = True
    ) -> List[PermissionCategory]:
        """Lista todas las categorías de una empresa."""
        conditions = [PermissionCategory.company_id == company_id]
        
        if not include_system:
            conditions.append(PermissionCategory.is_system == False)
        
        if only_active:
            conditions.append(PermissionCategory.is_active == True)
        
        result = await self.session.execute(
            select(PermissionCategory)
            .where(and_(*conditions))
            .order_by(PermissionCategory.is_system.desc(), PermissionCategory.name)
        )
        
        return list(result.scalars().all())
