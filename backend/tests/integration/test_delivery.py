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
# IMPORTS AND FIXTURES
# =============================================================================

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.company import Company
from app.models.branch import Branch
from app.models.user import User
from app.models.role import Role
from app.models.order import Order
from app.utils.security import get_password_hash, create_access_token
from datetime import datetime
import uuid

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
# FIXTURES ESTRATÉGICAS PARA DELIVERY
# =============================================================================

@pytest.fixture
async def delivery_role(session: AsyncSession, test_company: Company):
    """Crea el rol de Domiciliario."""
    idx = uuid.uuid4().hex[:4]
    role = Role(
        name="Domiciliario",
        code=f"DOM{idx}",
        company_id=test_company.id,
        is_system_role=False
    )
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role

@pytest.fixture
async def delivery_user(session: AsyncSession, test_company: Company, test_branch: Branch, delivery_role: Role):
    """Crea un usuario con rol Domiciliario."""
    uid = uuid.uuid4().hex[:4]
    hashed_password = get_password_hash("password123")
    user = User(
        username=f"driver_{uid}",
        email=f"driver_{uid}@test.com",
        full_name=f"Driver {uid}",
        hashed_password=hashed_password,
        company_id=test_company.id,
        branch_id=test_branch.id,
        role_id=delivery_role.id,
        is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@pytest.fixture
async def delivery_auth_headers(test_company: Company, delivery_user: User):
    """Headers de autenticación para el domiciliario."""
    data = {
        "sub": delivery_user.email,
        "company_slug": test_company.slug,
        "company_id": test_company.id,
        "user_id": delivery_user.id,
        "branch_id": delivery_user.branch_id
    }
    token = create_access_token(data=data)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def test_order_delivery(session: AsyncSession, test_company: Company, test_branch: Branch, test_user: User):
    """Crea un pedido listo para entrega."""
    from app.models.order import Order, OrderStatus
    
    order = Order(
        order_number=f"DEL-{uuid.uuid4().hex[:6]}",
        company_id=test_company.id,
        branch_id=test_branch.id,
        user_id=test_user.id,
        customer_id=None,
        delivery_type="delivery",
        status=OrderStatus.READY,
        total=Decimal("50.00"),
        subtotal=Decimal("45.00"),
        tax_total=Decimal("5.00"),
        delivery_address="Calle Falsa 123",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order

# =============================================================================
# TESTS DE FLUJO COMPLETO
# =============================================================================

class TestDeliveryFlow:
    """
    Test de flujo completo:
    1. Iniciar turno
    2. Asignar pedido (como Admin/Cajero)
    3. Marcar recogido (como Domiciliario)
    4. Marcar entregado (como Domiciliario)
    5. Cerrar turno
    """
    
    @pytest.mark.anyio
    async def test_full_delivery_flow(
        self, 
        client: AsyncClient, 
        auth_headers: dict,         # Admin/Cajero
        delivery_auth_headers: dict,# Domiciliario
        test_order_delivery: Order,
        delivery_user: User,
        test_branch: Branch
    ):
        """Flujo completo de entrega verificado."""
        # 1. Iniciar turno (Domiciliario)
        response = await client.post(
            "/delivery/shift/start",
            params={"branch_id": test_branch.id},
            headers=delivery_auth_headers
        )
        assert response.status_code == 200, f"Start Shift Failed: {response.text}"
        shift = response.json()
        assert shift["status"] == "active"
        shift_id = shift["id"]
        
        # 2. Asignar pedido (Admin asigna al Domiciliario)
        response = await client.post(
            f"/delivery/orders/{test_order_delivery.id}/assign",
            json={"driver_id": delivery_user.id},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Assign Driver Failed: {response.text}"
        data = response.json()
        assert data["driver_id"] == delivery_user.id
        assert data["order_id"] == test_order_delivery.id
        
        # 3. Domiciliario ve el pedido en sus órdenes
        response = await client.get("/delivery/my-orders", headers=delivery_auth_headers)
        assert response.status_code == 200, f"Get My Orders Failed: {response.text}"
        my_orders = response.json()["orders"]
        assert len(my_orders) >= 1, f"No orders found for driver. Response: {my_orders}"
        assert my_orders[0]["id"] == test_order_delivery.id
        
        # 4. Marcar recogido (Domiciliario)
        response = await client.post(
            f"/delivery/orders/{test_order_delivery.id}/picked-up",
            headers=delivery_auth_headers
        )
        assert response.status_code == 200, f"Pick Up Failed: {response.text}"
        assert response.json()["new_status"] == "picked_up"
        
        # 5. Marcar entregado (Domiciliario)
        response = await client.post(
            f"/delivery/orders/{test_order_delivery.id}/delivered",
            headers=delivery_auth_headers
        )
        assert response.status_code == 200, f"Delivered Failed: {response.text}"
        assert response.json()["new_status"] == "delivered"
        
        # 6. Cerrar turno (Domiciliario)
        # Asumiendo que recauda el total del pedido
        cash_collected = float(test_order_delivery.total)
        
        response = await client.post(
            "/delivery/shift/close",
            json={"cash_collected": cash_collected, "notes": "Cierre exitoso"},
            headers=delivery_auth_headers
        )
        assert response.status_code == 200, f"Close Shift Failed: {response.text}"
        summary = response.json()
        assert summary["status"] == "closed"
        assert summary["total_delivered"] >= 1
        assert float(summary["total_earnings"]) >= float(test_order_delivery.total)
