import socketio
from typing import Any, Dict, Optional
import jwt
from app.config import settings
from app.utils.security import ALGORITHM

# Initialize Socket.IO server (Async)
# cors_allowed_origins='*' allows connections from any origin (Dev mode)
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

@sio.event
async def connect(sid: str, environ: Dict[str, Any], auth: Optional[Dict[str, Any]] = None):
    """
    Handle new WebSocket connection.
    Authenticates user via JWT and assigns them to Rooms.
    """
    print(f"SocketIO Connect: {sid}")
    
    # 1. Extract Token
    token = None
    if auth and 'token' in auth:
        token = auth['token']
    else:
        # Fallback: Try query params if client library sends it there
        query_string = environ.get('QUERY_STRING', '')
        if 'token=' in query_string:
            # Simple parsing for query string
            try:
                params = dict(qc.split("=") for qc in query_string.split("&"))
                token = params.get('token')
            except Exception:
                pass

    if not token:
        print(f"Connection rejected: No token provided for {sid}")
        return False  # Reject connection

    # 2. Validate Token
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        company_id: int = payload.get("company_id")
        branch_id: int = payload.get("branch_id")
        role: str = payload.get("role")
        
        if not user_id or not company_id:
            print(f"Connection rejected: Invalid payload for {sid}")
            return False

        # 3. Store Session Data
        await sio.save_session(sid, {
            "user_id": user_id,
            "company_id": company_id,
            "branch_id": branch_id,
            "role": role
        })

        # 4. Join Rooms
        # Global Company Room (e.g., 'company_1')
        await sio.enter_room(sid, f"company_{company_id}")
        
        # Branch Room (e.g., 'branch_2')
        if branch_id:
            await sio.enter_room(sid, f"branch_{branch_id}")
            
            # Role-specific room per branch (e.g., 'role_kitchen_2')
            if role:
                await sio.enter_room(sid, f"role_{role}_{branch_id}")

        print(f"Client {sid} authenticated (User: {user_id}, Company: {company_id}, Role: {role})")
        return True

    except jwt.PyJWTError as e:
        print(f"Connection rejected: Token invalid ({str(e)}) for {sid}")
        return False
    except Exception as e:
        print(f"Connection error: {str(e)}")
        return False

@sio.event
async def disconnect(sid: str):
    """Handle disconnection"""
    print(f"SocketIO Disconnect: {sid}")
