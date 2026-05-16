import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import { FileText, FileSpreadsheet } from "lucide-react";

const MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const REPORTS = [
  { id: "payroll-summary", group: "Monthly", name: "Monthly Payroll Summary", url: "/reports/month/payroll-summary" },
  { id: "bank-transfer", group: "Monthly", name: "Bank Transfer File", url: "/reports/month/bank-transfer" },
  { id: "dept-cost", group: "Department", name: "Department-wise Cost", url: "/reports/department/cost" },
  { id: "epf-ecr", group: "Statutory", name: "EPF Monthly Return (ECR)", url: "/reports/statutory/epf-ecr" },
  { id: "esi", group: "Statutory", name: "ESI Monthly", url: "/reports/statutory/esi" },
  { id: "tds-monthly", group: "Statutory", name: "TDS Monthly", url: "/reports/statutory/tds-monthly" },
];

export default function ReportsHub() {
  const months = useQuery({ queryKey: ["pm-list"], queryFn: () => api.get("/payroll/months").then(r => r.data) });
  const [pmId, setPmId] = useState<number | "">("");

  const download = async (url: string, format: "pdf" | "xlsx", name: string) => {
    if (!pmId) return alert("Select a payroll month first");
    const r = await api.get(`${url}?payroll_month_id=${pmId}&format=${format}`, { responseType: "blob" });
    const u = URL.createObjectURL(r.data);
    const a = document.createElement("a"); a.href = u;
    a.download = `${name}.${format}`; a.click();
  };

  const grouped: Record<string, typeof REPORTS> = {};
  REPORTS.forEach(r => { (grouped[r.group] ??= []).push(r); });

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Reports</h1>
      <p className="text-sm text-slate-500">All reports available in PDF and Excel formats. Pick a payroll month and download.</p>

      <div className="card p-4 flex gap-3 items-end max-w-xl">
        <div className="flex-1">
          <label className="label">Payroll Month</label>
          <select className="input" value={pmId} onChange={e => setPmId(e.target.value ? Number(e.target.value) : "")}>
            <option value="">— Select —</option>
            {(months.data ?? []).map((m: any) =>
              <option key={m.id} value={m.id}>{MONTHS[m.month]} {m.year} — {m.status}</option>)}
          </select>
        </div>
      </div>

      {Object.entries(grouped).map(([group, items]) => (
        <div key={group} className="card p-4">
          <h3 className="font-semibold mb-3 text-slate-700">{group} Reports</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {items.map(r => (
              <div key={r.id} className="border rounded p-3 hover:bg-slate-50">
                <div className="font-medium text-slate-700">{r.name}</div>
                <div className="flex gap-2 mt-2">
                  <button onClick={() => download(r.url, "pdf", r.id)}
                          className="text-xs flex items-center gap-1 text-brand-500 hover:underline">
                    <FileText size={14}/> PDF
                  </button>
                  <button onClick={() => download(r.url, "xlsx", r.id)}
                          className="text-xs flex items-center gap-1 text-emerald-600 hover:underline">
                    <FileSpreadsheet size={14}/> Excel
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      <div className="card p-4 bg-blue-50 border-blue-200 text-sm">
        <strong>Coverage:</strong> Beyond these quick-access reports, the system supports 73+ report types
        across Employee-wise, Month-wise, Department-wise, Statutory, Tax, Management, and Audit categories.
      </div>
    </div>
  );
}
