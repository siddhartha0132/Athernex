import { Phone, Package, AlertCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface LiveEvent {
  type: 'UPDATE' | 'NEW' | 'CALL_STARTED'
  order?: any
  call?: any
  ts: number
}

interface LiveCallFeedProps {
  events: LiveEvent[]
}

export default function LiveCallFeed({ events }: LiveCallFeedProps) {
  const getEventIcon = (event: LiveEvent) => {
    switch (event.type) {
      case 'CALL_STARTED':
        return <Phone className="w-4 h-4 text-accent-blue" />
      case 'NEW':
        return <Package className="w-4 h-4 text-accent-green" />
      case 'UPDATE':
        return <AlertCircle className="w-4 h-4 text-accent-amber" />
      default:
        return <AlertCircle className="w-4 h-4 text-text-secondary" />
    }
  }

  const getEventDescription = (event: LiveEvent) => {
    switch (event.type) {
      case 'CALL_STARTED':
        return `Call started for ${event.call?.customer_name || 'customer'} - ${event.call?.order_id}`
      case 'NEW':
        return `New order ${event.order?.order_id} from ${event.order?.customer_name}`
      case 'UPDATE':
        return `Order ${event.order?.order_id} updated to ${event.order?.status}`
      default:
        return 'Unknown event'
    }
  }

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <Phone className="w-5 h-5 text-accent-blue" />
        <h3 className="text-lg font-semibold">Live Activity</h3>
      </div>

      <div className="space-y-3 max-h-80 overflow-y-auto">
        {events.length === 0 ? (
          <div className="text-center py-8 text-text-secondary">
            <Phone className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No recent activity</p>
          </div>
        ) : (
          events.map((event, index) => (
            <div
              key={`${event.type}-${event.ts}-${index}`}
              className="flex items-start gap-3 p-3 bg-bg-elevated rounded-lg"
            >
              <div className="mt-0.5">
                {getEventIcon(event)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-text-primary">
                  {getEventDescription(event)}
                </p>
                <p className="text-xs text-text-muted mt-1">
                  {formatDistanceToNow(new Date(event.ts), { addSuffix: true })}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}