import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { Download, FileText } from "lucide-react";

const MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export default function PayrollHistory() {
  const qc = useQueryClient();
  const months = useQuery({ queryKey: ["payroll-months"],
    queryFn: () => api.get("/payroll/months").then(r => r.data) });

  const approve = useMutation({
    mutationFn: (id: number) => api.post(`/payroll/months/${id}/approve`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payroll-months"] }),
  });
  const lock = useMutation({
    mutationFn: (id: number) => api.post(`/payroll/months/${id}/lock`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payroll-months"] }),
  });

  const downloadReport = async (monthId: number, format: "pdf" | "xlsx") => {
    const r = await api.get(`/reports/month/payroll-summary?payroll_month_id=${monthId}&format=${format}`,
      { responseType: "blob" });
    const url = URL.createObjectURL(r.data);
    const a = document.createElement("a"); a.href = url;
    a.download = `payroll_summary_${monthId}.${format}`; a.click();
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Payroll Months</h1>
        <Link to="/payroll/generate" className="btn-primary">+ New Payroll Month</Link>
      </div>

      <div className="card overflow-hidden">
        <table className="tbl">
          <thead>
            <tr>
              <th>Period</th><th>Status</th><th>Working Days</th>
              <th>Generated</th><th>Approved</th><th>Locked</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {(months.data ?? []).map((m: any) => (
              <tr key={m.id}>
                <td className="font-medium">{MONTHS[m.month]} {m.year}</td>
                <td>
                  <span className={
                    m.status === "PAID" ? "badge-success" :
                    m.status === "LOCKED" ? "badge-info" :
                    m.status === "APPROVED" ? "badge-info" :
                    m.status === "GENERATED" ? "badge-warning" : "badge-muted"
                  }>{m.status}</span>
                </td>
                <td>{m.working_days}</td>
                <td className="text-xs">{m.generated_at?.slice(0, 16).replace("T", " ") || "—"}</td>
                <td className="text-xs">{m.approved_at?.slice(0, 16).replace("T", " ") || "—"}</td>
                <td className="text-xs">{m.locked_at?.slice(0, 16).replace("T", " ") || "—"}</td>
                <td className="flex gap-2">
                  <button title="PDF Summary" onClick={() => downloadReport(m.id, "pdf")} className="text-brand-500"><FileText size={16} /></button>
                  <button title="Excel Summary" onClick={() => downloadReport(m.id, "xlsx")} className="text-emerald-600"><Download size={16} /></button>
                  {m.status === "GENERATED" &&
                    <button className="text-xs underline text-brand-600" onClick={() => approve.mutate(m.id)}>Approve</button>}
                  {m.status === "APPROVED" &&
                    <button className="text-xs underline text-amber-600" onClick={() => lock.mutate(m.id)}>Lock</button>}
                </td>
              </tr>
            ))}
            {months.data && months.data.length === 0 &&
              <tr><td colSpan={7} className="text-center text-slate-400 py-4">No payroll months created</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
