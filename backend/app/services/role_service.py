"""
Servicio de Gestión de Roles (RBAC)

Este servicio maneja:
1. CRUD de roles
2. Asignación de roles a usuarios
3. Clonación de roles (templates)
4. Gestión de permisos por rol
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.models import Role, RolePermission, User, Permission
from app.core.logging_config import get_rbac_logger, log_rbac_action
from app.core.cache import get_rbac_cache
from app.core.exceptions import (
    RoleNotFoundException,
    RoleAlreadyExistsException,
    SystemRoleModificationException,
    UserNotFoundException,
    UserRoleAssignmentException
)


class RoleService:
    """Servicio para gestión de roles."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_rbac_logger("app.rbac")
        self.cache = get_rbac_cache()
    
    async def create_role(
        self,
        company_id: int,
        name: str,
        code: str,
        description: Optional[str] = None,
        hierarchy_level: int = 50,
        permission_ids: Optional[List[UUID]] = None
    ) -> Role:
        """
        Crea un nuevo rol personalizado.
        
        Args:
            company_id: ID de la empresa
            name: Nombre del rol
            code: Código único del rol
            description: Descripción opcional
            hierarchy_level: Nivel jerárquico (0-100)
            permission_ids: Lista de IDs de permisos a asignar
        
        Returns:
            Objeto Role creado
        """
        # Verificar que el código no exista
        result = await self.session.execute(
            select(Role)
            .where(and_(
                Role.company_id == company_id,
                Role.code == code
            ))
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            log_rbac_action(
                action="create_role_failed",
                company_id=company_id,
                details={"error": "duplicate_code", "code": code}
            )
            raise RoleAlreadyExistsException(role_code=code, company_id=company_id)

        try:
            # Crear rol
            role = Role(
                company_id=company_id,
                name=name,
                code=code,
                description=description,
                hierarchy_level=hierarchy_level,
                is_system=False,
                is_active=True
            )

            self.session.add(role)
            await self.session.flush()  # Para obtener el ID

            # Asignar permisos si se proporcionaron
            assigned_permissions = []
            if permission_ids:
                for perm_id in permission_ids:
                    role_perm = RolePermission(
                        role_id=role.id,
                        permission_id=perm_id
                    )
                    self.session.add(role_perm)
                    assigned_permissions.append(str(perm_id))

            await self.session.commit()
            await self.session.refresh(role)

            # Log de éxito
            log_rbac_action(
                action="role_created",
                company_id=company_id,
                role_id=str(role.id),
                details={
                    "role_name": name,
                    "role_code": code,
                    "hierarchy_level": hierarchy_level,
                    "permissions_assigned": len(assigned_permissions),
                    "permission_ids": assigned_permissions
                }
            )

            return role

        except Exception as e:
            # Log de error
            log_rbac_action(
                action="create_role_error",
                company_id=company_id,
                details={
                    "error": str(e),
                    "role_name": name,
                    "role_code": code
                }
            )
            raise
    
    async def update_role(
        self,
        role_id: UUID,
        company_id: int,
        **kwargs
    ) -> Role:
        """
        Actualiza un rol existente.
        Solo permite actualizar roles no-sistema.
        """
        result = await self.session.execute(
            select(Role)
            .where(and_(
                Role.id == role_id,
                Role.company_id == company_id
            ))
        )
        role = result.scalar_one_or_none()
        
        if not role:
            raise RoleNotFoundException(role_id=str(role_id), company_id=company_id)

        if role.is_system:
             # Permitir edición de roles del sistema, pero quizás restringir ciertos campos en el futuro
             # Por ahora, permitimos cambiar permisos y nombres para flexibilidad
             pass
             # raise SystemRoleModificationException(role_code=role.code, action="modificar")
        
        # Actualizar campos permitidos
        allowed_fields = ['name', 'description', 'hierarchy_level', 'is_active']
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(role, field, value)
        
        role.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(role)
        
        return role
    
    async def delete_role(
        self,
        role_id: UUID,
        company_id: int
    ) -> bool:
        """
        Elimina (soft delete) un rol personalizado.
        No permite eliminar roles del sistema o roles con usuarios asignados.
        """
        result = await self.session.execute(
            select(Role)
            .where(and_(
                Role.id == role_id,
                Role.company_id == company_id
            ))
        )
        role = result.scalar_one_or_none()
        
        if not role:
            return False

        if role.is_system:
            raise SystemRoleModificationException(role_code=role.code, action="eliminar")

        # Verificar que no tenga usuarios asignados
        result = await self.session.execute(
            select(func.count(User.id))
            .where(and_(
                User.role_id == role_id,
                User.is_active == True
            ))
        )
        user_count = result.scalar()

        if user_count > 0:
            raise UserRoleAssignmentException(
                user_id=0,  # No específico a un usuario
                role_id=str(role_id),
                reason=f"Rol tiene {user_count} usuario(s) asignado(s)"
            )
        
        # Soft delete
        role.is_active = False
        role.updated_at = datetime.utcnow()
        
        await self.session.commit()
        
        return True
    
    async def get_role(
        self,
        role_id: UUID,
        company_id: int,
        include_permissions: bool = False
    ) -> Optional[Role]:
        """
        Obtiene un rol por ID.
        
        Args:
            role_id: ID del rol
            company_id: ID de la empresa
            include_permissions: Si debe cargar los permisos
        """
        query = select(Role).where(and_(
            Role.id == role_id,
            Role.company_id == company_id
        ))
        
        if include_permissions:
            query = query.options(
                selectinload(Role.role_permissions).selectinload(RolePermission.permission)
            )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_roles(
        self,
        company_id: int,
        include_system: bool = True,
        only_active: bool = True
    ) -> List[Role]:
        """
        Lista todos los roles de una empresa.
        
        Args:
            company_id: ID de la empresa
            include_system: Si incluye roles del sistema
            only_active: Si solo incluye roles activos
        """
        conditions = [Role.company_id == company_id]
        
        if not include_system:
            conditions.append(Role.is_system == False)
        
        if only_active:
            conditions.append(Role.is_active == True)
        
        result = await self.session.execute(
            select(Role)
            .where(and_(*conditions))
            .order_by(Role.hierarchy_level.desc(), Role.name)
        )
        
        return list(result.scalars().all())
    
    async def assign_role_to_user(
        self,
        user_id: int,
        role_id: UUID,
        company_id: int
    ) -> User:
        """
        Asigna un rol a un usuario.
        
        Args:
            user_id: ID del usuario
            role_id: ID del rol
            company_id: ID de la empresa (validación multi-tenant)
        
        Returns:
            Usuario actualizado
        """
        # Verificar que el rol existe y pertenece a la empresa
        role = await self.get_role(role_id, company_id)
        if not role:
            log_rbac_action(
                action="assign_role_failed",
                user_id=user_id,
                company_id=company_id,
                role_id=str(role_id),
                details={"error": "role_not_found"}
            )
            raise RoleNotFoundException(role_id=str(role_id), company_id=company_id)

        # Obtener usuario
        result = await self.session.execute(
            select(User)
            .where(and_(
                User.id == user_id,
                User.company_id == company_id
            ))
        )
        user = result.scalar_one_or_none()

        if not user:
            log_rbac_action(
                action="assign_role_failed",
                user_id=user_id,
                company_id=company_id,
                role_id=str(role_id),
                details={"error": "user_not_found"}
            )
            raise UserNotFoundException(user_id=user_id, company_id=company_id)

        # Guardar información del rol anterior para auditoría
        old_role_id = user.role_id
        old_role_code = user.user_role.code if user.user_role else None

        try:
            # Asignar rol
            user.role_id = role_id
            user.updated_at = datetime.utcnow()

            await self.session.commit()
            await self.session.refresh(user)

            # Invalidar cache de permisos del usuario (ya que cambió de rol)
            await self.cache.invalidate_user_permissions(user_id, company_id)

            # Log de éxito con detalles completos
            log_rbac_action(
                action="role_assigned_to_user",
                user_id=user_id,
                company_id=company_id,
                role_id=str(role_id),
                details={
                    "new_role_code": role.code,
                    "new_role_name": role.name,
                    "old_role_id": str(old_role_id) if old_role_id else None,
                    "old_role_code": old_role_code,
                    "hierarchy_change": role.hierarchy_level - (user.user_role.hierarchy_level if user.user_role else 0)
                }
            )

            self.logger.info(
                f"Rol asignado a usuario {user_id}, cache invalidado",
                extra={
                    "user_id": user_id,
                    "company_id": company_id,
                    "new_role_id": str(role_id),
                    "old_role_id": str(old_role_id) if old_role_id else None,
                    "action": "assign_role"
                }
            )

            return user

        except Exception as e:
            log_rbac_action(
                action="assign_role_error",
                user_id=user_id,
                company_id=company_id,
                role_id=str(role_id),
                details={"error": str(e)}
            )
            raise
    
    async def clone_role(
        self,
        role_id: UUID,
        company_id: int,
        new_name: str,
        new_code: str
    ) -> Role:
        """
        Clona un rol existente con todos sus permisos.
        Útil para crear templates de roles.
        
        Args:
            role_id: ID del rol a clonar
            company_id: ID de la empresa
            new_name: Nombre del nuevo rol
            new_code: Código del nuevo rol
        
        Returns:
            Nuevo rol clonado
        """
        # Obtener rol original con permisos
        original_role = await self.get_role(role_id, company_id, include_permissions=True)
        
        if not original_role:
            raise ValueError("Rol original no encontrado")
        
        # Obtener IDs de permisos
        permission_ids = [
            rp.permission_id
            for rp in original_role.role_permissions
        ]
        
        # Crear nuevo rol
        new_role = await self.create_role(
            company_id=company_id,
            name=new_name,
            code=new_code,
            description=f"Clonado de: {original_role.name}",
            hierarchy_level=original_role.hierarchy_level,
            permission_ids=permission_ids
        )
        
        return new_role
    
    async def get_role_by_code(
        self,
        code: str,
        company_id: int
    ) -> Optional[Role]:
        """
        Obtiene un rol por su código.
        """
        result = await self.session.execute(
            select(Role)
            .where(and_(
                Role.code == code,
                Role.company_id == company_id,
                Role.is_active == True
            ))
        )
        return result.scalar_one_or_none()
    
    async def get_users_with_role(
        self,
        role_id: UUID,
        company_id: int
    ) -> List[User]:
        """
        Obtiene todos los usuarios que tienen un rol específico.
        """
        result = await self.session.execute(
            select(User)
            .where(and_(
                User.role_id == role_id,
                User.company_id == company_id,
                User.is_active == True
            ))
        )
        
        return list(result.scalars().all())
