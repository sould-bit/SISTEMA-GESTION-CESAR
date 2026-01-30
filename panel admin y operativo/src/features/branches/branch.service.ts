import { api } from '../../lib/api';

export interface Branch {
    id: number;
    company_id: number;
    name: string;
    code: string;
    address: string | null;
    phone: string | null;
    is_main: boolean;
    is_active: boolean;
    created_at: string;
    updated_at: string | null;
    user_count: number;
}

export interface BranchList {
    items: Branch[];
    total: number;
    page: number;
    size: number;
}

export interface BranchCreate {
    name: string;
    code: string;
    address?: string;
    phone?: string;
    is_main?: boolean;
}

export interface BranchUpdate {
    name?: string;
    code?: string;
    address?: string;
    phone?: string;
    is_main?: boolean;
    is_active?: boolean;
}

export const BranchService = {
    async list(includeInactive = false): Promise<BranchList> {
        const response = await api.get('/branches', {
            params: { include_inactive: includeInactive }
        });
        return response.data;
    },

    async get(id: number): Promise<Branch> {
        const response = await api.get(`/branches/${id}`);
        return response.data;
    },

    async create(data: BranchCreate): Promise<Branch> {
        const response = await api.post('/branches', data);
        return response.data;
    },

    async update(id: number, data: BranchUpdate): Promise<Branch> {
        const response = await api.put(`/branches/${id}`, data);
        return response.data;
    },

    async delete(id: number): Promise<void> {
        await api.delete(`/branches/${id}`);
    },

    async setAsMain(id: number): Promise<Branch> {
        const response = await api.post(`/branches/${id}/set-main`);
        return response.data;
    }
};
