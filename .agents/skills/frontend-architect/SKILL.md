---
name: frontend_architect
description: Skill para asegurar que todas las modificaciones en el frontend sigan las reglas de diseño premium y arquitectura basada en features, respetando el desacoplamiento de la lógica de negocio.
---

# Skill: Frontend Architect

Esta habilidad me permite actuar como un Lead Frontend Engineer para crear interfaces de "grado de producción" que sean visualmente impactantes y técnicamente puras.

## 🎨 Diseño y UX (Premium Standard)
1. **Estética Visual**:
   - Uso de gradientes suaves, sombras sutiles y micro-animaciones.
   - Tipografía moderna (**Inter** para lectura, **JetBrains Mono** para datos técnicos).
   - Efectos de **Glassmorphism**, desenfoques y elevación profesional.
   - Temas oscuros elegantes o interfaces de alto contraste.
2. **Interactividad**:
   - Estados de carga (**Skeletons/Spinners**) siempre presentes para mejorar la percepción de velocidad.
   - Feedback inmediato mediante **Toasts** y cambios de estado visuales tras cada acción.
   - **Responsividad Total**: La aplicación debe ser impecable en cualquier tamaño de pantalla (Mobile First/PWA Ready).

## 🏗️ Arquitectura de Código (Feature-Driven)
- **Organización**: Todo reside bajo `src/features/[feature_name]/`.
- **Estructura por Feature**:
   - `components/`: UI específica de la funcionalidad.
   - `pages/`: Vistas principales.
   - `types.ts`: Tipado estricto compartido.
- **Estado y Datos**:
   - **Remoto**: Uso de `@tanstack/react-query` para sincronización con el servidor.
   - **Global/UI**: Uso de `@reduxjs/toolkit` para estado de la interfaz y sesión.
   - **Formularios**: `react-hook-form` + `zod` para validaciones de esquema antes del envío.

## ⚖️ Regla de Oro: Desacoplamiento de Lógica
- **Backend Solo**: La lógica de negocio pesada (cálculos de inventario, costos con mermas, impuestos complejos) reside **EXCLUSIVAMENTE** en el Backend.
- **Frontend Puro**: El frontend se encarga de la **presentación, captura de datos y experiencia de usuario**. 
- No se deben replicar cálculos complejos del backend en el cliente para evitar inconsistencias; se debe confiar en las respuestas del API.

## 🛠️ Reglas Técnicas
- **TypeScript**: Prohibido el uso de `any`. Definir interfaces precisas para cada endpoint.
- **Tailwind CSS (v4)**: Uso de utilidades nativas y mantenimiento del sistema de diseño.
- **Iconos**: Uso de `lucide-react` para mantener una línea estética uniforme.

## 🚀 Cómo usar esta Skill
Activa esta habilidad para garantizar que la UI sea de primer nivel y que la arquitectura respete la pureza del modelo cliente-servidor establecido.
