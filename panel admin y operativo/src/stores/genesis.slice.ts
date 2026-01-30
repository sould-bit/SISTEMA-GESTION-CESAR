import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface FoundationData {
    companyName: string;
    nitRut: string;
    ownerName: string; // Nombre del Fundador/Dueño
    phone: string;
    logo?: string; // Base64 or URL
}

interface TerritoryData {
    branchName: string;
    address: string;
    lat?: number;
    lng?: number;
}

interface AuthData {
    adminEmail: string;
    adminPassword: string;
    fullName: string;
    username: string;
}

export interface GenesisState {
    currentStep: number;
    foundation: FoundationData;
    territory: TerritoryData;
    auth: AuthData;
    // Supply data is now handled in the Setup Wizard
    isComplete: boolean;
}

const initialState: GenesisState = {
    currentStep: 1,
    foundation: {
        companyName: '',
        nitRut: '',
        ownerName: '',
        phone: ''
    },
    territory: {
        branchName: 'Sede Principal',
        address: ''
    },
    auth: {
        adminEmail: '',
        adminPassword: '',
        fullName: '',
        username: ''
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
        updateAuth: (state, action: PayloadAction<Partial<AuthData>>) => {
            state.auth = { ...state.auth, ...action.payload };
        },
        completeGenesis: (state) => {
            state.isComplete = true;
        },
        resetGenesis: () => initialState
    }
});

export const { setStep, updateFoundation, updateTerritory, updateAuth, completeGenesis, resetGenesis } = genesisSlice.actions;
export default genesisSlice.reducer;
