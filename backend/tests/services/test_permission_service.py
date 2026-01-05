"""
Pruebas unitarias para PermissionService.

Estas pruebas validan:
- Verificación de permisos de usuario
- Gestión de permisos por rol
- Cache de permisos (cuando se implemente)
- Validaciones de seguridad multi-tenant
"""

import pytest
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.permission_service import PermissionService
from app.models import Permission, RolePermission, User, Role, PermissionCategory
from sqlalchemy.ext.asyncio import AsyncSession


class TestPermissionService:
    """Pruebas para PermissionService."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.permission_service.get_rbac_cache')
    async def test_check_permission_user_has_permission(
        self,
        mock_get_cache
    ):
        """Test que verifica correctamente cuando un usuario tiene un permiso."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = PermissionService(mock_session)
        service.cache = AsyncMock() # Mock the cache specifically
        
        user = User(id=1, company_id=1, role_id=uuid4())
        permission = Permission(id=uuid4(), code="products.create")
        
        # side_effect for get_user_permissions calls:
        # 1. execute (User)
        # 2. execute (Permissions)
        
        mock_res_user = MagicMock()
        mock_res_user.scalar_one_or_none.return_value = user
        
        mock_res_perms = MagicMock()
        mock_res_perms.scalars.return_value.all.return_value = [permission]
        
        mock_session.execute.side_effect = [mock_res_user, mock_res_perms]

        # Act
        has_permission = await service.check_permission(
            user_id=1,
            permission_code="products.create",
            company_id=1
        )

        # Assert
        assert has_permission is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_permission_user_no_permission(self):
        """Test que verifica correctamente cuando un usuario NO tiene un permiso."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = PermissionService(mock_session)
        service.cache = AsyncMock()
        
        user = User(id=1, company_id=1, role_id=uuid4())
        
        mock_res_user = MagicMock()
        mock_res_user.scalar_one_or_none.return_value = user
        
        mock_res_perms = MagicMock()
        mock_res_perms.scalars.return_value.all.return_value = [] # No permissions
        
        mock_session.execute.side_effect = [mock_res_user, mock_res_perms]

        # Act
        has_permission = await service.check_permission(
            user_id=1,
            permission_code="nonexistent.permission",
            company_id=1
        )

        # Assert
        assert has_permission is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_permission_user_without_role(self):
        """Test que verifica permisos para usuario sin rol asignado."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = PermissionService(mock_session)
        service.cache = AsyncMock()
        
        user = User(id=1, company_id=1, role_id=None)
        
        mock_res_user = MagicMock()
        mock_res_user.scalar_one_or_none.return_value = user
        
        mock_session.execute.return_value = mock_res_user

        # Act
        has_permission = await service.check_permission(
            user_id=1,
            permission_code="any.permission",
            company_id=1
        )

        # Assert
        assert has_permission is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_user_permissions(self):
        """Test que obtiene correctamente los permisos de un usuario."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = PermissionService(mock_session)
        
        rid = uuid4()
        user = User(id=1, company_id=1, role_id=rid)
        permission = Permission(id=uuid4(), code="p1")
        
        mock_res_user = MagicMock()
        mock_res_user.scalar_one_or_none.return_value = user
        
        mock_res_perms = MagicMock()
        mock_res_perms.scalars.return_value.all.return_value = [permission]
        
        mock_session.execute.side_effect = [mock_res_user, mock_res_perms]

        # Act
        permissions = await service.get_user_permissions(user_id=1, company_id=1)

        # Assert
        assert len(permissions) == 1
        assert permissions[0].code == "p1"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_user_permission_codes(self):
        """Test que obtiene solo los códigos de permisos de un usuario."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = PermissionService(mock_session)
        
        user = User(id=1, company_id=1, role_id=uuid4())
        perms = [Permission(code="c1"), Permission(code="c2")]
        
        mock_res_user = MagicMock()
        mock_res_user.scalar_one_or_none.return_value = user
        mock_res_perms = MagicMock()
        mock_res_perms.scalars.return_value.all.return_value = perms
        
        mock_session.execute.side_effect = [mock_res_user, mock_res_perms]

        # Act
        codes = await service.get_user_permission_codes(user_id=1, company_id=1)

        # Assert
        assert codes == ["c1", "c2"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_grant_permission_to_role(self):
        """Test que otorga un permiso a un rol correctamente."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = PermissionService(mock_session)
        service.cache = AsyncMock()
        
        rid = uuid4()
        pid = uuid4()
        
        # side_effect for execute:
        # 1. check if already exists
        mock_res_exists = MagicMock()
        mock_res_exists.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_res_exists

        # Mock refresh to avoid DB access and provide role.company_id
        def mock_refresh(obj):
            obj.role = MagicMock()
            obj.role.company_id = 1
        mock_session.refresh.side_effect = mock_refresh

        # Act
        await service.grant_permission_to_role(
            role_id=rid,
            permission_id=pid,
            granted_by=1
        )

        # Assert
        assert mock_session.add.called
        assert mock_session.commit.called
        assert service.cache.invalidate_role_permissions.called

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_grant_duplicate_permission_fails(self):
        """Test que falla al intentar otorgar un permiso duplicado."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = PermissionService(mock_session)
        service.cache = AsyncMock()
        
        # Simular que ya existe
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = RolePermission(role_id=uuid4(), permission_id=uuid4())
        mock_session.execute.return_value = mock_res

        # Act & Assert
        with pytest.raises(ValueError, match="El permiso ya está asignado"):
            await service.grant_permission_to_role(
                role_id=uuid4(),
                permission_id=uuid4(),
                granted_by=1
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_revoke_permission_from_role(self):
        """Test que revoca un permiso de un rol correctamente."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = PermissionService(mock_session)
        service.cache = AsyncMock()
        
        rid = uuid4()
        pid = uuid4()
        
        # Simular que existe
        role = Role(id=rid, company_id=1)
        rp = RolePermission(role_id=rid, permission_id=pid)
        rp.role = role # Mock relationship
        
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = rp
        mock_session.execute.return_value = mock_res

        # Act
        success = await service.revoke_permission_from_role(
            role_id=rid,
            permission_id=pid
        )

        # Assert
        assert success is True
        assert mock_session.delete.called
        assert mock_session.commit.called
        assert service.cache.invalidate_role_permissions.called

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_revoke_nonexistent_permission(self):
        """Test que maneja correctamente la revocación de permiso inexistente."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = PermissionService(mock_session)
        service.cache = AsyncMock()
        
        # No existe
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_res

        # Act
        success = await service.revoke_permission_from_role(
            role_id=uuid4(),
            permission_id=uuid4()
        )

        # Assert
        assert success is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_role_permissions(self):
        """Test que obtiene permisos de un rol correctamente."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = PermissionService(mock_session)
        
        rid = uuid4()
        perms = [Permission(id=uuid4(), code="p1")]
        
        mock_res = MagicMock()
        mock_res.scalars.return_value.all.return_value = perms
        mock_session.execute.return_value = mock_res

        # Act
        result = await service.get_role_permissions(role_id=rid, company_id=1)

        # Assert
        assert len(result) == 1
        assert result[0].code == "p1"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_permissions(self):
        """Test que lista todos los permisos de una empresa."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = PermissionService(mock_session)
        
        perms = [Permission(id=uuid4(), code="p1")]
        
        mock_res = MagicMock()
        mock_res.scalars.return_value.all.return_value = perms
        mock_session.execute.return_value = mock_res

        # Act
        result = await service.list_permissions(company_id=1)

        # Assert
        assert len(result) == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_permission(self):
        """Test que crea un permiso correctamente."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = PermissionService(mock_session)
        
        # No existe
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_res

        # Act
        permission = await service.create_permission(
            company_id=1,
            category_id=uuid4(),
            code="new.p",
            name="New P",
            resource="res",
            action="act"
        )

        # Assert
        assert permission.code == "new.p"
        assert mock_session.add.called
        assert mock_session.commit.called

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_duplicate_permission_fails(self):
        """Test que falla al crear un permiso con código duplicado."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = PermissionService(mock_session)
        
        # Ya existe
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = Permission(code="dup")
        mock_session.execute.return_value = mock_res

        # Act & Assert
        with pytest.raises(ValueError, match="Ya existe un permiso"):
            await service.create_permission(
                company_id=1,
                category_id=uuid4(),
                code="dup",
                name="Duplicado",
                resource="r",
                action="a"
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_permission(self):
        """Test que actualiza un permiso correctamente."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = PermissionService(mock_session)
        
        pid = uuid4()
        permission = Permission(id=pid, name="Old", is_system=False)
        
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = permission
        mock_session.execute.return_value = mock_res

        # Act
        updated = await service.update_permission(
            permission_id=pid,
            company_id=1,
            name="Updated"
        )

        # Assert
        assert updated.name == "Updated"
        assert mock_session.commit.called

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_system_permission_fails(self):
        """Test que falla al intentar actualizar un permiso del sistema."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = PermissionService(mock_session)
        
        pid = uuid4()
        system_perm = Permission(id=pid, is_system=True)
        
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = system_perm
        mock_session.execute.return_value = mock_res

        # Act & Assert
        with pytest.raises(ValueError, match="No se pueden modificar permisos del sistema"):
            await service.update_permission(
                permission_id=pid,
                company_id=1,
                name="Novo"
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_permission(self):
        """Test que elimina (soft delete) un permiso correctamente."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = PermissionService(mock_session)
        
        pid = uuid4()
        permission = Permission(id=pid, is_active=True, is_system=False)
        
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = permission
        mock_session.execute.return_value = mock_res

        # Act
        success = await service.delete_permission(permission_id=pid, company_id=1)

        # Assert
        assert success is True
        assert permission.is_active is False
        assert mock_session.commit.called
