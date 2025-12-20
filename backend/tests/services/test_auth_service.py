"""
🧪 TESTS UNITARIOS - AuthService

Tests para el servicio de autenticación que cubren:
- ✅ Login exitoso con credenciales válidas
- ✅ Login fallido con credenciales inválidas
- ✅ Usuario inactivo rechazado
- ✅ Empresa no encontrada
- ✅ Generación de tokens JWT
- ✅ Validación de usuarios
- ✅ Refresh tokens

Ejecutar tests:
    pytest backend/tests/services/test_auth_service.py -v
"""

import pytest
from fastapi import HTTPException
from sqlmodel import select

from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest, Token, UserResponse, TokenVerification
from app.models.user import User
from app.models.company import Company



class TestAuthService:
    """
    🔐 Tests para AuthService

    Cada test es independiente y usa fixtures limpias.
    """

    
    @pytest.mark.asyncio
async def test_authenticate_user_success(self, auth_service: AuthService):
        """
        ✅ LOGIN EXITOSO - Credenciales válidas

        Debe retornar token JWT cuando las credenciales son correctas.
        """
        # Arrange
        login_data = LoginRequest(
            company_slug="test-company",
            username="testuser",
            password="testpass123"
        )

        # Act
        result = await auth_service.authenticate_user(login_data)

        # Assert
        assert isinstance(result, Token)
        assert result.token_type == "bearer"
        assert result.access_token is not None
        assert len(result.access_token) > 100  # Token JWT debe ser largo

    
    @pytest.mark.asyncio
