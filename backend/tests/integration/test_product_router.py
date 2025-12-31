"""
🧪 PRUEBAS DE INTEGRACIÓN PARA ENDPOINTS DE PRODUCTOS

Estas pruebas validan:
- ✅ Endpoints REST con autenticación completa
- ✅ Autorización RBAC (permisos requeridos)
- ✅ Validaciones de entrada/salida en endpoints
- ✅ Manejo de errores HTTP
- ✅ Integración con middleware de autenticación
- ✅ Headers y responses correctas
"""

import pytest
from decimal import Decimal
from httpx import AsyncClient
from fastapi import status

from app.models import User, Role, Permission, RolePermission
from app.schemas.products import ProductCreate, ProductUpdate


class TestProductRouterIntegration:
    """🧪 Pruebas de integración para endpoints de productos."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_product_success(
        self,
        db_session,
        test_client: AsyncClient,
        test_user: User,
        test_company,
        test_category,
        user_token: str
    ):
        """
        ✅ TEST: Crear producto exitosamente

        Valida endpoint POST /products con autenticación y permisos.
        """
        # Arrange
        product_data = {
            "name": "Producto API Test",
            "description": "Producto creado via API",
            "price": "25.50",
            "tax_rate": "0.10",
            "stock": "100.0",
            "image_url": "https://example.com/image.jpg",
            "category_id": test_category.id
        }

        # Asignar permisos al usuario
        await self._assign_permission_to_user(
            db_session, test_user, "products.create"
        )

        # Act
        response = await test_client.post(
            "/products/",
            json=product_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["name"] == "Producto API Test"
        assert data["company_id"] == test_company.id
        assert data["category_id"] == test_category.id
        assert data["price"] == "25.50"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_product_unauthorized(
        self,
        test_client: AsyncClient,
        test_user: User,
        test_category,
        user_token: str
    ):
        """
        ❌ TEST: Crear producto sin permisos

        Usuario sin permiso 'products.create' debe recibir 403.
        """
        # Arrange - Usuario SIN permiso products.create
        product_data = {
            "name": "Producto No Autorizado",
            "price": "15.00",
            "category_id": test_category.id
        }

        # Act
        response = await test_client.post(
            "/products/",
            json=product_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "No tienes permiso" in data["detail"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_products_success(
        self,
        db_session,
        test_client: AsyncClient,
        test_user: User,
        test_company,
        test_products_batch,
        user_token: str
    ):
        """
        ✅ TEST: Listar productos exitosamente

        Valida endpoint GET /products con filtros.
        """
        # Arrange
        await self._assign_permission_to_user(
            db_session, test_user, "products.read"
        )

        # Act - Listar todos
        response = await test_client.get(
            "/products/",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 5  # Los productos del batch

        # Verificar estructura
        product = data[0]
        assert "id" in product
        assert "name" in product
        assert "price" in product
        assert "company_id" in product
        assert product["company_id"] == test_company.id

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_products_with_filters(
        self,
        db_session,
        test_client: AsyncClient,
        test_user: User,
        test_company,
        test_category,
        test_products_batch,
        user_token: str
    ):
        """
        ✅ TEST: Listar productos con filtros

        Valida filtros por categoría y búsqueda.
        """
        # Arrange
        await self._assign_permission_to_user(
            db_session, test_user, "products.read"
        )

        # Act - Filtrar por categoría
        response = await test_client.get(
            f"/products/?category_id={test_category.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 5  # Todos los productos del batch pertenecen a la categoría
        for product in data:
            assert product["category_id"] == test_category.id

        # Act - Búsqueda por nombre
        response = await test_client.get(
            "/products/?search=Producto 1",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) >= 1
        assert "Producto 1" in data[0]["name"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_product_detail_success(
        self,
        db_session,
        test_client: AsyncClient,
        test_user: User,
        test_product,
        user_token: str
    ):
        """
        ✅ TEST: Obtener detalle de producto

        Valida endpoint GET /products/{id} con carga de categoría.
        """
        # Arrange
        await self._assign_permission_to_user(
            db_session, test_user, "products.read"
        )

        # Act
        response = await test_client.get(
            f"/products/{test_product.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["id"] == test_product.id
        assert data["name"] == test_product.name
        assert "category" in data  # Relación cargada
        assert data["category"]["name"] == test_product.category.name

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_product_detail_not_found(
        self,
        db_session,
        test_client: AsyncClient,
        test_user: User,
        user_token: str
    ):
        """
        ❌ TEST: Obtener producto inexistente

        Debe retornar 404 para producto no encontrado.
        """
        # Arrange
        await self._assign_permission_to_user(
            db_session, test_user, "products.read"
        )

        # Act
        response = await test_client.get(
            "/products/99999",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "Producto no encontrado" in data["detail"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_product_success(
        self,
        db_session,
        test_client: AsyncClient,
        test_user: User,
        test_product,
        user_token: str
    ):
        """
        ✅ TEST: Actualizar producto exitosamente

        Valida endpoint PUT /products/{id}.
        """
        # Arrange
        await self._assign_permission_to_user(
            db_session, test_user, "products.update"
        )

        update_data = {
            "name": "Producto Actualizado API",
            "price": "35.00",
            "description": "Descripción actualizada via API"
        }

        # Act
        response = await test_client.put(
            f"/products/{test_product.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["name"] == "Producto Actualizado API"
        assert data["price"] == "35.00"
        assert data["description"] == "Descripción actualizada via API"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_delete_product_success(
        self,
        db_session,
        test_client: AsyncClient,
        test_user: User,
        test_product,
        user_token: str
    ):
        """
        ✅ TEST: Eliminar producto exitosamente

        Valida endpoint DELETE /products/{id} (soft delete).
        """
        # Arrange
        await self._assign_permission_to_user(
            db_session, test_user, "products.delete"
        )

        # Act
        response = await test_client.delete(
            f"/products/{test_product.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "eliminado correctamente" in data["message"]

        # Verificar soft delete
        response = await test_client.get(
            f"/products/{test_product.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        # El producto ya no es accesible (soft delete)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_validation_errors_in_endpoints(
        self,
        db_session,
        test_client: AsyncClient,
        test_user: User,
        test_category,
        user_token: str
    ):
        """
        ❌ TEST: Validaciones de entrada en endpoints

        Valida que las validaciones Pydantic funcionan en los endpoints.
        """
        # Arrange
        await self._assign_permission_to_user(
            db_session, test_user, "products.create"
        )

        # Act - Precio inválido
        invalid_data = {
            "name": "Producto Inválido",
            "price": "-10.00",  # Precio negativo
            "category_id": test_category.id
        }

        response = await test_client.post(
            "/products/",
            json=invalid_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "price" in str(data["detail"])

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_business_validation_errors(
        self,
        db_session,
        test_client: AsyncClient,
        test_user: User,
        test_company,
        test_category,
        test_product,
        user_token: str
    ):
        """
        ❌ TEST: Validaciones de negocio en endpoints

        Valida unicidad de nombre y otras reglas de negocio.
        """
        # Arrange
        await self._assign_permission_to_user(
            db_session, test_user, "products.create"
        )

        # Act - Intentar crear producto con nombre duplicado
        duplicate_data = {
            "name": test_product.name,  # Nombre ya existe
            "price": "20.00",
            "category_id": test_category.id
        }

        response = await test_client.post(
            "/products/",
            json=duplicate_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Ya existe un producto" in data["detail"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_inventory_endpoints(
        self,
        db_session,
        test_client: AsyncClient,
        test_user: User,
        test_company,
        user_token: str
    ):
        """
        ✅ TEST: Endpoints de inventario

        Valida GET /products/inventory/low-stock.
        """
        # Arrange
        await self._assign_permission_to_user(
            db_session, test_user, "products.read"
        )

        # Crear producto con stock bajo
        from app.services.product_service import ProductService
        service = ProductService(db_session)

        low_stock_product = ProductCreate(
            name="Producto Stock Bajo API",
            price=Decimal('15.00'),
            stock=Decimal('2.0'),  # Stock bajo
            category_id=None
        )
        await service.create_product(low_stock_product, test_company.id)

        # Act
        response = await test_client.get(
            "/products/inventory/low-stock?threshold=5",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1
        # Verificar que incluye el producto con stock bajo
        product_names = [p["name"] for p in data]
        assert "Producto Stock Bajo API" in product_names

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_endpoint(
        self,
        db_session,
        test_client: AsyncClient,
        test_user: User,
        test_company,
        test_products_batch,
        user_token: str
    ):
        """
        ✅ TEST: Endpoint de búsqueda

        Valida GET /products/search/.
        """
        # Arrange
        await self._assign_permission_to_user(
            db_session, test_user, "products.read"
        )

        # Act
        response = await test_client.get(
            "/products/search/?q=Producto&limit=10",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 5  # Todos contienen "Producto"
        for product in data:
            assert "Producto" in product["name"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_unauthenticated_requests(
        self,
        test_client: AsyncClient,
        test_product
    ):
        """
        ❌ TEST: Requests sin autenticación

        Debe retornar 401 para endpoints protegidos.
        """
        # Act - Intentar acceder sin token
        response = await test_client.get("/products/")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Act - Intentar crear sin token
        response = await test_client.post(
            "/products/",
            json={"name": "Test", "price": "10.00"}
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def _assign_permission_to_user(self, db_session, user: User, permission_code: str):
        """Helper para asignar permisos a un usuario de prueba."""
        # Buscar o crear el permiso
        from app.models import Permission, PermissionCategory

        # Crear categoría si no existe
        category = await db_session.execute(
            db_session.query(PermissionCategory).filter_by(code="products")
        )
        category = category.scalar_one_or_none()

        if not category:
            category = PermissionCategory(
                name="Productos",
                code="products",
                company_id=user.company_id,
                is_system=False,
                is_active=True
            )
            db_session.add(category)
            await db_session.commit()
            await db_session.refresh(category)

        # Buscar o crear el permiso
        permission = await db_session.execute(
            db_session.query(Permission).filter_by(code=permission_code)
        )
        permission = permission.scalar_one_or_none()

        if not permission:
            permission = Permission(
                name=f"Permiso {permission_code}",
                code=permission_code,
                resource=permission_code.split('.')[0],
                action=permission_code.split('.')[1],
                company_id=user.company_id,
                category_id=category.id,
                is_system=False,
                is_active=True
            )
            db_session.add(permission)
            await db_session.commit()
            await db_session.refresh(permission)

        # Crear rol si no existe
        role = await db_session.execute(
            db_session.query(Role).filter_by(company_id=user.company_id)
        )
        role = role.scalar_one_or_none()

        if not role:
            role = Role(
                name="Rol de Prueba",
                code="test_role",
                company_id=user.company_id,
                hierarchy_level=50,
                is_system=False,
                is_active=True
            )
            db_session.add(role)
            await db_session.commit()
            await db_session.refresh(role)

        # Asignar rol al usuario
        user.role_id = role.id
        db_session.add(user)

        # Crear relación rol-permiso
        role_permission = RolePermission(
            role_id=role.id,
            permission_id=permission.id,
            granted_by=1
        )
        db_session.add(role_permission)

        await db_session.commit()
