---
name: E2E Testing Strategy
description: Standards and procedures for 100% realistic end-to-end testing with Playwright and Docker.
---

# 🧪 E2E Testing Strategy (Real User Simulation)

Este documento define la estrategia para pruebas End-to-End (E2E) mediante Playwright. Nuestro objetivo es garantizar la "calidad total" simulando el entorno de producción lo más fielmente posible.

## 🎯 Filosofía "Real World"
- **Cero Mocking de DB**: Los tests deben ejecutarse contra una base de datos PostgreSQL real (Dockerizada).
- **Cero Mocking de Backend**: El backend debe ejecutarse como un proceso real, conectado a la DB de prueba.
- **Flujos Completos**: Preferimos pocos tests largos que cubran procesos de negocio completos (ej: Crear Orden -> Cocina -> Entrega -> Pago) sobre muchos tests pequeños aislados.
- **Resilient Waiting**: Usar `await expect()` y `waitForResponse()` para manejar la asincronía de la UI y WebSockets. NUNCA usar `waitForTimeout()`.

## 🏗️ Arquitectura del Entorno de Test

Para evitar conflictos con el desarrollo local, el entorno de test usa **puertos dedicados**:

| Componente | Puerto Prod/Dev | Puerto TEST | Tecnología |
| :--- | :--- | :--- | :--- |
| **Base de Datos** | 5432 | **5433** | PostgreSQL (Docker) |
| **Backend API** | 8000 | **8001** | FastAPI (ASGI) |
| **Frontend** | 5173 | **5174** | React/Vite |

### Flujo de Inicialización
Antes de ejecutar cualquier test, el sistema de orquestación (`tests-e2e/utils/orchestrator.ts`) debe:
1.  **Docker Up**: Levantar contenedor `cesar_test_db`.
2.  **DB Reset**: Eliminar tablas viejas, ejecutar migraciones `alembic`, y poblar datos semilla (`manage.py seed`).
3.  **Start Services**:
    - Backend en puerto 8001 (ENV: `DB_PORT=5433`).
    - Frontend en puerto 5174 (ENV: `VITE_API_URL=http://localhost:8001`).
4.  **Health Check**: Esperar a que ambos servicios respondan "200 OK".

## 📋 Diseño de Escenarios y Alcance (Plantilla)

Antes de codificar un test, se debe definir su alcance siguiendo este formato modular. Esto garantiza que cualquier ingeniero (o IA) pueda entender la intención del test.

### Estructura de un Escenario (Template):
1. **ID/Nombre**: `E2E_0XX_Nombre_Del_Flujo`
2. **Roles Involucrados**: (ej: Mesero, Cocina, Admin)
3. **Pre-condiciones**: Estado de la DB y sesiones requeridas.
4. **Secuencia de Acciones**: Definición de pasos por rol.
5. **Validaciones Críticas**: Qué puntos NO pueden fallar (Trazabilidad 100%).

---

## 🏗️ Implementación Modular (Option B: POM)

Para maximizar la reutilización y legibilidad, se utiliza el patrón **Page Object Model**. Ningún test debe interactuar directamente con selectores CSS/IDs; debe hacerlo a través de métodos de una "Page".

### Ejemplo de Estándar en `pages/`:
- `LoginPage.ts`: Métodos para login exitoso, errores y cierre de sesión.
- `OrderModal.ts`: Componente compartido para ver detalles, solicitar cancelación y procesar rechazos.
- `TablesGrid.ts`: Interacción con el mapa de mesas y selección de pedidos.

---

## 📂 Organización del Código (`tests-e2e/`)

```text
tests-e2e/
├── specs/               # Escenarios de prueba (Business Flows)
│   ├── verified/        # Tests estables y aprobados
│   └── experimental/    # Tests en desarrollo
├── pages/               # Page Object Models (POM) - Abstracción de UI
│   ├── LoginPage.ts
│   ├── OrderPage.ts
│   └── KitchenBoard.ts
├── fixtures/            # Datos estáticos para seeds
├── utils/               # Scripts de infraestructura (DB reset, Auth setup)
├── global-setup.ts      # Configuración global de Playwright
└── playwright.config.ts # Configuración principal
```

## 📝 Convenciones de Código

### Page Object Model (POM)
Cada página o componente mayor debe tener su clase en `pages/`.
```typescript
// ✅ CORRECTO
await loginPage.loginAsWaiter();
await orderPage.addProduct('Coca Cola');

// ❌ INCORRECTO
await page.fill('#email', 'waiter@test.com');
await page.click('.btn-add-coke');
```

### Selectores Resilientes
Priorizar selectores accesibles sobre CSS/XPath frágiles.
1.  `getByRole('button', { name: 'Guardar' })` (Mejor)
2.  `getByTestId('submit-order')` (Bueno)
3.  `page.locator('.clase-random')` (Evitar)

## 🏃 Comandos de Ejecución

- **Ejecutar Toda la Suite**: `npm run test:e2e`
- **Modo Debug (UI)**: `npm run test:e2e:ui`
- **Resetear Solo DB**: `npm run db:reset`

---
**Nota**: Si modificas el modelo de datos (Backend), recuerda actualizar los `fixtures` y ejecutar una migración nueva en el entorno de test.
