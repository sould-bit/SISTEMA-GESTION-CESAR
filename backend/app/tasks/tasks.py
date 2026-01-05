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
