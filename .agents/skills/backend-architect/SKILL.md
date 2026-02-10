---
name: backend_architect
description: Skill para asegurar que todas las modificaciones en el backend sigan las reglas de arquitectura de producción y parámetros históricos del proyecto.
---

# Skill: Backend Architect

Esta habilidad me permite actuar como un Ingeniero Principal para asegurar la calidad, escalabilidad y la integridad del sistema de gestión.

## 📋 Arquitectura de Capas (Estandarizada)
1. **Domain Layer (`app/models/`)**: Modelado de datos puro con `SQLModel`. Representa la "verdad" de la base de datos.
2. **Infrastructure Layer (`app/schemas/`)**: Contratos de entrada y salida con `Pydantic`. Ninguna data sale del API sin esquema.
3. **Application Layer (`app/services/`)**: Única ubicación para la lógica de negocio (costos, stock, validaciones).
4. **Presentation Layer (`app/api/`)**: Routers que solo orquestan requests y responses.

## 📦 Gestión de Inventario Multinivel
- **Nivel A (Directo)**: Descuento directo para productos sin receta (bebidas).
- **Nivel B (Recetas)**: Descuento automático de `IngredientInventory` basado en recetas.
- **FIFO & Batches**: Consumo obligatorio de insumos basado en `IngredientBatch`.
- **Restauración**: Reintegrar stock automáticamente en devoluciones o ediciones de órdenes.

## 🛡️ Integridad y Seguridad
- **Multi-tenant**: Filtrado estricto por `company_id` en cada consulta.
- **UUIDs**: Uso de UUIDv4 para ingredientes, recetas y lotes.
- **Type Safety**: Uso obligatorio de Python `typing` en firmas de funciones.
- **Precisión Financiera**: Prohibido el uso de `float`. Uso exclusivo de `Decimal` para precios y cantidades.

## 📋 Manejo de Errores y Calidad
- **Fail Fast**: Validaciones tempranas con Pydantic.
- **Logging**: Bloques `try/except` con logs detallados del error y contexto.
- **Zero Secrets**: Uso exclusivo de `.env` para configuraciones sensibles.
- **Tests**: Cada nueva funcionalidad o bugfix debe incluir/ejecutar tests en `tests/`.

## 🚀 Cómo usar esta Skill
Activa esta habilidad antes de realizar cambios estructurales en el backend para garantizar que el sistema mantenga su estándar de grado de producción.
