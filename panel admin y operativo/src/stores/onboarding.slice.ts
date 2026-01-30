import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export type OnboardingStep = 'create_users' | 'create_roles' | 'assign_permissions' | 'create_branches' | 'finished';

export interface OnboardingState {
    isActive: boolean;
    currentStep: OnboardingStep;
    hasCompletedGenesis: boolean;
}

const initialState: OnboardingState = {
    isActive: false,
    currentStep: 'create_users',
    hasCompletedGenesis: false,
};

const onboardingSlice = createSlice({
    name: 'onboarding',
    initialState,
    reducers: {
        startOnboarding: (state) => {
            state.isActive = true;
            state.currentStep = 'create_users';
            state.hasCompletedGenesis = true;
        },
        advanceStep: (state, action: PayloadAction<OnboardingStep>) => {
            state.currentStep = action.payload;
        },
        finishOnboarding: (state) => {
            state.isActive = false;
            state.currentStep = 'finished';
        },
        resetOnboarding: (state) => {
            state.isActive = false;
            state.currentStep = 'create_users';
            state.hasCompletedGenesis = false;
        }
    },
});

export const { startOnboarding, advanceStep, finishOnboarding, resetOnboarding } = onboardingSlice.actions;
export default onboardingSlice.reducer;
