---
name: Mobile Safe Area & Layout
description: Reglas obligatorias para layouts móviles y PWA. Respetar safe-area (notch, home indicator) y evitar que carrito/navegación queden pegados al borde superior.
---

# Mobile Safe Area & Layout

Esta skill define patrones **obligatorios** que deben mantenerse en pantallas móviles y PWA. No modificar ni eliminar estas reglas sin justificación.

## 1. Viewport (index.html)

El meta viewport DEBE incluir `viewport-fit=cover` para habilitar `env(safe-area-inset-*)` en iOS/Android:

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
```

Sin esto, las variables CSS `env(safe-area-inset-top)` y `env(safe-area-inset-bottom)` no funcionan correctamente.

## 2. Altura del viewport en móvil

Usar `100dvh` (Dynamic Viewport Height) en lugar de `100vh` para adaptación correcta en móvil (evita problemas con barra de direcciones del browser):

```tsx
// Correcto
h-[calc(100dvh-80px)]

// Evitar
h-[calc(100vh-80px)]
```

## 3. Padding superior (safe-area top)

En contenedores que ocupan la parte superior de la pantalla en móvil, aplicar padding-top con safe-area:

```tsx
pt-[max(1rem,env(safe-area-inset-top))] lg:pt-0
```

- `max(1rem, env(safe-area-inset-top))`: usa el mayor entre 16px y el inset del notch/Dynamic Island
- `lg:pt-0`: en desktop no se aplica

**Dónde aplicar:**
- Contenedor principal de páginas full-screen en móvil
- Header del carrito cuando es el panel visible
- Cualquier header sticky en vistas móviles

## 4. Padding inferior (safe-area bottom)

Para elementos fijados al fondo (botones, FABs, footer):

```tsx
// FABs flotantes
bottom-[max(2.5rem,calc(2.5rem+env(safe-area-inset-bottom)))]

// Footer con botón de acción (ej. CONTINUAR)
pb-[max(1rem,calc(1rem+env(safe-area-inset-bottom)))] lg:pb-4
```

Esto evita que los controles queden tapados por la barra de gestos/home indicator.

## 5. Navegación de categorías (CreateOrderPage)

Los chips de categorías (Todos, Bebidas, etc.) deben tener espacio superior en móvil:

```tsx
// Contenedor de filtros (search + categorías)
mt-2 lg:mt-0
```

## 6. Checklist antes de cambios

Si vas a modificar `CreateOrderPage.tsx`, `Sidebar.tsx` o layouts móviles, verifica:

- [ ] El meta viewport sigue con `viewport-fit=cover`
- [ ] El contenedor principal tiene `pt-[max(1rem,env(safe-area-inset-top))] lg:pt-0`
- [ ] El header del carrito tiene `pt-[max(1rem,env(safe-area-inset-top))] lg:pt-4`
- [ ] Los FABs usan `bottom-[max(2.5rem,calc(2.5rem+env(safe-area-inset-bottom)))]`
- [ ] El footer del carrito tiene `pb-[max(1rem,calc(1rem+env(safe-area-inset-bottom)))] lg:pb-4`
- [ ] El Sidebar tiene ancho 72px en móvil (icon-only) y `pt-[max(1rem,env(safe-area-inset-top))] lg:pt-4`, `mb-[max(0.5rem,env(safe-area-inset-bottom))] lg:mb-0`
- [ ] Se usa `100dvh` para altura en móvil, no `100vh`

## 7. Sidebar (navegación lateral)

### Ancho en móvil
En móvil el sidebar debe ser **estrecho (72px)** – solo iconos, sin etiquetas – para no ocupar la mitad de la pantalla:
- `width: 72px` en móvil (vs 256px en desktop expandido)
- Usar `isCompact = isCollapsed || !isDesktop` para forzar vista icon-only en móvil

### Safe-area
El Sidebar en móvil (drawer) debe respetar safe-area para que los iconos no queden pegados al notch:

```tsx
// Contenedor del contenido del sidebar
pt-[max(1rem,env(safe-area-inset-top))] lg:pt-4

// Sección inferior (System Status, etc.)
mb-[max(0.5rem,env(safe-area-inset-bottom))] lg:mb-0
```

## Referencia rápida

| Elemento           | Clase / valor                                                                 |
|--------------------|-------------------------------------------------------------------------------|
| Viewport           | `viewport-fit=cover` en meta                                                 |
| Altura móvil       | `h-[calc(100dvh-80px)]`                                                      |
| Padding top móvil  | `pt-[max(1rem,env(safe-area-inset-top))] lg:pt-0`                            |
| Padding bottom     | `pb-[max(1rem,calc(1rem+env(safe-area-inset-bottom)))] lg:pb-4`              |
| FABs bottom        | `bottom-[max(2.5rem,calc(2.5rem+env(safe-area-inset-bottom)))]`              |
| Sidebar content    | `pt-[max(1rem,env(safe-area-inset-top))] lg:pt-4`                            |
| Sidebar bottom     | `mb-[max(0.5rem,env(safe-area-inset-bottom))] lg:mb-0`                       |
