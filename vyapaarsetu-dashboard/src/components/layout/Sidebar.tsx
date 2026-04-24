import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Package, CheckSquare, Users, Settings } from 'lucide-react'

export default function Sidebar() {
  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/orders', icon: Package, label: 'Orders' },
    { to: '/approvals', icon: CheckSquare, label: 'Approvals' },
  ]

  return (
    <div className="w-64 bg-bg-card border-r border-border flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-border">
        <h1 className="text-2xl font-display text-accent-saffron">
          VyapaarSetu
        </h1>
        <p className="text-text-secondary text-sm">AI Order System</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-accent-saffron/20 text-accent-saffron border border-accent-saffron/30'
                        : 'text-text-secondary hover:text-text-primary hover:bg-bg-elevated'
                    }`
                  }
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </NavLink>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className="text-xs text-text-muted">
          <p>VyapaarSetu AI v1.0</p>
          <p>© 2024 All rights reserved</p>
        </div>
      </div>
    </div>
  )
}