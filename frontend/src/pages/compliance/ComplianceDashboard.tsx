import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { AlertTriangle, AlertCircle, Info, CheckCircle2 } from "lucide-react";

export default function ComplianceDashboard() {
  const qc = useQueryClient();
  const [severity, setSeverity] = useState<string>("");
  const [resolved, setResolved] = useState(false);

  const alerts = useQuery({
    queryKey: ["alerts", severity, resolved],
    queryFn: () => api.get("/compliance/alerts", { params: { severity: severity || undefined, resolved } })
                      .then(r => r.data),
  });

  const resolve = useMutation({
    mutationFn: (id: number) => api.post(`/compliance/alerts/${id}/resolve`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });

  const icon = (sev: string) =>
    sev === "CRITICAL" ? <AlertCircle className="text-red-600" size={18} /> :
    sev === "WARNING" ? <AlertTriangle className="text-amber-600" size={18} /> :
    <Info className="text-blue-600" size={18} />;

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Compliance Dashboard</h1>

      <div className="card p-4 flex gap-3 items-end">
        <div>
          <label className="label">Severity</label>
          <select className="input w-40" value={severity} onChange={e => setSeverity(e.target.value)}>
            <option value="">All</option><option>CRITICAL</option><option>WARNING</option><option>INFO</option>
          </select>
        </div>
        <div>
          <label className="label">Resolved?</label>
          <select className="input w-32" value={String(resolved)} onChange={e => setResolved(e.target.value === "true")}>
            <option value="false">No</option><option value="true">Yes</option>
          </select>
        </div>
      </div>

      <div className="card overflow-hidden">
        <table className="tbl">
          <thead><tr><th></th><th>Type</th><th>Severity</th><th>Message</th><th>Employee</th><th>When</th><th></th></tr></thead>
          <tbody>
            {(alerts.data ?? []).map((a: any) => (
              <tr key={a.id}>
                <td>{icon(a.severity)}</td>
                <td className="font-mono text-xs">{a.type}</td>
                <td><span className={
                  a.severity === "CRITICAL" ? "badge-danger" :
                  a.severity === "WARNING" ? "badge-warning" : "badge-info"
                }>{a.severity}</span></td>
                <td className="text-sm">{a.message}</td>
                <td className="text-xs">EMP-{a.employee_id || "—"}</td>
                <td className="text-xs">{a.created_at?.slice(0, 16).replace("T", " ")}</td>
                <td>
                  {!a.is_resolved &&
                    <button className="text-xs underline text-green-700" onClick={() => resolve.mutate(a.id)}>Resolve</button>}
                </td>
              </tr>
            ))}
            {alerts.data && alerts.data.length === 0 &&
              <tr><td colSpan={7} className="text-center text-slate-400 py-6">
                <CheckCircle2 className="inline mb-1 text-green-600" /> All clear — no alerts
              </td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
