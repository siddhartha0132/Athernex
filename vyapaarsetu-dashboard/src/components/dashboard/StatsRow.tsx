import { Phone, Package, Clock, CheckCircle, AlertTriangle, DollarSign } from 'lucide-react'

interface StatsRowProps {
  stats?: {
    total_orders: number
    confirmed: number
    pending_approval: number
    flagged: number
    escalated: number
    calling: number
    total_revenue: number
  }
}

export default function StatsRow({ stats }: StatsRowProps) {
  const statCards = [
    {
      key: 'total_orders',
      label: 'Total Orders',
      icon: Package,
      color: 'text-accent-blue',
      bgColor: 'bg-accent-blue/10',
      borderColor: 'border-l-accent-blue'
    },
    {
      key: 'calling',
      label: 'Active Calls',
      icon: Phone,
      color: 'text-accent-saffron',
      bgColor: 'bg-accent-saffron/10',
      borderColor: 'border-l-accent-saffron',
      pulse: (stats?.calling || 0) > 0
    },
    {
      key: 'pending_approval',
      label: 'Awaiting Approval',
      icon: Clock,
      color: 'text-accent-amber',
      bgColor: 'bg-accent-amber/10',
      borderColor: 'border-l-accent-amber'
    },
    {
      key: 'confirmed',
      label: 'Confirmed',
      icon: CheckCircle,
      color: 'text-accent-green',
      bgColor: 'bg-accent-green/10',
      borderColor: 'border-l-accent-green'
    },
    {
      key: 'flagged',
      label: 'Flagged / Held',
      icon: AlertTriangle,
      color: 'text-accent-red',
      bgColor: 'bg-accent-red/10',
      borderColor: 'border-l-accent-red'
    },
    {
      key: 'total_revenue',
      label: 'Revenue Confirmed',
      icon: DollarSign,
      color: 'text-accent-green',
      bgColor: 'bg-accent-green/10',
      borderColor: 'border-l-accent-green',
      prefix: '₹',
      format: (value: number) => `₹${(value / 1000).toFixed(0)}K`
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {statCards.map((card) => {
        const Icon = card.icon
        const value = stats?.[card.key as keyof typeof stats] || 0
        const displayValue = card.format ? card.format(Number(value)) : value.toString()

        return (
          <div
            key={card.key}
            className={`
              card relative overflow-hidden border-l-4 ${card.borderColor}
              ${card.bgColor} transition-all duration-200 hover:scale-105
            `}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-text-secondary text-sm font-medium mb-1">
                  {card.label}
                </p>
                <p className={`text-2xl font-bold font-mono ${card.color}`}>
                  {displayValue}
                </p>
              </div>
              <div className={`relative ${card.pulse ? 'animate-pulse' : ''}`}>
                <Icon className={`w-8 h-8 ${card.color}`} />
                {card.pulse && (
                  <div className="absolute inset-0 rounded-full border-2 border-accent-saffron pulse-ring" />
                )}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}