# FastOps — Documento de Requisitos V2.1 (Con Alto Rendimiento)

**Versión: 2.1 (Actualizado con Multi-Tenant + Performance)**  
**Fecha:** Diciembre 2024  
**Autor:** Jhon (cliente) / Equipo de desarrollo  

## CAMBIOS EN VERSIÓN 2.1

✅ Sistema de Alto Rendimiento agregado (Sección 15)  
✅ Cola de impresión asíncrona con prioridades  
✅ Procesamiento paralelo con workers  
✅ Sistema de fallback y circuit breaker  
✅ Monitoreo proactivo y alertas  
✅ Modo Turbo para días pico  
✅ WebSockets optimizado para alta carga  

---

## 15. SISTEMA DE ALTO RENDIMIENTO (NUEVO) 🚀

### 15.1 Problema Identificado

**Dolor reportado por el cliente:**
> "En otro sistema, un día de muchos pedidos tardaba **30 minutos** en imprimir la comanda para enviarla a cocina debido al flujo alto de pedidos."

**Causas raíz identificadas:**
- Procesamiento síncrono (bloqueante)
- Sin cola de impresión
- Sin procesamiento paralelo
- Sistema se "congelaba" bajo carga
- Sin feedback al usuario

### 15.2 Arquitectura de Alto Rendimiento

#### Flujo Optimizado:

```
Cliente hace pedido
    ↓ (< 500ms)
Backend recibe y guarda en BD
    ↓ (< 200ms)
Encola en Redis/RabbitMQ
    ↓ (< 100ms)
✅ RESPUESTA INMEDIATA AL MESERO (< 1 seg total)
    ↓
Workers procesan en paralelo (3-10 workers)
    ↓ (< 5 seg)
Impresora recibe comanda
    ↓
WebSocket notifica a mesero "✅ Impreso"
```

#### Vs. Sistema Anterior (Bloqueante):

```
❌ Cliente hace pedido
    ↓
Backend procesa + imprime (BLOQUEADO esperando impresora)
    ↓ 30 MINUTOS EN DÍAS PICO
Sistema congelado, no puede recibir más pedidos
    ↓
Finalmente responde (demasiado tarde)
```

---

### 15.3 Componentes del Sistema

#### 15.3.1 Cola de Impresión con Prioridades

**Tabla nueva en BD:**

```sql
CREATE TABLE print_queue (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    branch_id INTEGER NOT NULL,
    order_id INTEGER NOT NULL,
    priority VARCHAR(20) NOT NULL,  -- urgent, normal, low
    status VARCHAR(20) NOT NULL,     -- pending, processing, completed, failed
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    printer_id VARCHAR(50),          -- impresora_cocina, impresora_bar
    payload JSONB NOT NULL,          -- datos de la comanda
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    INDEX idx_print_queue_status (company_id, branch_id, status, priority),
    INDEX idx_print_queue_created (created_at),
    FOREIGN KEY (company_id) REFERENCES companies(id),
    FOREIGN KEY (branch_id) REFERENCES branches(id),
    FOREIGN KEY (order_id) REFERENCES pedidos(id)
);
```

**Niveles de prioridad:**
- 🔴 **Urgent**: Pedidos modificados, cancelaciones (procesado de inmediato)
- 🟡 **Normal**: Pedidos nuevos (cola estándar)
- 🟢 **Low**: Reimpresiones (cuando hay capacidad)

#### 15.3.2 Workers de Procesamiento Paralelo

**Configuración adaptativa:**

```python
# config/performance.py

class PerformanceConfig:
    # Workers base
    MIN_WORKERS = 2
    MAX_WORKERS = 10
    
    # Auto-scaling
    SCALE_UP_THRESHOLD = 15    # pedidos en cola
    SCALE_DOWN_THRESHOLD = 5   # pedidos en cola
    SCALE_UP_INCREMENT = 2     # agregar workers
    
    # Timeouts
    WORKER_TIMEOUT = 10        # segundos
    PRINT_TIMEOUT = 5          # segundos
    
    # Reintentos
    MAX_RETRIES = 3
    RETRY_DELAY = 2            # segundos entre reintentos
    
    # Circuit breaker
    FAILURE_THRESHOLD = 5      # fallos consecutivos
    CIRCUIT_OPEN_DURATION = 60 # segundos
```

