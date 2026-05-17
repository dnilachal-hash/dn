import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import { useAuthStore } from '../store/authStore'
import { LogOut, User, ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

const BREADCRUMB_MAP: Record<string, string> = {
  dashboard: 'Dashboard',
  students: 'Students',
  courses: 'Courses & Batches',
  'financial-years': 'Financial Years',
  'fee-heads': 'Fee Heads',
  'fee-structures': 'Fee Structures',
  'fee-collection': 'Fee Collection',
  receipts: 'Receipts',
  'bulk-upload': 'Bulk Upload',
  reports: 'Reports',
  backup: 'Backup & Restore',
  'audit-logs': 'Audit Logs',
  users: 'User Management',
  settings: 'Settings',
  new: 'New',
  edit: 'Edit',
  'change-password': 'Change Password',
}

export default function Layout() {
  const { user, clearAuth } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    clearAuth()
    toast.success('Logged out successfully')
    navigate('/login')
  }

  // Build breadcrumb from path segments
  const segments = location.pathname.split('/').filter(Boolean)
  const breadcrumbs = segments.map((seg, i) => {
    const label = BREADCRUMB_MAP[seg] || (seg.match(/^\d+$/) ? '#' + seg : seg)
    const path = '/' + segments.slice(0, i + 1).join('/')
    return { label, path }
  })

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shrink-0 shadow-sm">
          {/* Breadcrumb */}
          <nav className="flex items-center gap-1 text-sm text-gray-500">
            <span className="text-gray-400">HMC</span>
            {breadcrumbs.map((crumb, i) => (
              <span key={i} className="flex items-center gap-1">
                <ChevronRight size={14} className="text-gray-300" />
                {i === breadcrumbs.length - 1 ? (
                  <span className="text-gray-800 font-medium">{crumb.label}</span>
                ) : (
                  <button
                    onClick={() => navigate(crumb.path)}
                    className="hover:text-indigo-600 transition-colors"
                  >
                    {crumb.label}
                  </button>
                )}
              </span>
            ))}
          </nav>

          {/* User controls */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
                <User size={16} className="text-indigo-600" />
              </div>
              <div className="hidden sm:block">
                <div className="font-medium text-gray-800">{user?.full_name}</div>
                <div className="text-xs text-gray-400 capitalize">{user?.role?.replace('_', ' ')}</div>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="btn-secondary btn-sm gap-1"
              title="Logout"
            >
              <LogOut size={14} />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
