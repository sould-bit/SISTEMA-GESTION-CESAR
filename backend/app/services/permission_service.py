"""
Servicio de Gestión de Permisos (RBAC)

Este servicio maneja:
1. Verificación de permisos de usuarios
2. Cache de permisos en Redis para alto rendimiento
3. Obtención de permisos por usuario/rol
4. Gestión de permisos (CRUD)
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, and_, or_

from app.models import Permission, Role, RolePermission, User, PermissionCategory
from app.core.logging_config import get_rbac_logger, log_permission_check, log_security_event
from app.core.cache import get_rbac_cache


class PermissionService:
    """Servicio para gestión de permisos."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_rbac_logger("app.permissions")
        # self.cache = get_rbac_cache()  # Cache Redis para permisos
        self.cache = None
    
    async def check_permission(
        self,
        user_id: int,
        permission_code: str,
        company_id: int
    ) -> bool:
        """
        Verifica si un usuario tiene un permiso específico.

        Args:
            user_id: ID del usuario
            permission_code: Código del permiso (ej: "products.create")
            company_id: ID de la empresa (multi-tenant)

        Returns:
            True si el usuario tiene el permiso, False en caso contrario

        Ejemplo:
            has_perm = await service.check_permission(1, "products.create", 1)
        """
        start_time = datetime.utcnow()

        try:
            # Intentar obtener desde cache primero
            # cached_permissions = await self.cache.get_user_permissions(user_id, company_id)
            cached_permissions = None

            if cached_permissions is not None:
                # Cache hit
                has_permission = permission_code in cached_permissions

                duration = (datetime.utcnow() - start_time).total_seconds() * 1000

                log_permission_check(
                    user_id=user_id,
                    permission_code=permission_code,
                    company_id=company_id,
                    granted=has_permission,
                    source="cache"
                )

                self.logger.debug(
                    f"Permiso verificado desde cache: {permission_code}",
                    extra={
                        "user_id": user_id,
                        "permission_code": permission_code,
                        "company_id": company_id,
                        "granted": has_permission,
                        "source": "cache",
                        "duration_ms": round(duration, 2)
                    }
                )

                return has_permission

            # Cache miss - obtener desde base de datos
            print(f"DEBUG: PermissionService.check_permission: Cache miss, llamando a get_user_permissions")
            user_permissions = await self.get_user_permissions(user_id, company_id)
            permission_codes = [p.code for p in user_permissions]
            has_permission = permission_code in permission_codes

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Log de la verificación desde DB
            log_permission_check(
                user_id=user_id,
                permission_code=permission_code,
                company_id=company_id,
                granted=has_permission,
                source="database"
            )

            # Cachear los permisos para futuras consultas (si cache está disponible)
            if self.cache:
                await self.cache.set_user_permissions(user_id, company_id, permission_codes)

            self.logger.debug(
                f"Permisos guardados en cache para usuario {user_id}",
                extra={
                    "user_id": user_id,
                    "company_id": company_id,
                    "permissions_count": len(permission_codes),
                    "source": "database_to_cache"
                }
            )

            # Log adicional si el permiso fue denegado (evento de seguridad)
            if not has_permission:
                log_security_event(
                    event="permission_denied",
                    user_id=user_id,
                    company_id=company_id,
                    details={
                        "permission_code": permission_code,
                        "check_duration_ms": round(duration, 2),
                        "user_permissions_count": len(user_permissions),
                        "available_permissions": permission_codes[:10]  # Primeros 10 para debugging
                    }
                )

            # Log de performance si es muy lento
            if duration > 100:  # Más de 100ms
                self.logger.warning(
                    f"Permiso check lento: {duration:.2f}ms",
                    extra={
                        "user_id": user_id,
                        "permission_code": permission_code,
                        "company_id": company_id,
                        "duration_ms": round(duration, 2),
                        "source": "database"
                    }
                )

            return has_permission

        except Exception as e:
            # Log de error en verificación de permisos
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            log_security_event(
                event="permission_check_error",
                user_id=user_id,
                company_id=company_id,
                details={
                    "permission_code": permission_code,
                    "error": str(e),
                    "check_duration_ms": round(duration, 2)
                },
                level="ERROR"
            )

            # En caso de error, denegar por seguridad
            return False
    
    async def get_user_permissions(
        self,
        user_id: int,
        company_id: int
    ) -> List[Permission]:
        """
        Obtiene todos los permisos de un usuario.
        
        Args:
            user_id: ID del usuario
            company_id: ID de la empresa
        
        Returns:
            Lista de objetos Permission
        """
        # Obtener usuario con su rol
        print(f"DEBUG: PermissionService.get_user_permissions: Ejecutando SELECT User")
        result = await self.session.execute(
            select(User)
            .where(and_(
                User.id == user_id,
                User.company_id == company_id,
                User.is_active == True
            ))
            .options(joinedload(User.user_role))
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.role_id:
            return []
        
        # Obtener permisos del rol
        result = await self.session.execute(
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(and_(
                RolePermission.role_id == user.role_id,
                Permission.company_id == company_id,
                Permission.is_active == True
            ))
            .options(joinedload(Permission.category))
        )
        
        permissions = result.scalars().all()
        return list(permissions)
    
    async def get_user_permission_codes(
        self,
        user_id: int,
        company_id: int
    ) -> List[str]:
        """
        Obtiene solo los códigos de permisos de un usuario.
        Útil para incluir en JWT tokens.
        
        Returns:
            Lista de strings con códigos de permisos
        """
        permissions = await self.get_user_permissions(user_id, company_id)
        return [p.code for p in permissions]
    
    async def grant_permission_to_role(
        self,
        role_id: UUID,
        permission_id: UUID,
        granted_by: int,
        expires_at: Optional[datetime] = None
    ) -> RolePermission:
        """
        Otorga un permiso a un rol.
        
        Args:
            role_id: ID del rol
            permission_id: ID del permiso
            granted_by: ID del usuario que otorga el permiso
            expires_at: Fecha de expiración (opcional)
        
        Returns:
            Objeto RolePermission creado
        """
        # 0. Obtener company_id del rol (y validar existencia)
        # Esto previene errores de Lazy Loading (MissingGreenlet) más adelante
        role_stmt = select(Role).where(Role.id == role_id)
        role_res = await self.session.execute(role_stmt)
        role = role_res.scalar_one_or_none()
        
        if not role:
            raise ValueError(f"Rol {role_id} no encontrado")
            
        company_id = role.company_id

        # Verificar si ya existe
        result = await self.session.execute(
            select(RolePermission)
            .where(and_(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id
            ))
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise ValueError("El permiso ya está asignado a este rol")
        
        # Crear nueva asignación
        role_permission = RolePermission(
            role_id=role_id,
            permission_id=permission_id,
            granted_by=granted_by,
            expires_at=expires_at
        )
        
        self.session.add(role_permission)
        await self.session.commit()
        await self.session.refresh(role_permission)

        # Invalidar cache de usuarios con este rol
        if self.cache:
            await self.cache.invalidate_role_permissions(str(role_id), company_id)

        self.logger.info(
            f"Permiso otorgado a rol {role_id}, cache invalidado",
            extra={
                "role_id": str(role_id),
                "permission_id": str(permission_id),
                "company_id": company_id,
                "action": "grant_permission"
            }
        )

        return role_permission
    
    async def revoke_permission_from_role(
        self,
        role_id: UUID,
        permission_id: UUID
    ) -> bool:
        """
        Revoca un permiso de un rol.
        
        Returns:
            True si se revocó, False si no existía
        """
        result = await self.session.execute(
            select(RolePermission)
            .where(and_(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id
            ))
            .options(joinedload(RolePermission.role))
        )
        role_permission = result.scalar_one_or_none()
        
        if not role_permission:
            return False

        # Guardar información antes de eliminar para invalidar cache
        role_id_str = str(role_id)
        company_id = role_permission.role.company_id

        await self.session.delete(role_permission)
        await self.session.commit()

        # Invalidar cache de usuarios con este rol
        if self.cache:
            await self.cache.invalidate_role_permissions(role_id_str, company_id)

        self.logger.info(
            f"Permiso revocado de rol {role_id}, cache invalidado",
            extra={
                "role_id": role_id_str,
                "permission_id": str(permission_id),
                "company_id": company_id,
                "action": "revoke_permission"
            }
        )

        return True
    
    async def get_role_permissions(
        self,
        role_id: UUID,
        company_id: int
    ) -> List[Permission]:
        """
        Obtiene todos los permisos de un rol.
        """
        result = await self.session.execute(
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(and_(
                RolePermission.role_id == role_id,
                Permission.company_id == company_id,
                Permission.is_active == True
            ))
            .options(selectinload(Permission.category))
        )
        
        return list(result.scalars().all())

    async def list_permissions(
        self,
        company_id: int,
        include_system: bool = True,
        only_active: bool = True
    ) -> List[Permission]:
        """
        Lista todos los permisos de una empresa.
        """
        conditions = [Permission.company_id == company_id]
        
        if not include_system:
            conditions.append(Permission.is_system == False)
        
        if only_active:
            conditions.append(Permission.is_active == True)
        
        result = await self.session.execute(
            select(Permission)
            .where(and_(*conditions))
            .options(selectinload(Permission.category))
            .order_by(Permission.resource, Permission.action)
        )
        
        return list(result.scalars().all())

    async def get_permissions_by_category(
        self,
        category_id: UUID,
        company_id: int,
        only_active: bool = True
    ) -> List[Permission]:
        """
        Lista todos los permisos dentro de una categoría específica.
        """
        conditions = [
            Permission.category_id == category_id,
            Permission.company_id == company_id
        ]
        
        if only_active:
            conditions.append(Permission.is_active == True)
        
        result = await self.session.execute(
            select(Permission)
            .where(and_(*conditions))
            .order_by(Permission.resource, Permission.action)
        )
        
        return list(result.scalars().all())
    
    async def create_permission(
        self,
        company_id: int,
        category_id: UUID,
        code: str,
        name: str,
        resource: str,
        action: str,
        description: Optional[str] = None,
        is_system: bool = False
    ) -> Permission:
        """
        Crea un nuevo permiso personalizado.
        
        Args:
            company_id: ID de la empresa
            category_id: ID de la categoría
            code: Código único del permiso
            name: Nombre legible
            resource: Recurso (ej: "products")
            action: Acción (ej: "create")
            description: Descripción opcional
            is_system: Si es permiso del sistema (no editable)
        
        Returns:
            Objeto Permission creado
        """
        # Verificar que el código no exista
        result = await self.session.execute(
            select(Permission)
            .where(and_(
                Permission.company_id == company_id,
                Permission.code == code
            ))
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise ValueError(f"Ya existe un permiso con el código '{code}'")
        
        permission = Permission(
            company_id=company_id,
            category_id=category_id,
            code=code,
            name=name,
            description=description,
            resource=resource,
            action=action,
            is_system=is_system,
            is_active=True
        )
        
        self.session.add(permission)
        await self.session.commit()
        await self.session.refresh(permission)
        
        return permission
    
    async def update_permission(
        self,
        permission_id: UUID,
        company_id: int,
        **kwargs
    ) -> Permission:
        """
        Actualiza un permiso existente.
        Solo permite actualizar permisos no-sistema.
        """
        result = await self.session.execute(
            select(Permission)
            .where(and_(
                Permission.id == permission_id,
                Permission.company_id == company_id
            ))
        )
        permission = result.scalar_one_or_none()
        
        if not permission:
            raise ValueError("Permiso no encontrado")
        
        if permission.is_system:
            raise ValueError("No se pueden modificar permisos del sistema")
        
        # Actualizar campos permitidos
        allowed_fields = ['name', 'description', 'is_active']
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(permission, field, value)
        
        permission.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(permission)
        
        return permission
    
    async def delete_permission(
        self,
        permission_id: UUID,
        company_id: int
    ) -> bool:
        """
        Elimina (soft delete) un permiso personalizado.
        No permite eliminar permisos del sistema.
        """
        result = await self.session.execute(
            select(Permission)
            .where(and_(
                Permission.id == permission_id,
                Permission.company_id == company_id
            ))
        )
        permission = result.scalar_one_or_none()
        
        if not permission:
            return False
        
        if permission.is_system:
            raise ValueError("No se pueden eliminar permisos del sistema")
        
        # Soft delete
        permission.is_active = False
        permission.updated_at = datetime.utcnow()
        
        await self.session.commit()
        
        return True
    
    # ========================================================================
    # MÉTODOS DE CACHE (TODO: Implementar con Redis)
    # ========================================================================
    
    async def cache_user_permissions(self, user_id: int) -> None:
        """
        Cachea los permisos de un usuario en Redis.
        TTL: 15 minutos
        """
        # TODO: Implementar cuando se agregue Redis
        pass
    
    async def invalidate_permission_cache(self, user_id: int) -> None:
        """
        Invalida el cache de permisos de un usuario.
        """
        # TODO: Implementar cuando se agregue Redis
        pass
    
    async def _invalidate_role_cache(self, role_id: UUID) -> None:
        """
        Invalida el cache de todos los usuarios con un rol específico.
        """
        # TODO: Implementar cuando se agregue Redis
        pass
