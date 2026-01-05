"""
Pruebas para decoradores de permisos.

Estas pruebas validan que los decoradores de autorización
funcionen correctamente con las dependencias FastAPI.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_permission, require_any_permission, require_all_permissions
from app.models import User


class TestPermissionDecorators:
    """Pruebas para decoradores de permisos."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.core.permissions.PermissionService')
    async def test_require_permission_grants_access_with_valid_permission(
        self,
        mock_service_cls
    ):
        """Test que el decorador permite acceso cuando el usuario tiene el permiso."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_user = Mock()
        mock_user.id = 1
        mock_user.company_id = 1

        # Mock service
        mock_instance = mock_service_cls.return_value
        mock_instance.check_permission = AsyncMock(return_value=True)

        # Crear decorador
        decorator = require_permission("test.permission")
        decorated_func = decorator(self.mock_endpoint)

        # Act
        result = await decorated_func(
            session=mock_session,
            current_user=mock_user
        )

        # Assert
        assert result == "success"
        # Verify check_permission called correctly
        mock_instance.check_permission.assert_called_once_with(
            user_id=mock_user.id,
            permission_code="test.permission",
            company_id=mock_user.company_id
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.core.permissions.PermissionService')
    async def test_require_permission_denies_access_without_permission(
        self,
        mock_service_cls
    ):
        """Test que el decorador deniega acceso cuando el usuario no tiene el permiso."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_user = Mock()
        mock_user.id = 1
        mock_user.company_id = 1

        mock_instance = mock_service_cls.return_value
        mock_instance.check_permission = AsyncMock(return_value=False)

        decorator = require_permission("nonexistent.permission")
        decorated_func = decorator(self.mock_endpoint)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await decorated_func(
                session=mock_session,
                current_user=mock_user
            )

        assert exc_info.value.status_code == 403
        assert "Permiso denegado" in exc_info.value.detail

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_require_permission_denies_access_without_user(self):
        """Test que el decorador deniega acceso cuando no hay usuario autenticado."""
        # Arrange
        # No necesitamos mock de session aqui porque falla antes
        mock_session = AsyncMock(spec=AsyncSession)
        
        decorator = require_permission("any.permission")
        decorated_func = decorator(self.mock_endpoint)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await decorated_func(
                session=mock_session,
                current_user=None
            )

        assert exc_info.value.status_code == 401
        # assert "No autenticado" in exc_info.value.detail

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_require_permission_denies_access_without_session(self):
        """Test que el decorador deniega acceso cuando no hay sesión de BD."""
        # Arrange
        mock_user = Mock()
        mock_user.id = 1
        
        decorator = require_permission("any.permission")
        decorated_func = decorator(self.mock_endpoint)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await decorated_func(
                session=None,
                current_user=mock_user
            )

        # assert "sesión de BD no disponible" in exc_info.value.detail
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.core.permissions.PermissionService')
    async def test_require_any_permission_grants_access_with_one_valid_permission(
        self,
        mock_service_cls
    ):
        """Test que permite acceso si el usuario tiene AL MENOS uno de los permisos requeridos."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_user = Mock()
        mock_user.id = 1
        mock_user.company_id = 1

        mock_instance = mock_service_cls.return_value
        
        # side_effect: si permission_code es "test.permission", return True.
        async def side_effect(user_id, permission_code, company_id):
            return permission_code == "test.permission"
            
        mock_instance.check_permission = AsyncMock(side_effect=side_effect)

        decorator = require_any_permission(["test.permission", "other.permission"])
        decorated_func = decorator(self.mock_endpoint)

        # Act
        result = await decorated_func(
            session=mock_session,
            current_user=mock_user
        )

        # Assert
        assert result == "success"

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.core.permissions.PermissionService')
    async def test_require_any_permission_denies_access_without_any_permission(
        self,
        mock_service_cls
    ):
        """Test que deniega acceso si el usuario no tiene ninguno de los permisos requeridos."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_user = Mock()
        mock_user.id = 1
        mock_user.company_id = 1

        mock_instance = mock_service_cls.return_value
        mock_instance.check_permission = AsyncMock(return_value=False)

        decorator = require_any_permission(["nonexistent.perm1", "nonexistent.perm2"])
        decorated_func = decorator(self.mock_endpoint)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await decorated_func(
                session=mock_session,
                current_user=mock_user
            )

        assert exc_info.value.status_code == 403
        assert "se requiere uno de" in exc_info.value.detail

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.core.permissions.PermissionService')
    async def test_require_all_permissions_grants_access_with_all_permissions(
        self,
        mock_service_cls
    ):
        """Test que permite acceso solo si el usuario tiene TODOS los permisos requeridos."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_user = Mock()
        mock_user.id = 1
        mock_user.company_id = 1

        mock_instance = mock_service_cls.return_value
        mock_instance.check_permission = AsyncMock(return_value=True)

        # Solo requiere el permiso que tiene
        decorator = require_all_permissions(["test.permission"])
        decorated_func = decorator(self.mock_endpoint)

        # Act
        result = await decorated_func(
            session=mock_session,
            current_user=mock_user
        )

        # Assert
        assert result == "success"

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.core.permissions.PermissionService')
    async def test_require_all_permissions_denies_access_missing_one_permission(
        self,
        mock_service_cls
    ):
        """Test que deniega acceso si falta al menos uno de los permisos requeridos."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_user = Mock()
        mock_user.id = 1
        mock_user.company_id = 1

        mock_instance = mock_service_cls.return_value
        # Mock behavior: True for 'test.permission', False for 'missing.permission'
        async def side_effect(user_id, permission_code, company_id):
            return permission_code == "test.permission"

        mock_instance.check_permission = AsyncMock(side_effect=side_effect)

        # Requiere un permiso que tiene y otro que no
        decorator = require_all_permissions(["test.permission", "missing.permission"])
        decorated_func = decorator(self.mock_endpoint)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await decorated_func(
                session=mock_session,
                current_user=mock_user
            )

        assert exc_info.value.status_code == 403
        assert "se requieren todos estos permisos" in exc_info.value.detail

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_decorator_preserves_function_metadata(self):
        """Test que los decoradores preservan los metadatos de la función original."""
        # Arrange
        decorator = require_permission("test.permission")
        decorated_func = decorator(self.mock_endpoint)

        # Assert
        assert decorated_func.__name__ == "mock_endpoint"
        assert decorated_func.__doc__ == "Mock endpoint for testing"

    async def mock_endpoint(self, session: AsyncSession, current_user: User):
        """Mock endpoint for testing"""
        return "success"

    async def mock_endpoint_with_metadata(self, session: AsyncSession, current_user: User):
        """Mock endpoint for testing"""
        return "success"
