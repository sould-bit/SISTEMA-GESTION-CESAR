# 🚀 FastOps Manager - Frontend

Panel Administrativo y Operativo para la plataforma FastOps (Sistema de Gestión para Restaurantes). 
Desarrollado con **React**, **TypeScript**, **Vite** y **Tailwind CSS v4**.

## 🛠️ Tecnologías

Este proyecto utiliza un stack moderno y robusto:

- **Core**: React 18 + TypeScript
- **Build Tool**: Vite 5
- **Estilos**: Tailwind CSS v4 (Nueva generación) + PostCSS
- **UI Components**: Shadcn/UI (Radix Primitives) + Lucide Icons + Material Symbols
- **Estado Global**: Redux Toolkit (Auth Slice, Store typed)
- **Data Fetching**: Axios (con interceptores para JWT) + TanStack Query (pendiente de integrar full)
- **Routing**: React Router DOM v6.28 (Data API Router)
- **Formularios**: React Hook Form + Zod (Validación de esquemas)

## 📂 Estructura del Proyecto

El proyecto sigue una arquitectura **Feature-Based** escalable:

```
src/
├── components/         # Componentes compartidos
│   ├── layout/         # Layouts (AuthLayout, MainLayout)
│   └── ui/             # Componentes base (Button, Input, etc - Shadcn)
├── config/             # Variables de entorno y configuraciones globales
├── features/           # Módulos de negocio (Auth, Products, Orders, etc)
│   └── auth/           # Login, Register, Auth Components
├── hooks/              # Custom Hooks globales
├── lib/                # Utilidades de infraestructura (api client, utils)
├── routes/             # Definición de rutas (Router)
├── stores/             # Estado global (Redux slices)
└── types/              # Definiciones de tipos globales
```

## ✨ Funcionalidades Implementadas (Fase Actual)

### 1. Autenticación (`/features/auth`)
- **Login**: Autenticación persistente con JWT. Integrado con endpoint `/auth/token`.
- **Registro de Empresa**: Flujo de registro multi-tenant (`/auth/register-company`).
- **Validación**: Esquemas robustos con Zod (email, password match, campos requeridos).
- **Persistencia**: Token almacenado en LocalStorage y sincronizado con Redux.

### 2. Infraestructura UI
- **Tailwind v4 Config**: Variables CSS nativas (`@theme`), modo oscuro forzado (`class="dark"`), paleta de colores personalizada (`asphalt`, `fastops-orange`).
- **Layouts**:
    - `AuthLayout`: Diseño centrado con fondo animado para pantallas públicas.
    - `MainLayout`: Estructura Dashboard con Sidebar y Header para rutas protegidas.
- **Error Boundary**: Pantalla de error global (`ErrorPage`) para capturar fallos de ruteo (404) o excepciones no controladas.

### 3. Networking
- **Cliente API (`lib/api.ts`)**:
    - Base URL dinámica (env vars).
    - **Interceptor de Request**: Inyecta automáticamente el `Bearer Token`.
    - **Interceptor de Response**: Manejo centralizado de errores 401 (Logout automático).

## 🚀 Instalación y Uso

1. **Instalar dependencias**:
   ```bash
   npm install
   ```

2. **Correr servidor de desarrollo**:
   ```bash
   npm run dev
   ```
   
   El servidor iniciará en `http://localhost:5173` (o siguiente puerto disponible).

3. **Construir para producción**:
   ```bash
   npm run build
   ```

4. **Linting**:
   ```bash
   npm run lint
   ```

## 🎨 Guía de Estilos

El sistema utiliza la fuente **Plus Jakarta Sans** para textos y **Material Symbols Outlined** para íconos.

- **Colores Principales**:
    - `bg-asphalt` (#0F172A): Fondo principal oscuro.
    - `text-fastops-orange` (#FF6B00): Color de acento/brand.
    - `bg-alert-red` (#EF4444): Errores.
    - `bg-success-green` (#10B981): Éxito/Estado activo.

---
© 2026 FastOps Technologies Inc.