async def test_authenticate_user_wrong_password(self, auth_service: AuthService):
        """
        ❌ LOGIN FALLIDO - Contraseña incorrecta

        Debe lanzar HTTPException 401 cuando la contraseña es inválida.
        """
        # Arrange
        login_data = LoginRequest(
            company_slug="test-company",
            username="testuser",
            password="wrongpassword"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user(login_data)

        assert exc_info.value.status_code == 401
        assert "Credenciales inválidas" in str(exc_info.value.detail)

    
    
    @pytest.mark.asyncio
async def test_authenticate_user_wrong_username(self, auth_service: AuthService):
        """
        ❌ LOGIN FALLIDO - Usuario inexistente

        Debe lanzar HTTPException 401 cuando el usuario no existe.
        """
        # Arrange
        login_data = LoginRequest(
            company_slug="test-company",
            username="nonexistent",
            password="testpass123"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user(login_data)

        assert exc_info.value.status_code == 401
        assert "Credenciales inválidas" in str(exc_info.value.detail)

    
    
    @pytest.mark.asyncio
async def test_authenticate_user_company_not_found(self, auth_service: AuthService):
        """
        ❌ LOGIN FALLIDO - Empresa inexistente

        Debe lanzar HTTPException 404 cuando la empresa no existe.
        """
        # Arrange
        login_data = LoginRequest(
            company_slug="nonexistent-company",
            username="testuser",
            password="testpass123"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user(login_data)

        assert exc_info.value.status_code == 404
        assert "Empresa no encontrada" in str(exc_info.value.detail)

    
    
    @pytest.mark.asyncio
async def test_authenticate_user_inactive_user(self, auth_service: AuthService, db_session):
        """
        ❌ LOGIN FALLIDO - Usuario inactivo

        Debe lanzar HTTPException 400 cuando el usuario está inactivo.
        """
        # Arrange - Desactivar usuario
        result = await db_session.execute(
            select(User).where(User.username == "testuser")
        )
        user = result.scalar_one()
        user.is_active = False
        await db_session.commit()

        login_data = LoginRequest(
            company_slug="test-company",
            username="testuser",
            password="testpass123"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user(login_data)

        assert exc_info.value.status_code == 400
        assert "Usuario inactivo" in str(exc_info.value.detail)

    
    
    @pytest.mark.asyncio
async def test_get_current_user_info(self, auth_service: AuthService, test_user: User):
        """
        👤 OBTENER INFORMACIÓN DEL USUARIO ACTUAL

        Debe retornar UserResponse con datos correctos.
        """
        # Act
        result = await auth_service.get_current_user_info(test_user)

        # Assert
        assert isinstance(result, UserResponse)
        assert result.id == test_user.id
        assert result.username == test_user.username
        assert result.email == test_user.email
        assert result.full_name == test_user.full_name
        assert result.role == test_user.role
        assert result.is_active == test_user.is_active
        assert result.company_id == test_user.company_id

    
    
    @pytest.mark.asyncio
async def test_verify_user_token(self, auth_service: AuthService, test_user: User):
        """
        ✅ VERIFICAR TOKEN DEL USUARIO

        Debe retornar TokenVerification válido.
        """
        # Act
        result = await auth_service.verify_user_token(test_user)

        # Assert
        assert isinstance(result, TokenVerification)
        assert result.valid == True
        assert result.user_id == test_user.id
        assert result.username == test_user.username
        assert result.company_id == test_user.company_id

    
    
    @pytest.mark.asyncio
async def test_refresh_user_token(self, auth_service: AuthService, test_user: User):
        """
        🔄 REFRESCAR TOKEN DEL USUARIO

        Debe generar un nuevo token válido.
        """
        # Act
        result = await auth_service.refresh_user_token(test_user)

        # Assert
        assert isinstance(result, Token)
        assert result.token_type == "bearer"
        assert result.access_token is not None
        assert len(result.access_token) > 100

    
    
    @pytest.mark.asyncio
async def test_logout_user(self, auth_service: AuthService, test_user: User):
        """
        🚪 LOGOUT DEL USUARIO

        Debe retornar mensaje de confirmación.
        """
        # Act
        result = await auth_service.logout_user(test_user)

        # Assert
        assert isinstance(result, dict)
        assert "message" in result
        assert "detail" in result
        assert "Logout exitoso" in result["message"]

    
    
    @pytest.mark.asyncio
async def test_generate_user_token_structure(self, auth_service: AuthService, test_user: User):
        """
        🎫 ESTRUCTURA DEL TOKEN JWT

        Verificar que el token contenga la información correcta.
        """
        # Act - Generar token
        token = await auth_service._generate_user_token(test_user)

        # Assert
        assert isinstance(token, Token)
        assert token.token_type == "bearer"

        # Decodificar token para verificar contenido (sin firma)
        import jwt
        from app.config import settings

        # Decodificar sin verificar firma para inspeccionar payload
        payload = jwt.decode(token.access_token, options={"verify_signature": False})

        # Verificar campos obligatorios
        assert payload["sub"] == str(test_user.id)
        assert payload["user_id"] == test_user.id
        assert payload["username"] == test_user.username
        assert payload["company_id"] == test_user.company_id
        assert payload["role"] == test_user.role
        assert "exp" in payload  # Expiración
        assert "iat" in payload  # Issued at

    
    
    @pytest.mark.asyncio
async def test_get_active_company_found(self, auth_service: AuthService):
        """
        🏢 BUSCAR EMPRESA ACTIVA - Encontrada

        Debe retornar la empresa cuando existe y está activa.
        """
        # Act
        company = await auth_service._get_active_company("test-company")

        # Assert
        assert company is not None
        assert company.slug == "test-company"
        assert company.is_active == True

    
    
    @pytest.mark.asyncio
async def test_get_active_company_not_found(self, auth_service: AuthService):
        """
        🏢 BUSCAR EMPRESA ACTIVA - No encontrada

        Debe retornar None cuando la empresa no existe.
        """
        # Act
        company = await auth_service._get_active_company("nonexistent")

        # Assert
        assert company is None

    
    
    @pytest.mark.asyncio
async def test_get_user_by_credentials_found(self, auth_service: AuthService, test_company: Company):
        """
        👤 BUSCAR USUARIO POR CREDENCIALES - Encontrado

        Debe retornar el usuario cuando existe en la empresa.
        """
        # Act
        user = await auth_service._get_user_by_credentials("testuser", test_company.id)

        # Assert
        assert user is not None
        assert user.username == "testuser"
        assert user.company_id == test_company.id

    
    
    @pytest.mark.asyncio
async def test_get_user_by_credentials_not_found(self, auth_service: AuthService, test_company: Company):
        """
        👤 BUSCAR USUARIO POR CREDENCIALES - No encontrado

        Debe retornar None cuando el usuario no existe.
        """
        # Act
        user = await auth_service._get_user_by_credentials("nonexistent", test_company.id)

        # Assert
        assert user is None
