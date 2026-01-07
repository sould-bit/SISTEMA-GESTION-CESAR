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
                plan=data.plan,
                is_active=True
            )
            self.db.add(company)
            await self.db.flush()  # Para obtener company.id
            
            logger.info(f"✅ Company creada: {company.name} (plan: {company.plan})")

            # 3. Crear Subscription
            subscription = await self._create_subscription(company, data.plan)
            
            # 4. Crear Branch principal
            branch = await self._create_default_branch(company)
            
            # 5. Obtener o crear Role admin para esta empresa
            admin_role = await self._get_or_create_admin_role(company)
            
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

    async def _create_default_branch(self, company: Company) -> Branch:
        """Crear sucursal principal por defecto."""
        branch = Branch(
            company_id=company.id,
            name="Principal",
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
        # Usar email como username (más fácil de recordar)
        username = data.owner_email.split("@")[0]
        
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
