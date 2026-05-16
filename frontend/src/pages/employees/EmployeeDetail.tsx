import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";

export default function EmployeeDetail() {
  const { id } = useParams();
  const emp = useQuery({
    queryKey: ["employee", id],
    queryFn: () => api.get(`/employees/${id}`).then(r => r.data),
  });
  const structures = useQuery({
    queryKey: ["sal-structs", id],
    queryFn: () => api.get(`/salary-structures?employee_id=${id}`).then(r => r.data),
  });

  if (emp.isLoading) return <div className="p-6">Loading…</div>;
  const e = emp.data;
  if (!e) return <div className="p-6">Not found</div>;

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{e.first_name} {e.last_name}</h1>
          <p className="text-sm text-slate-500">Code: <span className="font-mono">{e.emp_code}</span> · {e.employment_type}</p>
        </div>
        <Link to={`/employees/${id}/edit`} className="btn-primary">Edit</Link>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="card p-4">
          <h3 className="font-semibold mb-2 text-slate-700">Personal</h3>
          <dl className="text-sm grid grid-cols-2 gap-y-2">
            <dt className="text-slate-500">Email</dt><dd>{e.email || "—"}</dd>
            <dt className="text-slate-500">Phone</dt><dd>{e.phone || "—"}</dd>
            <dt className="text-slate-500">DOB</dt><dd>{e.dob || "—"}</dd>
            <dt className="text-slate-500">Gender</dt><dd>{e.gender || "—"}</dd>
            <dt className="text-slate-500">Address</dt><dd className="col-span-1">{e.address || "—"}</dd>
            <dt className="text-slate-500">State</dt><dd>{e.state || "—"}</dd>
          </dl>
        </div>
        <div className="card p-4">
          <h3 className="font-semibold mb-2 text-slate-700">Statutory</h3>
          <dl className="text-sm grid grid-cols-2 gap-y-2">
            <dt className="text-slate-500">PAN</dt><dd className="font-mono">{e.pan_masked || "—"}</dd>
            <dt className="text-slate-500">Aadhaar</dt><dd className="font-mono">{e.aadhaar_masked || "—"}</dd>
            <dt className="text-slate-500">UAN</dt><dd className="font-mono">{e.uan || "—"}</dd>
            <dt className="text-slate-500">ESI IP</dt><dd className="font-mono">{e.esi_ip_number || "—"}</dd>
            <dt className="text-slate-500">DOJ</dt><dd>{e.date_of_joining || "—"}</dd>
            <dt className="text-slate-500">Exit</dt><dd>{e.date_of_exit || "—"}</dd>
          </dl>
          <div className="mt-3 flex gap-1 flex-wrap">
            {["epf", "esi", "pt", "lwf", "tds"].map(k => (
              <span key={k} className={e[`${k}_applicable`] ? "badge-success" : "badge-muted"}>
                {k.toUpperCase()}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="card p-4">
        <h3 className="font-semibold mb-2 text-slate-700">Bank Details</h3>
        {(e.bank_details ?? []).map((b: any) => (
          <div key={b.id} className="text-sm grid grid-cols-4 gap-2 py-2 border-b last:border-0">
            <div><div className="text-slate-500 text-xs">Bank</div>{b.bank_name}</div>
            <div><div className="text-slate-500 text-xs">IFSC</div>{b.ifsc}</div>
            <div><div className="text-slate-500 text-xs">A/c No.</div><span className="font-mono">{b.account_masked}</span></div>
            <div><div className="text-slate-500 text-xs">Branch</div>{b.branch || "—"}</div>
          </div>
        ))}
      </div>

      <div className="card p-4">
        <h3 className="font-semibold mb-2 text-slate-700">Salary Structures</h3>
        <table className="tbl">
          <thead><tr><th>From</th><th>To</th><th>Basic</th><th>HRA</th><th>Gross</th><th>Status</th></tr></thead>
          <tbody>
            {(structures.data ?? []).map((s: any) => (
              <tr key={s.id}>
                <td>{s.effective_from}</td><td>{s.effective_to || "—"}</td>
                <td className="text-right">{Number(s.basic).toLocaleString("en-IN")}</td>
                <td className="text-right">{Number(s.hra).toLocaleString("en-IN")}</td>
                <td className="text-right font-medium">{Number(s.gross_monthly).toLocaleString("en-IN")}</td>
                <td><span className={s.status === "ACTIVE" ? "badge-success" : "badge-muted"}>{s.status}</span></td>
              </tr>
            ))}
            {structures.data && structures.data.length === 0 &&
              <tr><td colSpan={6} className="text-center text-slate-400 py-4">No salary structures defined</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
