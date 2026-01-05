from celery import shared_task
import logging
import time

logger = logging.getLogger(__name__)

@shared_task(name="print_order_task")
def print_order_task(order_id: int):
    """
    Simula la impresión de un pedido (Ticket 6.1).
    En el futuro (Ticket 6.2) esto conectará con el servicio de impresión real.
    """
    logger.info(f"🖨️ START: Procesando impresión para Orden #{order_id}")
    
    # Simular latencia de impresión
    time.sleep(2)
    
    logger.info(f"✅ END: Orden #{order_id} enviada a impresión")
    return {"status": "printed", "order_id": order_id}
