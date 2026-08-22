import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { usePlant } from '../contexts/PlantContext'
import { Select } from './ui'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/org', label: 'Organization' },
  { to: '/inventory', label: 'Inventory' },
  { to: '/warehouse', label: 'Warehouse' },
  { to: '/production', label: 'Production' },
  { to: '/procurement', label: 'Procurement' },
  { to: '/sales', label: 'Sales' },
  { to: '/maintenance', label: 'Maintenance' },
  { to: '/quality', label: 'Quality' },
]

export function Layout() {
  const { user, logout } = useAuth()
  const { plants, selectedPlantId, setSelectedPlantId } = usePlant()

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="w-56 shrink-0 border-r border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-4 py-4">
          <p className="text-lg font-bold text-indigo-600">Metam ERP</p>
        </div>
        <nav className="flex flex-col gap-0.5 p-2">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm font-medium ${
                  isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-100'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
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
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-600">{user?.full_name}</span>
            <button onClick={logout} className="text-sm font-medium text-slate-500 hover:text-slate-800">
              Log out
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
