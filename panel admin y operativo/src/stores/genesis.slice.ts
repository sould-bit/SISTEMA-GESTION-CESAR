import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface FoundationData {
    companyName: string;
    nitRut: string;
    slogan: string;
    logo?: string; // Base64 or URL
}

interface TerritoryData {
    branchName: string;
    address: string;
    phone: string;
    lat?: number;
    lng?: number;
}

interface CommandData {
    adminEmail: string;
    adminPassword: string;
    roles: string[]; // 'architect', 'commander', 'operator'
}

export interface GenesisState {
    currentStep: number;
    foundation: FoundationData;
    territory: TerritoryData;
    command: CommandData;
    // Supply data is now handled in the Setup Wizard
    isComplete: boolean;
}

const initialState: GenesisState = {
    currentStep: 1,
    foundation: {
        companyName: '',
        nitRut: '',
        slogan: ''
    },
    territory: {
        branchName: 'Sede Principal',
        address: '',
        phone: ''
    },
    command: {
        adminEmail: '',
        adminPassword: '',
        roles: ['architect']
    },
    isComplete: false
};

const genesisSlice = createSlice({
    name: 'genesis',
    initialState,
    reducers: {
        setStep: (state, action: PayloadAction<number>) => {
            state.currentStep = action.payload;
        },
        updateFoundation: (state, action: PayloadAction<Partial<FoundationData>>) => {
            state.foundation = { ...state.foundation, ...action.payload };
        },
        updateTerritory: (state, action: PayloadAction<Partial<TerritoryData>>) => {
            state.territory = { ...state.territory, ...action.payload };
        },
        updateCommand: (state, action: PayloadAction<Partial<CommandData>>) => {
            state.command = { ...state.command, ...action.payload };
        },
        completeGenesis: (state) => {
            state.isComplete = true;
        },
        resetGenesis: () => initialState
    }
});

export const { setStep, updateFoundation, updateTerritory, updateCommand, completeGenesis, resetGenesis } = genesisSlice.actions;
export default genesisSlice.reducer;
