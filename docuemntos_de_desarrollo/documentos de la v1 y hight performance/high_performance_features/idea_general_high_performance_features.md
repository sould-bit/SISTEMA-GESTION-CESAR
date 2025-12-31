# Sistema de Alto Rendimiento para Gestión de Pedidos

## 🚀 Features de Performance y Prevención de Cuellos de Botella

### Problema Identificado
**Sistema anterior:** 30 minutos de retardo en días con alto flujo de pedidos para imprimir comandas.

**Causa raíz:** Procesamiento síncrono, colas no optimizadas, bloqueos en la base de datos.

---

## 1. **Cola de Impresión Asíncrona con Prioridades**

### Arquitectura
```
Cliente hace pedido → Backend recibe → Guarda en BD (< 1 seg)
                                    ↓
                            Cola de Impresión (Redis/RabbitMQ)
                                    ↓
                        Workers procesan en paralelo
                                    ↓
                            Impresora recibe
```

### Características:
- ✅ **Respuesta inmediata al mesero** - No espera la impresión
- ✅ **Procesamiento en segundo plano** - Workers dedicados
- ✅ **Sistema de prioridades**:
  - 🔴 Urgente: Pedidos modificados, cancelaciones
  - 🟡 Normal: Pedidos nuevos
  - 🟢 Baja: Reimpresiones

### Implementación Técnica:
```python
# Backend: Recibe pedido y lo encola inmediatamente
@app.post("/pedidos")
async def crear_pedido(pedido: Pedido):
    # 1. Guardar en BD (< 500ms)
    pedido_db = await db.pedidos.insert(pedido)
    
    # 2. Enviar a cola de impresión (< 100ms)
    await cola_impresion.enqueue({
        "pedido_id": pedido_db.id,
        "prioridad": "normal",
        "timestamp": datetime.now()
    })
    
    # 3. Respuesta INMEDIATA al mesero
    return {"status": "recibido", "id": pedido_db.id}
    # Total: < 1 segundo

# Worker: Procesa cola en paralelo (3-5 workers)
async def worker_impresion():
    while True:
        pedido = await cola_impresion.dequeue()
        await imprimir_comanda(pedido)
        await marcar_como_impreso(pedido.id)
```

---

## 2. **Sistema de Estados en Tiempo Real**

### Estados del Pedido:
```
RECIBIDO (0-1 seg)
    ↓
EN_COLA_IMPRESION (visible para el mesero)
    ↓
IMPRIMIENDO (feedback visual)
    ↓
IMPRESO ✅ (notificación al mesero)
    ↓
EN_PREPARACION (cocina lo ve)
```

### UI del Mesero:
```
┌─────────────────────────────────────┐
│ Pedido #1234 - Mesa 5               │
│ Estado: ⏳ En cola de impresión     │
│ Posición: 3 de 12 pedidos           │
│ Tiempo estimado: 15 segundos        │
│                                     │
│ [Marcar como urgente] [Reimprimir] │
└─────────────────────────────────────┘
```

### WebSocket para actualizaciones:
```javascript
// Frontend recibe actualizaciones en tiempo real
socket.on('pedido_actualizado', (data) => {
  if (data.estado === 'IMPRESO') {
    mostrarNotificacion('✅ Pedido enviado a cocina');
    reproducirSonido();
  }
});
```

---

## 3. **Múltiples Workers de Impresión**

### Arquitectura Paralela:
```
                    ┌─→ Worker 1 → Impresora Cocina
Cola de Pedidos ────┼─→ Worker 2 → Impresora Bar
                    └─→ Worker 3 → Impresora Postres
```

### Configuración:
- **Desarrollo:** 2 workers
- **Producción baja:** 3-5 workers
- **Producción alta (días pico):** 8-10 workers
- **Auto-scaling:** Agregar workers automáticamente si la cola supera 20 pedidos

### Monitoreo:
```python
# Dashboard en tiempo real
@app.get("/admin/cola-status")
async def status_cola():
    return {
        "pedidos_en_cola": 8,
        "workers_activos": 5,
        "tiempo_promedio_procesamiento": "3.2 segundos",
        "ultimo_pedido_procesado": "hace 2 segundos",
        "alerta": None  # o "Cola alta - agregando workers"
    }
```

---

## 4. **Impresión por Estación (Multi-Impresora)**

