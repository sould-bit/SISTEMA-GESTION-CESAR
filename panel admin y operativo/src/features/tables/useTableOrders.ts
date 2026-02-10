import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import { Order } from '../admin/types';

interface TableOrderInfo {
    orderId: number;
    orderNumber: string;
    status: Order['status'];
    total: number;
    waiterName: string | null;
    itemCount: number;
    createdAt: string;
}

interface TableOrdersMap {
    [tableId: number]: TableOrderInfo;
}

/**
 * Fetches active orders for all tables in a branch.
 * Returns a map of tableId -> order info for quick lookup.
 */
export const useTableOrders = (branchId: number | null) => {
    return useQuery({
        queryKey: ['tableOrders', branchId],
        queryFn: async (): Promise<TableOrdersMap> => {
            if (!branchId) return {};

            // Fetch all potentially active orders including those served but maybe not paid
            const response = await api.get<Order[]>('/orders/', {
                params: {
                    branch_id: branchId,
                    status: 'pending,confirmed,preparing,ready,delivered',
                    limit: 100,
                }
            });

            // Build map of tableId -> order info
            const ordersMap: TableOrdersMap = {};

            for (const order of response.data) {
                if (order.table_id && order.delivery_type === 'dine_in') {
                    // Calcular si está pagado
                    const totalPaid = order.payments?.reduce((acc, p) => acc + (p.status === 'completed' ? Number(p.amount) : 0), 0) || 0;
                    const isPaid = totalPaid >= order.total;

                    // Si está entregado Y pagado, el pedido ya no bloquea la mesa
                    if (order.status === 'delivered' && isPaid) continue;

                    // Si ya existe una orden para esta mesa (ej multiple orders by mistake),
                    // priorizamos la que NO esté entregada o la más reciente
                    if (ordersMap[order.table_id]) {
                        // Logic to pick the most relevant order if multiple exist
                        continue;
                    }

                    ordersMap[order.table_id] = {
                        orderId: order.id,
                        orderNumber: order.order_number,
                        status: order.status,
                        total: order.total,
                        waiterName: order.created_by_name || null,
                        itemCount: order.items?.length || 0,
                        createdAt: order.created_at,
                    };
                }
            }

            return ordersMap;
        },
        enabled: !!branchId,
        staleTime: 5000,
        refetchOnWindowFocus: false,
    });
};

export type { TableOrderInfo, TableOrdersMap };