**Implementación de workers:**

```python
# backend/app/workers/print_worker.py

import asyncio
from redis import Redis
from app.core.database import get_db
from app.services.printer import PrinterService
from app.core.websockets import socketio

class PrintWorker:
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.redis = Redis()
        self.printer_service = PrinterService()
        self.is_running = False
        self.processed_count = 0
        
    async def start(self):
        """Inicia el worker"""
        self.is_running = True
        print(f"🟢 Worker {self.worker_id} iniciado")
        
        while self.is_running:
            try:
                # 1. Obtener siguiente trabajo de la cola
                job = await self.get_next_job()
                
                if job:
                    await self.process_job(job)
                else:
                    # No hay trabajos, esperar
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"❌ Worker {self.worker_id} error: {e}")
                await asyncio.sleep(2)
    
    async def get_next_job(self):
        """Obtiene siguiente trabajo según prioridad"""
        db = next(get_db())
        
        # Priorizar por: urgent > normal > low
        job = db.query(PrintQueue).filter(
            PrintQueue.status == 'pending',
            PrintQueue.attempts < PrintQueue.max_attempts
        ).order_by(
            # Prioridad: urgent primero
            case(
                (PrintQueue.priority == 'urgent', 1),
                (PrintQueue.priority == 'normal', 2),
                (PrintQueue.priority == 'low', 3)
            ),
            PrintQueue.created_at  # Más antiguo primero
        ).with_for_update(skip_locked=True).first()
        
        if job:
            # Marcar como procesando
            job.status = 'processing'
            job.attempts += 1
            db.commit()
            
        return job
    
    async def process_job(self, job):
        """Procesa trabajo de impresión"""
        start_time = time.time()
        
        try:
            # 1. Actualizar estado en WebSocket
            await self.emit_status(job, 'printing')
            
            # 2. Imprimir con timeout
            await asyncio.wait_for(
                self.printer_service.print(job.payload),
                timeout=PRINT_TIMEOUT
            )
            
            # 3. Marcar como completado
            db = next(get_db())
            job.status = 'completed'
            job.processed_at = datetime.now()
            job.completed_at = datetime.now()
            db.commit()
            
            # 4. Notificar éxito
            await self.emit_status(job, 'printed')
            
            duration = time.time() - start_time
            self.processed_count += 1
            
            print(f"✅ Worker {self.worker_id}: Pedido #{job.order_id} "
                  f"impreso en {duration:.2f}s")
            
        except asyncio.TimeoutError:
            # Timeout - reintentar
            await self.handle_failure(job, "Timeout de impresión")
            
        except Exception as e:
            # Error general
            await self.handle_failure(job, str(e))
    
    async def handle_failure(self, job, error_message):
        """Maneja fallos en impresión"""
        db = next(get_db())
        
        job.error_message = error_message
        
        if job.attempts >= job.max_attempts:
            # Máximo de intentos alcanzado - usar fallback
            job.status = 'failed'
            await self.use_fallback(job)
        else:
            # Reintentar
            job.status = 'pending'
            await asyncio.sleep(RETRY_DELAY)
        
        db.commit()
        
        print(f"⚠️ Worker {self.worker_id}: Fallo en pedido #{job.order_id} "
              f"(intento {job.attempts}/{job.max_attempts})")
    
    async def use_fallback(self, job):
        """Método alternativo cuando falla impresión"""
        # Opción 1: Mostrar en pantalla de cocina
        await socketio.emit(
            'print_fallback',
            {
                'order_id': job.order_id,
                'payload': job.payload,
                'message': 'Imprimir manualmente'
            },
            room=f"kitchen_company_{job.company_id}_branch_{job.branch_id}"
        )
        
        # Opción 2: Enviar por email (emergencia)
        # await send_email_backup(job)
        
        # Alertar al admin
        await socketio.emit(
            'system_alert',
            {
                'type': 'printer_failed',
                'order_id': job.order_id,
                'message': f'Impresora falló después de {job.attempts} intentos'
            },
            room=f"admin_company_{job.company_id}"
        )
    
    async def emit_status(self, job, status):
        """Emite actualización de estado por WebSocket"""
        await socketio.emit(
            'print_status_update',
            {
                'order_id': job.order_id,
                'status': status,
                'worker_id': self.worker_id
            },
            room=f"kitchen_company_{job.company_id}_branch_{job.branch_id}"
        )
    
    def stop(self):
        """Detiene el worker"""
        self.is_running = False
        print(f"🔴 Worker {self.worker_id} detenido "
              f"(procesó {self.processed_count} trabajos)")


# Gestor de workers
class WorkerManager:
    def __init__(self):
        self.workers = []
        self.active_workers = MIN_WORKERS
        
    async def start(self):
        """Inicia workers base"""
        for i in range(MIN_WORKERS):
            await self.add_worker()
        
        # Iniciar monitor de auto-scaling
        asyncio.create_task(self.monitor_queue())
    
    async def add_worker(self):
        """Agrega un nuevo worker"""
        worker_id = len(self.workers) + 1
        worker = PrintWorker(worker_id)
        self.workers.append(worker)
        asyncio.create_task(worker.start())
        self.active_workers += 1
        print(f"➕ Worker {worker_id} agregado (total: {self.active_workers})")
    
    async def remove_worker(self):
        """Remueve un worker (gracefully)"""
        if self.active_workers > MIN_WORKERS and self.workers:
            worker = self.workers.pop()
            worker.stop()
            self.active_workers -= 1
            print(f"➖ Worker removido (total: {self.active_workers})")
    
    async def monitor_queue(self):
        """Monitorea cola y ajusta workers automáticamente"""
        while True:
            db = next(get_db())
            queue_size = db.query(PrintQueue).filter(
                PrintQueue.status == 'pending'
            ).count()
            
            # Auto-scaling UP
            if queue_size > SCALE_UP_THRESHOLD:
                if self.active_workers < MAX_WORKERS:
                    for _ in range(SCALE_UP_INCREMENT):
                        await self.add_worker()
                    print(f"⚡ AUTO-SCALE UP: Cola alta ({queue_size} pedidos)")
            
            # Auto-scaling DOWN
            elif queue_size < SCALE_DOWN_THRESHOLD:
                if self.active_workers > MIN_WORKERS:
                    await self.remove_worker()
                    print(f"📉 AUTO-SCALE DOWN: Cola baja ({queue_size} pedidos)")
            
            await asyncio.sleep(10)  # Revisar cada 10 segundos


# Inicializar en startup
worker_manager = WorkerManager()

@app.on_event("startup")
async def startup():
    await worker_manager.start()
```

