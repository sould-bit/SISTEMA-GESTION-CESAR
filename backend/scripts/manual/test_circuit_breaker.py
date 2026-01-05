import asyncio
import sys
import os
from fastapi import HTTPException

sys.path.append(os.getcwd())
from app.database import async_session
from app.services.print_service import PrintService
from app.models.print_queue import PrintJob

async def main():
    print("🚀 Iniciando prueba de CIRCUIT BREAKER...")
    
    async with async_session() as session:
        service = PrintService(session)
        
        # 1. Verificar estado inicial (debe estar CERRADO)
        print("\n--- FASE 1: Estado Inicial ---")
        cb = await service._get_cb()
        is_open = await cb.is_open()
        print(f"Estado CB: {'O ABIERTO' if is_open else 'O CERRADO'}")
        if is_open:
            print("❌ El circuito ya estaba abierto, limpiando Redis...")
            await cb.redis.delete(cb.key_failures)
            await cb.redis.delete(cb.key_state)
        
        # 2. Forzar Fallos (Simulado)
        # Vamos a invocar record_failure() manualmente para no esperar el ciclo de Celery
        print("\n--- FASE 2: Forzando Fallos ---")
        for i in range(1, 6):
            print(f"   Simulando fallo #{i}...")
            await cb.record_failure()
            
        is_open = await cb.is_open()
        print(f"Estado CB tras 5 fallos: {'🔴 ABIERTO' if is_open else '🟢 CERRADO'}")
        
        if not is_open:
            print("❌ PRUEBA FALLIDA: El circuito debería estar abierto.")
            return

        # 3. Intentar crear un Job (Debe ser rechazado)
        print("\n--- FASE 3: Verificando Rechazo (Fail Fast) ---")
        try:
            await service.create_print_job(order_id=777, company_id=1)
            print("❌ PRUEBA FALLIDA: Se permitió crear el trabajo a pesar del bloqueo.")
        except HTTPException as e:
            if e.status_code == 503:
                print(f"✅ EXITO: Trabajo rechazado con 503: {e.detail}")
            else:
                print(f"⚠️ Error inesperado: {e}")
        
        # 4. Limpieza
        print("\n--- FASE 4: Recuperación (Limpieza manual) ---")
        await cb.redis.delete(cb.key_state)
        await cb.redis.delete(cb.key_failures)
        print("✅ Redis limpiado.")

if __name__ == "__main__":
    asyncio.run(main())
