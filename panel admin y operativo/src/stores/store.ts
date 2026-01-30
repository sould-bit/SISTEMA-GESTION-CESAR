import { configureStore } from '@reduxjs/toolkit';
import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';
import authReducer from './auth.slice';
import genesisReducer from './genesis.slice';
import uiReducer from './ui.slice';
import onboardingReducer from './onboarding.slice';

export const store = configureStore({
    reducer: {
        auth: authReducer,
        genesis: genesisReducer,
        ui: uiReducer,
        onboarding: onboardingReducer,
    },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
