import { configureStore } from '@reduxjs/toolkit';

export const store = configureStore({
  reducer: {
    // Los reducers se agregarán en Fase 5
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
