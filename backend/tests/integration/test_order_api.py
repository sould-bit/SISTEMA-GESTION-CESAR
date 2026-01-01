import pytest
from httpx import AsyncClient
from fastapi import status
from decimal import Decimal

from app.models.order import OrderStatus
from app.models.product import Product

@pytest.mark.asyncio
async def test_create_order_success(
    db_session,
    test_client: AsyncClient,
    test_company,
    test_branch,
    user_token: str,
    test_product # Using existing fixture from conftest
):
    """
    ✅ TEST: Crear pedido exitosamente via API
    """
    # Arrange
    order_data = {
        "branch_id": test_branch.id,
        "customer_notes": "Pedido API Test",
        "items": [
            {
                "product_id": test_product.id,
                "quantity": 2,
                "notes": "Sin cebolla"
            }
        ],
        "payments": [
            {
                "amount": "56.10", # 2 * 25.50 + 10% tax
                "method": "cash"
            }
        ]
    }

    # Act
    # Asegurar que el token tenga el branch_id correcto si se validara? 
    # Por ahora el token mockeado en conftest tiene branch_id=1 hardcoded, 
    # pero test_branch podría tener otro ID.
    # Si get_current_active_user no valida branch_id vs token, estamos bien.
    
    response = await test_client.post(
        "/orders/",
        json=order_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    
    assert data["order_number"].startswith("PED-") # O el prefijo configurado
    assert data["company_id"] == test_company.id
    assert data["branch_id"] == test_branch.id
    assert data["status"] == OrderStatus.CONFIRMED # Porque pagamos todo
    
    # Validar totales
    assert Decimal(str(data["subtotal"])) == Decimal("51.00")
    assert Decimal(str(data["tax_total"])) == Decimal("5.10")
    assert Decimal(str(data["total"])) == Decimal("56.10")
    
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == test_product.id
    assert Decimal(str(data["items"][0]["quantity"])) == Decimal("2")

@pytest.mark.asyncio
async def test_create_order_invalid_product(
    test_client: AsyncClient,
    test_branch,
    user_token: str
):
    """
    ❌ TEST: Intentar crear pedido con producto inexistente
    """
    order_data = {
        "branch_id": test_branch.id,
        "items": [
            {
                "product_id": 999999,
                "quantity": 1
            }
        ]
    }
    
    response = await test_client.post(
        "/orders/",
        json=order_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Productos no válidos" in response.json()["detail"]
