from typing import List, Dict, Optional, Set
from uuid import UUID
from sqlmodel import select, Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.permission import Permission
from app.models.permission_category import PermissionCategory
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.core.rbac_defaults import (
    DEFAULT_PERMISSION_CATEGORIES,
    DEFAULT_PERMISSIONS,
    DEFAULT_ROLES,
    DEFAULT_ROLE_PERMISSIONS_MAP
)
from app.core.logging_config import get_rbac_logger

logger = get_rbac_logger("rbac_sync")

class RBACSyncService:
    """
    Servicio de Sincronización de RBAC (System Sync).
    
    Responsabilidades:
    1. Mantener la consistencia de Permisos y Categorías Globales (Code-First).
    2. Inicializar Roles y Permisos por defecto para nuevas empresas (Genesis).
    3. Garantizar que actualizaciones de código se reflejen en la BD sin romper datos de usuario.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def sync_global_metadata(self) -> Dict[str, int]:
        """
        Sincroniza Categorías y Permisos GLOBALES desde rbac_defaults.py hacia la BD.
        Esta operación es Idempotente y NO destructiva.
        
        Returns:
            Dict con conteo de creados/actualizados.
        """
        stats = {"categories_created": 0, "permissions_created": 0, "permissions_updated": 0}
        
        # 1. Sincronizar Categorías
        category_map: Dict[str, UUID] = {} # code -> uuid
        
        # Cache existing categories to avoid N+1 queries
        existing_cats_result = await self.session.execute(
            select(PermissionCategory).where(PermissionCategory.company_id == None)
        )
        existing_cats = {cat.code: cat for cat in existing_cats_result.scalars().all()}

        for cat_def in DEFAULT_PERMISSION_CATEGORIES:
            code = cat_def["code"]
            category = existing_cats.get(code)
            
            if not category:
                # Crear si no existe
                category = PermissionCategory(
                    code=code,
                    name=cat_def["name"],
                    company_id=None, # GLOBAL
                    is_system=True,
                    icon=cat_def.get("icon"),
                    color=cat_def.get("color")
                )
                self.session.add(category)
                stats["categories_created"] += 1
                logger.debug(f"Categoría Global Creada: {cat_def['name']}")
                
                # Flush para obtener ID
                await self.session.flush()
            else:
                # Actualizar metadatos (opcionalmente)
                if category.name != cat_def["name"] or category.company_id is not None:
                    category.name = cat_def["name"]
                    category.company_id = None # Ensure it is global
                    self.session.add(category)
            
            category_map[category.code] = category.id

        # 2. Sincronizar Permisos
        # Cache existing permissions
        existing_perms_result = await self.session.execute(
            select(Permission).where(Permission.company_id == None)
        )
        existing_perms = {p.code: p for p in existing_perms_result.scalars().all()}

        for perm_def in DEFAULT_PERMISSIONS:
            perm_code = perm_def["code"]
            cat_code = perm_def["category"]
            
            if cat_code not in category_map:
                logger.error(f"❌ Categoría '{cat_code}' no encontrada para permiso '{perm_code}'")
                continue
                
            permission = existing_perms.get(perm_code)
            
            parts = perm_code.split(".")
            resource = parts[0]
            action = parts[1] if len(parts) > 1 else "manage"
            
            if not permission:
                # Crear nuevo permiso global
                permission = Permission(
                    code=perm_code,
                    name=perm_def["name"],
                    description=perm_def.get("description"),
                    resource=resource,
                    action=action,
                    company_id=None, # GLOBAL
                    category_id=category_map[cat_code],
                    is_system=True
                )
                self.session.add(permission)
                stats["permissions_created"] += 1
                logger.debug(f"Permiso Global Creado: {perm_code}")
            else:
                # Actualizar info (Code-First Authority)
                updated = False
                if permission.name != perm_def["name"]:
                    permission.name = perm_def["name"]
                    updated = True
                
                # Ensure it's global
                if permission.company_id is not None:
                    permission.company_id = None
                    updated = True
                
                if updated:
                    self.session.add(permission)
                    stats["permissions_updated"] += 1

        await self.session.commit()
        logger.info(f"🔄 Sync Global RBAC: {stats}")
        return stats

    async def initialize_company_roles(self, company_id: int) -> int:
        """
        Inicializa los Roles base para una empresa nueva (Genesis).
        Si los roles ya existen, NO se tocan (respeto a personalización).
        
        Args:
            company_id: ID de la empresa.
            
        Returns:
            Número de roles creados.
        """
        roles_created = 0
        
        # 1. Obtener todos los permisos globales para mapear
        global_perms_query = select(Permission).where(Permission.company_id == None)
        result = await self.session.execute(global_perms_query)
        all_global_permissions = result.scalars().all()
        # Map code -> ID
        perm_map = {p.code: p.id for p in all_global_permissions}
        
        for role_def in DEFAULT_ROLES:
            role_code = role_def["code"]
            
            # Verificar si el rol existe en esta empresa
            query = select(Role).where(
                Role.code == role_code,
                Role.company_id == company_id
            )
            result = await self.session.execute(query)
            existing_role = result.scalar_one_or_none()
            
            if existing_role:
                # El rol ya existe. ZONA SAGRADA. No tocamos nada.
                continue
                
            # Crear Rol
            new_role = Role(
                company_id=company_id,
                code=role_code,
                name=role_def["name"],
                description=role_def.get("description", ""),
                is_system=True, # Es un rol base del sistema
                hierarchy_level=role_def.get("level", 10),
                is_active=True
            )
            self.session.add(new_role)
            await self.session.flush() # Obtener ID para hacer relaciones
            
            roles_created += 1
            logger.info(f"✨ Rol creado para Empresa {company_id}: {new_role.name}")
            
            # Asignar permisos por defecto al rol recién nacido
            permission_patterns = DEFAULT_ROLE_PERMISSIONS_MAP.get(role_code, [])
            permissions_to_assign: Set[UUID] = set()

            for pattern in permission_patterns:
                if pattern == "*":
                    # Todos los permisos
                    for pid in perm_map.values():
                        permissions_to_assign.add(pid)
                elif pattern.endswith(".*"):
                    # Wilcard de recurso (ej: "products.*")
                    resource_prefix = pattern[:-2] # "products"
                    for code, pid in perm_map.items():
                        if code.startswith(resource_prefix + "."):
                            permissions_to_assign.add(pid)
                else:
                    # Literal
                    if pattern in perm_map:
                        permissions_to_assign.add(perm_map[pattern])
                    else:
                        logger.warning(f"⚠️ Permiso '{pattern}' requerido por rol '{role_code}' no existe en globales.")

            # Crear relaciones en batch
            for perm_id in permissions_to_assign:
                self._assign_permission(new_role.id, perm_id)
        
        await self.session.flush() # Flush permisos
        # No hacemos commit aquí, dejamos que el llamador (RegistrationService) haga commit de la transacción completa
        return roles_created

    def _assign_permission(self, role_id: UUID, permission_id: UUID):
        """Helper para crear relación RolePermission"""
        link = RolePermission(
            role_id=role_id,
            permission_id=permission_id
            # granted_by puede ser None indicando 'System'
        )
        self.session.add(link)
