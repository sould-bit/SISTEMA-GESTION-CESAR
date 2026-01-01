import pytest
from httpx import AsyncClient
from sqlmodel import select, Session
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.order_counter import OrderCounter
from app.services.order_counter_service import OrderCounterService

@pytest.mark.asyncio
async def test_order_counter_increments(db_session: Session, test_company, test_branch):
    """
    Verifica que el servicio de contadores incremente correctamente
    y genere formatos esperados (PED-00001, etc.)
    """
    service = OrderCounterService(db_session)
    
    # 1. Primer número para la sucursal
    num_1 = await service.get_next_number(test_company.id, test_branch.id, "general")
    assert num_1 == "PED-00001"
    
    # 2. Segundo número
    num_2 = await service.get_next_number(test_company.id, test_branch.id, "general")
    assert num_2 == "PED-00002"
    
    # 3. Validar en BD
    result = await db_session.execute(
        select(OrderCounter).where(
            OrderCounter.branch_id == test_branch.id,
            OrderCounter.counter_type == "general"
        )
    )
    counter = result.scalar_one()
    assert counter.last_value == 2

@pytest.mark.asyncio
async def test_order_creation_persistence(db_session: Session, test_company, test_branch):
    """
    Verifica que podemos crear un pedido con sus items y persistirlo.
    """
    # 1. Crear pedido básico manualmente (sin servicio completo aún)
    order = Order(
        company_id=test_company.id,
        branch_id=test_branch.id,
        order_number="TEST-001",
        status=OrderStatus.PENDING,
        subtotal=100.00,
        total=100.00
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    
    assert order.id is not None
    assert order.status == OrderStatus.PENDING
    assert order.order_number == "TEST-001"
    
    # 2. Verificar índices (implícito si no falla query)
    result = await db_session.execute(
        select(Order).where(Order.company_id == test_company.id)
    )
    orders = result.scalars().all()
    assert len(orders) == 1

@pytest.mark.asyncio
async def test_order_counter_isolation_per_branch(db_session: Session, test_company, test_branch):
    """
    Verifica que los contadores sean independientes por sucursal.
    """
    # Crear segunda sucursal dummy
    from app.models.branch import Branch
    branch_2 = Branch(company_id=test_company.id, code="BR-2", name="Sucursal 2", address="Calle Falsa")
    db_session.add(branch_2)
    # Necesitamos commit para obtener ID si es autoincrement, o flush
    await db_session.commit() 
    await db_session.refresh(branch_2)

    service = OrderCounterService(db_session)
    
    # Generar para Brach 1 (debería ser 00003 si el tests anterior corrió, o 00001 si es nueva sesión limpia)
    # En test integration DB suele limpiarse. Asumimos limpia.
    val_b1 = await service.get_next_number(test_company.id, test_branch.id, "delivery")
    assert val_b1 == "PED-00001"
    
    # Generar para Branch 2
    val_b2 = await service.get_next_number(test_company.id, branch_2.id, "delivery")
    assert val_b2 == "PED-00001" # Debe empezar en 1 también
    
    # Avanzar Branch 1
    val_b1_next = await service.get_next_number(test_company.id, test_branch.id, "delivery")
    assert val_b1_next == "PED-00002"
    
    # Branch 2 sigue igual?
    result = await db_session.execute(
        select(OrderCounter).where(
            OrderCounter.branch_id == branch_2.id, 
            OrderCounter.counter_type == "delivery"
        )
    )
    counter_b2 = result.scalar_one()
    assert counter_b2.last_value == 1
