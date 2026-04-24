import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSocket } from '../hooks/useSocket'
import { apiClient } from '../api/client'
import StatsRow from '../components/dashboard/StatsRow'
import OrderTable from '../components/dashboard/OrderTable'
import LiveCallFeed from '../components/dashboard/LiveCallFeed'
import RiskAlertPanel from '../components/dashboard/RiskAlertPanel'
import ApprovalQueue from '../components/dashboard/ApprovalQueue'

interface DashboardStats {
  total_orders: number
  confirmed: number
  pending_approval: number
  flagged: number
  escalated: number
  calling: number
  total_revenue: number
}

interface LiveEvent {
  type: 'UPDATE' | 'NEW' | 'CALL_STARTED'
  order?: any
  call?: any
  ts: number
}

interface RiskAlert {
  order_id: string
  risk: {
    decision: string
    score: number
    flags: string[]
    reason: string
  }
  ts: number
}

export default function DashboardPage() {
  const { socket, connected } = useSocket()
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([])
  const [pendingApprovals, setPendingApprovals] = useState<any[]>([])
  const [riskAlerts, setRiskAlerts] = useState<RiskAlert[]>([])

  // Fetch dashboard stats
  const { data: stats, refetch: refetchStats } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/dashboard/stats')
      return response.data
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  // Fetch pending approvals
  const { data: approvals } = useQuery({
    queryKey: ['pending-approvals'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/orders?status=AWAITING_APPROVAL')
      return response.data.orders
    },
    refetchInterval: 10000, // Refetch every 10 seconds
  })

  useEffect(() => {
    if (approvals) {
      setPendingApprovals(approvals)
    }
  }, [approvals])

  useEffect(() => {
    if (!socket) return

    // Listen for real-time events
    socket.on('order_update', (order) => {
      setLiveEvents(prev => [
        { type: 'UPDATE', order, ts: Date.now() },
        ...prev.slice(0, 49)
      ])
      refetchStats() // Update stats when orders change
    })

    socket.on('new_order', (order) => {
      setLiveEvents(prev => [
        { type: 'NEW', order, ts: Date.now() },
        ...prev.slice(0, 49)
      ])
      refetchStats()
    })

    socket.on('call_started', (call) => {
      setLiveEvents(prev => [
        { type: 'CALL_STARTED', call, ts: Date.now() },
        ...prev.slice(0, 49)
      ])
    })

    socket.on('approval_needed', (order) => {
      setPendingApprovals(prev => {
        // Avoid duplicates
        const exists = prev.some(p => p.order_id === order.order_id)
        if (exists) return prev
        return [order, ...prev]
      })
    })

    socket.on('risk_alert', ({ order_id, risk }) => {
      setRiskAlerts(prev => [
        { order_id, risk, ts: Date.now() },
        ...prev.slice(0, 9)
      ])
    })

    socket.on('escalation_needed', (order) => {
      setRiskAlerts(prev => [
        { 
          order_id: order.order_id, 
          risk: { decision: 'ESCALATED', score: 100, flags: ['ESCALATED'], reason: 'Human intervention required' }, 
          ts: Date.now() 
        },
        ...prev.slice(0, 9)
      ])
    })

    return () => {
      socket.off('order_update')
      socket.off('new_order')
      socket.off('call_started')
      socket.off('approval_needed')
      socket.off('risk_alert')
      socket.off('escalation_needed')
    }
  }, [socket, refetchStats])

  const handleApprove = async (orderId: string) => {
    try {
      await apiClient.post(`/api/v1/orders/${orderId}/approve`, {
        action: 'APPROVE',
        agent_name: 'Dashboard User'
      })
      
      // Remove from pending approvals
      setPendingApprovals(prev => prev.filter(p => p.order_id !== orderId))
      refetchStats()
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
      
      // Remove from pending approvals
      setPendingApprovals(prev => prev.filter(p => p.order_id !== orderId))
      refetchStats()
    } catch (error) {
      console.error('Failed to reject order:', error)
    }
  }

  return (
    <div className="dashboard-layout">
      {/* Connection status pill */}
      <div className={`connection-pill ${connected ? 'connected' : 'disconnected'}`}>
        <span className="dot" />
        {connected ? 'Live' : 'Reconnecting...'}
      </div>

      {/* Top: Stats Cards */}
      <StatsRow stats={stats} />

      {/* Middle: 3-column layout */}
      <div className="dashboard-grid">
        {/* Left 60%: Main order table */}
        <div className="main-panel">
          <OrderTable />
        </div>

        {/* Right 40%: Live panels */}
        <div className="side-panels">
          {/* Pending Human Approval Queue — HIGHEST PRIORITY */}
          <ApprovalQueue 
            items={pendingApprovals} 
            onApprove={handleApprove} 
            onReject={handleReject} 
          />

          {/* Risk Alerts */}
          <RiskAlertPanel alerts={riskAlerts} />

          {/* Live Call Feed */}
          <LiveCallFeed events={liveEvents} />
        </div>
      </div>
    </div>
  )
}