import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";

const ROLES = ["super_admin", "admin", "hr_manager", "payroll_executive", "accounts_user", "auditor"];

export default function UserManagement() {
  const qc = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ username: "", email: "", full_name: "", password: "", role: "auditor" });
  const [error, setError] = useState<string | null>(null);

  const users = useQuery({ queryKey: ["users"], queryFn: () => api.get("/users").then(r => r.data) });
  const create = useMutation({
    mutationFn: (data: any) => api.post("/users", data).then(r => r.data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["users"] }); setCreating(false); setError(null); },
    onError: (e: any) => setError(e?.response?.data?.detail ?? "Failed"),
  });

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">User Management</h1>
        <button className="btn-primary" onClick={() => setCreating(true)}>+ New User</button>
      </div>

      <div className="card overflow-hidden">
        <table className="tbl">
          <thead><tr><th>Username</th><th>Email</th><th>Full Name</th><th>Role</th><th>Active</th><th>Last Login</th></tr></thead>
          <tbody>
            {(users.data ?? []).map((u: any) => (
              <tr key={u.id}>
                <td className="font-mono">{u.username}</td>
                <td>{u.email}</td>
                <td>{u.full_name || "—"}</td>
                <td><span className="badge-info capitalize">{u.role.replace("_", " ")}</span></td>
                <td>{u.is_active ? <span className="badge-success">Active</span> : <span className="badge-muted">Inactive</span>}</td>
                <td className="text-xs">{u.last_login?.slice(0, 16).replace("T", " ") || "Never"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {creating && (
        <div className="card p-4 max-w-xl">
          <h3 className="font-semibold mb-3">Create User</h3>
          <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); create.mutate(form); }}>
            <div><label className="label">Username</label>
              <input className="input" required value={form.username} onChange={e=>setForm({...form, username: e.target.value})} /></div>
            <div><label className="label">Email</label>
              <input className="input" type="email" required value={form.email} onChange={e=>setForm({...form, email: e.target.value})} /></div>
            <div><label className="label">Full Name</label>
              <input className="input" value={form.full_name} onChange={e=>setForm({...form, full_name: e.target.value})} /></div>
            <div><label className="label">Password</label>
              <input className="input" type="password" required value={form.password} onChange={e=>setForm({...form, password: e.target.value})} />
              <p className="text-xs text-slate-400 mt-1">User must change on first login</p></div>
            <div><label className="label">Role</label>
              <select className="input" value={form.role} onChange={e=>setForm({...form, role: e.target.value})}>
                {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
              </select></div>
            {error && <div className="text-sm text-red-600">{error}</div>}
            <div className="flex gap-2 justify-end">
              <button type="button" className="btn-secondary" onClick={() => setCreating(false)}>Cancel</button>
              <button type="submit" className="btn-primary" disabled={create.isPending}>Save</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
