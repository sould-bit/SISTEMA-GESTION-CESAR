
import pytest
from httpx import AsyncClient
from fastapi import status
from app.models.user import User
from decimal import Decimal

@pytest.mark.asyncio
@pytest.mark.integration
class TestCategoryRouter:
    """🧪 Pruebas de integración para endpoints de categorías."""

    async def test_create_category_success(
        self,
        test_client: AsyncClient,
        test_user: User,
        test_company,
        user_token: str
    ):
        """
        ✅ TEST: Crear categoría exitosamente
        """
        category_data = {
            "name": "Bebidas Calientes",
            "description": "Cafés y tes",
            "is_active": True
        }

        response = await test_client.post(
            "/categories/",
            json=category_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Bebidas Calientes"
        assert data["company_id"] == test_company.id
        assert data["is_active"] is True

    async def test_list_categories(
        self,
        test_client: AsyncClient,
        test_user: User,
        test_company,
        test_category, # Existing fixture category
        user_token: str
    ):
        """
        ✅ TEST: Listar categorías
        """
        # Create another category to ensure list has multiple
        response = await test_client.post(
            "/categories/",
            json={"name": "Postres", "description": "Dulces"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK

        # List
        response = await test_client.get(
            "/categories/",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 2
        names = [c["name"] for c in data]
        assert "Postres" in names
        assert test_category.name in names

    async def test_get_category_by_id(
        self,
        test_client: AsyncClient,
        test_user: User,
        test_category,
        user_token: str
    ):
        """
        ✅ TEST: Obtener categoría por ID
        """
        response = await test_client.get(
            f"/categories/{test_category.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_category.id
        assert data["name"] == test_category.name

    async def test_update_category(
        self,
        test_client: AsyncClient,
        test_user: User,
        test_category,
        user_token: str
    ):
        """
        ✅ TEST: Actualizar categoría
        """
        update_data = {"name": "Categoria Actualizada"}

        response = await test_client.put(
            f"/categories/{test_category.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Categoria Actualizada"
        # Verify persistence

        response = await test_client.get(
            f"/categories/{test_category.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.json()["name"] == "Categoria Actualizada"

    async def test_delete_category(
        self,
        test_client: AsyncClient,
        test_user: User,
        test_category,
        user_token: str
    ):
        """
        ✅ TEST: Eliminar categoría (Soft Delete)
        """
        response = await test_client.delete(
            f"/categories/{test_category.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert f"Categoría '{test_category.name}' eliminada correctamente" in data["message"]

        # Verify it is gone (404 or filtered out)
        # Service logic raises 404 if not found or inactive usually
        response = await test_client.get(
            f"/categories/{test_category.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        # Depending on implementation, get_category_by_id checks NOT is_deleted?
        # Typically soft delete means is_active=False or is_deleted=True
        # Let's assume it returns 404 or inactive.
        # Router: get_category -> service.get_category_by_id

        # If the service filters active, it should be 404.
        # But if it returns the object with is_active=False (Soft Delete), then 200.
        # Based on current service logic (get_category_by_id doesn't filter is_active), it returns 200.
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_active"] is False

    async def test_create_category_duplicate_name(
        self,
        test_client: AsyncClient,
        test_user: User,
        test_category,
        user_token: str
    ):
        """
        ❌ TEST: Error al crear nombre duplicado
        """
        dup_data = {
            "name": test_category.name,
            "description": "Duplicate"
        }

        response = await test_client.post(
            "/categories/",
            json=dup_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Expect 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
