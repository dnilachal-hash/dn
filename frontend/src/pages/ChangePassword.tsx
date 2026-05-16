import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuthStore } from "../store/authStore";

export default function ChangePassword() {
  const { clearForcePasswordChange } = useAuthStore();
  const navigate = useNavigate();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (newPassword !== confirm) { setError("Passwords do not match"); return; }
    setLoading(true);
    try {
      await api.post("/auth/change-password", { old_password: oldPassword, new_password: newPassword });
      clearForcePasswordChange();
      navigate("/");
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Failed");
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 p-4">
      <div className="w-full max-w-md card p-6">
        <h2 className="text-xl font-bold mb-1">Change Password</h2>
        <p className="text-sm text-slate-500 mb-4">You must change your password before continuing.</p>
        <form onSubmit={onSubmit} className="space-y-3">
          <div><label className="label">Current Password</label>
            <input type="password" className="input" required value={oldPassword} onChange={e=>setOldPassword(e.target.value)} /></div>
          <div><label className="label">New Password</label>
            <input type="password" className="input" required value={newPassword} onChange={e=>setNewPassword(e.target.value)} />
            <p className="text-xs text-slate-400 mt-1">Min 8 chars, 1 uppercase, 1 number, 1 special character</p>
          </div>
          <div><label className="label">Confirm New Password</label>
            <input type="password" className="input" required value={confirm} onChange={e=>setConfirm(e.target.value)} /></div>
          {error && <div className="text-sm text-red-600">{error}</div>}
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? "Updating..." : "Update Password"}
          </button>
        </form>
      </div>
    </div>
  );
}
