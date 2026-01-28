"""
🏢 REGISTRATION SERVICE
Servicio para registro público de nuevos negocios.
Crea Company + Subscription + Branch + User Admin en una transacción.
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi import HTTPException, status

from app.models.company import Company
from app.models.subscription import Subscription
from app.models.branch import Branch
from app.models.user import User
from app.models.role import Role
from app.models.permission_category import PermissionCategory
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.schemas.registration import (
    RegistrationRequest, 
    RegistrationResponse,
    CompanyAvailabilityCheck,
    CompanyAvailabilityResponse
)
from app.utils.security import get_password_hash, create_access_token, create_refresh_token
from app.config import settings

import logging

logger = logging.getLogger(__name__)


class RegistrationService:
    """
    🏢 Servicio de Registro de Negocios
    
    Maneja el registro público de nuevos negocios con:
    - Validación de slug único
    - Creación de Company con plan seleccionado
    - Creación de Subscription
    - Creación de Branch principal
    - Creación de User admin (owner)
    - Auto-login (retorna JWT)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_slug_availability(self, slug: str) -> CompanyAvailabilityResponse:
        """
        Verificar si un slug de empresa está disponible.
        """
        result = await self.db.execute(
            select(Company).where(Company.slug == slug)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Sugerir alternativa
            suggestion = f"{slug}-{datetime.now().strftime('%y%m')}"
            return CompanyAvailabilityResponse(
                slug=slug,
                available=False,
                suggestion=suggestion
            )
        
        return CompanyAvailabilityResponse(slug=slug, available=True)

    async def register_company(self, data: RegistrationRequest) -> RegistrationResponse:
        """
        🚀 Registrar un nuevo negocio completo.
        
        Flujo:
        1. Validar slug único
        2. Crear Company
        3. Crear Subscription
        4. Crear Branch principal
        5. Obtener/crear Role admin
        6. Crear User admin
        7. Generar tokens JWT
        
        Returns:
            RegistrationResponse con tokens y datos del usuario
        """
        try:
            # 1. Validar slug único
            availability = await self.check_slug_availability(data.company_slug)
            if not availability.available:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El identificador '{data.company_slug}' ya está en uso. Sugerencia: {availability.suggestion}"
                )

            # 2. Crear Company
            company = Company(
                name=data.company_name,
                slug=data.company_slug,
                owner_name=data.owner_name,
                owner_email=data.owner_email,
                owner_phone=data.owner_phone,
                # Datos Legales
                legal_name=data.legal_name,
                tax_id=data.tax_id,
                plan=data.plan,
                is_active=True
            )
            self.db.add(company)
            await self.db.flush()  # Para obtener company.id
            
            logger.info(f"✅ Company creada: {company.name} (plan: {company.plan})")

            # 3. Crear Subscription
            subscription = await self._create_subscription(company, data.plan)
            
            # 4. Crear Branch principal (usando datos del registro si existen)
            branch = await self._create_default_branch(company, data)
            
            # 5. Obtener o crear Role admin para esta empresa
            admin_role = await self._get_or_create_admin_role(company)
            
            # 5.5 Crear permisos por defecto y asignarlos al admin
            await self._create_default_permissions(company, admin_role)
            
            # 5.6 CREAR ROLES POR DEFECTO (Managers, Cajeros, etc)
            await self._create_operational_roles(company)
            
            # 6. Crear User admin (owner)
            user = await self._create_admin_user(
                company=company,
                branch=branch,
                role=admin_role,
                data=data
            )

            # Commit todo
            await self.db.commit()
            
            # 7. Generar tokens
            access_token, refresh_token = await self._generate_tokens(user, company)

            logger.info(f"✅ Registro completo: {user.username}@{company.slug}")

            return RegistrationResponse(
                message="Registro exitoso. ¡Bienvenido!",
                company_slug=company.slug,
                access_token=access_token,
                refresh_token=refresh_token,
                user_id=user.id,
                username=user.username,
                email=user.email,
                plan=company.plan
            )

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error en registro: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al procesar el registro. Intente nuevamente."
            )

    async def _create_subscription(self, company: Company, plan: str) -> Subscription:
        """Crear subscription según el plan."""
        now = datetime.utcnow()
        
        if plan == "free":
            subscription = Subscription(
                company_id=company.id,
                plan="free",
                status="active",
                started_at=now,
                amount=0.0
            )
        else:
            # Premium/Basic: trial de 14 días
            subscription = Subscription(
                company_id=company.id,
                plan=plan,
                status="trialing",
                started_at=now,
                current_period_start=now,
                current_period_end=now + timedelta(days=14),
                amount=0.0  # Se actualizará al activar pago
            )
        
        self.db.add(subscription)
        await self.db.flush()
        logger.info(f"✅ Subscription creada: {plan} ({subscription.status})")
        return subscription

    async def _create_default_branch(self, company: Company, data: RegistrationRequest) -> Branch:
        """Crear sucursal principal."""
        
        name = data.branch_name if data.branch_name else "Principal"
        address = data.branch_address  # Puede ser None
        phone = data.branch_phone      # Puede ser None
        
        branch = Branch(
            company_id=company.id,
            name=name,
            address=address,
            phone=phone,
            code="MAIN",
            is_main=True,
            is_active=True
        )
        self.db.add(branch)
        await self.db.flush()
        logger.info(f"✅ Branch creada: {branch.name}")
        return branch

    async def _get_or_create_admin_role(self, company: Company) -> Role:
        """Obtener o crear rol admin para la empresa."""
        # Buscar rol admin existente para esta empresa
        result = await self.db.execute(
            select(Role).where(
                Role.company_id == company.id,
                Role.code == "admin"
            )
        )
        role = result.scalar_one_or_none()
        
        if not role:
            # Crear rol admin
            role = Role(
                company_id=company.id,
                name="Administrador",
                code="admin",
                description="Administrador con acceso completo",
                hierarchy_level=100,  # Máximo nivel
                is_system=True,
                is_active=True
            )
            self.db.add(role)
            await self.db.flush()
            logger.info(f"✅ Role admin creado para {company.slug}")
        
        return role

    async def _create_admin_user(
        self, 
        company: Company, 
        branch: Branch, 
        role: Role,
        data: RegistrationRequest
    ) -> User:
        """Crear usuario admin (owner del negocio)."""
        # Usar username proporcionado
        username = data.username
        
        user = User(
            username=username,
            email=data.owner_email,
            hashed_password=get_password_hash(data.password),
            full_name=data.owner_name,
            company_id=company.id,
            branch_id=branch.id,
            role_id=role.id,
            role="admin",  # Campo legacy
            is_active=True
        )
        self.db.add(user)
        await self.db.flush()
        logger.info(f"✅ User admin creado: {user.username}")
        return user

    async def _create_operational_roles(self, company: Company):
        """Crear roles operativos base (Cajero, Cocinero, etc)."""
        from app.utils.role_seeder import seed_default_roles
        await seed_default_roles(self.db, company.id)

    async def _generate_tokens(self, user: User, company: Company) -> tuple[str, str]:
        """Generar tokens JWT para el usuario."""
        from datetime import timedelta
        
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "company_id": company.id,
            "branch_id": user.branch_id,
            "role_id": str(user.role_id) if user.role_id else None,
            "role_code": "admin",
            "plan": company.plan
        }
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_refresh_token(data=token_data)
        
        return access_token, refresh_token

    async def _create_default_permissions(self, company: Company, admin_role: Role):
        """
        Crear categorías de permisos y permisos por defecto.
        Asignar todos los permisos al rol admin.
        """
        # Definir categorías y permisos del sistema
        default_categories = [
            {"code": "products", "name": "Productos", "icon": "inventory_2", "color": "#4CAF50"},
            {"code": "orders", "name": "Pedidos", "icon": "receipt_long", "color": "#2196F3"},
            {"code": "inventory", "name": "Inventario", "icon": "warehouse", "color": "#FF9800"},
            {"code": "cash", "name": "Caja", "icon": "point_of_sale", "color": "#9C27B0"},
            {"code": "reports", "name": "Reportes", "icon": "analytics", "color": "#607D8B"},
            {"code": "users", "name": "Usuarios", "icon": "people", "color": "#F44336"},
            {"code": "settings", "name": "Configuración", "icon": "settings", "color": "#795548"},
            {"code": "admin", "name": "Administración", "icon": "admin_panel_settings", "color": "#673AB7"},
        ]
        
        default_permissions = [
            # Productos
            {"category": "products", "code": "products.create", "name": "Crear productos", "resource": "products", "action": "create"},
            {"category": "products", "code": "products.read", "name": "Ver productos", "resource": "products", "action": "read"},
            {"category": "products", "code": "products.update", "name": "Editar productos", "resource": "products", "action": "update"},
            {"category": "products", "code": "products.delete", "name": "Eliminar productos", "resource": "products", "action": "delete"},
            # Pedidos
            {"category": "orders", "code": "orders.create", "name": "Crear pedidos", "resource": "orders", "action": "create"},
            {"category": "orders", "code": "orders.read", "name": "Ver pedidos", "resource": "orders", "action": "read"},
            {"category": "orders", "code": "orders.update", "name": "Actualizar pedidos", "resource": "orders", "action": "update"},
            {"category": "orders", "code": "orders.cancel", "name": "Cancelar pedidos", "resource": "orders", "action": "cancel"},
            # Inventario
            {"category": "inventory", "code": "inventory.read", "name": "Ver inventario", "resource": "inventory", "action": "read"},
            {"category": "inventory", "code": "inventory.adjust", "name": "Ajustar inventario", "resource": "inventory", "action": "adjust"},
            # Caja
            {"category": "cash", "code": "cash.open", "name": "Abrir caja", "resource": "cash", "action": "open"},
            {"category": "cash", "code": "cash.close", "name": "Cerrar caja", "resource": "cash", "action": "close"},
            {"category": "cash", "code": "cash.read", "name": "Ver movimientos", "resource": "cash", "action": "read"},
            # Reportes
            {"category": "reports", "code": "reports.sales", "name": "Ver reportes de ventas", "resource": "reports", "action": "sales"},
            {"category": "reports", "code": "reports.financial", "name": "Ver reportes financieros", "resource": "reports", "action": "financial"},
            # Usuarios
            {"category": "users", "code": "users.create", "name": "Crear usuarios", "resource": "users", "action": "create"},
            {"category": "users", "code": "users.read", "name": "Ver usuarios", "resource": "users", "action": "read"},
            {"category": "users", "code": "users.update", "name": "Editar usuarios", "resource": "users", "action": "update"},
            {"category": "users", "code": "users.delete", "name": "Eliminar usuarios", "resource": "users", "action": "delete"},
            # Configuración
            {"category": "settings", "code": "settings.read", "name": "Ver configuración", "resource": "settings", "action": "read"},
            {"category": "settings", "code": "settings.update", "name": "Modificar configuración", "resource": "settings", "action": "update"},
            # Admin RBAC
            {"category": "admin", "code": "admin.roles.create", "name": "Crear roles", "resource": "admin.roles", "action": "create"},
            {"category": "admin", "code": "admin.roles.read", "name": "Ver roles", "resource": "admin.roles", "action": "read"},
            {"category": "admin", "code": "admin.roles.update", "name": "Editar roles", "resource": "admin.roles", "action": "update"},
            {"category": "admin", "code": "admin.roles.delete", "name": "Eliminar roles", "resource": "admin.roles", "action": "delete"},
            {"category": "admin", "code": "admin.permissions.read", "name": "Ver permisos", "resource": "admin.permissions", "action": "read"},
            {"category": "admin", "code": "admin.permissions.update", "name": "Asignar permisos", "resource": "admin.permissions", "action": "update"},
        ]
        
        # Crear categorías
        category_map = {}
        for cat_data in default_categories:
            category = PermissionCategory(
                company_id=company.id,
                code=cat_data["code"],
                name=cat_data["name"],
                icon=cat_data["icon"],
                color=cat_data["color"],
                is_system=True,
                is_active=True
            )
            self.db.add(category)
            await self.db.flush()
            category_map[cat_data["code"]] = category
        
        logger.info(f"✅ {len(category_map)} categorías de permisos creadas")
        
        # Crear permisos y asignar al admin
        permissions_created = 0
        for perm_data in default_permissions:
            category = category_map.get(perm_data["category"])
            if not category:
                continue
                
            permission = Permission(
                company_id=company.id,
                category_id=category.id,
                code=perm_data["code"],
                name=perm_data["name"],
                resource=perm_data["resource"],
                action=perm_data["action"],
                is_system=True,
                is_active=True
            )
            self.db.add(permission)
            await self.db.flush()
            
            # Asignar al rol admin
            role_permission = RolePermission(
                role_id=admin_role.id,
                permission_id=permission.id,
                granted_at=datetime.utcnow()
            )
            self.db.add(role_permission)
            permissions_created += 1
        
        await self.db.flush()
        logger.info(f"✅ {permissions_created} permisos creados y asignados a admin")
