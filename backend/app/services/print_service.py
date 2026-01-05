from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
import logging

from app.models.print_queue import PrintJob, PrintJobStatus

logger = logging.getLogger(__name__)

class PrintService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Lazy initialization or direct? prefer direct but need async client.
        # Since __init__ is sync, we can't await get_redis_client here easily 
        # unless we do it in methods or use a singleton pattern.
        # Better approach: Instantiate CB in methods or init with None and load on demand
        self.circuit_breaker = None

    async def _get_cb(self):
        if not self.circuit_breaker:
            from app.core.redis import get_redis_client
            from app.core.circuit_breaker import CircuitBreaker
            redis = await get_redis_client()
            self.circuit_breaker = CircuitBreaker(redis, "print_service")
        return self.circuit_breaker

    async def create_print_job(self, order_id: int, company_id: int) -> PrintJob:
        """
        Crea un trabajo de impresión y lo envía a la cola (Celery).
        """
        # Importación local para evitar ciclo
        from app.tasks.tasks import print_order_task

        # Check Circuit Breaker
        cb = await self._get_cb()
        if await cb.is_open():
            logger.warning(f"⛔ PrintService Circuit Breaker OPEN. Rejecting Order {order_id}")
            raise HTTPException(
                status_code=503, 
                detail="El servicio de impresión no está disponible temporalmente (Circuit Breaker Abierto)"
            )

        job = PrintJob(
            company_id=company_id,
            order_id=order_id,
            status=PrintJobStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        # Enviar a Celery (pasamos solo el ID)
        print_order_task.delay(job.id)
        
        logger.info(f"🖨️ PrintJob creado: {job.id} para Order {order_id}")
        return job

    async def process_print_job(self, job_id: int):
        """
        Lógica de procesamiento de impresión (ejecutada por Celery worker).
        Simula la comunicación con impresora.
        """
        logger.info(f"🔄 Procesando PrintJob {job_id}...")
        
        # 1. Obtener job
        job = await self.db.get(PrintJob, job_id)
        if not job:
            logger.error(f"❌ PrintJob {job_id} no encontrado")
            return

        # 2. Marcar como PROCESSING
        job.status = PrintJobStatus.PROCESSING
        job.attempts += 1
        job.updated_at = datetime.utcnow()
        await self.db.commit()

        try:
            # 3. Simular impresión (lógica de negocio real iría aquí)
            import asyncio
            await asyncio.sleep(2) # Simular latencia de red/impresora
            
            # TODO: Aquí se conectaría con la impresora real o servicio de impresión cloud
            
            # 4. Marcar como COMPLETED
            job.status = PrintJobStatus.COMPLETED
            job.updated_at = datetime.utcnow()
            await self.db.commit()
            
            # Report Success to Circuit Breaker
            cb = await self._get_cb()
            await cb.record_success()
            
            logger.info(f"✅ PrintJob {job_id} completado con éxito")

        except Exception as e:
            # 5. Manejo de errores 
            logger.error(f"❌ Error procesando PrintJob {job_id}: {e}")
            job.status = PrintJobStatus.FAILED
            job.last_error = str(e)
            job.updated_at = datetime.utcnow()
            await self.db.commit()
            
            # Report Failure to Circuit Breaker (only on real exceptions, not business logic errors if handled differently)
            # Here ANY exception in processing counts as execution failure
            try:
                cb = await self._get_cb()
                await cb.record_failure()
            except Exception as cb_exc:
                logger.error(f"Error updating circuit breaker: {cb_exc}")
                
            raise e
