import { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuthStore } from "../store/authStore";
import { Lock, User } from "lucide-react";

export default function Login() {
  const { user, setAuth } = useAuthStore();
  const navigate = useNavigate();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError(null);
    try {
      const { data } = await api.post("/auth/login", { username, password });
      setAuth(data);
      navigate(data.force_password_change ? "/change-password" : "/");
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-700 to-brand-500 p-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow-xl p-8">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-brand-700">HMC Payroll System</h1>
          <p className="text-sm text-slate-500 mt-1">Homoeopathic Medical College &amp; Hospital</p>
          <p className="text-xs text-slate-400 mt-1">Version 2.0 — NCH-Compliant</p>
        </div>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="label">Username</label>
            <div className="relative">
              <User size={16} className="absolute left-3 top-3 text-slate-400" />
              <input className="input pl-9" value={username} onChange={e=>setUsername(e.target.value)} required autoFocus />
            </div>
          </div>
          <div>
            <label className="label">Password</label>
            <div className="relative">
              <Lock size={16} className="absolute left-3 top-3 text-slate-400" />
              <input type="password" className="input pl-9" value={password} onChange={e=>setPassword(e.target.value)} required />
            </div>
          </div>
          {error && <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2">{error}</div>}
          <button type="submit" disabled={loading} className="btn-primary w-full py-2.5">
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
        <div className="mt-6 text-xs text-slate-400 text-center border-t pt-4">
          <p>Default: admin / Admin@1234 (force change on first login)</p>
          <p className="mt-1">All statutory rates are configurable — no hard-coded values.</p>
        </div>
      </div>
    </div>
  );
}
