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
from fastapi.concurrency import run_in_threadpool as run_in_executor

from app.models.user import User
from app.models.company import Company
from app.schemas.auth import LoginRequest, Token, UserResponse, TokenVerification, LoginResponse, CompanyOption
from app.utils.security import verify_password, create_access_token, create_refresh_token, decode_access_token
from app.config import settings
from app.services.audit_service import AuditService
from app.models.audit_log import AuditAction

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

    async def authenticate_user(self, login_data: LoginRequest) -> LoginResponse:
        """
        🔑 AUTENTICAR USUARIO (Smart Auth v3.5)

        Estrategia:
        1. Buscar todos los usuarios con el email proporcionado.
        2. Validar contraseña para cada coincidencia.
        3. Si hay 0 coincidencias válidas: Error 401.
        4. Si hay 1 coincidencia válida: Login directo.
        5. Si hay >1 coincidencias válidas:
            - Si se envió company_slug: Filtrar y loguear.
            - Si NO se envió slug: Retornar lista de empresas para que usuario elija.
        """
        try:
            from sqlalchemy.orm import selectinload

            # 1. Buscar usuarios por email (activo)
            # Cargamos relación company y role para construir la respuesta
            stmt = select(User).where(
                User.email == login_data.email, 
                User.is_active == True
            ).options(
                selectinload(User.company),
                selectinload(User.user_role)
            )
            result = await self.db.execute(stmt)
            users = result.scalars().all()

            valid_users = []
            
            # 2. Validar contraseñas
            # Nota: Esto mitiga enumeración de usuarios porque siempre verificamos el pass
            # antes de confirmar que el usuario existe en alguna empresa.
            for user in users:
                if verify_password(login_data.password, user.hashed_password):
                    # Verificar también que la empresa esté activa
                    if user.company and user.company.is_active:
                        valid_users.append(user)

            # 3. Análisis de resultados
            if not valid_users:
                logger.warning(f"🔒 Login fallido (credenciales/inactivo): {login_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email o contraseña incorrectos",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 4. Selección de usuario final
            selected_user = None

            # Caso A: Solo hay un usuario válido -> Login directo
            if len(valid_users) == 1:
                selected_user = valid_users[0]

            # Caso B: Hay múltiples (Multi-tenant)
            else:
                # Si el cliente ya especificó a cual quiere entrar
                if login_data.company_slug:
                    for u in valid_users:
                        if u.company.slug == login_data.company_slug:
                            selected_user = u
                            break
                    
                    if not selected_user:
                        # Credenciales vaidas pero slug incorrecto para este user
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="No tienes acceso a la empresa solicitada"
                        )
                
                # Si no especificó -> Devolver lista para elegir
                else:
                    options = []
                    for u in valid_users:
                        options.append(CompanyOption(
                            name=u.company.name,
                            slug=u.company.slug,
                            role=u.user_role.name if u.user_role else "Usuario"
                        ))
                    
                    logger.info(f"🤔 Usuario multi-tenant requiere selección: {login_data.email}")
                    return LoginResponse(
                        requires_selection=True,
                        options=options
                    )

            # 5. Generar token y loguear (Login Final)
            token = await self._generate_user_token(selected_user)
            
            # Auditoría
            audit_service = AuditService(self.db)
            await audit_service.log_simple(
                action=AuditAction.LOGIN_SUCCESS,
                company_id=selected_user.company_id,
                description=f"Login Smart Auth: {selected_user.username}",
                user_id=selected_user.id,
                username=selected_user.username
            )

            logger.info(f"✅ Login Smart Auth exitoso: {selected_user.username} @ {selected_user.company.slug}")
            return LoginResponse(
                token=token,
                requires_selection=False
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error en autenticación Smart Auth: {e}")
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

        Genera un nuevo par de tokens para el usuario actual.

        Args:
            user: Usuario ya validado por middleware (a través del access token anterior)

        Returns:
            Token: Nuevos tokens JWT (Access + Refresh)
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
        # Auditoría - Logout
        audit_service = AuditService(self.db)
        await audit_service.log_simple(
            action=AuditAction.LOGOUT,
            company_id=user.company_id,
            description=f"Usuario {user.username} cerró sesión",
            user_id=user.id,
            username=user.username
        )
        
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
        
        Actualizado en v3.3 para cargar relación con rol.

        Args:
            username: Nombre de usuario
            company_id: ID de la empresa

        Returns:
            User or None: Usuario si existe en la empresa
        """
        from sqlalchemy.orm import selectinload
        
        result = await self.db.execute(
            select(User)
            .where(
                User.username == username,
                User.company_id == company_id
            )
            .options(
                selectinload(User.user_role),  # Cargar rol para permisos
                selectinload(User.company)     # Cargar empresa para plan
            )
        )
        return result.scalar_one_or_none()

    async def _generate_user_token(self, user: User) -> Token:
        """
        🎫 GENERAR TOKEN JWT PARA USUARIO
        
        Actualizado en v3.3 para incluir permisos del sistema RBAC.

        Args:
            user: Usuario para el cual generar el token

        Returns:
            Token: Token JWT con información del usuario y permisos
        """
        # Calcular expiración
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Cargar permisos del usuario (v3.3)
        permissions = []
        role_id = None
        role_code = None
        
        if user.role_id:
            from app.services.permission_service import PermissionService
            permission_service = PermissionService(self.db)
            
            try:
                # Obtener códigos de permisos
                permissions = await permission_service.get_user_permission_codes(
                    user_id=user.id,
                    company_id=user.company_id
                )
                
                # Obtener información del rol
                if user.user_role:
                    role_id = user.role_id
                    role_code = user.user_role.code
                    
                logger.info(f"✅ Cargados {len(permissions)} permisos para {user.username}")
            except Exception as e:
                logger.warning(f"⚠️ Error cargando permisos para {user.username}: {e}")
                # Continuar sin permisos en caso de error

        # Payload del token con información multi-tenant
        token_payload = {
            "sub": str(user.id),
            "user_id": user.id,
            "username": user.username,
            "company_id": user.company_id,
            "branch_id": user.branch_id,
            "role": user.role,  # Legacy
            "plan": user.company.plan if user.company else "trial"
        }

        # Generar token con permisos (v3.3)
        access_token = create_access_token(
            data=token_payload,
            expires_delta=access_token_expires,
            permissions=permissions,
            role_id=role_id,
            role_code=role_code
        )
        
        # Generar refresh token (v3.4 - Ticket 3.1)
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "user_id": user.id, "company_id": user.company_id},
            expires_delta=timedelta(days=7)
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
