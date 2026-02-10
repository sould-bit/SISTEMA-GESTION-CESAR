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
            owner_name: state.auth.fullName, // Use the explicit full name from Auth step
            username: state.auth.username, // Send the explicit username
            owner_email: state.auth.adminEmail,
            owner_phone: state.foundation.phone,
            password: state.auth.adminPassword,
            // Datos Legales
            tax_id: state.foundation.nitRut,
            legal_name: state.foundation.companyName, // As per user request: legal name same as organization name
            plan: 'free',
            // New fields for branch
            branch_name: state.territory.branchName,
            branch_address: state.territory.address
        };

        // 2. Register Company
        console.log('📡 Sending registration signal...', registrationPayload);
        const registerResponse = await api.post('/auth/register', registrationPayload);
        const { access_token } = registerResponse.data;

        if (!access_token) {
            throw new Error('No access token received from registration');
        }

        // 3. Store token in Redux FIRST so the Axios request interceptor can find it
        // The interceptor reads from store.getState().auth.token, NOT from api.defaults
        console.log('🔑 Storing access token in Redux store...');
        dispatch(setCredentials({
            token: access_token,
            user: null as unknown as User // Temporary: will be updated with full profile
        }));

        // 4. Now fetch full user profile (interceptor will attach the token automatically)
        console.log('👤 Fetching commander profile...');
        const userResponse = await api.get<User>('/auth/me');
        const user = userResponse.data;

        // 5. Update Redux with full user profile
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
