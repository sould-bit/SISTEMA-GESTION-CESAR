---
name: xstate_model_driven_dev
description: Skill para implementar y mantener la lógica de la aplicación utilizando XState y el Stately Inspector, siguiendo los principios de Model-Driven Development (MDD) y el Modelo de Actores.
---

# Skill: XState & Model-Driven Development (MDD)

Esta habilidad asegura que la lógica compleja de la aplicación (POS, KDS, Inventario) sea predecible, visualizable y robusta mediante el uso de máquinas de estado y el **Modelo de Actores**.

## 🧠 Arquitectura de Actores (Advanced)
1.  **Encapsulamiento Total**: Cada máquina es un actor independiente. No comparten estado; se comunican mediante mensajes (eventos).
2.  **Jerarquía de Agentes**:
    - **Invoke**: Para actores con ciclo de vida vinculado a un estado (ej. una llamada a API o un sub-proceso de validación). Se detienen automáticamente al salir del estado.
    - **Spawn**: Para actores dinámicos con ciclo de vida independiente. Úselo para procesos que deben persistir o ser creados bajo demanda (ej. múltiples temporizadores de mesa o agentes de chat).
    - **Limpieza**: Siempre detenga actores hijos (`stopChild`) y limpie referencias en `context` para evitar fugas de memoria.
3.  **Comunicación Inter-Actor**:
    - **Explicit ID**: Prefiera usar IDs claros para `invoke` (ej. `id: 'fetch-order'`).
    - **sendTo**: Use `sendTo(({ context }) => context.actorRef, { type: 'MSG' })` para comunicación dirigida.
    - **sendParent**: Úselo con moderación; es mejor pasar el `ActorRef` del padre explícitamente en el `input` del hijo para mantener el tipado fuerte.

## 🛠️ Lógica Compleja y Resiliencia
- **Decision Matrix**: Use arreglos de transiciones con **Guards** (`and`, `or`, `not`). La primera que evalúe a `true` será la ganadora.
- **Invocaciones Asíncronas**: 
    - **Prohibido**: Ejecutar `async/await` dentro de acciones `assign` o `actions` simples (fire-and-forget).
    - **Mandatorio**: Usar `invoke` con `src: fromPromise(...)`. Maneje sistemáticamente los eventos `onDone` y `onError`. Esto permite que la máquina capture errores de red y decida si reintentar o cambiar de estado.
- **Acciones Encoladas**: Use `enqueueActions` para asegurar que los efectos secundarios ocurran en el orden correcto durante una transición.

## ⚡ Integración con React (@xstate/react)
- **useMachine**: Para máquinas locales al componente.
- **useActorRef**: Para crear referencias persistentes que no provocan re-renders innecesarios.
- **useSelector**: **Crítico para rendimiento**. No desestructure todo el `state`. Use selectores para escuchar solo los datos específicos que la UI necesita renderizar.
    ```typescript
    const status = useSelector(actorRef, (state) => state.value);
    ```
- **Global Store**: Centralice actores globales (ej. Auth, Carrito) en un `React.Context` para que puedan ser accedidos y observados desde cualquier parte de la App sin re-inicializaciones.

## 🤖 Orquestación de Inteligencia Artificial (LLM)
Al integrar agentes inteligentes:
1.  **Estados de Pensamiento**: Modele estados explícitos como `thinking`, `streaming`, `validating`.
2.  **Memoria en Context**: Mantenga el historial de la conversación en el `context`. Use `assign` para acumular mensajes.
3.  **Guards de Validación**: Use guards para verificar si la respuesta del LLM tiene el formato correcto antes de transicionar a `success`.
4.  **Herramientas como Actores**: Si el AI necesita llamar a una función (ej. "consultar stock"), invoque esa función como un actor hijo y devuelva el resultado al flujo principal.

## 🔍 Stately Inspector: Living Documentation
- **Trazabilidad**: Use el Inspector para ver el **Diagrama de Secuencia**. Esto muestra exactamente quién envió qué evento y en qué orden.
- **Simulación Directa**: No pierda tiempo recreando estados difíciles manualmente. Envíe eventos directamente desde el Inspector para forzar flujos de error o estados de borde.
- **Snapshot Testing**: El estado visual en Stately es la documentación técnica del negocio disponible en tiempo real para el equipo.

## 🚀 Cómo usar esta Skill
Activa esta habilidad para transformar el código imperativo "espagueti" en una red de actores coordinados, permitiendo que el sistema escale a 10x sin perder control sobre los flujos críticos.
