# 🧪 E2E Testing Suite (End-to-End)

Este espacio dedicado en `tests-e2e` implementa la estrategia de pruebas End-to-End con Playwright y Docker para asegurar la calidad del sistema completo.

## 📘 Estándares y Documentación
Toda la documentación detallada, filosofía, arquitectura y convenciones de código se encuentran en la **Skill Dedicada**:

👉 [E2E Testing Skill](../../.agents/skills/tests-e2e/SKILL.md)

Consúltalo para entender:
- **Arquitectura**: Puertos 5433 (DB), 8001 (Backend), 5174 (Frontend).
- **Filosofía**: Tests reales, NO mocks.
- **Estructura**: Page Objects, Specs, Fixtures.

## 🚀 Inicio Rápido

1.  **Configurar Entorno**:
    Copia `.env.example` a `.env` y ajusta las credenciales si es necesario (por defecto funcionan con Docker).

2.  **Levantar Base de Datos (Docker)**:
    ```bash
    docker-compose -f docker-compose.test.yml up -d
    ```

3.  **Ejecutar Tests**:
    ```bash
    npm install
    npm run test:e2e
    ```

4.  **Ver Reporte / Debug (UI)**:
    ```bash
    npm run test:e2e:ui
    ```

---
**Nota**: El comando `npm run test:e2e` se encargará de resetear la DB, ejecutar migraciones, poblar datos semilla y levantar los servicios backend/frontend automáticamente gracias al `global-setup`.
