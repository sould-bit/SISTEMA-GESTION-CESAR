"""
🧪 TESTS DE INTEGRACIÓN - Category Router

Tests end-to-end para el router de categorías que cubren:
- ✅ GET /categories/ - Listar categorías
- ✅ POST /categories/ - Crear categoría
- ✅ GET /categories/{id} - Obtener categoría específica
- ✅ PUT /categories/{id} - Actualizar categoría
- ✅ DELETE /categories/{id} - Eliminar categoría
- ✅ Validaciones multi-tenant
- ✅ Manejo de errores HTTP

Ejecutar tests:
    pytest backend/tests/routers/test_category_router.py -v
"""

import pytest
from httpx import AsyncClient


class TestCategoryRouter:
    """
    🌐 Tests de integración para Category Router

    Tests completos de endpoints HTTP con autenticación y multi-tenant.
    """

    @pytest.mark.asyncio
    async def test_get_categories_success(self, test_client: AsyncClient, auth_headers: dict):
        """
        ✅ GET /categories/ - Éxito

        Debe retornar lista de categorías de la empresa autenticada.
        """
        # Act
        response = await test_client.get("/categories/", headers=auth_headers)

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # Al menos la categoría de prueba

        # Verificar estructura de respuesta
        for category in data:
            assert "id" in category
            assert "name" in category
            assert "company_id" in category
            assert "is_active" in category
            assert "created_at" in category

    @pytest.mark.asyncio
    async def test_get_categories_no_auth(self, test_client: AsyncClient):
        """
        ❌ GET /categories/ - Sin autenticación

        Debe retornar 401 Unauthorized.
        """
        # Act
        response = await test_client.get("/categories/")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_category_success(self, test_client: AsyncClient, auth_headers: dict):
        """
        ✅ POST /categories/ - Éxito

        Debe crear categoría correctamente.
        """
        # Arrange
        category_data = {
            "name": "Nueva Categoría API",
            "description": "Creada desde API test",
            "is_active": True
        }

        # Act
        response = await test_client.post("/categories/", json=category_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == category_data["name"]
        assert data["description"] == category_data["description"]
        assert data["is_active"] == category_data["is_active"]
        assert "id" in data
        assert "company_id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_category_duplicate_name(self, test_client: AsyncClient, auth_headers: dict):
        """
        ❌ POST /categories/ - Nombre duplicado

        Debe fallar al crear categoría con nombre existente.
        """
        # Arrange - Crear primera categoría
        category_data = {
            "name": "Categoría Duplicada",
            "description": "Primera versión",
            "is_active": True
        }

        # Crear primera
        response1 = await test_client.post("/categories/", json=category_data, headers=auth_headers)
        assert response1.status_code == 200

        # Intentar crear segunda con mismo nombre
        category_data["description"] = "Segunda versión"

        # Act
        response2 = await test_client.post("/categories/", json=category_data, headers=auth_headers)

        # Assert
        assert response2.status_code == 400

        data = response2.json()
        assert "detail" in data
        assert "Ya existe una categoría" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_category_validation_error(self, test_client: AsyncClient, auth_headers: dict):
        """
        ❌ POST /categories/ - Datos inválidos

        Debe validar campos requeridos.
        """
        # Arrange - Datos incompletos
        invalid_data = {
            "description": "Sin nombre",  # Falta name
            "is_active": True
        }

        # Act
        response = await test_client.post("/categories/", json=invalid_data, headers=auth_headers)

        # Assert
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_category_by_id_success(self, test_client: AsyncClient, auth_headers: dict):
        """
        ✅ GET /categories/{id} - Éxito

        Debe retornar categoría específica.
        """
        # Primero crear una categoría
        category_data = {
            "name": "Categoría Específica",
            "description": "Para test de GET by ID",
            "is_active": True
        }

        create_response = await test_client.post("/categories/", json=category_data, headers=auth_headers)
        assert create_response.status_code == 200

        category_id = create_response.json()["id"]

        # Act
        response = await test_client.get(f"/categories/{category_id}", headers=auth_headers)

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == category_id
        assert data["name"] == category_data["name"]
        assert data["description"] == category_data["description"]

    @pytest.mark.asyncio
    async def test_get_category_by_id_not_found(self, test_client: AsyncClient, auth_headers: dict):
        """
        ❌ GET /categories/{id} - No encontrada

        Debe retornar 404 para ID inexistente.
        """
        # Act
        response = await test_client.get("/categories/99999", headers=auth_headers)

        # Assert
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "no encontrada" in data["detail"]

    @pytest.mark.asyncio
    async def test_update_category_success(self, test_client: AsyncClient, auth_headers: dict):
        """
        ✅ PUT /categories/{id} - Éxito

        Debe actualizar categoría correctamente.
        """
        # Crear categoría
        category_data = {
            "name": "Categoría Original",
            "description": "Descripción original",
            "is_active": True
        }

        create_response = await test_client.post("/categories/", json=category_data, headers=auth_headers)
        category_id = create_response.json()["id"]

        # Actualizar
        update_data = {
            "name": "Categoría Actualizada",
            "description": "Descripción actualizada"
        }

        # Act
        response = await test_client.put(f"/categories/{category_id}", json=update_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == category_id
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["is_active"] == True  # No cambió

    @pytest.mark.asyncio
    async def test_update_category_not_found(self, test_client: AsyncClient, auth_headers: dict):
        """
        ❌ PUT /categories/{id} - No encontrada

        Debe retornar 404 para ID inexistente.
        """
        update_data = {"name": "Nuevo nombre"}

        # Act
        response = await test_client.put("/categories/99999", json=update_data, headers=auth_headers)

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_category_duplicate_name(self, test_client: AsyncClient, auth_headers: dict):
        """
        ❌ PUT /categories/{id} - Nombre duplicado

        Debe fallar al actualizar con nombre que ya existe.
        """
        # Crear dos categorías
        cat1_data = {"name": "Categoría 1", "description": "Primera", "is_active": True}
        cat2_data = {"name": "Categoría 2", "description": "Segunda", "is_active": True}

        cat1_response = await test_client.post("/categories/", json=cat1_data, headers=auth_headers)
        cat2_response = await test_client.post("/categories/", json=cat2_data, headers=auth_headers)

        cat1_id = cat1_response.json()["id"]

        # Intentar actualizar cat1 con nombre de cat2
        update_data = {"name": "Categoría 2"}

        # Act
        response = await test_client.put(f"/categories/{cat1_id}", json=update_data, headers=auth_headers)

        # Assert
        assert response.status_code == 400

        data = response.json()
        assert "Ya existe una categoría" in data["detail"]

    @pytest.mark.asyncio
    async def test_delete_category_success(self, test_client: AsyncClient, auth_headers: dict):
        """
        ✅ DELETE /categories/{id} - Éxito

        Debe eliminar categoría (soft delete).
        """
        # Crear categoría
        category_data = {
            "name": "Categoría a Eliminar",
            "description": "Será eliminada",
            "is_active": True
        }

        create_response = await test_client.post("/categories/", json=category_data, headers=auth_headers)
        category_id = create_response.json()["id"]

        # Act
        response = await test_client.delete(f"/categories/{category_id}", headers=auth_headers)

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "eliminada correctamente" in data["message"]

    @pytest.mark.asyncio
    async def test_delete_category_not_found(self, test_client: AsyncClient, auth_headers: dict):
        """
        ❌ DELETE /categories/{id} - No encontrada

        Debe retornar 404 para ID inexistente.
        """
        # Act
        response = await test_client.delete("/categories/99999", headers=auth_headers)

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation_create(self, test_client: AsyncClient, db_session):
        """
        🔒 MULTI-TENANT - Crear en diferentes empresas

        Categorías con mismo nombre pueden existir en empresas diferentes.
        """
        # Crear segunda empresa para simular multi-tenant
        from app.models.company import Company
        from app.models.user import User
        from app.utils.security import get_password_hash

        # Empresa 2
        company2 = Company(
            name="Company 2",
            slug="company-2",
            owner_name="Owner 2",
            owner_email="owner2@test.com",
            plan="trial",
            is_active=True
        )
        db_session.add(company2)

        # Usuario de empresa 2
        user2 = User(
            company_id=company2.id,
            username="user2",
            email="user2@test.com",
            full_name="User 2",
            password_hash=get_password_hash("pass123"),
            role="admin",
            is_active=True
        )
        db_session.add(user2)
        await db_session.commit()

        # Login con usuario de empresa 2
        login_data = {
            "company_slug": "company-2",
            "username": "user2",
            "password": "pass123"
        }

        login_response = await test_client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200

        token2 = login_response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Crear categoría con mismo nombre en ambas empresas
        category_data = {
            "name": "Shared Category Name",
            "description": "En empresa 1",
            "is_active": True
        }

        # Crear en empresa 1
        response1 = await test_client.post("/categories/", json=category_data, headers=auth_headers)
        assert response1.status_code == 200

        # Crear en empresa 2 (mismo nombre)
        category_data["description"] = "En empresa 2"
        response2 = await test_client.post("/categories/", json=category_data, headers=headers2)
        assert response2.status_code == 200  # Debe funcionar

        # Verificar que son diferentes
        data1 = response1.json()
        data2 = response2.json()
        assert data1["id"] != data2["id"]
        assert data1["name"] == data2["name"]  # Mismo nombre
        assert data1["company_id"] != data2["company_id"]  # Empresas diferentes

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation_list(self, test_client: AsyncClient, db_session):
        """
        🔒 MULTI-TENANT - Listar por empresa

        Cada empresa solo ve sus propias categorías.
        """
        # Crear segunda empresa (similar al test anterior)
        from app.models.company import Company
        from app.models.user import User
        from app.utils.security import get_password_hash

        company2 = Company(
            name="Company 2",
            slug="company-2",
            owner_name="Owner 2",
            owner_email="owner2@test.com",
            plan="trial",
            is_active=True
        )
        db_session.add(company2)

        user2 = User(
            company_id=company2.id,
            username="user2",
            email="user2@test.com",
            full_name="User 2",
            password_hash=get_password_hash("pass123"),
            role="admin",
            is_active=True
        )
        db_session.add(user2)
        await db_session.commit()

        # Crear categorías en ambas empresas
        cat1_data = {"name": "Company 1 Exclusive", "description": "Solo en empresa 1", "is_active": True}
        cat2_data = {"name": "Company 2 Exclusive", "description": "Solo en empresa 2", "is_active": True}

        # Empresa 1
        await test_client.post("/categories/", json=cat1_data, headers=auth_headers)

        # Empresa 2
        login_response = await test_client.post("/auth/login", json={
            "company_slug": "company-2",
            "username": "user2",
            "password": "pass123"
        })
        token2 = login_response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        await test_client.post("/categories/", json=cat2_data, headers=headers2)

        # Listar categorías de cada empresa
        list1 = await test_client.get("/categories/", headers=auth_headers)
        list2 = await test_client.get("/categories/", headers=headers2)

        data1 = list1.json()
        data2 = list2.json()

        # Extraer nombres
        names1 = [cat["name"] for cat in data1]
        names2 = [cat["name"] for cat in data2]

        # Assert - Aislamiento completo
        assert "Company 1 Exclusive" in names1
        assert "Company 2 Exclusive" not in names1

        assert "Company 2 Exclusive" in names2
        assert "Company 1 Exclusive" not in names2
