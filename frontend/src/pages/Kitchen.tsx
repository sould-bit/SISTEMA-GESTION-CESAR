import React from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Clock, CheckCircle, Loader2 } from 'lucide-react';
import { useGetOrdersQuery, useUpdateOrderStatusMutation } from '../features/orders/ordersApi';
import { Order } from '../types';

const Kitchen = () => {
  const { data: orders, isLoading } = useGetOrdersQuery();
  const [updateStatus, { isLoading: isUpdating }] = useUpdateOrderStatusMutation();

  if (isLoading) {
      return <div className="flex justify-center items-center h-full"><Loader2 className="animate-spin text-primary" size={48} /></div>
  }

  // Filter for active kitchen orders (pending/preparing)
  const activeOrders = orders?.filter(o => ['pending', 'preparing'].includes(o.status)) || [];

  const handleStatusUpdate = async (id: number, currentStatus: string) => {
      const newStatus = currentStatus === 'pending' ? 'preparing' : 'ready';
      await updateStatus({ id, status: newStatus as Order['status'] });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Kitchen Display</h1>
        <div className="flex space-x-2">
           <Badge variant="warning">Pending: {activeOrders.filter(o => o.status === 'pending').length}</Badge>
           <Badge variant="default">Preparing: {activeOrders.filter(o => o.status === 'preparing').length}</Badge>
        </div>
      </div>

      {activeOrders.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
              <CheckCircle size={48} className="mb-4 text-green-500" />
              <p className="text-lg">All caught up! No active orders.</p>
          </div>
      ) : (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {activeOrders.map((order: Order) => (
          <Card key={order.id} className="flex flex-col border-l-4 border-l-primary h-full">
            <CardHeader className="pb-2">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">{order.consecutive}</CardTitle>
                  <p className="text-sm text-gray-500 font-medium mt-1">
                    {order.orderType === 'Dine-in' ? `Table ${order.tableNumber}` : order.orderType}
                  </p>
                </div>
                <Badge variant={order.status === 'pending' ? 'warning' : 'default'}>
                  {order.status}
                </Badge>
              </div>
              <div className="flex items-center text-xs text-gray-500 mt-2">
                <Clock className="mr-1 h-3 w-3" />
                {order.createdAt}
              </div>
            </CardHeader>
            <CardContent className="flex-1">
              {/* Mock items for now as the type definition has empty items in mock data */}
              <ul className="space-y-2">
                 <li className="text-sm border-b border-gray-100 last:border-0 pb-1 last:pb-0">
                    <div className="flex justify-between font-medium">
                      <span>Mock Item (Burger)</span>
                      <span className="bg-gray-100 px-1.5 rounded text-gray-700">x1</span>
                    </div>
                  </li>
              </ul>
            </CardContent>
            <CardFooter className="pt-2">
               {order.status === 'pending' ? (
                 <Button
                    className="w-full"
                    size="sm"
                    onClick={() => handleStatusUpdate(order.id, order.status)}
                    disabled={isUpdating}
                 >
                     Start Preparing
                 </Button>
               ) : (
                 <Button
                    className="w-full bg-green-600 hover:bg-green-700 text-white"
                    size="sm"
                    onClick={() => handleStatusUpdate(order.id, order.status)}
                    disabled={isUpdating}
                 >
                   <CheckCircle className="mr-2 h-4 w-4" />
                   Mark Ready
                 </Button>
               )}
            </CardFooter>
          </Card>
        ))}
      </div>
      )}
    </div>
  );
};

export default Kitchen;
