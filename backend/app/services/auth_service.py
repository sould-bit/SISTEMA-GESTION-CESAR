"""
🔐 AUTH SERVICE - Lógica de Autenticación y Seguridad

Este servicio centraliza toda la lógica de autenticación del sistema:
- Login y validación de credenciales
- Generación y validación de tokens JWT
- Verificación de usuarios y empresas
- Manejo de sesiones multi-tenant

Principios de seguridad:
- ✅ Multi-tenant: Aislamiento completo por empresa
- ✅ Hashing: Contraseñas siempre hasheadas
- ✅ JWT: Tokens seguros con expiración
- ✅ Logging: Auditoría completa de accesos
"""

from datetime import timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi import HTTPException, status

from app.models.user import User
from app.models.company import Company
from app.schemas.auth import LoginRequest, Token, UserResponse, TokenVerification
from app.utils.security import verify_password, create_access_token
from app.config import settings

import logging

logger = logging.getLogger(__name__)


class AuthService:
    """
    🔐 Servicio de Autenticación

    Maneja toda la lógica de autenticación del sistema de manera centralizada.
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializar servicio con sesión de BD

        Args:
            db: Sesión asíncrona de SQLAlchemy
        """
        self.db = db

    async def authenticate_user(self, login_data: LoginRequest) -> Token:
        """
        🔑 AUTENTICAR USUARIO

        Proceso completo de login:
        1. Buscar empresa por slug
        2. Validar que esté activa
        3. Buscar usuario en esa empresa
        4. Validar credenciales
        5. Generar token JWT

        Args:
            login_data: Datos de login (company_slug, username, password)

        Returns:
            Token: Token JWT generado

        Raises:
            HTTPException: Si credenciales inválidas o empresa no existe
        """
        try:
            # 1. Buscar empresa
            company = await self._get_active_company(login_data.company_slug)
            if not company:
                logger.warning(f"🔒 Intento de login con empresa inexistente: {login_data.company_slug}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Empresa no encontrada o inactiva"
                )

            # 2. Buscar usuario en la empresa
            user = await self._get_user_by_credentials(
                login_data.username,
                company.id
            )

            # 3. Validar contraseña
            if not user or not verify_password(login_data.password, user.hashed_password):
                logger.warning(f"🔒 Intento de login fallido: {login_data.username}@{login_data.company_slug}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales inválidas o token expirado",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 4. Validar que usuario esté activo
            if not user.is_active:
                logger.warning(f"🔒 Usuario inactivo intentando login: {user.username}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Usuario inactivo"
                )

            # 5. Generar token
            token = await self._generate_user_token(user)

            logger.info(f"✅ Login exitoso: {user.username} (Empresa: {company.name})")
            return token

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error en autenticación: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno del servidor"
            )

    async def get_current_user_info(self, user: User) -> UserResponse:
        """
        👤 OBTENER INFORMACIÓN DEL USUARIO ACTUAL

        Args:
            user: Usuario ya validado por middleware

        Returns:
            UserResponse: Datos públicos del usuario
        """
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            company_id=user.company_id,
            branch_id=user.branch_id
        )

    async def verify_user_token(self, user: User) -> TokenVerification:
        """
        ✅ VERIFICAR VALIDEZ DEL TOKEN DEL USUARIO

        Args:
            user: Usuario ya validado por middleware

        Returns:
            TokenVerification: Confirmación de que el token es válido
        """
        return TokenVerification(
            valid=True,
            user_id=user.id,
            username=user.username,
            company_id=user.company_id
        )

    async def refresh_user_token(self, user: User) -> Token:
        """
        🔄 REFRESCAR TOKEN DEL USUARIO

        Genera un nuevo token para el usuario actual.

        Args:
            user: Usuario ya validado por middleware

        Returns:
            Token: Nuevo token JWT
        """
        token = await self._generate_user_token(user)
        logger.info(f"✅ Token refrescado para: {user.username}")
        return token

    async def logout_user(self, user: User) -> Dict[str, str]:
        """
        🚪 PROCESAR LOGOUT DEL USUARIO

        En JWT stateless, el logout es principalmente del lado del cliente,
        pero podemos usar esto para logging/auditoría.

        Args:
            user: Usuario que está cerrando sesión

        Returns:
            dict: Confirmación de logout
        """
        logger.info(f"👋 Logout: {user.username}")
        return {
            "message": "Logout exitoso",
            "detail": "Elimina el token del cliente"
        }

    # ==================== MÉTODOS PRIVADOS ====================

    async def _get_active_company(self, company_slug: str) -> Optional[Company]:
        """
        🏢 BUSCAR EMPRESA ACTIVA POR SLUG

        Args:
            company_slug: Slug único de la empresa

        Returns:
            Company or None: Empresa activa si existe
        """
        result = await self.db.execute(
            select(Company).where(
                Company.slug == company_slug,
                Company.is_active == True
            )
        )
        return result.scalar_one_or_none()

    async def _get_user_by_credentials(self, username: str, company_id: int) -> Optional[User]:
        """
        👤 BUSCAR USUARIO POR CREDENCIALES

        Args:
            username: Nombre de usuario
            company_id: ID de la empresa

        Returns:
            User or None: Usuario si existe en la empresa
        """
        result = await self.db.execute(
            select(User).where(
                User.username == username,
                User.company_id == company_id
            )
        )
        return result.scalar_one_or_none()

    async def _generate_user_token(self, user: User) -> Token:
        """
        🎫 GENERAR TOKEN JWT PARA USUARIO

        Args:
            user: Usuario para el cual generar el token

        Returns:
            Token: Token JWT con información del usuario
        """
        # Calcular expiración
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        # Payload del token con información multi-tenant
        token_payload = {
            "sub": str(user.id),
            "user_id": user.id,
            "username": user.username,
            "company_id": user.company_id,
            "branch_id": user.branch_id,
            "role": user.role,
            "plan": user.company.plan if user.company else "trial"
        }

        # Generar token
        access_token = create_access_token(
            data=token_payload,
            expires_delta=access_token_expires
        )

        return Token(
            access_token=access_token,
            token_type="bearer"
        )
