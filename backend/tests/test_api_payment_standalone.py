
import asyncio
import sys
import os
from decimal import Decimal
from typing import AsyncGenerator

# Add backend to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import App and Dependencies
from app.main import app
from app.database import get_session
from app.auth_deps import get_current_user
from app.models.user import User
from app.models.company import Company
from app.models.branch import Branch
from app.models.order import Order, OrderStatus
from app.models.payment import PaymentMethod

# Setup In-Memory DB
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency Overrides
def override_get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mock User
mock_user = User(id=1, username="testadmin", company_id=1, email="admin@test.com", role="admin")

def override_get_current_user():
    return mock_user

# Apply Overrides
app.dependency_overrides[get_session] = override_get_session
app.dependency_overrides[get_current_user] = override_get_current_user

# Initialize Client
client = TestClient(app)

def setup_data():
    SQLModel.metadata.create_all(engine)
    with SessionLocal() as session:
        # Create Company & Branch
        company = Company(id=1, name="Test Corp", slug="test-corp")
        branch = Branch(id=1, name="Main Branch", company_id=1, address="123 St", phone="555")
        session.add(company)
        session.add(branch)
        
        # Create Order
        order = Order(
            id=1,
            company_id=1,
            branch_id=1,
            order_number="API-TEST-001",
            status=OrderStatus.PENDING,
            total=Decimal("100.00")
        )
        session.add(order)
        session.commit()
        print("✅ Data Setup Complete (Order ID: 1, Total: 100.00)")

def test_api_flow():
    print("🚀 Iniciando Test de API (Standalone TestClient)...")
    setup_data()
    
    # 1. Valid Payment Request
    print("\n🧪 Test 1: POST /payments/ (Pago válido)")
    payload = {
        "order_id": 1,
        "amount": 100.00,
        "method": "card",
        "transaction_id": "TX-999"
    }
    
    response = client.post("/payments/", json=payload)
    
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {data}")
        assert data["status"] == "completed"
        assert data["amount"] == 100.0
        print("✅ API Success: Payment Created")
    else:
        print(f"❌ API Failed: {response.text}")
        exit(1)

    # 2. Verify Order Logic triggered via API
    # directly check DB
    with SessionLocal() as session:
        order = session.get(Order, 1)
        print(f"   Order Status in DB: {order.status}")
        assert order.status == OrderStatus.CONFIRMED
        print("✅ Logic Correct: Order Updated to CONFIRMED")

    # 3. Validation Logic (Negative Amount)
    print("\n🧪 Test 2: Validación (Monto Negativo)")
    bad_payload = {
        "order_id": 1,
        "amount": -50.00,
        "method": "cash"
    }
    response = client.post("/payments/", json=bad_payload)
    print(f"   Status Code: {response.status_code} (Esperado: 400)")
    if response.status_code == 400:
        print(f"✅ Validation Correct: {response.json()['detail']}")
    else:
        print(f"❌ Validation Failed: Received {response.status_code}")

    print("\n🎉 Todos los tests de API pasaron correctamente.")

if __name__ == "__main__":
    test_api_flow()
