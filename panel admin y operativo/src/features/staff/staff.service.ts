import { api } from '../../lib/api';

export interface User {
    id: number;
    username: string;
    email: string;
    full_name: string;
    role: string; // code
    role_id: string; // uuid
    is_active: boolean;
    company_id: number;
}

export interface CreateUserDto {
    username: string;
    email: string;
    password: string;
    full_name: string;
    role_id: string;
}

export interface UpdateUserDto {
    username?: string;
    email?: string;
    full_name?: string;
    role_id?: string;
    is_active?: boolean;
    password?: string;
}

export interface Role {
    id: string;
    name: string;
    code: string;
    description: string;
}

export const StaffService = {
    getUsers: async () => {
        const response = await api.get<User[]>('/users/');
        return response.data;
    },

    createUser: async (data: CreateUserDto) => {
        const response = await api.post<User>('/users/', data);
        return response.data;
    },

    updateUser: async (id: number, data: UpdateUserDto) => {
        const response = await api.put<User>(`/users/${id}`, data);
        return response.data;
    },

    deleteUser: async (id: number) => {
        await api.delete(`/users/${id}`);
    },

    getRoles: async () => {
        const response = await api.get<Role[]>('/rbac/roles');
        return response.data;
    },

    fixRoles: async () => {
        const response = await api.post<{ message: string }>('/users/fix-roles');
        return response.data;
    }
};
