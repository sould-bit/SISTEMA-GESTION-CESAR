import pytest
import socketio
import asyncio
from app.config import settings
from app.utils.security import create_access_token
from datetime import timedelta

# Allow connecting to self
BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_websocket_connect_and_auth():
    """
    Test flow:
    1. Create a valid JWT token.
    2. Connect to Socket.IO server with the token.
    3. Verify connection is accepted.
    4. Verify joining rooms (implicitly via logs or event acknowledgment - explicit can be hard without server support).
    5. Test invalid token rejection.
    """
    
    # 1. Create Token
    token_data = {
        "sub": "1",
        "company_id": 1,
        "branch_id": 1,
        "role": "admin"
    }
    access_token = create_access_token(
        data=token_data, 
        expires_delta=timedelta(minutes=5)
    )
    
    # 2. Connect
    sio = socketio.AsyncClient()
    
    connected = False
    
    @sio.event
    async def connect():
        nonlocal connected
        connected = True
        print("Connected!")
        
    @sio.event
    async def disconnect():
        print("Disconnected!")

    # Connect with Auth Header (or query param as fallback)
    try:
        # Note: python-socketio client sends auth in 'auth' dict
        await sio.connect(
            BASE_URL, 
            auth={'token': access_token},
            wait_timeout=5,
            transports=['websocket', 'polling'] # Force websocket if possible or allow polling
        )
        
        assert connected == True, "Client should be connected"
        assert sio.connected == True
        
        # Keep connection open briefly
        await asyncio.sleep(1)
        
        await sio.disconnect()
        
    except Exception as e:
        pytest.fail(f"WebSocket connection failed: {e}")

@pytest.mark.asyncio
async def test_websocket_invalid_auth():
    """Test connection rejection with bad token"""
    sio = socketio.AsyncClient()
    
    try:
        await sio.connect(
            BASE_URL, 
            auth={'token': "invalid_token_xyz"},
            wait_timeout=2
        )
        # Should NOT reach here
        await sio.disconnect()
        pytest.fail("Should have rejected connection")
    except Exception:
        # Expected failure
        pass
