import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import DashboardPage from './pages/DashboardPage'
import OrdersPage from './pages/OrdersPage'
import ApprovalPage from './pages/ApprovalPage'
import LoginPage from './pages/LoginPage'
import Sidebar from './components/layout/Sidebar'
import TopBar from './components/layout/TopBar'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check for existing auth token
    const token = localStorage.getItem('vyapaarsetu_token')
    if (token) {
      setIsAuthenticated(true)
    }
    setIsLoading(false)
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-accent-saffron text-xl font-display">Loading VyapaarSetu...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LoginPage onLogin={() => setIsAuthenticated(true)} />
  }

  return (
    <Router>
      <div className="min-h-screen bg-bg-primary flex">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <TopBar onLogout={() => setIsAuthenticated(false)} />
          <main className="flex-1 overflow-auto">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/orders" element={<OrdersPage />} />
              <Route path="/approvals" element={<ApprovalPage />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  )
}

export default App