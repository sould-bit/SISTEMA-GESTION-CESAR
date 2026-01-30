from celery import shared_task
import logging
import asyncio
from app.database import async_session
from app.services.print_service import PrintService

logger = logging.getLogger(__name__)

async def process_print_job_async(job_id: int):
    """
    Wrapper asíncrono para ejecutar la lógica de servicio
    dentro de la tarea síncrona de Celery.
    """
    async with async_session() as session:
        service = PrintService(session)
        await service.process_print_job(job_id)

@shared_task(name="print_order_task")
def print_order_task(job_id: int):
    """
    Tarea de Celery para procesar trabajos de impresión.
    Ejecuta el servicio asíncrono en un event loop.
    """
    logger.info(f"⚡ CELERY: Iniciando tarea para Job ID {job_id}")
    
    try:
        # Ejecutar lógica asíncrona
        asyncio.run(process_print_job_async(job_id))
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"❌ CELERY ERROR: {e}")
        return {"status": "error", "error": str(e)}


# ============================================================
# MENU ENGINEERING TASKS
# ============================================================

async def deduct_inventory_async(branch_id: int, product_id: int, quantity: int, user_id: int, order_id: str):
    """
    Wrapper asíncrono para la deducción de inventario basada en recetas.
    """
    from app.services.inventory_service import InventoryService
    
    async with async_session() as session:
        service = InventoryService(session)
        await service.process_recipe_deduction(
            branch_id=branch_id,
            product_id=product_id,
            quantity_sold=quantity,
            user_id=user_id,
            reference_id=order_id
        )


@shared_task(name="deduct_inventory_from_order_task")
def deduct_inventory_from_order_task(branch_id: int, product_id: int, quantity: int, user_id: int, order_id: str):
    """
    Tarea de Celery para descontar inventario de forma asíncrona.
    
    Flujo:
    1. Verifica si el producto tiene receta activa.
    2. Si tiene, descuenta ingredientes según la receta.
    3. Si no tiene, descuenta stock del producto directamente.
    """
    logger.info(f"⚡ CELERY: Deducción de inventario para Producto {product_id}, Orden {order_id}")
    
    try:
        asyncio.run(deduct_inventory_async(branch_id, product_id, quantity, user_id, order_id))
        return {"status": "success", "product_id": product_id, "order_id": order_id}
    except Exception as e:
        logger.error(f"❌ CELERY ERROR (Inventory): {e}")
        return {"status": "error", "error": str(e)}

