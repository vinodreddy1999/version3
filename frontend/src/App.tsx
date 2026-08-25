import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import { PlantProvider } from './contexts/PlantContext'
import { Layout } from './components/Layout'

// Route-level code splitting: each page ships as its own chunk and is only
// fetched when its route is actually visited, instead of one bundle with
// every module's UI up front.
const LoginPage = lazy(() => import('./pages/LoginPage').then((m) => ({ default: m.LoginPage })))
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage').then((m) => ({ default: m.ResetPasswordPage })))
const DashboardPage = lazy(() => import('./pages/DashboardPage').then((m) => ({ default: m.DashboardPage })))
const OrgPage = lazy(() => import('./pages/OrgPage').then((m) => ({ default: m.OrgPage })))
const InventoryPage = lazy(() => import('./pages/InventoryPage').then((m) => ({ default: m.InventoryPage })))
const WarehousePage = lazy(() => import('./pages/WarehousePage').then((m) => ({ default: m.WarehousePage })))
const ProductionPage = lazy(() => import('./pages/ProductionPage').then((m) => ({ default: m.ProductionPage })))
const ProcurementPage = lazy(() => import('./pages/ProcurementPage').then((m) => ({ default: m.ProcurementPage })))
const SalesPage = lazy(() => import('./pages/SalesPage').then((m) => ({ default: m.SalesPage })))
const MaintenancePage = lazy(() => import('./pages/MaintenancePage').then((m) => ({ default: m.MaintenancePage })))
const QualityPage = lazy(() => import('./pages/QualityPage').then((m) => ({ default: m.QualityPage })))
const AdminUsersPage = lazy(() => import('./pages/AdminUsersPage').then((m) => ({ default: m.AdminUsersPage })))
const AdminRolesPage = lazy(() => import('./pages/AdminRolesPage').then((m) => ({ default: m.AdminRolesPage })))
const AdminAuditLogPage = lazy(() => import('./pages/AdminAuditLogPage').then((m) => ({ default: m.AdminAuditLogPage })))

function PageLoading() {
  return <div className="flex min-h-[40vh] items-center justify-center text-sm text-slate-500">Loading…</div>
}

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
    <Suspense fallback={<PageLoading />}>
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
    </Suspense>
  )
}
