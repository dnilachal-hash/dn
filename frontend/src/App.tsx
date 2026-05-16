import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import Login from "./pages/Login";
import ChangePassword from "./pages/ChangePassword";
import Layout from "./components/layout/Layout";
import Dashboard from "./pages/Dashboard";
import EmployeeList from "./pages/employees/EmployeeList";
import EmployeeForm from "./pages/employees/EmployeeForm";
import EmployeeDetail from "./pages/employees/EmployeeDetail";
import SalaryStructure from "./pages/salary/SalaryStructure";
import PayrollGenerate from "./pages/payroll/PayrollGenerate";
import PayrollHistory from "./pages/payroll/PayrollHistory";
import StatutorySettings from "./pages/statutory/StatutorySettings";
import ReportsHub from "./pages/reports/ReportsHub";
import ComplianceDashboard from "./pages/compliance/ComplianceDashboard";
import AuditLogs from "./pages/audit/AuditLogs";
import UserManagement from "./pages/settings/UserManagement";

function Protected({ children }: { children: React.ReactNode }) {
  const { user, forcePasswordChange } = useAuthStore();
  const loc = useLocation();
  if (!user) return <Navigate to="/login" replace />;
  if (forcePasswordChange && loc.pathname !== "/change-password") {
    return <Navigate to="/change-password" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/change-password" element={<Protected><ChangePassword /></Protected>} />
      <Route path="/" element={<Protected><Layout /></Protected>}>
        <Route index element={<Dashboard />} />
        <Route path="employees" element={<EmployeeList />} />
        <Route path="employees/new" element={<EmployeeForm />} />
        <Route path="employees/:id" element={<EmployeeDetail />} />
        <Route path="employees/:id/edit" element={<EmployeeForm />} />
        <Route path="salary" element={<SalaryStructure />} />
        <Route path="payroll" element={<PayrollHistory />} />
        <Route path="payroll/generate" element={<PayrollGenerate />} />
        <Route path="statutory" element={<StatutorySettings />} />
        <Route path="reports" element={<ReportsHub />} />
        <Route path="compliance" element={<ComplianceDashboard />} />
        <Route path="audit" element={<AuditLogs />} />
        <Route path="users" element={<UserManagement />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
