import OrderTable from '../components/dashboard/OrderTable'

export default function OrdersPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary mb-2">Orders</h1>
        <p className="text-text-secondary">Manage all customer orders and track their status</p>
      </div>
      
      <OrderTable />
    </div>
  )
}