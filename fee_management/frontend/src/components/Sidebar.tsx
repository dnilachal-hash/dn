import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import {
  LayoutDashboard, Users, BookOpen, Calendar, CreditCard, FileText,
  BarChart3, Database, ClipboardList, UserCog, Settings, Upload,
  Layers, ChevronLeft, ChevronRight, Building2, DollarSign
} from 'lucide-react'

interface NavItem {
  path: string
  label: string
  icon: React.ReactNode
  permission?: string
  role?: string
}

const NAV_ITEMS: NavItem[] = [
  { path: '/dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} /> },
  { path: '/students', label: 'Students', icon: <Users size={18} />, permission: 'VIEW_STUDENTS' },
  { path: '/fee-collection', label: 'Fee Collection', icon: <DollarSign size={18} />, permission: 'COLLECT_FEES' },
  { path: '/receipts', label: 'Receipts', icon: <FileText size={18} />, permission: 'VIEW_RECEIPTS' },
  { path: '/bulk-upload', label: 'Bulk Upload', icon: <Upload size={18} />, permission: 'BULK_UPLOAD' },
  { path: '/courses', label: 'Courses', icon: <BookOpen size={18} />, permission: 'VIEW_COURSES' },
  { path: '/financial-years', label: 'Financial Years', icon: <Calendar size={18} /> },
  { path: '/fee-heads', label: 'Fee Heads', icon: <CreditCard size={18} />, permission: 'VIEW_FEE_HEADS' },
  { path: '/fee-structures', label: 'Fee Structures', icon: <Layers size={18} />, permission: 'VIEW_FEE_STRUCTURES' },
  { path: '/reports', label: 'Reports', icon: <BarChart3 size={18} />, permission: 'VIEW_REPORTS' },
  { path: '/audit-logs', label: 'Audit Logs', icon: <ClipboardList size={18} />, permission: 'VIEW_AUDIT_LOGS' },
  { path: '/backup', label: 'Backup & Restore', icon: <Database size={18} />, role: 'super_admin' },
  { path: '/users', label: 'Users', icon: <UserCog size={18} />, role: 'super_admin' },
  { path: '/settings', label: 'Settings', icon: <Settings size={18} />, role: 'super_admin' },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const { user, hasPermission } = useAuthStore()
  const navigate = useNavigate()

  const visibleItems = NAV_ITEMS.filter((item) => {
    if (item.role) return user?.role === item.role || user?.role === 'super_admin'
    if (item.permission) return hasPermission(item.permission)
    return true
  })

  return (
    <aside
      className={`${
        collapsed ? 'w-16' : 'w-64'
      } bg-indigo-950 text-white flex flex-col transition-all duration-300 shrink-0`}
    >
      {/* Logo area */}
      <div
        className={`flex items-center gap-3 px-4 py-5 border-b border-indigo-800 cursor-pointer`}
        onClick={() => navigate('/dashboard')}
      >
        <div className="w-9 h-9 bg-indigo-500 rounded-lg flex items-center justify-center shrink-0">
          <Building2 size={20} className="text-white" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <div className="font-bold text-sm leading-tight">HMC Fee</div>
            <div className="text-indigo-300 text-xs leading-tight">Management System</div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 overflow-y-auto">
        {visibleItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            title={collapsed ? item.label : undefined}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 mx-2 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-indigo-200 hover:bg-indigo-800 hover:text-white'
              }`
            }
          >
            <span className="shrink-0">{item.icon}</span>
            {!collapsed && <span className="truncate">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center p-3 border-t border-indigo-800 hover:bg-indigo-800 transition-colors text-indigo-300 hover:text-white"
        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? <ChevronRight size={18} /> : (
          <span className="flex items-center gap-2 text-xs">
            <ChevronLeft size={18} />
            {!collapsed && <span>Collapse</span>}
          </span>
        )}
      </button>
    </aside>
  )
}
