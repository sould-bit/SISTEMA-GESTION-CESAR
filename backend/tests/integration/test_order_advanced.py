import pytest
import asyncio
from httpx import AsyncClient
from app.models.order import OrderStatus

@pytest.mark.asyncio
async def test_concurrency_optimistic_locking(test_client: AsyncClient, user_token: str, test_product, test_branch):
    """
    PRUEBA DE ESTRÉS / CONCURRENCIA:
    Simula dos peticiones simultáneas para cambiar el estado de la misma orden.
    Una debe ganar (200 OK) y la otra debe fallar (409 Conflict).
    """
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # 1. Crear orden inicial (Status: PENDING)
    payload = {
        "branch_id": test_branch.id,
        "items": [{"product_id": test_product.id, "quantity": 1}],
        "payments": []
    }
    res_create = await test_client.post("/orders/", json=payload, headers=headers)
    order_id = res_create.json()["id"]

    # 2. Lanzar dos peticiones simultáneas para pasar a 'confirmed'
    # Nota: En SQLite/aiosqlite esto probará si rowcount funciona correctamente.
    task1 = test_client.patch(f"/orders/{order_id}/status", json={"status": "confirmed"}, headers=headers)
    task2 = test_client.patch(f"/orders/{order_id}/status", json={"status": "confirmed"}, headers=headers)
    
    results = await asyncio.gather(task1, task2, return_exceptions=True)
    
    status_codes = [r.status_code for r in results if not isinstance(r, Exception)]
    
    # Una debe ser 200, la otra debe ser 409 (Conflicto)
    # SI EL CÓDIGO ACTUAL TIENE EL BUG, VEREMOS UN 500 EN LUGAR DE 409
    assert 200 in status_codes
    assert 409 in status_codes, f"Se esperaba un 409 Conflict, pero se obtuvo: {status_codes}"

@pytest.mark.asyncio
async def test_rbac_waiter_cannot_cancel_order(test_client: AsyncClient, test_user, test_company, test_product, test_branch):
    """
    VERIFICACIÓN DE ROLES (RBAC):
    Un mesero (WAITER) NO debería poder cancelar una orden (según regla de negocio sugerida).
    """
    from app.utils.security import create_access_token
    
    # Crear token con rol 'waiter'
    token_waiter = create_access_token(data={
        "sub": test_user.username,
        "user_id": test_user.id,
        "company_id": test_company.id,
        "role": "waiter" # Rol restringido
    })
    headers = {"Authorization": f"Bearer {token_waiter}"}

    # 1. Crear orden (El mesero SI puede crear órdenes)
    payload = {
        "branch_id": test_branch.id,
        "items": [{"product_id": test_product.id, "quantity": 1}],
        "payments": []
    }
    res_create = await test_client.post("/orders/", json=payload, headers=headers)
    order_id = res_create.json()["id"]

    # 2. Intentar cancelar (Debería ser denegado 403 Forbidden)
    # SI NO HAY RBAC IMPLEMENTADO, ESTO PASARÁ CON 200 (LO CUAL ES UN HALLAZGO)
    res_patch = await test_client.patch(
        f"/orders/{order_id}/status",
        json={"status": "cancelled"},
        headers=headers
    )
    
    assert res_patch.status_code == 403, f"Se esperaba 403 Forbidden para mesero cancelando, pero se obtuvo {res_patch.status_code}"
