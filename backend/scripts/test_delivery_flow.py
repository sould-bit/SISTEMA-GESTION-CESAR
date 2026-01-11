#!/usr/bin/env python3
"""
Test del Flujo de Domiciliarios
================================
Prueba el flujo completo:
1. Login como cajero
2. Listar domiciliarios disponibles
3. Crear pedido delivery (desde test de customer)
4. Asignar domiciliario
5. Login como domiciliario
6. Ver mis pedidos
7. Marcar recogido
8. Marcar entregado
"""

import httpx
from typing import Optional

BASE_URL = "http://localhost:8000"

# Colores para output
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def log_ok(msg): print(f"{GREEN}✅ {msg}{RESET}")
def log_error(msg): print(f"{RED}❌ {msg}{RESET}")
def log_info(msg): print(f"{BLUE}ℹ️  {msg}{RESET}")


def login(username: str, password: str, company_slug: str) -> Optional[str]:
    """Login y retorna token."""
    response = httpx.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": username,
            "password": password,
            "company_slug": company_slug
        }
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


def main():
    print(f"\n{BLUE}🚚 TEST FLUJO DOMICILIARIOS{RESET}\n")
    
    # ===== PASO 1: Login como cajero =====
    log_info("1. Login como Cajero...")
    cajero_token = login("cajero1", "password123", "fastops")
    
    if not cajero_token:
        log_error("No se pudo loguear como cajero")
        return
    log_ok("Logueado como Cajero")
    
    headers_cajero = {"Authorization": f"Bearer {cajero_token}"}
    
    # ===== PASO 2: Listar domiciliarios =====
    log_info("2. Listando domiciliarios disponibles...")
    response = httpx.get(
        f"{BASE_URL}/delivery/available",
        headers=headers_cajero
    )
    
    if response.status_code != 200:
        log_error(f"Error listando domiciliarios: {response.status_code} - {response.text}")
        return
    
    drivers = response.json()
    log_ok(f"Encontrados {len(drivers)} domiciliarios")
    
    if not drivers:
        log_info("No hay domiciliarios. Creando uno...")
        # Aquí podrías crear uno si no existe
        log_error("Necesitas tener al menos 1 usuario con rol 'Domiciliario'")
        return
    
    driver = drivers[0]
    log_info(f"   Domiciliario: {driver['full_name']} (ID: {driver['id']})")
    
    # ===== PASO 3: Buscar pedido delivery en estado READY =====
    log_info("3. Buscando pedido delivery para asignar...")
    
    # Por ahora simulamos que ya existe un pedido - en producción buscaríamos uno real
    # Este paso requiere que ya exista un pedido delivery en estado READY
    log_info("   (Este test asume que ya existe un pedido delivery en estado READY)")
    log_info("   Puedes crear uno ejecutando: test_customer_flow.py")
    
    # ===== PASO 4: Intentar asignar (puede fallar si no hay pedidos) =====
    log_info("4. Intento de asignar domiciliario a pedido ficticio (ID=1)...")
    response = httpx.post(
        f"{BASE_URL}/delivery/orders/1/assign",
        headers=headers_cajero,
        json={"driver_id": driver['id']}
    )
    
    if response.status_code == 200:
        result = response.json()
        log_ok(f"Asignado: {result['message']}")
    else:
        log_info(f"No se pudo asignar (esperado si no hay pedido): {response.status_code}")
    
    # ===== PASO 5: Login como domiciliario =====
    log_info("5. Login como Domiciliario...")
    domiciliario_token = login("domiciliario1", "password123", "fastops")
    
    if not domiciliario_token:
        log_error("No se pudo loguear como domiciliario")
        log_info("Asegúrate de tener un usuario 'domiciliario1' con rol 'Domiciliario'")
        return
    log_ok("Logueado como Domiciliario")
    
    headers_domiciliario = {"Authorization": f"Bearer {domiciliario_token}"}
    
    # ===== PASO 6: Ver mis pedidos =====
    log_info("6. Listando mis pedidos asignados...")
    response = httpx.get(
        f"{BASE_URL}/delivery/my-orders",
        headers=headers_domiciliario
    )
    
    if response.status_code != 200:
        log_error(f"Error: {response.status_code} - {response.text}")
        return
    
    my_orders = response.json()
    log_ok(f"Tengo {my_orders['total_count']} pedidos asignados")
    
    if my_orders['total_count'] > 0:
        order = my_orders['orders'][0]
        log_info(f"   Pedido: {order['order_number']} - {order['delivery_address']}")
        
        # PASO 7: Marcar recogido
        log_info("7. Marcando pedido como recogido...")
        response = httpx.post(
            f"{BASE_URL}/delivery/orders/{order['id']}/picked-up",
            headers=headers_domiciliario
        )
        
        if response.status_code == 200:
            log_ok("Pedido marcado como RECOGIDO")
            
            # PASO 8: Marcar entregado
            log_info("8. Marcando pedido como entregado...")
            response = httpx.post(
                f"{BASE_URL}/delivery/orders/{order['id']}/delivered",
                headers=headers_domiciliario
            )
            
            if response.status_code == 200:
                log_ok("Pedido ENTREGADO exitosamente!")
            else:
                log_error(f"Error: {response.text}")
        else:
            log_error(f"Error al marcar recogido: {response.text}")
    else:
        log_info("No hay pedidos asignados para probar el flujo completo")
    
    print(f"\n{GREEN}✅ TEST COMPLETADO{RESET}")
    print("Para probar el flujo completo:")
    print("1. Ejecuta test_customer_flow.py para crear un pedido delivery")
    print("2. Cambia el estado del pedido a READY manualmente")
    print("3. Ejecuta este script de nuevo")


if __name__ == "__main__":
    main()
