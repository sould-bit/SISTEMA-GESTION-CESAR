import asyncio
import sys
import os

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

from app.database import async_session
from app.services.print_service import PrintService
from app.models.print_queue import PrintJob, PrintJobStatus
from sqlalchemy import select

async def main():
    print("🚀 Iniciando prueba de Cola de Impresión...")
    from app.config import settings
    print(f"🔧 Configured Broker: {settings.CELERY_BROKER_URL}")
    from app.tasks.celery_app import celery_app
    print(f"🔧 Celery App Broker: {celery_app.conf.broker_url}")
    
    async with async_session() as session:
        service = PrintService(session)
        
        # 1. Crear Job (ficticio, order_id=99999)
        print("1️⃣  Creando PrintJob para Orden #99999...")
        job = await service.create_print_job(order_id=99999, company_id=1)
        print(f"   ✅ Job Creado: ID={job.id}, Status={job.status}")
        
        # 2. Esperar a que Celery procese
        print("2️⃣  Esperando 5 segundos para que Celery procese...")
        await asyncio.sleep(5)
        
        # 3. Verificar estado
        print("3️⃣  Verificando estado final...")
        await session.refresh(job)
        print(f"   📊 Estado Final: ID={job.id}, Status={job.status}, Attempts={job.attempts}")
        
        if job.status == PrintJobStatus.COMPLETED:
            print("✅ PRUEBA EXITOSA: El trabajo fue procesado por el worker.")
        elif job.status == PrintJobStatus.PROCESSING:
             print("⚠️  PRUEBA EN CURSO: El trabajo sigue procesándose (¿worker lento?).")
        else:
             print(f"❌ PRUEBA FALLIDA: Estado inesperado ({job.status}). Verifica los logs del worker.")

if __name__ == "__main__":
    asyncio.run(main())
