"""
📍 BRANCH SERVICE - Servicio de Gestión de Sucursales

Operaciones CRUD para sucursales con validaciones de negocio.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from logging import getLogger

from app.models.branch import Branch
from app.models.user import User
from app.schemas.branch import BranchCreate, BranchUpdate, BranchResponse

logger = getLogger(__name__)


class BranchService:
    """
    Servicio para gestión de sucursales.
    
    Responsabilidades:
    - CRUD de sucursales
    - Validación de códigos únicos por empresa
    - Control de sucursal principal
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def list_branches(
        self,
        company_id: int,
        include_inactive: bool = False,
        page: int = 1,
        size: int = 50
    ) -> tuple[List[Branch], int]:
        """
        Lista todas las sucursales de una empresa.
        
        Args:
            company_id: ID de la empresa
            include_inactive: Si incluir sucursales inactivas
            page: Página actual
            size: Tamaño de página
            
        Returns:
            Tuple de (lista de sucursales, total)
        """
        # Query base
        conditions = [Branch.company_id == company_id]
        if not include_inactive:
            conditions.append(Branch.is_active == True)
        
        # Contar total
        count_stmt = select(func.count(Branch.id)).where(and_(*conditions))
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # Obtener items paginados
        stmt = (
            select(Branch)
            .where(and_(*conditions))
            .order_by(Branch.is_main.desc(), Branch.name)
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.session.execute(stmt)
        branches = list(result.scalars().all())
        
        return branches, total
    
    async def get_branch(self, branch_id: int, company_id: int) -> Optional[Branch]:
        """
        Obtiene una sucursal por ID.
        
        Valida que pertenezca a la empresa del usuario.
        """
        stmt = select(Branch).where(
            Branch.id == branch_id,
            Branch.company_id == company_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_branch_or_404(self, branch_id: int, company_id: int) -> Branch:
        """Obtiene sucursal o lanza 404."""
        branch = await self.get_branch(branch_id, company_id)
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sucursal con ID {branch_id} no encontrada"
            )
        return branch
    
    async def create_branch(self, company_id: int, data: BranchCreate) -> Branch:
        """
        Crea una nueva sucursal.
        
        Validaciones:
        - El código debe ser único por empresa
        - Si es la primera sucursal, se marca como principal
        - Si se marca como principal, desmarca las otras
        """
        # Verificar código único
        existing = await self._get_by_code(company_id, data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una sucursal con el código '{data.code}'"
            )
        
        # Verificar si es la primera sucursal
        count_stmt = select(func.count(Branch.id)).where(Branch.company_id == company_id)
        count_result = await self.session.execute(count_stmt)
        is_first = (count_result.scalar() or 0) == 0
        
        # Si es la primera, debe ser principal
        is_main = data.is_main or is_first
        
        # Si se marca como principal, desmarcar otras
        if is_main:
            await self._unset_main_branch(company_id)
        
        # Crear sucursal
        branch = Branch(
            company_id=company_id,
            name=data.name,
            code=data.code.upper(),  # Normalizar a mayúsculas
            address=data.address,
            phone=data.phone,
            is_main=is_main,
            is_active=True
        )
        
        self.session.add(branch)
        await self.session.commit()
        await self.session.refresh(branch)
        
        logger.info(f"✅ Sucursal creada: {branch.name} ({branch.code}) - Company {company_id}")
        return branch
    
    async def update_branch(
        self,
        branch_id: int,
        company_id: int,
        data: BranchUpdate
    ) -> Branch:
        """
        Actualiza una sucursal.
        
        Validaciones:
        - Si cambia el código, verificar unicidad
        - Si se marca como principal, desmarcar otras
        """
        branch = await self.get_branch_or_404(branch_id, company_id)
        
        # Validar código único si cambia
        if data.code and data.code != branch.code:
            existing = await self._get_by_code(company_id, data.code)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe una sucursal con el código '{data.code}'"
                )
        
        # Si se marca como principal, desmarcar otras
        if data.is_main and not branch.is_main:
            await self._unset_main_branch(company_id)
        
        # Aplicar cambios
        update_data = data.model_dump(exclude_unset=True)
        if 'code' in update_data:
            update_data['code'] = update_data['code'].upper()
        
        for field, value in update_data.items():
            setattr(branch, field, value)
        
        branch.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(branch)
        
        logger.info(f"📝 Sucursal actualizada: {branch.name} ({branch.code})")
        return branch
    
    async def delete_branch(self, branch_id: int, company_id: int) -> bool:
        """
        Elimina (soft delete) una sucursal.
        
        Validaciones:
        - No se puede eliminar la sucursal principal si hay otras
        - No se puede eliminar si tiene usuarios asignados activos
        """
        branch = await self.get_branch_or_404(branch_id, company_id)
        
        # Verificar si es la única sucursal principal
        if branch.is_main:
            other_active = await self.session.execute(
                select(Branch).where(
                    Branch.company_id == company_id,
                    Branch.id != branch_id,
                    Branch.is_active == True
                )
            )
            if other_active.scalars().all():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No puedes eliminar la sucursal principal mientras existan otras activas. Marca otra como principal primero."
                )
        
        # Verificar usuarios asignados
        users_stmt = select(func.count(User.id)).where(
            User.branch_id == branch_id,
            User.is_active == True
        )
        users_result = await self.session.execute(users_stmt)
        user_count = users_result.scalar() or 0
        
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No puedes eliminar esta sucursal porque tiene {user_count} usuarios asignados. Reasígnalos primero."
            )
        
        # Soft delete
        branch.is_active = False
        branch.updated_at = datetime.utcnow()
        
        await self.session.commit()
        
        logger.info(f"🗑️ Sucursal desactivada: {branch.name} ({branch.code})")
        return True
    
    async def get_user_count(self, branch_id: int) -> int:
        """Obtiene cantidad de usuarios en una sucursal."""
        stmt = select(func.count(User.id)).where(
            User.branch_id == branch_id,
            User.is_active == True
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def _get_by_code(self, company_id: int, code: str) -> Optional[Branch]:
        """Busca sucursal por código (case insensitive)."""
        stmt = select(Branch).where(
            Branch.company_id == company_id,
            func.upper(Branch.code) == code.upper()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _unset_main_branch(self, company_id: int) -> None:
        """Desmarca todas las sucursales como principal."""
        stmt = select(Branch).where(
            Branch.company_id == company_id,
            Branch.is_main == True
        )
        result = await self.session.execute(stmt)
        for branch in result.scalars().all():
            branch.is_main = False
            branch.updated_at = datetime.utcnow()
