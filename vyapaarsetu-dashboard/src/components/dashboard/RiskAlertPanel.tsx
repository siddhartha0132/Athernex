import { AlertTriangle, Shield, AlertCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

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

interface RiskAlertPanelProps {
  alerts: RiskAlert[]
}

export default function RiskAlertPanel({ alerts }: RiskAlertPanelProps) {
  const getRiskIcon = (decision: string) => {
    switch (decision) {
      case 'SUSPICIOUS':
        return <AlertTriangle className="w-4 h-4 text-accent-red" />
      case 'ESCALATED':
        return <AlertCircle className="w-4 h-4 text-accent-red" />
      case 'MEDIUM':
        return <Shield className="w-4 h-4 text-accent-amber" />
      default:
        return <Shield className="w-4 h-4 text-accent-green" />
    }
  }

  const getRiskColor = (decision: string) => {
    switch (decision) {
      case 'SUSPICIOUS':
      case 'ESCALATED':
        return 'border-accent-red/50 bg-accent-red/10'
      case 'MEDIUM':
        return 'border-accent-amber/50 bg-accent-amber/10'
      default:
        return 'border-accent-green/50 bg-accent-green/10'
    }
  }

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-accent-red" />
        <h3 className="text-lg font-semibold">Risk Alerts</h3>
        {alerts.length > 0 && (
          <span className="bg-accent-red/20 text-accent-red px-2 py-1 rounded-full text-xs font-bold">
            {alerts.length}
          </span>
        )}
      </div>

      <div className="space-y-3 max-h-80 overflow-y-auto">
        {alerts.length === 0 ? (
          <div className="text-center py-8 text-text-secondary">
            <Shield className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No risk alerts</p>
          </div>
        ) : (
          alerts.map((alert, index) => (
            <div
              key={`${alert.order_id}-${alert.ts}-${index}`}
              className={`p-3 rounded-lg border ${getRiskColor(alert.risk.decision)}`}
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5">
                  {getRiskIcon(alert.risk.decision)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <code className="bg-bg-elevated px-2 py-1 rounded text-xs">
                      {alert.order_id}
                    </code>
                    <span className={`status-badge risk-${alert.risk.decision.toLowerCase()}`}>
                      {alert.risk.decision}
                    </span>
                  </div>
                  
                  <p className="text-sm text-text-primary mb-2">
                    {alert.risk.reason}
                  </p>
                  
                  {alert.risk.flags && alert.risk.flags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {alert.risk.flags.map((flag, flagIndex) => (
                        <span
                          key={flagIndex}
                          className="bg-bg-elevated text-text-secondary px-2 py-1 rounded text-xs"
                        >
                          {flag.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-text-muted">
                      Score: {alert.risk.score}/100
                    </span>
                    <span className="text-xs text-text-muted">
                      {formatDistanceToNow(new Date(alert.ts), { addSuffix: true })}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}