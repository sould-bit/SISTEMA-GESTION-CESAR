export interface User {
  id: number;
  username: string;
  email: string;
  fullName: string;
  role: 'admin' | 'cashier' | 'kitchen' | 'delivery';
  companyId: number;
  branchId?: number;
}

export interface Company {
  id: number;
  name: string;
  slug: string;
}

export interface Product {
  id: number;
  name: string;
  price: number;
  category: string;
  imageUrl?: string;
  description?: string;
}

export interface OrderItem {
  id?: number;
  productId: number;
  productName: string; // denormalized for convenience
  quantity: number;
  unitPrice: number;
  subtotal: number;
  notes?: string;
}

export interface Order {
  id: number;
  consecutive: string;
  orderType: 'Dine-in' | 'Takeaway' | 'Delivery';
  status: 'pending' | 'preparing' | 'ready' | 'completed' | 'cancelled';
  total: number;
  customerName?: string;
  tableNumber?: string;
  items: OrderItem[];
  createdAt: string;
}

export interface InventoryItem {
    id: number;
    name: string;
    category: string;
    currentStock: number;
    unitOfMeasure: string;
    minStock: number;
    averageCost: number;
}
