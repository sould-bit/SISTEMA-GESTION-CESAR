import { api } from '../../lib/api';
import { AppDispatch } from '../../stores/store';
import { setCredentials, User } from '../../stores/auth.slice';
import { GenesisState } from '../../stores/genesis.slice';
import { AxiosError } from 'axios';



export const submitGenesis = async (
    state: GenesisState,
    dispatch: AppDispatch
): Promise<void> => {
    try {
        console.log('🚀 Starting Genesis Protocol sequence...');

        // 1. Prepare Registration Payload
        // We include branch details directly now that the backend supports them
        const registrationPayload = {
            company_name: state.foundation.companyName,
            company_slug: state.foundation.companyName.toLowerCase().replace(/[^a-z0-9-]/g, '-'),
            owner_name: state.foundation.companyName, // Or ask for owner name in step 1/3
            owner_email: state.command.adminEmail,
            passwor: state.command.adminPassword, // TYPO FIX: password
            password: state.command.adminPassword,
            plan: 'free',
            // New fields for branch
            branch_name: state.territory.branchName,
            branch_address: state.territory.address,
            branch_phone: state.territory.phone
        };

        // 2. Register Company
        console.log('📡 Sending registration signal...', registrationPayload);
        const registerResponse = await api.post('/auth/register', registrationPayload);
        const { access_token } = registerResponse.data;

        if (!access_token) {
            throw new Error('No access token received from registration');
        }

        // 3. Set Auth Header & Get Full User
        // We need to set the header manually for the immediate next requests
        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

        console.log('👤 Fetching commander profile...');
        const userResponse = await api.get<User>('/auth/me');
        const user = userResponse.data;

        // 4. Update Redux State
        dispatch(setCredentials({
            token: access_token,
            user: user
        }));

        // 5. Seed Inventory (Categories & Products) - MOVED TO SETUP WIZARD
        // The Genesis Protocol now concludes after registration and auth.

        console.log('✅ Genesis Protocol Complete (Authentication Established).');

        console.log('✅ Genesis Protocol Complete.');

    } catch (error) {
        console.error('❌ Genesis Protocol Failed:', error);
        if (error instanceof AxiosError) {
            throw new Error(error.response?.data?.detail || 'Error en el despliegue del protocolo');
        }
        throw error;
    }
};
