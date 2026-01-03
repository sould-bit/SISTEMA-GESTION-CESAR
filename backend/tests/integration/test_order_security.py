import pytest
from httpx import AsyncClient
from app.models.order import OrderStatus
from app.utils.security import create_access_token

@pytest.fixture
def user_token_company_2(test_user_company_2, test_company_2):
    """Generar token para el usuario de la Empresa 2."""
    token_data = {
        "sub": test_user_company_2.username,
        "user_id": test_user_company_2.id,
        "company_id": test_company_2.id,
        "branch_id": 1,
        "role": "admin",
        "username": test_user_company_2.username
    }
    return create_access_token(data=token_data)

@pytest.mark.asyncio
async def test_access_other_company_order_denied(test_client: AsyncClient, user_token: str, user_token_company_2: str, test_product, test_branch):
    """
    Verifica que un usuario de la Empresa A no pueda ver una orden de la Empresa B.
    """
    headers_1 = {"Authorization": f"Bearer {user_token}"}
    headers_2 = {"Authorization": f"Bearer {user_token_company_2}"}

    # 1. Crear orden en Empresa 1
    payload = {
        "branch_id": test_branch.id,
        "items": [{"product_id": test_product.id, "quantity": 2}],
        "payments": []
    }
    res_create = await test_client.post("/orders/", json=payload, headers=headers_1)
    assert res_create.status_code == 201
    order_id = res_create.json()["id"]

    # 2. Intentar acceder desde Empresa 2
    res_get = await test_client.get(f"/orders/{order_id}", headers=headers_2)
    assert res_get.status_code == 404
    assert res_get.json()["detail"] == "Pedido no encontrado"

@pytest.mark.asyncio
async def test_update_other_company_order_denied(test_client: AsyncClient, user_token: str, user_token_company_2: str, test_product, test_branch):
    """
    Verifica que un usuario de la Empresa A no pueda modificar el estado de una orden de la Empresa B.
    """
    headers_1 = {"Authorization": f"Bearer {user_token}"}
    headers_2 = {"Authorization": f"Bearer {user_token_company_2}"}

    # 1. Crear orden en Empresa 1
    payload = {
        "branch_id": test_branch.id,
        "items": [{"product_id": test_product.id, "quantity": 1}],
        "payments": []
    }
    res_create = await test_client.post("/orders/", json=payload, headers=headers_1)
    order_id = res_create.json()["id"]

    # 2. Intentar cambiar estado desde Empresa 2
    res_patch = await test_client.patch(
        f"/orders/{order_id}/status",
        json={"status": "confirmed"},
        headers=headers_2
    )
    assert res_patch.status_code == 404

@pytest.mark.asyncio
async def test_create_order_with_other_company_product_denied(test_client: AsyncClient, user_token: str, test_product_company_2, test_branch):
    """
    Verifica que no se pueda crear una orden usando productos que pertenecen a otra empresa.
    """
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Intentar crearon con producto de Empresa 2 siendo usuario de Empresa 1
    payload = {
        "branch_id": test_branch.id,
        "items": [{"product_id": test_product_company_2.id, "quantity": 1}],
        "payments": []
    }
    
    response = await test_client.post("/orders/", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Productos no válidos" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_order_invalid_data_validation(test_client: AsyncClient, user_token: str, test_product, test_branch):
    """
    Verifica validaciones de datos básicos (casos de borde).
    Nota: Algunas validaciones son por Pydantic (422), otras por lógica (400).
    """
    headers = {"Authorization": f"Bearer {user_token}"}

    # 1. Cantidad negativa (Pydantic debería atraparlo si pusimos gt=0 en el schema, o el servicio)
    payload_neg = {
        "branch_id": test_branch.id,
        "items": [{"product_id": test_product.id, "quantity": -5}],
        "payments": []
    }
    res_neg = await test_client.post("/orders/", json=payload_neg, headers=headers)
    # Si el schema no tiene gt=0, podría fallar en DB o pasar. 
    # Idealmente esperamos error.
    assert res_neg.status_code in [400, 422]