---

#### 15.3.3 Endpoint de Creación de Pedidos Optimizado

```python
# backend/app/routers/orders.py

from fastapi import APIRouter, Depends, BackgroundTasks
from app.services.print_queue import enqueue_print

router = APIRouter()

@router.post("/orders")
async def create_order(
    order: OrderCreate,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Crear pedido con procesamiento asíncrono
    
    Tiempo objetivo: < 1 segundo
    """
    start_time = time.time()
    
    # 1. Validar datos básicos (< 100ms)
    if not order.items:
        raise HTTPException(400, "Pedido vacío")
    
    # 2. Generar consecutivo (< 200ms)
    consecutive = generate_consecutive(
        company_id=current_user.company_id,
        branch_id=current_user.branch_id,
        order_type=order.tipo,
        db=db
    )
    
    # 3. Calcular total (< 100ms)
    total = calculate_order_total(order.items, db)
    
    # 4. Crear pedido en BD (< 300ms)
    db_order = Order(
        company_id=current_user.company_id,
        branch_id=current_user.branch_id,
        consecutivo=consecutive,
        tipo=order.tipo,
        total=total,
        estado='pendiente',
        creado_por=current_user.id,
        **order.dict(exclude={'items'})
    )
    db.add(db_order)
    db.flush()  # Obtener ID sin commit completo
    
    # 5. Agregar items (< 200ms)
    for item in order.items:
        db_item = OrderItem(
            order_id=db_order.id,
            **item.dict()
        )
        db.add(db_item)
    
    # 6. Commit transacción (< 100ms)
    db.commit()
    db.refresh(db_order)
    
    # 7. Encolar impresión (< 100ms) - NO BLOQUEANTE
    await enqueue_print(
        order_id=db_order.id,
        company_id=current_user.company_id,
        branch_id=current_user.branch_id,
        priority='normal',
        db=db
    )
    
    # 8. Notificar por WebSocket (< 50ms)
    background_tasks.add_task(
        notify_new_order,
        db_order.id,
        current_user.company_id,
        current_user.branch_id
    )
    
    duration = time.time() - start_time
    
    # Log de performance
    if duration > 1.0:
        print(f"⚠️ Pedido creado en {duration:.2f}s (objetivo: < 1s)")
    else:
        print(f"✅ Pedido {consecutive} creado en {duration:.3f}s")
    
    # 9. RESPUESTA INMEDIATA
    return {
        "id": db_order.id,
        "consecutivo": consecutive,
        "total": total,
        "estado": "recibido",
        "print_status": "en_cola",
        "position_in_queue": await get_queue_position(db_order.id),
        "estimated_print_time": "5-10 segundos"
    }


async def enqueue_print(
    order_id: int,
    company_id: int,
    branch_id: int,
    priority: str,
    db: Session
):
    """Encola pedido para impresión"""
    
    # 1. Generar payload de impresión
    order = db.query(Order).get(order_id)
    payload = generate_print_payload(order)
    
    # 2. Determinar impresora destino
    printer_id = determine_printer(order, db)
    
    # 3. Insertar en cola
    print_job = PrintQueue(
        company_id=company_id,
        branch_id=branch_id,
        order_id=order_id,
        priority=priority,
        status='pending',
        printer_id=printer_id,
        payload=payload
    )
    db.add(print_job)
    db.commit()
    
    print(f"📋 Pedido #{order_id} encolado para impresión (prioridad: {priority})")
```

