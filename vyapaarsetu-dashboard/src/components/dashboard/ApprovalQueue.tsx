import { CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface ApprovalQueueProps {
  items: any[]
  onApprove: (orderId: string) => void
  onReject: (orderId: string) => void
}

export default function ApprovalQueue({ items, onApprove, onReject }: ApprovalQueueProps) {
  if (items.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <CheckCircle className="w-5 h-5 text-accent-green" />
          <h3 className="text-lg font-semibold">Approval Queue</h3>
        </div>
        <div className="text-center py-8 text-text-secondary">
          <Clock className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p>No orders awaiting approval</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-accent-amber animate-pulse" />
        <h3 className="text-lg font-semibold">Approval Queue</h3>
        <span className="bg-accent-amber/20 text-accent-amber px-2 py-1 rounded-full text-xs font-bold">
          {items.length}
        </span>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {items.map((order) => (
          <div
            key={order.order_id}
            className="bg-bg-elevated border border-border rounded-lg p-4 hover:border-accent-amber/50 transition-colors"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h4 className="font-semibold text-text-primary">
                  {order.order_id}
                </h4>
                <p className="text-text-secondary text-sm">
                  {order.customer_name} • {order.customer_phone}
                </p>
                <p className="text-accent-green font-mono font-bold">
                  ₹{order.amount?.toFixed(0)}
                </p>
              </div>
              <div className="text-right">
                <div className="status-badge status-awaiting mb-1">
                  Awaiting Approval
                </div>
                <p className="text-xs text-text-muted">
                  {formatDistanceToNow(new Date(order.created_at), { addSuffix: true })}
                </p>
              </div>
            </div>

            {order.items && (
              <div className="mb-3">
                <p className="text-xs text-text-secondary mb-1">Items:</p>
                <p className="text-sm text-text-primary">
                  {Array.isArray(order.items) ? order.items.join(', ') : order.items}
                </p>
              </div>
            )}

            {order.risk_level && (
              <div className="mb-3">
                <span className={`status-badge risk-${order.risk_level.toLowerCase()}`}>
                  Risk: {order.risk_level}
                </span>
              </div>
            )}

            <div className="flex gap-2">
              <button
                onClick={() => onApprove(order.order_id)}
                className="flex-1 btn-success flex items-center justify-center gap-2 text-sm py-2"
              >
                <CheckCircle className="w-4 h-4" />
                Approve
              </button>
              <button
                onClick={() => onReject(order.order_id)}
                className="flex-1 btn-danger flex items-center justify-center gap-2 text-sm py-2"
              >
                <XCircle className="w-4 h-4" />
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}