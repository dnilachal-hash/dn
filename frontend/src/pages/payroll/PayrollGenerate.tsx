import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { api } from "../../api/client";

const MONTHS = [
  ["January", 1], ["February", 2], ["March", 3], ["April", 4],
  ["May", 5], ["June", 6], ["July", 7], ["August", 8],
  ["September", 9], ["October", 10], ["November", 11], ["December", 12],
] as const;

export default function PayrollGenerate() {
  const nav = useNavigate();
  const [fy, setFy] = useState(3);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [workingDays, setWorkingDays] = useState(30);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const generate = useMutation({
    mutationFn: async () => {
      const cm = await api.post("/payroll/months", {
        financial_year_id: fy, month, year, working_days: workingDays,
      });
      const r = await api.post(`/payroll/months/${cm.data.id}/generate`, {});
      return { month_id: cm.data.id, ...r.data };
    },
    onSuccess: (d) => { setResult(d); setError(null); },
    onError: (e: any) => setError(e?.response?.data?.detail ?? "Generation failed"),
  });

  return (
    <div className="p-6 space-y-4 max-w-3xl">
      <h1 className="text-2xl font-bold">Generate Payroll</h1>
      <p className="text-sm text-slate-500">
        This runs the full payroll engine: pro-rata pay → EPF/EPS/EDLI → ESI → PT → LWF → TDS (with regime selection)
        → loan EMI → net salary → CTC. Compliance checks run automatically.
      </p>

      <div className="card p-4 grid grid-cols-4 gap-3">
        <div><label className="label">FY ID</label>
          <input className="input" type="number" value={fy} onChange={e => setFy(Number(e.target.value))} /></div>
        <div><label className="label">Month</label>
          <select className="input" value={month} onChange={e => setMonth(Number(e.target.value))}>
            {MONTHS.map(([n, v]) => <option key={v} value={v}>{n}</option>)}
          </select></div>
        <div><label className="label">Year</label>
          <input className="input" type="number" value={year} onChange={e => setYear(Number(e.target.value))} /></div>
        <div><label className="label">Working Days</label>
          <input className="input" type="number" value={workingDays} onChange={e => setWorkingDays(Number(e.target.value))} /></div>
      </div>

      <div className="flex gap-2">
        <button className="btn-primary" disabled={generate.isPending} onClick={() => generate.mutate()}>
          {generate.isPending ? "Generating…" : "Generate Payroll for All Active Employees"}
        </button>
        <button className="btn-secondary" onClick={() => nav("/payroll")}>Back to Payroll List</button>
      </div>

      {error && <div className="card p-4 text-red-600">{error}</div>}

      {result && (
        <div className="card p-4 bg-green-50 border-green-200">
          <h3 className="font-semibold text-green-700 mb-2">Payroll Generated</h3>
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div><div className="text-slate-500 text-xs">Records Generated</div><div className="text-xl font-bold">{result.generated}</div></div>
            <div><div className="text-slate-500 text-xs">Skipped</div><div className="text-xl font-bold">{result.skipped}</div></div>
            <div><div className="text-slate-500 text-xs">Alerts Raised</div><div className="text-xl font-bold">{result.alerts}</div></div>
            <div><div className="text-slate-500 text-xs">Critical Alerts</div><div className="text-xl font-bold text-red-600">{result.critical}</div></div>
          </div>
          <button className="btn-primary mt-3" onClick={() => nav("/payroll")}>Go to Approval</button>
        </div>
      )}

      <div className="card p-4 bg-amber-50 border-amber-200 text-sm">
        <strong>Note:</strong> All statutory rates (EPF 12%, ESI 0.75%/3.25%, PT slabs, TDS slabs, etc.) are pulled
        from the Statutory Settings module. Verify they match current government notifications before approving payroll.
      </div>
    </div>
  );
}
