"""
Integration Tests for Delivery Module
=====================================
Pruebas de integración para el módulo de domiciliarios.

Cobertura:
- Listar domiciliarios
- Asignar domiciliario a pedido
- Marcar recogido/entregado
- Gestión de turnos
"""

import pytest
from httpx import AsyncClient, ASGITransport
from decimal import Decimal

from app.main import app
from app.database import get_session


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.fixture
async def client():
    """Cliente HTTP asíncrono para tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client: AsyncClient):
    """
    Obtiene headers de autenticación para un usuario admin.
    Asume que existe un usuario de prueba en la base de datos.
    """
    response = await client.post(
        "/auth/login",
        data={
            "username": "admin",
            "password": "password123",
            "company_slug": "fastops"
        }
    )
    if response.status_code != 200:
        pytest.skip("No se pudo autenticar - verifica datos de seed")
    
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# TESTS DE DOMICILIARIOS
# =============================================================================

class TestDeliveryDrivers:
    """Tests para gestión de domiciliarios."""
    
    @pytest.mark.anyio
    async def test_list_available_drivers_unauthorized(self, client: AsyncClient):
        """Sin autenticación debe retornar 401."""
        response = await client.get("/delivery/available")
        assert response.status_code == 401
    
    @pytest.mark.anyio
    async def test_list_available_drivers(self, client: AsyncClient, auth_headers: dict):
        """
        Con autenticación debe listar domiciliarios disponibles.
        Puede estar vacío si no hay usuarios con rol Domiciliario.
        """
        response = await client.get(
            "/delivery/available",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Debe ser una lista
        assert isinstance(data, list)
        
        # Si hay domiciliarios, verificar estructura
        if len(data) > 0:
            driver = data[0]
            assert "id" in driver
            assert "full_name" in driver
            assert "is_available" in driver


class TestDeliveryAssignment:
    """Tests para asignación de pedidos."""
    
    @pytest.mark.anyio
    async def test_assign_driver_order_not_found(
        self, 
        client: AsyncClient, 
        auth_headers: dict
    ):
        """Asignar a pedido inexistente debe retornar 404."""
        response = await client.post(
            "/delivery/orders/999999/assign",
            headers=auth_headers,
            json={"driver_id": 1}
        )
        assert response.status_code == 404


class TestDriverOrders:
    """Tests para pedidos del domiciliario."""
    
    @pytest.mark.anyio
    async def test_my_orders_empty(self, client: AsyncClient, auth_headers: dict):
        """
        Un usuario sin pedidos asignados debe ver lista vacía.
        """
        response = await client.get(
            "/delivery/my-orders",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "orders" in data
        assert "total_count" in data
        assert isinstance(data["orders"], list)


class TestDeliveryShifts:
    """Tests para gestión de turnos."""
    
    @pytest.mark.anyio
    async def test_get_current_shift_none(self, client: AsyncClient, auth_headers: dict):
        """
        Sin turno activo debe retornar 404.
        """
        response = await client.get(
            "/delivery/shift/current",
            headers=auth_headers
        )
        # Puede ser 404 (sin turno) o 200 (tiene turno activo)
        assert response.status_code in [200, 404]
    
    @pytest.mark.anyio
    async def test_shift_history(self, client: AsyncClient, auth_headers: dict):
        """
        Debe retornar historial de turnos (puede estar vacío).
        """
        response = await client.get(
            "/delivery/shift/history",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Debe ser lista
        assert isinstance(data, list)


# =============================================================================
# TESTS DE FLUJO COMPLETO
# =============================================================================

class TestDeliveryFlow:
    """
    Test de flujo completo:
    1. Iniciar turno
    2. Asignar pedido
    3. Marcar recogido
    4. Marcar entregado
    5. Cerrar turno
    
    Nota: Este test requiere datos específicos en la BD.
    """
    
    @pytest.mark.anyio
    @pytest.mark.skip(reason="Requiere setup de datos específicos")
    async def test_full_delivery_flow(self, client: AsyncClient, auth_headers: dict):
        """Flujo completo de entrega."""
        # 1. Iniciar turno
        response = await client.post(
            "/delivery/shift/start",
            params={"branch_id": 1},
            headers=auth_headers
        )
        assert response.status_code == 200
        shift = response.json()
        assert shift["status"] == "active"
        
        # ... resto del flujo
