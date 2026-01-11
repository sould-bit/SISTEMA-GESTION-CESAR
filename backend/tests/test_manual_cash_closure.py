
import asyncio
import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta

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
from app.models.cash_closure import CashClosure, CashClosureStatus

# Import Service
from app.services.cash_service import CashService

# Setup in-memory SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def run_test():
    print("🚀 Iniciando Test Manual de Cierre de Caja (DB: Memory)...")
    await init_db()

    async with async_session() as session:
        # 1. Setup Data
        print("📝 Creando datos base...")
        company = Company(name="Test Corp", slug="test-corp")
        session.add(company)
        await session.flush()

        branch = Branch(name="Main Branch", company_id=company.id, address="123", phone="555", code="BR-1")
        session.add(branch)
        await session.flush()
        
        user = User(username="cashier", email="cashier@test.com", hashed_password="pw", company_id=company.id, branch_id=branch.id)
        session.add(user)
        session.add(Order(company_id=company.id, branch_id=branch.id, order_number="ORD-1", total=Decimal("300.00")))
        await session.commit()
        await session.refresh(user)

        # 2. Open Register
        print("\n🔓 Paso 1: Abrir Caja")
        cash_service = CashService(session)
        closure = await cash_service.open_register(user, initial_cash=Decimal("500.00"))
        print(f"   Caja abierta ID: {closure.id}, Base: {closure.initial_cash}")
        
        # 3. Simulate Payments (After Open)
        print("\n💸 Paso 2: Registrar Pagos")
        # Payment 1: Cash 100
        p1 = Payment(company_id=company.id, branch_id=branch.id, order_id=1, amount=Decimal("100.00"), method=PaymentMethod.CASH, created_at=datetime.utcnow(), user_id=user.id)
        session.add(p1)
        
        # Payment 2: Card 50
        p2 = Payment(company_id=company.id, branch_id=branch.id, order_id=1, amount=Decimal("50.00"), method=PaymentMethod.CARD, created_at=datetime.utcnow(), user_id=user.id)
        session.add(p2)
        
        # Payment 3: Nequi 20
        p3 = Payment(company_id=company.id, branch_id=branch.id, order_id=1, amount=Decimal("20.00"), method=PaymentMethod.NEQUI, created_at=datetime.utcnow(), user_id=user.id)
        session.add(p3)
        
        await session.commit()
        print("   Pagos registrados: Cash=100, Card=50, Nequi=20")
        
        # 4. Get Current Status
        print("\n👀 Paso 3: Consultar Estado Actual (Pre-Cierre)")
        totals = await cash_service.calculate_current_totals(closure)
        print(f"   Totales Calculados: {totals}")
        assert totals["cash"] == Decimal("100.00")
        assert totals["card"] == Decimal("50.00")
        assert totals["transfer"] == Decimal("20.00") # Nequi should fall into transfer bucket logic if we updated mapper
        # NOTE: My logic in CashService mapped NEQUI to transfer? 
        # Code: elif method in [PaymentMethod.TRANSFER, PaymentMethod.NEQUI, PaymentMethod.DAVIPLATA]: totals["transfer"] += total
        # YES.
        
        # 5. Close Register with Discrepancy
        print("\n🔒 Paso 4: Cerrar Caja (Con Diferencia)")
        # Real Cash: 600 (500 base + 100 ventas) - ok
        # Real Card: 50 (ok)
        # Real Transfer: 15 (Faltan 5 pesos, tal vez comision?)
        
        real_cash = Decimal("600.00") # 500 Initial + 100 Sales
        real_card = Decimal("50.00")
        real_transfer = Decimal("15.00") # Expected 20
        
        closed = await cash_service.close_register(closure.id, real_cash, real_card, real_transfer, notes="Faltan 5 en Nequi")
        
        print(f"   Cierre ID: {closed.id}, Estado: {closed.status}")
        print(f"   Esperado Transfer: {closed.expected_transfer}")
        print(f"   Real Transfer: {closed.real_transfer}")
        print(f"   Diferencia Global: {closed.difference}")
        
        assert closed.status == CashClosureStatus.CLOSED
        assert closed.expected_transfer == Decimal("20.00")
        assert closed.difference == Decimal("-5.00")
        
        print("\n✅ Test de Cierre de Caja Exitoso!")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_test())
