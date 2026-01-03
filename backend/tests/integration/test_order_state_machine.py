import pytest
from httpx import AsyncClient
from sqlmodel import select, func
from app.models.order import Order, OrderStatus
from app.models.order_audit import OrderAudit

# Use the same fixture logic as test_order_api.py
# Assuming conftest.py provides test_client and user_token

@pytest.mark.asyncio
async def test_order_state_transitions_success(test_client: AsyncClient, user_token: dict, test_product, test_branch):
    """
    Verifica el flujo completo de vida de un pedido:
    PENDING -> CONFIRMED -> PREPARING -> READY -> DELIVERED
    """
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # 1. Crear Pedido (PENDING por defecto)
    payload = {
        "branch_id": test_branch.id,
        "items": [
            {"product_id": test_product.id, "quantity": 1}
        ]
    }
    response = await test_client.post("/orders/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    order_id = data["id"]
    assert data["status"] == "pending"

    # 2. Transición PENDING -> CONFIRMED
    response = await test_client.patch(
        f"/orders/{order_id}/status",
        json={"status": "confirmed"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"

    # Verificar Auditoría - OMITIDO en tests integrados por concurrencia SQLite
    # result = await db_session.execute(select(OrderAudit).where(OrderAudit.order_id == order_id))
    # ...
    
    # 3. Transición CONFIRMED -> PREPARING

    # 3. Transición CONFIRMED -> PREPARING
    response = await test_client.patch(
        f"/orders/{order_id}/status",
        json={"status": "preparing"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "preparing"

    # 4. Transición PREPARING -> READY
    response = await test_client.patch(
        f"/orders/{order_id}/status",
        json={"status": "ready"},
        headers=headers
    )
    assert response.status_code == 200

    # 5. Transición READY -> DELIVERED
    response = await test_client.patch(
        f"/orders/{order_id}/status",
        json={"status": "delivered"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "delivered"


@pytest.mark.asyncio
async def test_invalid_state_transition(test_client: AsyncClient, user_token: dict, test_product, test_branch):
    """
    Verifica que se rechacen transiciones inválidas (Grafo estricto).
    Ej: PENDING -> DELIVERED (Saltándose pasos)
    """
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # 1. Crear Pedido
    payload = {
        "branch_id": test_branch.id,
        "items": [{"product_id": test_product.id, "quantity": 1}]
    }
    response = await test_client.post("/orders/", json=payload, headers=headers)
    order_id = response.json()["id"]

    # 2. Intentar PENDING -> DELIVERED
    response = await test_client.patch(
        f"/orders/{order_id}/status",
        json={"status": "delivered"},
        headers=headers
    )
    assert response.status_code == 400
    assert "no es permitida" in response.json()["detail"]


@pytest.mark.asyncio
async def test_idempotent_transition(test_client: AsyncClient, user_token: dict, test_product, test_branch):
    """
    Verifica que pedir el mismo cambio de estado dos veces retorne 200 OK (sin error).
    """
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # 1. Crear Pedido
    payload = {
        "branch_id": test_branch.id,
        "items": [{"product_id": test_product.id, "quantity": 1}]
    }
    response = await test_client.post("/orders/", json=payload, headers=headers)
    order_id = response.json()["id"]

    # 2. PENDING -> CONFIRMED (Primera vez)
    response = await test_client.patch(
        f"/orders/{order_id}/status",
        json={"status": "confirmed"},
        headers=headers
    )
    assert response.status_code == 200

    # 3. PENDING -> CONFIRMED (Segunda vez, estado actual ya es CONFIRMED)
    response = await test_client.patch(
        f"/orders/{order_id}/status",
        json={"status": "confirmed"},
        headers=headers
    )
    assert response.status_code == 200
    # No debería haber cambiado nada, idealmente revisar logs si fuese posible para ver "Idempotente"

@pytest.mark.asyncio
async def test_terminal_state_reopen_forbidden(test_client: AsyncClient, user_token: dict, test_product, test_branch):
    """
    Verifica que no se pueda reabrir un pedido CANCELLED.
    """
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # 1. Crear Pedido
    payload = {
        "branch_id": test_branch.id,
        "items": [{"product_id": test_product.id, "quantity": 1}]
    }
    res = await test_client.post("/orders/", json=payload, headers=headers)
    order_id = res.json()["id"]

    # 2. Cancelar (PENDING -> CANCELLED es válido)
    res_cancel = await test_client.patch(
        f"/orders/{order_id}/status",
        json={"status": "cancelled"},
        headers=headers
    )
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "cancelled"

    # 3. Intentar reabrir (CANCELLED -> PENDING/CONFIRMED)
    res = await test_client.patch(
        f"/orders/{order_id}/status",
        json={"status": "pending"},
        headers=headers
    )
    assert res.status_code == 400
