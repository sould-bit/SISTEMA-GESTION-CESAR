
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.company import Company
from app.models.branch import Branch
from app.models.user import User
from app.utils.security import get_password_hash, verify_password

@pytest.mark.asyncio
async def test_auth_login_flow(client: AsyncClient, session: AsyncSession):
    # 1. Setup User
    company = Company(name="Auth Corp", slug="auth-corp")
    session.add(company)
    await session.flush()
    branch = Branch(name="Main Branch", company_id=company.id, address="123", phone="555", code="BR-1")
    session.add(branch)
    await session.flush()
    
    password = "securepassword"
    hashed = get_password_hash(password)
    user = User(
        username="authuser", 
        email="auth@test.com", 
        hashed_password=hashed, 
        company_id=company.id, 
        branch_id=branch.id,
        is_active=True,
        role="admin"
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    # await session.refresh(user)
    
    # 2. Test Login
    login_data = {
        "username": "auth@test.com",
        "password": "securepassword",
        "company_slug": "auth-corp"
    }
    resp = await client.post("/auth/login", json=login_data)
    
    if resp.status_code != 200:
        print(f"❌ Login Failed: {resp.text}")
        
    assert resp.status_code == 200
    token_data = resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    # 3. Test Protected Route with Token
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Verify /users/me or similar
    resp = await client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    user_data = resp.json()
    assert user_data["email"] == "auth@test.com"

@pytest.mark.asyncio
async def test_password_hashing():
    pw = "secret"
    hashed = get_password_hash(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("wrong", hashed) is False
