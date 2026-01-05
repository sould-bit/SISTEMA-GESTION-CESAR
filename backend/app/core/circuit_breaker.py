from redis.asyncio import Redis
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CircuitBreaker:
    def __init__(
        self, 
        redis: Redis, 
        service_name: str, 
        failure_threshold: int = 5, 
        recovery_timeout: int = 60
    ):
        """
        :param redis: Instancia de cliente Redis.
        :param service_name: Identificador del servicio (ej. 'print_service').
        :param failure_threshold: Número de fallos consecutivos para abrir el circuito.
        :param recovery_timeout: Tiempo en segundos que el circuito permanece abierto (t_open).
        """
        self.redis = redis
        self.service_name = service_name
        self.threshold = failure_threshold
        self.timeout = recovery_timeout
        
        # Keys
        self.key_prefix = f"circuit:{service_name}"
        self.key_failures = f"{self.key_prefix}:failures"
        self.key_state = f"{self.key_prefix}:open"

    async def is_open(self) -> bool:
        """
        Retorna True si el circuito está ABIERTO (servicio no disponible).
        """
        is_open = await self.redis.exists(self.key_state)
        return bool(is_open)

    async def record_failure(self):
        """
        Registra un fallo. Si se supera el umbral, abre el circuito.
        """
        # Incrementar contador de fallos
        failures = await self.redis.incr(self.key_failures)
        logger.warning(f"⚠️ CircuitBreaker [{self.service_name}] Fallos: {failures}/{self.threshold}")
        
        if failures >= self.threshold:
            await self.open_circuit()

    async def record_success(self):
        """
        Registra un éxito. Cierra el circuito (resetea contadores).
        """
        # Solo necesitamos borrar si hay fallos acumulados, para optimizar
        # verificamos primero o simplemente borramos (borrar es rápido).
        await self.redis.delete(self.key_failures)
        # Nota: No borramos key_state aquí a menos que queramos lógica Half-Open compleja.
        # En patrón simple, 'open' expira solo por TTL (timeout), 
        # o podríamos forzar cierre si detectamos éxito (Half-Open logic).
        # Por simplicidad: si entra una llamada exitosa (quizas un reintento manual o concurrencia),
        # asumimos que el sistema está sano.
        
        # Opcional: Si el circuito estaba abierto y logramos éxito, lo cerramos manual?
        # Para este ticket implementaremos Reset completo.
        await self.redis.delete(self.key_state)

    async def open_circuit(self):
        """
        Abre el circuito, impidiendo ejecuciones futuras por 'timeout' segundos.
        """
        logger.error(f"⛔ CircuitBreaker [{self.service_name}] ABIERTO por {self.timeout}s")
        # Setear flag de OPEN con expiración
        await self.redis.setex(self.key_state, self.timeout, "1")
        # Resetear contador para el próximo ciclo
        await self.redis.delete(self.key_failures)