---

#### 15.3.4 Sistema de Fallback (Circuit Breaker)

```python
# backend/app/services/circuit_breaker.py

from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"      # Normal - todo OK
    OPEN = "open"          # Impresora caída - usar fallback
    HALF_OPEN = "half_open"  # Probando si recuperó

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # segundos
        self.last_failure_time = None
        self.success_count = 0
        
    async def call(self, func, *args, **kwargs):
        """Ejecuta función con circuit breaker"""
        
        # Si circuito está abierto
        if self.state == CircuitState.OPEN:
            # Verificar si es tiempo de probar de nuevo
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                print("🔄 Circuit Breaker: Probando reconexión...")
            else:
                # Todavía en cooldown - usar fallback
                raise CircuitBreakerOpen("Impresora fuera de servicio")
        
        try:
            # Intentar ejecutar
            result = await func(*args, **kwargs)
            
            # Éxito - resetear contador
            self._on_success()
            return result
            
        except Exception as e:
            # Fallo - incrementar contador
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Maneja éxito"""
        self.failures = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            # Después de 3 éxitos consecutivos, cerrar circuito
            if self.success_count >= 3:
                self.state = CircuitState.CLOSED
                self.success_count = 0
                print("✅ Circuit Breaker: Impresora recuperada")
    
    def _on_failure(self):
        """Maneja fallo"""
        self.failures += 1
        self.last_failure_time = datetime.now()
        
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            print(f"🔴 Circuit Breaker ABIERTO: {self.failures} fallos consecutivos")
            
            # Alertar al admin
            asyncio.create_task(
                notify_admin_printer_down()
            )
        
        if self.state == CircuitState.HALF_OPEN:
            # Si falla en half-open, volver a abrir
            self.state = CircuitState.OPEN
            self.success_count = 0
    
    def _should_attempt_reset(self):
        """Verifica si es tiempo de probar reconexión"""
        if not self.last_failure_time:
            return False
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout


# Instancia global por impresora
circuit_breakers = {
    'impresora_cocina': CircuitBreaker(),
    'impresora_bar': CircuitBreaker(),
    'impresora_postres': CircuitBreaker()
}


async def print_with_circuit_breaker(printer_id: str, payload):
    """Imprime con protección de circuit breaker"""
    cb = circuit_breakers.get(printer_id)
    
    try:
        return await cb.call(
            printer_service.print,
            printer_id,
            payload
        )
    except CircuitBreakerOpen:
        # Usar fallback inmediatamente
        return await use_print_fallback(printer_id, payload)


class CircuitBreakerOpen(Exception):
    """Excepción cuando circuit breaker está abierto"""
    pass
```

