import React, { useState } from 'react';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Plus, Search, AlertTriangle, Package, Loader2 } from 'lucide-react';
import { useGetInventoryQuery } from '../features/inventory/inventoryApi';
import { InventoryItem } from '../types';

const Inventory = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const { data: inventory, isLoading } = useGetInventoryQuery();

  if (isLoading) {
      return <div className="flex justify-center items-center h-full"><Loader2 className="animate-spin text-primary" size={48} /></div>
  }

  const filteredInventory = inventory?.filter(item =>
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const lowStockCount = inventory?.filter(i => i.currentStock <= i.minStock).length || 0;
  const totalItems = inventory?.length || 0;
  // Mock total value calculation
  const totalValue = inventory?.reduce((acc, item) => acc + (item.currentStock * item.averageCost), 0) || 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Inventory</h1>
          <p className="text-sm text-gray-500">Track your stock levels and costs</p>
        </div>
        <div className="flex space-x-2">
            <Button variant="outline">
               Stock Adjustment
            </Button>
            <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Item
            </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-orange-50 border-orange-100">
              <CardContent className="p-6 flex items-center space-x-4">
                  <div className="p-3 bg-orange-100 rounded-full text-orange-600">
                      <AlertTriangle size={24} />
                  </div>
                  <div>
                      <p className="text-sm font-medium text-orange-800">Low Stock Alerts</p>
                      <h3 className="text-2xl font-bold text-orange-900">{lowStockCount} Items</h3>
                  </div>
              </CardContent>
          </Card>
          <Card className="bg-blue-50 border-blue-100">
              <CardContent className="p-6 flex items-center space-x-4">
                  <div className="p-3 bg-blue-100 rounded-full text-blue-600">
                      <Package size={24} />
                  </div>
                  <div>
                      <p className="text-sm font-medium text-blue-800">Total Items</p>
                      <h3 className="text-2xl font-bold text-blue-900">{totalItems}</h3>
                  </div>
              </CardContent>
          </Card>
          <Card className="bg-green-50 border-green-100">
              <CardContent className="p-6 flex items-center space-x-4">
                  <div className="p-3 bg-green-100 rounded-full text-green-600">
                      <span className="text-xl font-bold">$</span>
                  </div>
                  <div>
                      <p className="text-sm font-medium text-green-800">Total Value</p>
                      <h3 className="text-2xl font-bold text-green-900">${(totalValue/1000000).toFixed(1)}M</h3>
                  </div>
              </CardContent>
          </Card>
      </div>

      <Card>
        <CardHeader>
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
              <Input
                placeholder="Search items..."
                className="pl-9 max-w-sm"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border border-gray-200 overflow-hidden">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-50 text-gray-500 font-medium border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3">Item Name</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Stock Level</th>
                  <th className="px-4 py-3">Unit Cost</th>
                  <th className="px-4 py-3 text-right">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {filteredInventory?.map((item: InventoryItem) => (
                  <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-900">{item.name}</td>
                    <td className="px-4 py-3 text-gray-500">{item.category}</td>
                    <td className="px-4 py-3">
                      <span className="font-medium">{item.currentStock}</span> <span className="text-gray-400 text-xs">{item.unitOfMeasure}</span>
                    </td>
                    <td className="px-4 py-3">${item.averageCost.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right">
                        {item.currentStock <= item.minStock ? (
                             <Badge variant="destructive">Low Stock</Badge>
                        ) : (
                             <Badge variant="success" className="bg-green-100 text-green-800 hover:bg-green-200 border-none">In Stock</Badge>
                        )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button variant="ghost" size="sm">
                        Edit
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Inventory;
