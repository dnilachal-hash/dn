import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";

export default function AuditLogs() {
  const [entity, setEntity] = useState("");
  const logs = useQuery({
    queryKey: ["audit", entity],
    queryFn: () => api.get("/audit/logs", { params: { entity_type: entity || undefined } })
                      .then(r => r.data),
  });

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Audit Logs</h1>
      <div className="card p-4 flex gap-3 items-end">
        <div>
          <label className="label">Entity Type</label>
          <input className="input w-56" placeholder="e.g. PayrollMonth"
                 value={entity} onChange={e => setEntity(e.target.value)} />
        </div>
      </div>
      <div className="card overflow-hidden">
        <table className="tbl">
          <thead><tr><th>When</th><th>User</th><th>Action</th><th>Entity</th><th>ID</th><th>Changes</th><th>IP</th></tr></thead>
          <tbody>
            {(logs.data ?? []).map((l: any) => (
              <tr key={l.id}>
                <td className="text-xs">{l.ts?.slice(0, 19).replace("T", " ")}</td>
                <td>{l.user || "system"}</td>
                <td className="font-mono text-xs">{l.action}</td>
                <td>{l.entity}</td>
                <td>{l.entity_id || "—"}</td>
                <td className="text-xs max-w-md truncate">
                  {l.new ? JSON.stringify(l.new).slice(0, 100) : "—"}
                </td>
                <td className="text-xs">{l.ip || "—"}</td>
              </tr>
            ))}
            {logs.data && logs.data.length === 0 &&
              <tr><td colSpan={7} className="text-center text-slate-400 py-6">No audit entries</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