---

#### 15.3.5 Monitoreo y Dashboard de Performance

```python
# backend/app/routers/monitoring.py

@router.get("/admin/performance/dashboard")
async def performance_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dashboard de performance en tiempo real"""
    
    # Estadísticas de cola
    queue_stats = db.query(
        PrintQueue.status,
        func.count(PrintQueue.id).label('count'),
        func.avg(
            extract('epoch', PrintQueue.processed_at - PrintQueue.created_at)
        ).label('avg_duration')
    ).filter(
        PrintQueue.company_id == current_user.company_id,
        PrintQueue.created_at >= datetime.now() - timedelta(hours=1)
    ).group_by(PrintQueue.status).all()
    
    # Workers activos
    active_workers = worker_manager.active_workers
    
    # Pedidos por hora (últimas 24 horas)
    orders_per_hour = db.query(
        func.date_trunc('hour', Order.created_at).label('hour'),
        func.count(Order.id).label('orders')
    ).filter(
        Order.company_id == current_user.company_id,
        Order.created_at >= datetime.now() - timedelta(hours=24)
    ).group_by('hour').all()
    
    # Circuit breakers status
    circuit_status = {
        printer_id: {
            'state': cb.state.value,
            'failures': cb.failures,
            'last_failure': cb.last_failure_time
        }
        for printer_id, cb in circuit_breakers.items()
    }
    
    # Tiempo promedio de procesamiento
    avg_processing_time = db.query(
        func.avg(
            extract('epoch', PrintQueue.completed_at - PrintQueue.created_at)
        )
    ).filter(
        PrintQueue.company_id == current_user.company_id,
        PrintQueue.status == 'completed',
        PrintQueue.completed_at >= datetime.now() - timedelta(hours=1)
    ).scalar() or 0
    
    return {
        "queue": {
            "pending": next((s.count for s in queue_stats if s.status == 'pending'), 0),
            "processing": next((s.count for s in queue_stats if s.status == 'processing'), 0),
            "completed_last_hour": next((s.count for s in queue_stats if s.status == 'completed'), 0),
            "failed": next((s.count for s in queue_stats if s.status == 'failed'), 0)
        },
        "workers": {
            "active": active_workers,
            "min": MIN_WORKERS,
            "max": MAX_WORKERS
        },
        "performance": {
            "avg_processing_time": round(avg_processing_time, 2),
            "target": 5.0,
            "status": "good" if avg_processing_time < 10 else "warning"
        },
        "circuit_breakers": circuit_status,
        "orders_trend": [
            {"hour": o.hour.isoformat(), "count": o.orders}
            for o in orders_per_hour
        ],
        "alerts": await get_active_alerts(current_user.company_id, db)
    }


@router.post("/admin/performance/turbo-mode")
async def toggle_turbo_mode(
    enabled: bool,
    current_user: User = Depends(require_admin)
):
    """Activa/desactiva modo turbo"""
    
    if enabled:
        # Aumentar workers al máximo
        while worker_manager.active_workers < MAX_WORKERS:
            await worker_manager.add_worker()
        
        # Reducir timeouts para mayor velocidad
        global PRINT_TIMEOUT
        PRINT_TIMEOUT = 3  # Más agresivo
        
        # Activar procesamiento batch
        enable_batch_processing()
        
        return {
            "status": "turbo_enabled",
            "workers": MAX_WORKERS,
            "message": "Modo turbo activado - rendimiento máximo"
        }
    else:
        # Volver a configuración normal
        PRINT_TIMEOUT = 5
        disable_batch_processing()
        
        return {
            "status": "turbo_disabled",
            "message": "Modo normal restaurado"
        }
```

