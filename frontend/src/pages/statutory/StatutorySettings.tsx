import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";

const TABS = ["EPF", "ESI", "TDS", "PT", "LWF"] as const;

export default function StatutorySettings() {
  const [tab, setTab] = useState<typeof TABS[number]>("EPF");
  const epf = useQuery({ queryKey: ["epf"], queryFn: () => api.get("/statutory/epf").then(r => r.data) });
  const esi = useQuery({ queryKey: ["esi"], queryFn: () => api.get("/statutory/esi").then(r => r.data) });
  const tds = useQuery({ queryKey: ["tds"], queryFn: () => api.get("/statutory/tds").then(r => r.data) });
  const pt = useQuery({ queryKey: ["pt"], queryFn: () => api.get("/statutory/pt").then(r => r.data) });
  const lwf = useQuery({ queryKey: ["lwf"], queryFn: () => api.get("/statutory/lwf").then(r => r.data) });

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Statutory Settings</h1>
      <p className="text-sm text-slate-500">All rates are configurable per Financial Year. Verify against current government notifications before saving.</p>

      <div className="card">
        <div className="border-b flex">
          {TABS.map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm border-b-2 ${tab === t ? "border-brand-500 text-brand-700" : "border-transparent text-slate-500"}`}>
              {t}
            </button>
          ))}
        </div>
        <div className="p-4">
          {tab === "EPF" && (
            <table className="tbl">
              <thead><tr><th>FY ID</th><th>Employee %</th><th>Employer %</th><th>EPS %</th><th>EPS Ceiling</th><th>EDLI %</th><th>Admin %</th><th>PF Wage Ceiling</th></tr></thead>
              <tbody>
                {(epf.data ?? []).map((s: any) => (
                  <tr key={s.id}>
                    <td>{s.financial_year_id}</td>
                    <td className="text-right">{s.employee_rate}%</td>
                    <td className="text-right">{s.employer_rate}%</td>
                    <td className="text-right">{s.eps_rate}%</td>
                    <td className="text-right">₹{Number(s.eps_wage_ceiling).toLocaleString("en-IN")}</td>
                    <td className="text-right">{s.edli_rate}%</td>
                    <td className="text-right">{s.admin_charge_rate}%</td>
                    <td className="text-right">₹{Number(s.pf_wage_ceiling).toLocaleString("en-IN")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {tab === "ESI" && (
            <table className="tbl">
              <thead><tr><th>FY ID</th><th>Employee %</th><th>Employer %</th><th>Wage Ceiling</th></tr></thead>
              <tbody>
                {(esi.data ?? []).map((s: any) => (
                  <tr key={s.id}>
                    <td>{s.financial_year_id}</td>
                    <td className="text-right">{s.employee_rate}%</td>
                    <td className="text-right">{s.employer_rate}%</td>
                    <td className="text-right">₹{Number(s.wage_ceiling).toLocaleString("en-IN")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {tab === "TDS" && (
            <div className="space-y-4">
              {(tds.data ?? []).map((s: any) => (
                <div key={s.id} className="border rounded p-3">
                  <div className="flex justify-between mb-2">
                    <div><strong>FY ID:</strong> {s.financial_year_id} · Default regime: <span className="badge-info">{s.tax_regime_default}</span></div>
                    <div className="text-sm text-slate-500">Cess: {s.cess_rate}%</div>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <div className="font-medium mb-1">Old Regime Slabs</div>
                      <table className="tbl">
                        <thead><tr><th>Upto</th><th>Rate %</th></tr></thead>
                        <tbody>
                          {(s.tax_slabs_old ?? []).map((sl: any, i: number) => (
                            <tr key={i}><td>{sl.upto ? `₹${Number(sl.upto).toLocaleString("en-IN")}` : "Above all"}</td><td>{sl.rate}%</td></tr>
                          ))}
                        </tbody>
                      </table>
                      <div className="text-xs text-slate-500 mt-1">Std Deduction: ₹{s.standard_deduction_old} · Rebate 87A: ₹{s.rebate_87a_amount_old} (upto ₹{s.rebate_87a_limit_old})</div>
                    </div>
                    <div>
                      <div className="font-medium mb-1">New Regime Slabs</div>
                      <table className="tbl">
                        <thead><tr><th>Upto</th><th>Rate %</th></tr></thead>
                        <tbody>
                          {(s.tax_slabs_new ?? []).map((sl: any, i: number) => (
                            <tr key={i}><td>{sl.upto ? `₹${Number(sl.upto).toLocaleString("en-IN")}` : "Above all"}</td><td>{sl.rate}%</td></tr>
                          ))}
                        </tbody>
                      </table>
                      <div className="text-xs text-slate-500 mt-1">Std Deduction: ₹{s.standard_deduction_new} · Rebate 87A: ₹{s.rebate_87a_amount_new} (upto ₹{s.rebate_87a_limit_new})</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          {tab === "PT" && (
            <table className="tbl">
              <thead><tr><th>State</th><th>FY</th><th>Slabs (Min - Max → Amount)</th><th>Periodicity</th></tr></thead>
              <tbody>
                {(pt.data ?? []).map((s: any) => (
                  <tr key={s.id}>
                    <td>{s.state_code}</td><td>{s.financial_year_id}</td>
                    <td className="text-xs">{(s.slabs ?? []).map((sl: any, i: number) =>
                      <span key={i} className="inline-block mr-2 mb-1 px-2 py-0.5 bg-slate-100 rounded">
                        ₹{sl.min}–{sl.max ?? "∞"}: ₹{sl.amount}
                      </span>)}</td>
                    <td>{s.periodicity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {tab === "LWF" && (
            <table className="tbl">
              <thead><tr><th>State</th><th>FY</th><th>Employee</th><th>Employer</th><th>Periodicity</th></tr></thead>
              <tbody>
                {(lwf.data ?? []).map((s: any) => (
                  <tr key={s.id}>
                    <td>{s.state_code}</td><td>{s.financial_year_id}</td>
                    <td>₹{s.employee_amount}</td><td>₹{s.employer_amount}</td>
                    <td>{s.periodicity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
