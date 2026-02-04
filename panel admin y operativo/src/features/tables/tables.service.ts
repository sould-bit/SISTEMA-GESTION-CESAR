import { api } from '../../lib/api';

export interface Table {
    id: number;
    branch_id: number;
    table_number: number;
    seat_count: number;
    status: 'available' | 'occupied' | 'reserved' | 'attention';
    pos_x?: number;
    pos_y?: number;
    is_active: boolean;
}

export const tablesService = {
    setupTables: async (count: number, branchId?: number): Promise<Table[]> => {
        const params = branchId ? { branch_id: branchId } : {};
        const response = await api.post<Table[]>(`/tables/setup?count=${count}`, null, { params });
        return response.data;
    },

    getTables: async (branchId?: number): Promise<Table[]> => {
        const params = branchId ? { branch_id: branchId } : {};
        const response = await api.get<Table[]>('/tables', { params });
        return response.data;
    },

    updateStatus: async (tableId: number, status: string): Promise<Table> => {
        const response = await api.patch<Table>(`/tables/${tableId}/status?status=${status}`);
        return response.data;
    }
};
