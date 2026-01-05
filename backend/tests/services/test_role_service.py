"""
Pruebas unitarias para RoleService.

Estas pruebas validan:
- CRUD de roles
- Asignación de roles a usuarios
- Clonación de roles
- Validaciones de jerarquía y multi-tenancy
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.role_service import RoleService
from app.models import Role, User, RolePermission
from sqlalchemy.ext.asyncio import AsyncSession


class TestRoleService:
    """Pruebas para RoleService."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_create_role(
        self,
        mock_get_cache
    ):
        """Test que crea un rol correctamente."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_get_cache.return_value = mock_cache
        
        service = RoleService(mock_session)
        
        # Mocking el chequeo de duplicados (no existe)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        role = await service.create_role(
            company_id=1,
            name="Rol de Prueba",
            code="test_role",
            description="Descripción de prueba",
            hierarchy_level=50,
            permission_ids=[uuid4()]
        )

        # Assert
        assert role.name == "Rol de Prueba"
        assert role.code == "test_role"
        assert mock_session.add.call_count >= 2 # Role + RolePermission
        assert mock_session.commit.called

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_create_role_without_permissions(
        self,
        mock_get_cache
    ):
        """Test que crea un rol sin permisos asignados."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = RoleService(mock_session)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        role = await service.create_role(
            company_id=1,
            name="Rol Simple",
            code="simple_role"
        )

        # Assert
        assert role.name == "Rol Simple"
        assert role.code == "simple_role"
        assert mock_session.add.called

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_create_duplicate_role_fails(self, mock_get_cache):
        """Test que falla al crear un rol con código duplicado."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = RoleService(mock_session)
        
        # Simular que ya existe
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = Role(id=uuid4(), code="test_role")
        mock_session.execute.return_value = mock_result

        # Act & Assert
        from app.core.exceptions import RoleAlreadyExistsException
        with pytest.raises(RoleAlreadyExistsException):
            await service.create_role(
                company_id=1,
                name="Rol Duplicado",
                code="test_role"
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_update_role(self, mock_get_cache):
        """Test que actualiza un rol correctamente."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = RoleService(mock_session)
        
        rid = uuid4()
        existing_role = Role(id=rid, name="Old", company_id=1, is_system=False)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_role
        mock_session.execute.return_value = mock_result

        # Act
        updated = await service.update_role(
            role_id=rid,
            company_id=1,
            name="New Name"
        )

        # Assert
        assert updated.name == "New Name"
        assert mock_session.commit.called

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_update_system_role_fails(self, mock_get_cache):
        """Test que falla al intentar actualizar un rol del sistema."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = RoleService(mock_session)
        
        rid = uuid4()
        system_role = Role(id=rid, name="Sys", is_system=True, company_id=1)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = system_role
        mock_session.execute.return_value = mock_result

        # Act & Assert
        from app.core.exceptions import SystemRoleModificationException
        with pytest.raises(SystemRoleModificationException):
            await service.update_role(
                role_id=rid,
                company_id=1,
                name="Nuevo Nombre"
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_delete_role(self, mock_get_cache):
        """Test que elimina (soft delete) un rol correctamente."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = RoleService(mock_session)
        
        rid = uuid4()
        role = Role(id=rid, name="To Delete", is_system=False, is_active=True)
        
        # Mock role search
        mock_res_role = MagicMock()
        mock_res_role.scalar_one_or_none.return_value = role
        
        # Mock user count (0 users)
        mock_res_count = MagicMock()
        mock_res_count.scalar.return_value = 0
        
        mock_session.execute.side_effect = [mock_res_role, mock_res_count]

        # Act
        success = await service.delete_role(role_id=rid, company_id=1)

        # Assert
        assert success is True
        assert role.is_active is False
        assert mock_session.commit.called

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_delete_system_role_fails(self, mock_get_cache):
        """Test que falla al intentar eliminar un rol del sistema."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = RoleService(mock_session)
        rid = uuid4()
        system_role = Role(id=rid, name="Sys", is_system=True)
        
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = system_role
        mock_session.execute.return_value = mock_res

        # Act & Assert
        from app.core.exceptions import SystemRoleModificationException
        with pytest.raises(SystemRoleModificationException):
            await service.delete_role(role_id=rid, company_id=1)

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_delete_role_with_users_fails(self, mock_get_cache):
        """Test que falla al intentar eliminar un rol con usuarios asignados."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = RoleService(mock_session)
        rid = uuid4()
        role = Role(id=rid, name="In Use", is_system=False)
        
        mock_res_role = MagicMock()
        mock_res_role.scalar_one_or_none.return_value = role
        
        mock_res_count = MagicMock()
        mock_res_count.scalar.return_value = 1 # 1 user assigned
        
        mock_session.execute.side_effect = [mock_res_role, mock_res_count]

        # Act & Assert
        from app.core.exceptions import UserRoleAssignmentException
        with pytest.raises(UserRoleAssignmentException):
            await service.delete_role(role_id=rid, company_id=1)

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_get_role(self, mock_get_cache):
        """Test que obtiene un rol correctamente."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = RoleService(mock_session)
        rid = uuid4()
        role = Role(id=rid, name="Found")
        
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = role
        mock_session.execute.return_value = mock_res

        # Act
        result = await service.get_role(role_id=rid, company_id=1)

        # Assert
        assert result.id == rid

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_get_role_with_permissions(self, mock_get_cache):
        """Test que obtiene un rol con sus permisos."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = RoleService(mock_session)
        rid = uuid4()
        pid = uuid4()
        role = Role(id=rid, name="With Perms")
        # Simular relación cargada
        from app.models import RolePermission
        role.role_permissions = [RolePermission(role_id=rid, permission_id=pid)]
        
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = role
        mock_session.execute.return_value = mock_res

        # Act
        result = await service.get_role(role_id=rid, company_id=1, include_permissions=True)

        # Assert
        assert len(result.role_permissions) == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_list_roles(self, mock_get_cache):
        """Test que lista roles de una empresa."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = RoleService(mock_session)
        roles_list = [Role(id=uuid4(), name=f"R{i}") for i in range(3)]
        
        mock_res = MagicMock()
        mock_res.scalars.return_value.all.return_value = roles_list
        mock_session.execute.return_value = mock_res

        # Act
        result = await service.list_roles(company_id=1)

        # Assert
        assert len(result) == 3

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_assign_role_to_user(self, mock_get_cache):
        """Test que asigna un rol a un usuario correctamente."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_get_cache.return_value = mock_cache
        service = RoleService(mock_session)
        
        rid = uuid4()
        role = Role(id=rid, code="admin", hierarchy_level=100)
        user = User(id=1, username="test", company_id=1, role_id=None)
        
        # side_effect para get_role y luego búsqueda del usuario
        mock_res_role = MagicMock()
        mock_res_role.scalar_one_or_none.return_value = role
        
        mock_res_user = MagicMock()
        mock_res_user.scalar_one_or_none.return_value = user
        
        mock_session.execute.side_effect = [mock_res_role, mock_res_user]

        # Act
        updated_user = await service.assign_role_to_user(user_id=1, role_id=rid, company_id=1)

        # Assert
        assert updated_user.role_id == rid
        assert mock_cache.invalidate_user_permissions.called
        assert mock_session.commit.called

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_assign_nonexistent_role_fails(self, mock_get_cache):
        """Test que falla al asignar un rol inexistente."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = RoleService(mock_session)
        
        # Role not found
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_res

        # Act & Assert
        from app.core.exceptions import RoleNotFoundException
        with pytest.raises(RoleNotFoundException):
            await service.assign_role_to_user(user_id=1, role_id=uuid4(), company_id=1)

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_assign_role_to_nonexistent_user_fails(self, mock_get_cache):
        """Test que falla al asignar rol a usuario inexistente."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = RoleService(mock_session)
        
        role = Role(id=uuid4(), code="dev")
        
        mock_res_role = MagicMock()
        mock_res_role.scalar_one_or_none.return_value = role
        
        # User not found
        mock_res_user = MagicMock()
        mock_res_user.scalar_one_or_none.return_value = None
        
        mock_session.execute.side_effect = [mock_res_role, mock_res_user]

        # Act & Assert
        from app.core.exceptions import UserNotFoundException
        with pytest.raises(UserNotFoundException):
            await service.assign_role_to_user(user_id=99, role_id=uuid4(), company_id=1)

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_clone_role(self, mock_get_cache):
        """Test que clona un rol con todos sus permisos."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = RoleService(mock_session)
        rid = uuid4()
        pid = uuid4()
        original = Role(id=rid, name="Template", code="tpl", hierarchy_level=10)
        original.role_permissions = [RolePermission(role_id=rid, permission_id=pid)]
        
        # Protocol:
        # 1. get_role (original)
        # 2. execute (check uniqueness of new code)
        # 3. add role
        # 4. add permission
        
        mock_res_orig = MagicMock()
        mock_res_orig.scalar_one_or_none.return_value = original
        
        mock_res_unique = MagicMock()
        mock_res_unique.scalar_one_or_none.return_value = None
        
        mock_session.execute.side_effect = [mock_res_orig, mock_res_unique]

        # Act
        cloned = await service.clone_role(
            role_id=rid, company_id=1, new_name="Clone", new_code="cln"
        )

        # Assert
        assert cloned.name == "Clone"
        assert cloned.code == "cln"
        assert cloned.hierarchy_level == 10

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_get_role_by_code(self, mock_get_cache):
        """Test que obtiene un rol por código."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = RoleService(mock_session)
        role = Role(id=uuid4(), code="admin")
        
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = role
        mock_session.execute.return_value = mock_res

        # Act
        result = await service.get_role_by_code(code="admin", company_id=1)

        # Assert
        assert result.code == "admin"

    @pytest.mark.asyncio
    @pytest.mark.unit
    @patch('app.services.role_service.get_rbac_cache')
    async def test_get_users_with_role(self, mock_get_cache):
        """Test que obtiene usuarios con un rol específico."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = RoleService(mock_session)
        rid = uuid4()
        users_list = [User(id=1), User(id=2)]
        
        mock_res = MagicMock()
        mock_res.scalars.return_value.all.return_value = users_list
        mock_session.execute.return_value = mock_res

        # Act
        result = await service.get_users_with_role(role_id=rid, company_id=1)

        # Assert
        assert len(result) == 2

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_higher_role_can_inherit_from_lower(self):
        """Un rol superior hereda de uno inferior."""
        role = Role(hierarchy_level=80)
        lower = Role(hierarchy_level=50)
        assert role.can_inherit_from(lower) is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_lower_role_cannot_inherit_from_higher(self):
        """Un rol inferior NO hereda de uno superior."""
        role = Role(hierarchy_level=50)
        higher = Role(hierarchy_level=80)
        assert role.can_inherit_from(higher) is False