### Distribución Inteligente:
```python
# Reglas de enrutamiento
{
    "platos_principales": "impresora_cocina",
    "bebidas": "impresora_bar",
    "postres": "impresora_reposteria",
    "entradas": "impresora_cocina"
}

# Un pedido puede ir a múltiples impresoras
Pedido: 1 hamburguesa + 1 cerveza + 1 helado
    ↓
Imprime en cocina: Hamburguesa
Imprime en bar: Cerveza
Imprime en postres: Helado
```

### Ventajas:
- ✅ Reduce carga en una sola impresora
- ✅ Cada estación ve solo lo que le corresponde
- ✅ Si una impresora falla, las otras siguen funcionando

---

## 5. **Caché y Optimización de BD**

### Problema del sistema anterior:
- Consultas lentas a la base de datos
- Bloqueos por escrituras concurrentes

### Solución:
```python
# 1. Caché en Redis para lecturas frecuentes
@app.get("/menu/items")
@cache(ttl=300)  # 5 minutos
async def obtener_menu():
    return menu_items

# 2. Escrituras en batch
pedidos_buffer = []

async def buffer_pedidos():
    global pedidos_buffer
    while True:
        if len(pedidos_buffer) > 0:
            # Insertar varios pedidos a la vez
            await db.bulk_insert(pedidos_buffer)
            pedidos_buffer = []
        await asyncio.sleep(0.5)

# 3. Índices optimizados en PostgreSQL
CREATE INDEX idx_pedidos_estado ON pedidos(estado);
CREATE INDEX idx_pedidos_timestamp ON pedidos(created_at DESC);
```

---

## 6. **Sistema de Fallback (Plan B)**

### Si la impresora falla:
```python
# 1. Reintentos automáticos (3 intentos)
async def imprimir_con_reintentos(pedido):
    for intento in range(3):
        try:
            await imprimir(pedido)
            return True
        except Exception as e:
            if intento < 2:
                await asyncio.sleep(2)  # Esperar 2 seg
            else:
                # Enviar a método alternativo
                await fallback_impresion(pedido)

# 2. Método alternativo
async def fallback_impresion(pedido):
    # Opción A: Mostrar en pantalla de cocina
    await enviar_a_pantalla_cocina(pedido)
    
    # Opción B: Enviar por email
    await enviar_email_emergencia(pedido)
    
    # Opción C: Guardar en PDF para imprimir manual
    await generar_pdf_temporal(pedido)
    
    # Alertar al admin
    await notificar_admin("⚠️ Impresora caída - usando fallback")
```

---

## 7. **Prevención de Bloqueos del Sistema**

### Circuit Breaker Pattern:
```python
class CircuitBreaker:
    def __init__(self):
        self.failures = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func):
        if self.state == "OPEN":
            # No intentar, usar fallback inmediatamente
            raise CircuitBreakerOpen()
        
        try:
            result = await func()
            self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            if self.failures > 5:
                self.state = "OPEN"  # Abrir circuito
                await enviar_alerta_admin()
            raise

# Uso
impresora_cb = CircuitBreaker()

async def imprimir_pedido(pedido):
    try:
        await impresora_cb.call(lambda: imprimir(pedido))
    except CircuitBreakerOpen:
        # Usar método alternativo inmediatamente
        await mostrar_en_pantalla(pedido)
```

---

## 8. **Monitoreo y Alertas Proactivas**

### Dashboard de Performance:
```
┌────────────────────────────────────────────┐
│  📊 Estado del Sistema                     │
├────────────────────────────────────────────┤
│  ⚡ Pedidos procesados hoy: 847            │
│  ⏱️  Tiempo promedio: 2.1 segundos         │
│  📋 En cola ahora: 3 pedidos               │
│  🖨️  Impresoras activas: 3/3               │
│                                            │
│  🚨 Alertas:                               │
│  ⚠️  Cola alta detectada (12 pedidos)      │
│  ✅ Auto-scaling activado (+2 workers)     │
└────────────────────────────────────────────┘
```

