from app.core.websockets import sio
from typing import Any, Dict

class NotificationService:
    @staticmethod
    async def notify_order_created(order: Dict[str, Any], company_id: int):
        """Notify kitchen and admins about a new order"""
        room = f"company_{company_id}"
        await sio.emit("order:created", order, room=room)
        print(f"WS Event: order:created sent to {room}")

    @staticmethod
    async def notify_order_status(order_id: int, status: str, company_id: int, branch_id: int):
        """Notify status change"""
        payload = {"order_id": order_id, "status": status}
        
        # Notify branch specific room
        await sio.emit("order:status", payload, room=f"branch_{branch_id}")
        
        # Also notify tracking room for this order if we decide to have granular rooms
        # or simplified approach:
        print(f"WS Event: order:status sent to branch_{branch_id}")

    @staticmethod
    async def notify_kitchen(order: Dict[str, Any], branch_id: int):
        """Send order specifically to kitchen display"""
        room = f"role_kitchen_{branch_id}"
        await sio.emit("kitchen:new_order", order, room=room)
