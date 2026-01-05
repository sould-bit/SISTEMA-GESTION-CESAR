import React, { useState } from 'react';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Plus, Search, Filter, Loader2 } from 'lucide-react';
import { Input } from '../components/ui/Input';
import { useGetOrdersQuery } from '../features/orders/ordersApi';
import { Order } from '../types';

const statusColors: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  pending: 'warning',
  preparing: 'default',
  ready: 'success',
  completed: 'secondary',
  cancelled: 'destructive',
};

const Orders = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const { data: orders, isLoading, error } = useGetOrdersQuery();

  if (isLoading) {
      return <div className="flex justify-center items-center h-full"><Loader2 className="animate-spin text-primary" size={48} /></div>
  }

  if (error) {
      return <div className="text-red-500">Error loading orders</div>
  }

  const filteredOrders = orders?.filter(order =>
    order.consecutive.toLowerCase().includes(searchTerm.toLowerCase()) ||
    order.customerName?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Orders</h1>
          <p className="text-sm text-gray-500">Manage your active orders here</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New Order
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
              <Input
                placeholder="Search orders..."
                className="pl-9"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Button variant="outline" className="w-full sm:w-auto">
              <Filter className="mr-2 h-4 w-4" />
              Filter
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border border-gray-200 overflow-hidden">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-50 text-gray-500 font-medium border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3">Consecutive</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Details</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Total</th>
                  <th className="px-4 py-3 text-right">Time</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {filteredOrders?.map((order: Order) => (
                  <tr key={order.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-900">{order.consecutive}</td>
                    <td className="px-4 py-3">
                      <Badge variant="outline">{order.orderType}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      {order.orderType === 'Dine-in' ? `Table ${order.tableNumber}` : order.customerName}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={statusColors[order.status]}>{order.status}</Badge>
                    </td>
                    <td className="px-4 py-3 font-medium">
                      ${order.total.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-500">{order.createdAt}</td>
                    <td className="px-4 py-3 text-right">
                      <Button variant="ghost" size="sm">
                        View
                      </Button>
                    </td>
                  </tr>
                ))}
                {filteredOrders?.length === 0 && (
                    <tr>
                        <td colSpan={7} className="px-4 py-8 text-center text-gray-500">No orders found</td>
                    </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Orders;
