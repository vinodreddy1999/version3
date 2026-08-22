import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import { PlantProvider } from './contexts/PlantContext'
import { Layout } from './components/Layout'
import { LoginPage } from './pages/LoginPage'
import { ResetPasswordPage } from './pages/ResetPasswordPage'
import { DashboardPage } from './pages/DashboardPage'
import { OrgPage } from './pages/OrgPage'
import { InventoryPage } from './pages/InventoryPage'
import { WarehousePage } from './pages/WarehousePage'
import { ProductionPage } from './pages/ProductionPage'
import { ProcurementPage } from './pages/ProcurementPage'
import { SalesPage } from './pages/SalesPage'
import { MaintenancePage } from './pages/MaintenancePage'
import { QualityPage } from './pages/QualityPage'
import { AdminUsersPage } from './pages/AdminUsersPage'
import { AdminRolesPage } from './pages/AdminRolesPage'
import { AdminAuditLogPage } from './pages/AdminAuditLogPage'

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

function RequirePermission({ code, children }: { code: string; children: React.ReactNode }) {
  const { hasPermission } = useAuth()
  if (!hasPermission(code)) {
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
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
        <Route
          path="admin/users"
          element={
            <RequirePermission code="admin:manage_users">
              <AdminUsersPage />
            </RequirePermission>
          }
        />
        <Route
          path="admin/roles"
          element={
            <RequirePermission code="admin:manage_roles">
              <AdminRolesPage />
            </RequirePermission>
          }
        />
        <Route
          path="admin/audit-log"
          element={
            <RequirePermission code="admin:view_audit_log">
              <AdminAuditLogPage />
            </RequirePermission>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
