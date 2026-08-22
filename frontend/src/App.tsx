import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import { PlantProvider } from './contexts/PlantContext'
import { Layout } from './components/Layout'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { OrgPage } from './pages/OrgPage'
import { InventoryPage } from './pages/InventoryPage'
import { WarehousePage } from './pages/WarehousePage'
import { ProductionPage } from './pages/ProductionPage'
import { ProcurementPage } from './pages/ProcurementPage'
import { SalesPage } from './pages/SalesPage'
import { MaintenancePage } from './pages/MaintenancePage'
import { QualityPage } from './pages/QualityPage'

function ProtectedApp() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-slate-500">Loading…</div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return (
    <PlantProvider>
      <Layout />
    </PlantProvider>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<ProtectedApp />}>
        <Route index element={<DashboardPage />} />
        <Route path="org" element={<OrgPage />} />
        <Route path="inventory" element={<InventoryPage />} />
        <Route path="warehouse" element={<WarehousePage />} />
        <Route path="production" element={<ProductionPage />} />
        <Route path="procurement" element={<ProcurementPage />} />
        <Route path="sales" element={<SalesPage />} />
        <Route path="maintenance" element={<MaintenancePage />} />
        <Route path="quality" element={<QualityPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
