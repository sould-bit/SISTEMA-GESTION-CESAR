import { api } from '../../lib/api';

export interface User {
    id: number;
    username: string;
    email: string;
    full_name: string;
    role: string; // code
    role_id: string; // uuid
    role_name: string;
    branch_id: number | null;
    branch_name: string | null;
    is_active: boolean;
    company_id: number;
}

export interface CreateUserDto {
    username: string;
    email: string;
    password: string;
    full_name: string;
    role_id: string;
    branch_id?: number | null;
}

export interface UpdateUserDto {
    username?: string;
    email?: string;
    full_name?: string;
    role_id?: string;
    is_active?: boolean;
    password?: string;
    branch_id?: number | null;
}

export interface Role {
    id: string;
    name: string;
    code: string;
    description: string;
    hierarchy_level?: number;
    is_system?: boolean;
    permissions?: Permission[];
}

export interface Permission {
    id: string;
    code: string;
    name: string;
    description?: string;
    category_id: string;
    resource: string;
    action: string;
    is_system: boolean;
}

export interface PermissionCategory {
    id: string;
    name: string;
    code: string;
    icon?: string;
    color?: string;
}

export interface CreateRoleDto {
    name: string;
    code: string;
    description?: string;
    hierarchy_level?: number;
    permission_ids?: string[];
}

export interface UpdateRoleDto {
    name?: string;
    description?: string;
    hierarchy_level?: number;
    is_active?: boolean;
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

    // RBAC MANAGEMENT

    getRoles: async () => {
        const response = await api.get<Role[]>('/rbac/roles');
        return response.data;
    },

    getRoleDetails: async (roleId: string) => {
        const response = await api.get<Role>('/rbac/roles/' + roleId);
        return response.data;
    },

    createRole: async (data: CreateRoleDto) => {
        const response = await api.post<Role>('/rbac/roles', data);
        return response.data;
    },

    updateRole: async (id: string, data: UpdateRoleDto) => {
        const response = await api.put<Role>(`/rbac/roles/${id}`, data);
        return response.data;
    },

    deleteRole: async (id: string) => {
        await api.delete(`/rbac/roles/${id}`);
    },

    getPermissions: async () => {
        const response = await api.get<Permission[]>('/rbac/permissions');
        return response.data;
    },

    getCategories: async () => {
        const response = await api.get<PermissionCategory[]>('/rbac/categories');
        return response.data;
    },

    assignPermission: async (roleId: string, permissionId: string) => {
        await api.post(`/rbac/roles/${roleId}/permissions/${permissionId}`);
    },

    revokePermission: async (roleId: string, permissionId: string) => {
        await api.delete(`/rbac/roles/${roleId}/permissions/${permissionId}`);
    },

    fixRoles: async () => {
        const response = await api.post<{ message: string }>('/users/fix-roles');
        return response.data;
    }
};
