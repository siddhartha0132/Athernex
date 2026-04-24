import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import ApprovalQueue from '../components/dashboard/ApprovalQueue'

export default function ApprovalPage() {
  const { data: approvals, refetch } = useQuery({
    queryKey: ['approvals'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/orders?status=AWAITING_APPROVAL')
      return response.data.orders
    },
    refetchInterval: 5000, // Refetch every 5 seconds
  })

  const handleApprove = async (orderId: string) => {
    try {
      await apiClient.post(`/api/v1/orders/${orderId}/approve`, {
        action: 'APPROVE',
        agent_name: 'Dashboard User'
      })
      refetch()
    } catch (error) {
      console.error('Failed to approve order:', error)
    }
  }

  const handleReject = async (orderId: string) => {
    try {
      await apiClient.post(`/api/v1/orders/${orderId}/approve`, {
        action: 'REJECT',
        agent_name: 'Dashboard User'
      })
      refetch()
    } catch (error) {
      console.error('Failed to reject order:', error)
    }
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary mb-2">Order Approvals</h1>
        <p className="text-text-secondary">Review and approve orders that require human verification</p>
      </div>
      
      <div className="max-w-4xl">
        <ApprovalQueue 
          items={approvals || []} 
          onApprove={handleApprove} 
          onReject={handleReject} 
        />
      </div>
    </div>
  )
}