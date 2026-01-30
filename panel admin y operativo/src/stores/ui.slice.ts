
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface UiState {
    accessDenied: boolean;
    isAccessDeniedBlocking: boolean;
}

const initialState: UiState = {
    accessDenied: false,
    isAccessDeniedBlocking: false,
};

const uiSlice = createSlice({
    name: 'ui',
    initialState,
    reducers: {
        setAccessDenied: (state, action: PayloadAction<{ isOpen: boolean; isBlocking?: boolean }>) => {
            state.accessDenied = action.payload.isOpen;
            state.isAccessDeniedBlocking = action.payload.isBlocking || false;
        },
    },
});

export const { setAccessDenied } = uiSlice.actions;
export default uiSlice.reducer;