---

### 15.4 WebSockets Optimizado para Alta Carga

```python
# backend/app/core/websockets_optimized.py

from socketio import AsyncServer
import asyncio

# Configuración optimizada
sio = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1024 * 1024,  # 1MB
    compression_threshold=1024,  # Comprimir mensajes > 1KB
    engineio_logger=False,  # Reducir logs en producción
    logger=False
)

# Buffer para batch de eventos
event_buffer = defaultdict(list)
BUFFER_SIZE = 10
BUFFER_TIMEOUT = 1.0  # segundos

async def emit_buffered(event, data, room):
    """
    Emite eventos en batch para reducir overhead
    """
    buffer_key = f"{event}:{room}"
    event_buffer[buffer_key].append(data)
    
    # Si el buffer está lleno, enviar inmediatamente
    if len(event_buffer[buffer_key]) >= BUFFER_SIZE:
        await flush_buffer(event, room)

async def flush_buffer(event, room):
    """Vacía el buffer y envía eventos"""
    buffer_key = f"{event}:{room}"
    
    if buffer_key in event_buffer and event_buffer[buffer_key]:
        batch = event_buffer[buffer_key]
        event_buffer[buffer_key] = []
        
        await sio.emit(
            event,
            {'batch': batch},
            room=room
        )

# Task periódica para vaciar buffers
async def buffer_flusher():
    """Vacía buffers periódicamente"""
    while True:
        await asyncio.sleep(BUFFER_TIMEOUT)
        
        for buffer_key in list(event_buffer.keys()):
            event, room = buffer_key.split(':', 1)
            await flush_buffer(event, room)

# Iniciar flusher en startup
@app.on_event("startup")
async def start_buffer_flusher():
    asyncio.create_task(buffer_flusher())
```

---

### 15.5 Endpoints de Control de Performance

```python
# backend/app/routers/performance.py

@router.post("/performance/scale-workers")
async def scale_workers(
    action: str,  # 'up' o 'down'
    count: int = 1,
    current_user: User = Depends(require_admin)
):
    """Escalar workers manualmente"""
    
    if action == 'up':
        for _ in range(count):
            if worker_manager.active_workers < MAX_WORKERS:
                await worker_manager.add_worker()
        
        return {
            "action": "scaled_up",
            "workers": worker_manager.active_workers
        }
    
    elif action == 'down':
        for _ in range(count):
            if worker_manager.active_workers > MIN_WORKERS:
                await worker_manager.remove_worker()
        
        return {
            "action": "scaled_down",
            "workers": worker_manager.active_workers
        }


@router.get("/performance/queue-status")
async def queue_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Estado actual de la cola"""
    
    queue = db.query(
        PrintQueue.priority,
        PrintQueue.status,
        func.count(PrintQueue.id).label('count')
    ).filter(
        PrintQueue.company_id == current_user.company_id,
        PrintQueue.status.in_(['pending', 'processing'])
    ).group_by(PrintQueue.priority, PrintQueue.status).all()
    
    return {
        "urgent": sum(q.count for q in queue if q.priority == 'urgent'),
        "normal": sum(q.count for q in queue if q.priority == 'normal'),
        "low": sum(q.count for q in queue if q.priority == 'low'),
        "total": sum(q.count for q in queue),
        "workers_active": worker_manager.active_workers
    }


@router.post("/performance/clear-failed")
async def clear_failed_jobs(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Limpiar trabajos fallidos"""
    
    deleted = db.query(PrintQueue).filter(
        PrintQueue.company_id == current_user.company_id,
        PrintQueue.status == 'failed',
        PrintQueue.completed_at < datetime.now() -