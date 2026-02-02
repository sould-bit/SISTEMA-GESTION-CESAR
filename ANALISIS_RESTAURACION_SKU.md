# Análisis y Propuesta: Gestión de SKU en Restauración de Insumos

## 1. Situación Actual
Al eliminar un insumo, el sistema realiza un "Soft Delete" (marcado lógico) y modifica el SKU automáticamente para liberarlo.

**Comportamiento de Eliminación:**
- **SKU Original:** `ING-CARNE-001`
- **SKU Eliminado:** `ING-CARNE-001-DEL-1706645823`
- **Estado:** `is_active = False`

**Problema:**
Al restaurar el insumo (cambiando `is_active = True`), el SKU **mantiene el sufijo** `-DEL-{timestamp}`. Esto ensucia la base de datos y confunde al usuario, ya que el código de barras o identificador visual ya no coincide con el original.

## 2. Opciones de Solución

### Opción A: Restauración Automática de SKU (Recomendada)
El sistema intenta automáticamente revertir el SKU a su estado original al momento de restaurar.

*   **Flujo:**
    1.  Frontend envía solicitud de restauración.
    2.  Backend detecta patrón `-DEL-` y extrae el SKU original.
    3.  Backend verifica si el SKU original está libre.
    4.  **Si está libre:** Se restaura el SKU original.
    5.  **Si está ocupado:** Se mantiene el SKU con sufijo (o se añade `-RESTORED`) y se notifica al usuario.

*   **Pros:** Mejor experiencia de usuario (UX invisible), mantiene la limpieza de datos.
*   **Contras:** Requiere lógica extra en el backend para manejar colisiones (si ya creaste otro producto con el mismo SKU mientras el original estaba borrado).

### Opción B: Prompt al Usuario (Intermedio)
Al dar clic en "Restaurar", se abre un modal pidiendo confirmar el SKU deseado.

*   **Flujo:**
    1.  Usuario clic en "Restaurar".
    2.  Modal muestra: *"El SKU actual es ...-DEL-..., ¿deseas cambiarlo a [SKU Original]?"*
    3.  Usuario confirma o edita.

*   **Pros:** Control total del usuario, evita errores automáticos.
*   **Contras:** Añade un paso extra (fricción) en un proceso que debería ser rápido.

### Opción C: Edición Manual Posterir (Status Quo)
El usuario restaura el item (quedando con `-DEL-...`) y luego debe entrar a "Editar" para corregir el SKU manualmente.

*   **Pros:** Cero costo de desarrollo inmediato.
*   **Contras:** Pésima UX, propenso a olvidos, deja "basura" en los códigos.

## 3. Recomendación Técnica

Se sugiere implementar la **Opción A (Automática)** con una pequeña modificación en el backend (`ingredients.py` o `ingredient_service.py`).

**Lógica propuesta para el Backend (`update` override o lógica pre-update):**

```python
if is_active is True and ingredient.sku.endswith("-DEL-..."):
    original_sku = extract_original(ingredient.sku)
    if is_sku_available(original_sku):
        ingredient.sku = original_sku
```

**Plan de Acción Sugerido:**
1.  Modificar `IngredientService.update` para interceptar la reactivación (`is_active: true`).
2.  Si el SKU tiene el patrón de borrado, intentar sanearlo.
3.  Si falla por duplicado, dejarlo como está y retornar una alerta no bloqueante (o simplemente éxito con el SKU modificado).

---
*Este documento sirve de base para la toma de decisión sobre la implementación de la mejora en el módulo de inventarios.*
