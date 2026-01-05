FastOps — Documento Maestro de Arquitectura y Especificación Técnica V4.0
Versión: 4.0 (Edición Unificada y Definitiva)
Fecha: Enero 2026
Autor: Jhon (CEO) / Robert Arquitecto
Estado: Biblia del Proyecto para Desarrollo
📋 VISIÓN EJECUTIVA
FastOps es una Plataforma SaaS de Inteligencia Operativa para negocios de comida rápida.
Se diferencia de un POS tradicional en tres pilares:
Verdad Operativa ("Receta Viva"): Auditoría de inventario basada en balance de masa para detectar robos y mermas.
Alto Rendimiento: Arquitectura asíncrona que no se bloquea en horas pico.
Ciclo Completo: Desde el pedido del cliente en su móvil (PWA) hasta la entrega del domiciliario (Logística).
1. PRINCIPIOS DE ARQUITECTURA (NO NEGOCIABLES)
1.1 Reglas de Oro
Multi-Tenant Nativo: Aislamiento total. Todo query SQL debe filtrar por company_id.
Zero-Blocking: Procesos pesados (impresión, cálculos de auditoría) van a colas asíncronas (Redis/Celery).
Conteo Ciego (Blind Count): La UI de auditoría NUNCA muestra el stock teórico al empleado.
Local-First Resilience: Capacidad de operar funciones básicas con intermitencia de red.
1.2 Stack Tecnológico
Frontend: React 18 + TypeScript + TailwindCSS + Redux Toolkit (PWA).
Backend: FastAPI (Python 3.11+) Async.
Base de Datos: PostgreSQL 16+ + SQLModel (ORM).
Colas & Caché: Redis + Celery.
Tiempo Real: Socket.IO.
Infraestructura: Docker Compose + VPS Linux + Nginx.
2. MODELO DE DATOS UNIFICADO
Estructura completa de la base de datos para soportar todas las funcionalidades.
2.1 Núcleo SaaS (Administrativo)
companies: El cliente que paga. (id, name, slug, plan, is_active).
branches: Sucursales. (id, company_id, name, code, timezone).
users: Empleados con RBAC. (id, company_id, branch_id, role, password_hash).
2.2 Catálogo y Modificadores (El Menú)
products: Platos base. (id, name, price, category_id).
product_modifiers: Configuración de extras.
id, product_id, name (ej: "Extra Queso"), price, modifier_type ('addition'/'exclusion').
recipes: Receta teórica del producto.
modifier_recipes: Receta teórica del modificador (ej: Extra Carne = 150g de carne).
2.3 Motor de Pedidos (Transactional)
orders: Cabecera.
consecutive (Generado por sucursal: M-NORTE-001).
status: queued -> cooking -> ready -> assigned -> delivered.
channel: pos, client_pwa, waiter.
order_items: Detalle.
order_item_modifiers: Personalización del cliente.
order_item_id, modifier_id, quantity, price_at_moment.
2.4 Inventario e Inteligencia (Audit)
inventory_items: Insumos (current_stock TEÓRICO).
movements: Entradas (Compras) y Salidas (Ventas/Mermas).
inventory_audits: Evento de conteo. (audit_mode: top10/custom/full).
inventory_audit_details: La inteligencia.
snapshot_theoretical (Lo que el sistema esperaba).
physical_count (Lo que se contó).
real_grammage (Cálculo estadístico: Consumo Real / Ventas).
deviation_percent (Diferencia vs Receta).
3. MÓDULOS FUNCIONALES DEL SISTEMA
3.1 Módulo PWA Cliente (Pedidos Online)
Web App ligera para que el cliente final pida desde su mesa o casa.
Catálogo Visual: Fotos y categorías.
Builder de Pedido:
Selección de producto.
Modificadores: Checkboxes para Adiciones (Suma precio) y Exclusiones.
Notas de cocina.
Checkout: Tipo de entrega (Mesa/Llevar/Domicilio) + Dirección/GPS.
3.2 Módulo POS & Caja (Dispatcher)
El centro de comando del restaurante.
Recepción Asíncrona: Confirmación de pedido en <200ms.
Gestión de Despachos:
Columna "Listos para Entregar".
Lista de Domiciliarios (Disponibles/Ocupados).
Asignación: Drag & Drop del pedido al domiciliario.
Cierre de Caja: Arqueo de dinero ciego (Esperado vs Real).
3.3 Módulo de Cocina (KDS) & Impresión
KDS (Pantalla): Feed en tiempo real (WebSockets) de nuevas comandas.
Cola de Impresión:
Backend envía tarea a Redis.
Worker imprime en background.
Circuit Breaker: Si falla la impresora, alerta visual en KDS.
3.4 Módulo de Inventario Inteligente ("Receta Viva")
Modos de Auditoría:
⚡ Flash (Top 10): Carga los 10 insumos más costosos (Pareto).
🎯 Custom: Selección manual.
📦 Full: Inventario total.
Conteo Ciego: UI simple para ingresar cantidades físicas sin ver el teórico.
Motor de Análisis: Calcula y reporta desviaciones de gramaje automáticamente.
3.5 Módulo de Domiciliarios (Driver App)
Notificaciones: "Nuevo Pedido Asignado".
Detalle: Dirección (waze/maps), Teléfono cliente, Total a cobrar.
Estados: "Recogido" -> "Entregado" (Captura GPS).
4. FLUJOS DE NEGOCIO CRÍTICOS
4.1 Flujo de Pedido Completo (Con Extras)
Cliente (PWA): Pide "Hamburguesa Doble" + "Extra Tocineta" + "Sin Cebolla".
Backend:
Calcula Total: Precio Base + Precio Tocineta.
Descuento Inventario: Receta Hamburguesa + Receta Tocineta.
Encola impresión y notifica a Cocina (Socket).
Cocina: Ve comanda con nota resaltada "SIN CEBOLLA". Marca "Listo".
Caja: Ve pedido en columna "Listo". Asigna a Domiciliario "Juan".
Domiciliario: Recibe alerta, recoge y entrega.
4.2 Flujo de Auditoría "Receta Viva"
Gerente: Inicia "Auditoría Flash" (Top 10 Carnes).
Cocina: Pesa la carne y escribe "5.2 Kg". Envía.
Sistema (Background):
Calcula Consumo Real: (Inicial + Compras) - 5.2kg.
Busca Ventas: Hamburguesas vendidas + Extras de carne vendidos.
Divide: Consumo Real / Unidades.
Resultado: Genera alerta: "Cuidado: Estás gastando 180g por carne en vez de 150g".
5. API ENDPOINTS (SPEC RESUMIDA)
Cliente Final
GET /api/v1/client/menu/{slug} (Público)
POST /api/v1/client/orders (Crea pedido con modificadores)
Operación
POST /api/v1/orders/{id}/assign (Asignar driver)
POST /api/v1/orders/{id}/status (Cambio estado cocina)
GET /api/v1/drivers/available (Lista para dispatcher)
Inventario
GET /api/v1/inventory/audit-template?mode=top10
POST /api/v1/inventory/audit (Cierra auditoría y ajusta stock)
GET /api/v1/reports/intelligence (Dashboard desviaciones)
6. PLAN DE DESARROLLO (ROADMAP CONSOLIDADO)
🏁 FASE 1: CIMIENTOS (Semanas 1-2)
Setup Infraestructura (Docker, Nginx).
Auth Multi-Tenant & RBAC.
CRUD Productos, Categorías y Modificadores.
🚀 FASE 2: MOTOR DE VENTAS (Semanas 3-4)
Backend de Pedidos (Lógica de precios y descuento de inventario complejo).
PWA Cliente (Catálogo y Carrito).
Sistema de Impresión Asíncrono (Redis).
🚚 FASE 3: LOGÍSTICA Y COCINA (Semanas 5-6)
KDS (Pantalla Cocina) con WebSockets.
Dispatcher (Panel Caja) para asignación.
App Domiciliario (Vista móvil).
🧠 FASE 4: INTELIGENCIA DE INVENTARIO (Semanas 7-8)
Lógica de Movimientos y Kardex.
Algoritmo "Receta Viva".
UI de Auditoría (Wizard de conteo).
Dashboard de Reportes Financieros.
📦 FASE 5: LANZAMIENTO (Semana 9)
Pruebas de Carga (Stress Testing).
Despliegue Producción.
7. ANEXO: INFRAESTRUCTURA DE ALTO RENDIMIENTO
Para garantizar la estabilidad:
Base de Datos: PostgreSQL con índices en company_id, created_at y status.
Cache Strategy: Redis para sesiones de usuario y menú del cliente (evitar hits a DB).
Workers: Celery configurado con autoscale para procesar picos de impresión y cálculos de auditoría.
Firma de Aprobación: Robert Arquitecto
Versión: 4.0 Definitiva
