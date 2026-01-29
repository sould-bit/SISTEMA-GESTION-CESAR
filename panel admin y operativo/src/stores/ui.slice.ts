
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UiState {
    accessDenied: boolean;
}

const initialState: UiState = {
    accessDenied: false,
};

const uiSlice = createSlice({
    name: 'ui',
    initialState,
    reducers: {
        setAccessDenied: (state, action: PayloadAction<boolean>) => {
            state.accessDenied = action.payload;
        },
    },
});

export const { setAccessDenied } = uiSlice.actions;
export default uiSlice.reducer;
