import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import {
  Users, GraduationCap, Briefcase, AlertTriangle,
  CheckCircle2, IndianRupee, Calendar
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from "recharts";

const COLORS = ["#1f4e79", "#2e75b6", "#5b9bd5", "#9dc3e6", "#bdd7ee",
                "#deebf7", "#0070c0", "#0066cc", "#3399ff", "#66b2ff"];

function StatCard({ title, value, icon: Icon, color }: any) {
  return (
    <div className="card p-4 flex items-center gap-4">
      <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${color}`}>
        <Icon className="text-white" size={24} />
      </div>
      <div>
        <div className="text-sm text-slate-500">{title}</div>
        <div className="text-2xl font-bold text-slate-800">{value}</div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const stats = useQuery({ queryKey: ["dash-stats"], queryFn: () => api.get("/dashboard/stats").then(r => r.data) });
  const trend = useQuery({ queryKey: ["dash-trend"], queryFn: () => api.get("/dashboard/payroll-trend").then(r => r.data) });
  const dept = useQuery({ queryKey: ["dash-dept"], queryFn: () => api.get("/dashboard/department-headcount").then(r => r.data) });

  if (stats.isLoading) return <div className="p-6">Loading dashboard…</div>;
  const s = stats.data ?? {};

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
          <p className="text-sm text-slate-500">Overview of payroll, employees, compliance.</p>
        </div>
        <div className="text-sm text-slate-500">
          Latest payroll month: <span className="font-medium">{s.latest_month ?? "—"}</span>
          {" · "}
          <span className="badge badge-info">{s.latest_month_status ?? "—"}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Active Employees" value={s.active_employees ?? 0} icon={Users} color="bg-brand-500" />
        <StatCard title="Teaching Staff" value={s.teaching_employees ?? 0} icon={GraduationCap} color="bg-emerald-500" />
        <StatCard title="Non-Teaching" value={s.non_teaching_employees ?? 0} icon={Briefcase} color="bg-amber-500" />
        <StatCard title="Latest Gross" value={"₹" + (s.latest_month_gross ?? 0).toLocaleString("en-IN")} icon={IndianRupee} color="bg-violet-500" />
        <StatCard title="Pending Approval" value={s.pending_approvals ?? 0} icon={Calendar} color="bg-blue-500" />
        <StatCard title="Critical Alerts" value={s.critical_alerts ?? 0} icon={AlertTriangle} color="bg-red-500" />
        <StatCard title="Warnings" value={s.warnings ?? 0} icon={AlertTriangle} color="bg-yellow-500" />
        <StatCard title="Compliance" value={s.critical_alerts === 0 ? "OK" : "Action Needed"} icon={CheckCircle2}
                   color={s.critical_alerts === 0 ? "bg-green-500" : "bg-red-500"} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-4">
          <h3 className="font-semibold mb-3 text-slate-700">Payroll Trend (Gross / Net / CTC)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trend.data ?? []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" />
                <YAxis />
                <Tooltip formatter={(v: any) => "₹" + Number(v).toLocaleString("en-IN")} />
                <Legend />
                <Bar dataKey="gross" fill="#1f4e79" />
                <Bar dataKey="net" fill="#2e75b6" />
                <Bar dataKey="ctc" fill="#5b9bd5" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card p-4">
          <h3 className="font-semibold mb-3 text-slate-700">Department Headcount</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={dept.data ?? []} dataKey="count" nameKey="department"
                     cx="50%" cy="50%" outerRadius={80} label>
                  {(dept.data ?? []).map((_: any, i: number) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
