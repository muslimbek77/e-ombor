import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import DocumentsPage from './pages/DocumentsPage'
import InventoryPage from './pages/InventoryPage'
import TicketsPage from './pages/TicketsPage'
import { AuthProvider, useAuth } from './auth/AuthContext'

function PrivateRoute({ children }) {
  const { user, authLoading } = useAuth()
  if (authLoading) {
    return <div className="route-loader">Ma&apos;lumotlar yuklanmoqda...</div>
  }
  return user ? children : <Navigate to="/login" />
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <DashboardPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/documents"
            element={
              <PrivateRoute>
                <DocumentsPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/inventory"
            element={
              <PrivateRoute>
                <InventoryPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/tickets"
            element={
              <PrivateRoute>
                <TicketsPage />
              </PrivateRoute>
            }
          />
          <Route path="*" element={<Navigate to="/dashboard" />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
