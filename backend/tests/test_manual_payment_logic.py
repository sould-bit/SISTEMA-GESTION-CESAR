
import asyncio
import sys
import os
from decimal import Decimal
from datetime import datetime

# Add backend to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine

# Import Models
from app.models.user import User
from app.models.company import Company
from app.models.branch import Branch
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.product import Product

# Import Service and Schemas
from app.services.payment_service import PaymentService
from app.schemas.payment import PaymentCreate

# Setup in-memory SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def run_test():
    print("🚀 Iniciando Test Manual de Pagos (DB: Memory)...")
    await init_db()

    async with async_session() as session:
        # 1. Setup Data (Company, Branch, User, Order)
        print("📝 Creando datos de prueba...")
        company = Company(name="Test Corp", slug="test-corp")
        session.add(company)
        await session.flush()

        branch = Branch(name="Main Branch", company_id=company.id, address="123 Test St", phone="555-0000", code="BR-1")
        session.add(branch)
        await session.flush()
        
        user = User(username="testuser", email="test@example.com", hashed_password="pw", company_id=company.id, role="admin", is_active=True)
        session.add(user)
        
        # Order with total 100
        order = Order(
            company_id=company.id,
            branch_id=branch.id,
            order_number="ORD-001",
            status=OrderStatus.PENDING,
            subtotal=Decimal("80.00"),
            tax_total=Decimal("20.00"),
            total=Decimal("100.00")
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        
        print(f"✅ Orden creada: ID={order.id}, Total={order.total}, Status={order.status}")

        # 2. Test Payment Service
        service = PaymentService(session)
        
        # Test 1: Partial Payment
        print("\n🧪 Test 1: Pago Parcial (50.00)")
        payment_data = PaymentCreate(
            order_id=order.id,
            amount=Decimal("50.00"),
            method=PaymentMethod.CASH
        )
        payment1 = await service.process_payment(payment_data, user.id, company.id)
        print(f"   Payment ID: {payment1.id} - Status: {payment1.status}")
        
        # Reload Order
        await session.refresh(order)
        print(f"   Order Status: {order.status} (Esperado: pending)")
        assert order.status == OrderStatus.PENDING

        # Test 2: Complete Payment
        print("\n🧪 Test 2: Completar Pago (50.00)")
        payment_data2 = PaymentCreate(
            order_id=order.id,
            amount=Decimal("50.00"),
            method=PaymentMethod.CARD
        )
        payment2 = await service.process_payment(payment_data2, user.id, company.id)
        
        # Reload Order
        await session.refresh(order)
        print(f"   Order Status: {order.status} (Esperado: confirmed)")
        if order.status == OrderStatus.CONFIRMED:
            print("🎉 ÉXITO: La orden se actualizó a CONFIRMED automáticamente.")
        else:
            print(f"❌ FALLO: La orden sigue en {order.status}")

    print("\n✅ Test Completado.")

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(run_test())
    except Exception as e:
        print(f"❌ Error CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
