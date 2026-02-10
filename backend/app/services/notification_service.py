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
    async def notify_order_status(order_id: int, status: str, company_id: int, branch_id: int, order_number: str = None):
        """Notify status change to branch and company admins"""
        payload = {"order_id": order_id, "status": status, "order_number": order_number}
        
        # Notify branch specific room
        await sio.emit("order:status", payload, room=f"branch_{branch_id}")
        
        # Notify company room (for admin dashboard)
        await sio.emit("order:status", payload, room=f"company_{company_id}")
        
        print(f"WS Event: order:status sent to branch_{branch_id} and company_{company_id}")

    @staticmethod
    async def notify_kitchen(order: Dict[str, Any], branch_id: int):
        """Send order specifically to kitchen display"""
        room = f"role_kitchen_{branch_id}"
        await sio.emit("kitchen:new_order", order, room=room)

    @staticmethod
    async def notify_cancellation_request(order_id: int, order_number: str, reason: str, company_id: int, branch_id: int):
        """Notify roles capable of approving a cancellation"""
        payload = {
            "order_id": order_id, 
            "order_number": order_number, 
            "reason": reason,
            "type": "CANCELLATION_REQUEST"
        }
        # Notify Admin, Cashier and Kitchen
        rooms = [f"company_{company_id}", f"branch_{branch_id}", f"role_kitchen_{branch_id}", f"role_cashier_{branch_id}"]
        for room in rooms:
            await sio.emit("order:cancellation_requested", payload, room=room)
        
        print(f"WS Event: order:cancellation_requested sent to {rooms}")

    @staticmethod
    async def notify_cancellation_denied(order_id: int, order_number: str, denial_reason: str, company_id: int, branch_id: int):
        """Notify the waiter that their cancellation request was denied"""
        payload = {
            "order_id": order_id, 
            "order_number": order_number, 
            "denial_reason": denial_reason,
            "type": "CANCELLATION_DENIED"
        }
        # Notify everyone in branch (especially the waiter)
        rooms = [f"branch_{branch_id}", f"company_{company_id}"]
        for room in rooms:
            await sio.emit("order:cancellation_denied", payload, room=room)
        
        print(f"WS Event: order:cancellation_denied sent to {rooms}")

    @staticmethod
    async def notify_cancellation_approved(order_id: int, order_number: str, company_id: int, branch_id: int):
        """Notify the waiter that their cancellation request was approved"""
        payload = {
            "order_id": order_id, 
            "order_number": order_number, 
            "type": "CANCELLATION_APPROVED"
        }
        rooms = [f"branch_{branch_id}", f"company_{company_id}"]
        for room in rooms:
            await sio.emit("order:cancellation_approved", payload, room=room)
        
        print(f"WS Event: order:cancellation_approved sent to {rooms}")
