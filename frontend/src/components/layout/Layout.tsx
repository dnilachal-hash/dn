import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import {
  LayoutDashboard, Users, Wallet, FileText, ShieldCheck,
  Settings, Activity, LogOut, Building2, Calculator, ScrollText
} from "lucide-react";

const nav = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard", perm: "dashboard.view" },
  { to: "/employees", icon: Users, label: "Employees", perm: "employee.view" },
  { to: "/salary", icon: Wallet, label: "Salary Structures", perm: "salary.view" },
  { to: "/payroll", icon: Calculator, label: "Payroll", perm: "payroll.view" },
  { to: "/statutory", icon: Building2, label: "Statutory Settings", perm: "statutory.view" },
  { to: "/reports", icon: FileText, label: "Reports", perm: "report.view" },
  { to: "/compliance", icon: ShieldCheck, label: "Compliance", perm: "payroll.view" },
  { to: "/audit", icon: ScrollText, label: "Audit Logs", perm: "audit.view" },
  { to: "/users", icon: Settings, label: "Users", perm: "user.manage" },
];

export default function Layout() {
  const { user, logout, hasPermission } = useAuthStore();
  const navigate = useNavigate();
  const handleLogout = () => { logout(); navigate("/login"); };

  return (
    <div className="flex h-screen bg-slate-50">
      <aside className="w-64 bg-brand-700 text-white flex flex-col">
        <div className="p-4 border-b border-brand-600">
          <h1 className="font-bold text-lg leading-tight">HMC Payroll</h1>
          <p className="text-xs text-brand-100">Homoeopathic Medical College</p>
        </div>
        <nav className="flex-1 overflow-y-auto py-2">
          {nav.filter(n => hasPermission(n.perm)).map(n => (
            <NavLink key={n.to} to={n.to} end={n.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 text-sm transition ${
                  isActive ? "bg-brand-500 text-white" : "text-brand-100 hover:bg-brand-600"
                }`}>
              <n.icon size={18} />
              <span>{n.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-brand-600">
          <div className="text-sm font-medium">{user?.full_name || user?.username}</div>
          <div className="text-xs text-brand-100 capitalize mb-2">{user?.role.replace("_", " ")}</div>
          <button onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 text-sm px-3 py-1.5 rounded bg-brand-600 hover:bg-brand-500 transition">
            <LogOut size={14} /> Logout
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
