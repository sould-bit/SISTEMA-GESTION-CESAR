
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface UiState {
    accessDenied: boolean;
    isAccessDeniedBlocking: boolean;
    sidebarOpen: boolean;
}

const initialState: UiState = {
    accessDenied: false,
    isAccessDeniedBlocking: false,
    sidebarOpen: false,
};

const uiSlice = createSlice({
    name: 'ui',
    initialState,
    reducers: {
        setAccessDenied: (state, action: PayloadAction<{ isOpen: boolean; isBlocking?: boolean }>) => {
            state.accessDenied = action.payload.isOpen;
            state.isAccessDeniedBlocking = action.payload.isBlocking || false;
        },
        toggleSidebar: (state) => {
            state.sidebarOpen = !state.sidebarOpen;
        },
        setSidebarOpen: (state, action: PayloadAction<boolean>) => {
            state.sidebarOpen = action.payload;
        },
    },
});

export const { setAccessDenied, toggleSidebar, setSidebarOpen } = uiSlice.actions;
export default uiSlice.reducer;
