import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Phone, Eye, CheckCircle, XCircle } from 'lucide-react'
import { apiClient } from '../../api/client'
import { formatDistanceToNow } from 'date-fns'

export default function OrderTable() {
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [page, setPage] = useState(1)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['orders', statusFilter, page],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '20'
      })
      if (statusFilter) params.append('status', statusFilter)
      
      const response = await apiClient.get(`/api/v1/orders?${params}`)
      return response.data
    },
    refetchInterval: 15000, // Refetch every 15 seconds
  })

  const handleCall = async (order: any) => {
    try {
      await apiClient.post('/api/v1/call/initiate', {
        order_id: order.order_id,
        phone_number: order.customer_phone
      })
      refetch()
    } catch (error) {
      console.error('Failed to initiate call:', error)
    }
  }

  const getStatusBadge = (status: string) => {
    const statusClasses = {
      'PENDING': 'status-pending',
      'CALLING': 'status-calling',
      'AWAITING_APPROVAL': 'status-awaiting',
      'APPROVED': 'status-approved',
      'FLAGGED': 'status-flagged',
      'REJECTED_BY_CUSTOMER': 'status-rejected',
      'REJECTED_BY_AGENT': 'status-rejected',
      'ESCALATED': 'status-flagged'
    }
    
    return (
      <span className={`status-badge ${statusClasses[status as keyof typeof statusClasses] || 'status-pending'}`}>
        {status.replace(/_/g, ' ')}
      </span>
    )
  }

  const getRiskBadge = (riskLevel: string | null) => {
    if (!riskLevel) return null
    
    const riskClasses = {
      'SAFE': 'risk-safe',
      'MEDIUM': 'risk-medium',
      'SUSPICIOUS': 'risk-suspicious'
    }
    
    return (
      <span className={`status-badge ${riskClasses[riskLevel as keyof typeof riskClasses]}`}>
        {riskLevel}
      </span>
    )
  }

  const filterTabs = [
    { key: '', label: 'All' },
    { key: 'PENDING', label: 'Pending' },
    { key: 'CALLING', label: 'Calling' },
    { key: 'AWAITING_APPROVAL', label: 'Awaiting Approval' },
    { key: 'FLAGGED', label: 'Flagged' },
    { key: 'APPROVED', label: 'Approved' }
  ]

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold">Orders</h3>
        <div className="text-sm text-text-secondary">
          {data?.total || 0} total orders
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto">
        {filterTabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setStatusFilter(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
              statusFilter === tab.key
                ? 'bg-accent-saffron text-white'
                : 'bg-bg-elevated text-text-secondary hover:text-text-primary'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Customer</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Risk</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={7} className="text-center py-8 text-text-secondary">
                  Loading orders...
                </td>
              </tr>
            ) : data?.orders?.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-8 text-text-secondary">
                  No orders found
                </td>
              </tr>
            ) : (
              data?.orders?.map((order: any) => (
                <tr key={order.order_id}>
                  <td>
                    <code className="bg-bg-elevated px-2 py-1 rounded text-sm">
                      {order.order_id}
                    </code>
                  </td>
                  <td>
                    <div>
                      <div className="font-medium">{order.customer_name}</div>
                      <div className="text-sm text-text-secondary">{order.customer_phone}</div>
                    </div>
                  </td>
                  <td>
                    <span className="font-mono font-bold text-accent-green">
                      ₹{order.amount?.toFixed(0)}
                    </span>
                  </td>
                  <td>{getStatusBadge(order.status)}</td>
                  <td>{getRiskBadge(order.risk_level)}</td>
                  <td className="text-sm text-text-secondary">
                    {formatDistanceToNow(new Date(order.created_at), { addSuffix: true })}
                  </td>
                  <td>
                    <div className="flex gap-2">
                      {(order.status === 'PENDING' || order.status === 'CALL_FAILED') && (
                        <button
                          onClick={() => handleCall(order)}
                          className="p-2 text-accent-blue hover:bg-accent-blue/20 rounded transition-colors"
                          title="Call Now"
                        >
                          <Phone className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        className="p-2 text-text-secondary hover:bg-bg-elevated rounded transition-colors"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-between mt-6">
          <div className="text-sm text-text-secondary">
            Page {data.current_page} of {data.pages}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => Math.min(data.pages, p + 1))}
              disabled={page === data.pages}
              className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}