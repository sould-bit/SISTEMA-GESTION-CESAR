import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface UiState {
    accessDenied: boolean;
    isAccessDeniedBlocking: boolean;
    sidebarOpen: boolean;
    sidebarCollapsed: boolean;
    requiredPermission?: string;     // Nombre amigable del permiso (ej. "Actualizar pedidos")
    requiredPermissionCode?: string; // Código técnico (ej. "orders.update")
    actionName?: string;             // Acción que se intentó (ej. "Aceptar y preparar pedido")
}

const initialState: UiState = {
    accessDenied: false,
    isAccessDeniedBlocking: false,
    sidebarOpen: false,
    sidebarCollapsed: true,
};

const uiSlice = createSlice({
    name: 'ui',
    initialState,
    reducers: {
        setAccessDenied: (state, action: PayloadAction<{
            isOpen: boolean;
            isBlocking?: boolean;
            requiredPermission?: string;
            requiredPermissionCode?: string;
            actionName?: string;
        }>) => {
            state.accessDenied = action.payload.isOpen;
            state.isAccessDeniedBlocking = action.payload.isBlocking || false;
            state.requiredPermission = action.payload.requiredPermission;
            state.requiredPermissionCode = action.payload.requiredPermissionCode;
            state.actionName = action.payload.actionName;
        },
        toggleSidebar: (state) => {
            state.sidebarOpen = !state.sidebarOpen;
        },
        setSidebarOpen: (state, action: PayloadAction<boolean>) => {
            state.sidebarOpen = action.payload;
        },
        toggleSidebarCollapsed: (state) => {
            state.sidebarCollapsed = !state.sidebarCollapsed;
        },
        setSidebarCollapsed: (state, action: { payload: boolean }) => {
            state.sidebarCollapsed = action.payload;
        },
    },
});

export const { setAccessDenied, toggleSidebar, setSidebarOpen, toggleSidebarCollapsed, setSidebarCollapsed } = uiSlice.actions;
export default uiSlice.reducer;
