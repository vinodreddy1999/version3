import { NavLink, Outlet } from 'react-router-dom'
import {
  Boxes,
  Building2,
  ClipboardCheck,
  Factory,
  History,
  LayoutDashboard,
  LogOut,
  ShieldCheck,
  ShoppingCart,
  Truck,
  Users,
  Warehouse as WarehouseIcon,
  Wrench,
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { usePlant } from '../contexts/PlantContext'
import { Select } from './ui'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', end: true, icon: LayoutDashboard },
  { to: '/org', label: 'Organization', icon: Building2 },
  { to: '/inventory', label: 'Inventory', icon: Boxes },
  { to: '/warehouse', label: 'Warehouse', icon: WarehouseIcon },
  { to: '/production', label: 'Production', icon: Factory },
  { to: '/procurement', label: 'Procurement', icon: ShoppingCart },
  { to: '/sales', label: 'Sales', icon: Truck },
  { to: '/maintenance', label: 'Maintenance', icon: Wrench },
  { to: '/quality', label: 'Quality', icon: ClipboardCheck },
]

const ADMIN_NAV_ITEMS = [
  { to: '/admin/users', label: 'Users', icon: Users, permission: 'admin:manage_users' },
  { to: '/admin/roles', label: 'Roles', icon: ShieldCheck, permission: 'admin:manage_roles' },
  { to: '/admin/audit-log', label: 'Audit log', icon: History, permission: 'admin:view_audit_log' },
]

function initials(name: string) {
  return name
    .split(' ')
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

export function Layout() {
  const { user, logout, hasPermission } = useAuth()
  const { plants, selectedPlantId, setSelectedPlantId } = usePlant()
  const visibleAdminItems = ADMIN_NAV_ITEMS.filter((item) => hasPermission(item.permission))

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="flex w-60 shrink-0 flex-col border-r border-slate-200 bg-white">
        <div className="flex items-center gap-2 border-b border-slate-100 px-5 py-5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-sm font-bold text-white shadow-sm">
            M
          </span>
          <p className="text-base font-bold text-slate-800">Metam ERP</p>
        </div>
        <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-3">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`
              }
            >
              <item.icon className="h-4 w-4" strokeWidth={2} />
              {item.label}
            </NavLink>
          ))}

          {visibleAdminItems.length > 0 && (
            <>
              <p className="mt-4 mb-1 px-3 text-xs font-semibold uppercase tracking-wide text-slate-400">Admin</p>
              {visibleAdminItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                      isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    }`
                  }
                >
                  <item.icon className="h-4 w-4" strokeWidth={2} />
                  {item.label}
                </NavLink>
              ))}
            </>
          )}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-500">Plant</span>
            <Select
              value={selectedPlantId ?? ''}
              onChange={(e) => setSelectedPlantId(e.target.value || null)}
              className="w-48"
            >
              <option value="">All plants</option>
              {plants.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-700">
                {user ? initials(user.full_name) : ''}
              </span>
              <span className="text-sm font-medium text-slate-700">{user?.full_name}</span>
            </div>
            <button
              onClick={logout}
              className="flex items-center gap-1 rounded-lg px-2 py-1.5 text-sm font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-800"
            >
              <LogOut className="h-4 w-4" />
              Log out
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto flex max-w-6xl flex-col gap-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
