import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Layout from './components/Layout'
import Login from './pages/Login'
import ChangePassword from './pages/ChangePassword'
import Dashboard from './pages/Dashboard'
import Students from './pages/Students'
import StudentForm from './pages/StudentForm'
import StudentDetail from './pages/StudentDetail'
import Courses from './pages/Courses'
import FinancialYears from './pages/FinancialYears'
import FeeHeads from './pages/FeeHeads'
import FeeStructures from './pages/FeeStructures'
import FeeCollection from './pages/FeeCollection'
import Receipts from './pages/Receipts'
import ReceiptDetail from './pages/ReceiptDetail'
import BulkUpload from './pages/BulkUpload'
import Reports from './pages/Reports'
import Backup from './pages/Backup'
import AuditLogs from './pages/AuditLogs'
import UserManagement from './pages/UserManagement'
import Settings from './pages/Settings'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, forcePasswordChange } = useAuthStore()
  if (!user) return <Navigate to="/login" replace />
  if (forcePasswordChange && window.location.pathname !== '/change-password') {
    return <Navigate to="/change-password" replace />
  }
  return <>{children}</>
}

function RootRedirect() {
  const { user } = useAuthStore()
  return <Navigate to={user ? '/dashboard' : '/login'} replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<RootRedirect />} />
      <Route
        path="/change-password"
        element={
          <ProtectedRoute>
            <ChangePassword />
          </ProtectedRoute>
        }
      />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/students" element={<Students />} />
        <Route path="/students/new" element={<StudentForm />} />
        <Route path="/students/:id" element={<StudentDetail />} />
        <Route path="/students/:id/edit" element={<StudentForm />} />
        <Route path="/courses" element={<Courses />} />
        <Route path="/financial-years" element={<FinancialYears />} />
        <Route path="/fee-heads" element={<FeeHeads />} />
        <Route path="/fee-structures" element={<FeeStructures />} />
        <Route path="/fee-collection" element={<FeeCollection />} />
        <Route path="/receipts" element={<Receipts />} />
        <Route path="/receipts/:id" element={<ReceiptDetail />} />
        <Route path="/bulk-upload" element={<BulkUpload />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/backup" element={<Backup />} />
        <Route path="/audit-logs" element={<AuditLogs />} />
        <Route path="/users" element={<UserManagement />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