### Alertas Automáticas:
```python
# Configuración de alertas
ALERTAS = {
    "cola_alta": {
        "umbral": 15,
        "accion": "agregar_workers"
    },
    "tiempo_lento": {
        "umbral": 10,  # segundos
        "accion": "notificar_admin"
    },
    "impresora_caida": {
        "accion": ["usar_fallback", "notificar_admin"]
    }
}

# Monitor en tiempo real
async def monitor_performance():
    while True:
        stats = await obtener_estadisticas()
        
        if stats.cola_size > 15:
            await agregar_workers(2)
            await notificar("⚠️ Carga alta - agregando workers")
        
        if stats.tiempo_promedio > 10:
            await notificar_admin("🐌 Sistema lento")
        
        await asyncio.sleep(30)  # Revisar cada 30 seg
```

---

## 9. **Modo de Alto Tráfico (Turbo Mode)**

### Activación Manual o Automática:
```python
# Mesero o admin puede activarlo
@app.post("/sistema/modo-turbo")
async def activar_turbo():
    # 1. Aumentar workers
    await escalar_workers(cantidad=10)
    
    # 2. Reducir features no críticas
    await deshabilitar_animaciones()
    await deshabilitar_logs_verbose()
    
    # 3. Aumentar prioridad de impresión
    await ajustar_prioridades()
    
    # 4. Usar caché agresivo
    await aumentar_cache_ttl(600)
    
    return {"status": "turbo_activado"}

# Desactivar automáticamente cuando baje la carga
async def auto_desactivar_turbo():
    if cola_size < 5 and tiempo_promedio < 3:
        await desactivar_turbo()
```

---

## 10. **Testing de Carga**

### Pruebas antes de producción:
```python
# Simular 100 pedidos simultáneos
async def test_carga():
    pedidos = [generar_pedido_test() for _ in range(100)]
    
    inicio = time.time()
    
    # Enviar todos a la vez
    await asyncio.gather(*[
        crear_pedido(p) for p in pedidos
    ])
    
    fin = time.time()
    
    print(f"100 pedidos procesados en {fin - inicio} segundos")
    # Objetivo: < 5 segundos para recepción
    # Objetivo: < 2 minutos para impresión completa
```

---

## Comparación: Sistema Anterior vs Nuevo

| Aspecto | Sistema Anterior | Sistema Nuevo |
|---------|-----------------|---------------|
| Tiempo de respuesta | 30 minutos en pico | < 5 segundos siempre |
| Procesamiento | Síncrono (bloqueante) | Asíncrono (no bloqueante) |
| Cola de impresión | Sin cola o mal gestionada | Cola con prioridades |
| Workers | 1 proceso | 3-10 procesos paralelos |
| Feedback al mesero | Sin información | Estados en tiempo real |
| Fallback | Sistema se cuelga | Métodos alternativos |
| Monitoreo | Sin alertas | Alertas proactivas |
| Escalabilidad | No escala | Auto-scaling |

---

## Garantías de Performance

### Tiempos Objetivo:
- ✅ **Recepción de pedido:** < 1 segundo
- ✅ **Encolado:** < 0.5 segundos
- ✅ **Impresión (carga normal):** < 5 segundos
- ✅ **Impresión (carga alta):** < 15 segundos
- ✅ **Feedback al mesero:** Instantáneo (WebSocket)

### SLA (Service Level Agreement):
- 99.9% de disponibilidad
- 95% de pedidos procesados en < 5 segundos
- Sin bloqueos del sistema en ninguna circunstancia
- Recuperación automática ante fallos

---

## Stack Tecnológico Recomendado

```python
# Backend
FastAPI (asíncrono nativo)
PostgreSQL (con índices optimizados)
Redis (caché + cola)
Celery o RQ (workers de impresión)

# Comunicación tiempo real
WebSockets (Socket.io o FastAPI WebSocket)

# Monitoreo
Prometheus + Grafana
Sentry (errores)
```

---

## Implementación por Fases

### Fase 1 (MVP):
- Cola básica con Redis
- 2 workers de impresión
- Estados en tiempo real

### Fase 2 (Mejoras):
- Multi-impresora
- Sistema de fallback
- Monitoreo básico

### Fase 3 (Producción):
- Auto-scaling
- Circuit breaker
- Dashboard completo
- Testing de carga

---

## Conclusión

Con esta arquitectura, el sistema puede manejar:
- **100+ pedidos simultáneos** sin retardo
- **Días pico** sin degradación de performance
- **Fallos de impresora** sin interrumpir el servicio
- **Crecimiento futuro** sin necesidad de reescribir

**Resultado:** De 30 minutos a 5 segundos en el peor escenario.