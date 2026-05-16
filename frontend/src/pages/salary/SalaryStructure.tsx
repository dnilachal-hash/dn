import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";

const FIELDS = [
  "basic", "da", "hra", "medical_allowance", "conveyance_allowance",
  "transport_allowance", "special_allowance", "other_allowance",
  "children_education_allowance", "uniform_allowance", "telephone_allowance",
  "internet_allowance", "research_allowance",
] as const;

export default function SalaryStructure() {
  const qc = useQueryClient();
  const [empId, setEmpId] = useState<number | "">("");
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<any>({
    financial_year_id: 3,
    effective_from: "2025-04-01",
    ...Object.fromEntries(FIELDS.map(f => [f, 0])),
  });

  const employees = useQuery({ queryKey: ["employees-all"],
    queryFn: () => api.get("/employees?page_size=200").then(r => r.data) });
  const structures = useQuery({
    queryKey: ["structures", empId],
    queryFn: () => empId ? api.get(`/salary-structures?employee_id=${empId}`).then(r => r.data) : Promise.resolve([]),
    enabled: !!empId,
  });

  const create = useMutation({
    mutationFn: (data: any) => api.post("/salary-structures", data).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["structures"] });
      setCreating(false);
    },
  });
  const activate = useMutation({
    mutationFn: (id: number) => api.post(`/salary-structures/${id}/activate`).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["structures"] }),
  });

  const gross = FIELDS.reduce((sum, f) => sum + Number(form[f] || 0), 0);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!empId) return;
    create.mutate({
      employee_id: empId,
      ...Object.fromEntries(FIELDS.map(f => [f, Number(form[f] || 0)])),
      financial_year_id: form.financial_year_id,
      effective_from: form.effective_from,
      custom_allowances: [],
    });
  };

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Salary Structures</h1>

      <div className="card p-4 flex gap-3 items-end">
        <div className="flex-1">
          <label className="label">Select Employee</label>
          <select className="input" value={empId} onChange={e => setEmpId(e.target.value ? Number(e.target.value) : "")}>
            <option value="">— Choose —</option>
            {(employees.data?.items ?? []).map((e: any) =>
              <option key={e.id} value={e.id}>{e.emp_code} — {e.first_name} {e.last_name}</option>)}
          </select>
        </div>
        {empId && <button className="btn-primary" onClick={() => setCreating(true)}>+ New Structure</button>}
      </div>

      {empId && (
        <div className="card overflow-hidden">
          <table className="tbl">
            <thead>
              <tr><th>From</th><th>To</th><th>Basic</th><th>DA</th><th>HRA</th><th>Gross</th><th>Status</th><th></th></tr>
            </thead>
            <tbody>
              {(structures.data ?? []).map((s: any) => (
                <tr key={s.id}>
                  <td>{s.effective_from}</td>
                  <td>{s.effective_to || "—"}</td>
                  <td className="text-right">{Number(s.basic).toLocaleString("en-IN")}</td>
                  <td className="text-right">{Number(s.da).toLocaleString("en-IN")}</td>
                  <td className="text-right">{Number(s.hra).toLocaleString("en-IN")}</td>
                  <td className="text-right font-medium">{Number(s.gross_monthly).toLocaleString("en-IN")}</td>
                  <td><span className={s.status === "ACTIVE" ? "badge-success" : "badge-muted"}>{s.status}</span></td>
                  <td>{s.status === "DRAFT" && <button className="btn-secondary" onClick={() => activate.mutate(s.id)}>Activate</button>}</td>
                </tr>
              ))}
              {structures.data && structures.data.length === 0 &&
                <tr><td colSpan={8} className="text-center text-slate-400 py-4">No structures yet</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {creating && (
        <div className="card p-4">
          <h3 className="font-semibold mb-3">New Salary Structure</h3>
          <form onSubmit={onSubmit} className="grid grid-cols-3 gap-3">
            <div><label className="label">FY ID</label>
              <input className="input" type="number" value={form.financial_year_id} onChange={e => setForm({ ...form, financial_year_id: Number(e.target.value) })} /></div>
            <div className="col-span-2"><label className="label">Effective From</label>
              <input className="input" type="date" value={form.effective_from} onChange={e => setForm({ ...form, effective_from: e.target.value })} /></div>
            {FIELDS.map(f => (
              <div key={f}>
                <label className="label">{f.replace(/_/g, " ")}</label>
                <input className="input" type="number" step="0.01"
                  value={form[f]} onChange={e => setForm({ ...form, [f]: e.target.value })} />
              </div>
            ))}
            <div className="col-span-3 flex items-center justify-between pt-2 border-t">
              <div className="text-lg">Gross Monthly: <span className="font-bold text-brand-700">₹ {gross.toLocaleString("en-IN")}</span></div>
              <div className="flex gap-2">
                <button type="button" className="btn-secondary" onClick={() => setCreating(false)}>Cancel</button>
                <button type="submit" className="btn-primary" disabled={create.isPending}>
                  {create.isPending ? "Saving…" : "Save Draft"}
                </button>
              </div>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
