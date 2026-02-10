
export type OrderStatus = 'pending' | 'confirmed' | 'preparing' | 'ready' | 'delivered' | 'cancelled';

export interface OrderItem {
    id: number;
    quantity: number;
    product_name: string;
    notes?: string;
    unit_price: number;
    subtotal: number;
    removed_ingredients?: string[];
    modifiers?: Array<{
        id: number;
        modifier_id?: number;
        quantity: number;
        unit_price: number;
        modifier?: {
            name: string;
            extra_price: number;
        };
    }>;
}

export interface Payment {
    id: number;
    amount: number;
    method: string;
    status: string;
    created_at: string;
}

export interface Order {
    id: number;
    order_number: string;
    status: OrderStatus;
    branch_id: number;
    table_id?: number;
    delivery_type: 'dine_in' | 'takeaway' | 'delivery';
    total: number;
    subtotal: number;
    tax_total: number;
    created_at: string;
    updated_at?: string;
    created_by_name?: string;
    items: OrderItem[];
    payments: Payment[];
    customer_notes?: string;

    // Cancellation Flow
    cancellation_status?: 'pending' | 'approved' | 'denied';
    cancellation_reason?: string;
    cancellation_requested_at?: string;
    cancellation_denied_reason?: string;
}
