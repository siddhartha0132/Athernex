import { LogOut, Plus, Bell } from 'lucide-react'

interface TopBarProps {
  onLogout: () => void
}

export default function TopBar({ onLogout }: TopBarProps) {
  const handleLogout = () => {
    localStorage.removeItem('vyapaarsetu_token')
    onLogout()
  }

  return (
    <div className="h-16 bg-bg-card border-b border-border flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <h2 className="text-xl font-semibold text-text-primary">
          Merchant Dashboard
        </h2>
      </div>

      <div className="flex items-center gap-4">
        <button className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          New Order
        </button>

        <button className="p-2 text-text-secondary hover:text-text-primary transition-colors">
          <Bell className="w-5 h-5" />
        </button>

        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-3 py-2 text-text-secondary hover:text-accent-red transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </div>
  )
}