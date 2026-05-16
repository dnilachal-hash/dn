import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import { Plus, Search, Upload, Eye, Edit } from "lucide-react";

export default function EmployeeList() {
  const [search, setSearch] = useState("");
  const [dept, setDept] = useState<number | "">("");
  const [active, setActive] = useState<boolean | "">(true);

  const employees = useQuery({
    queryKey: ["employees", search, dept, active],
    queryFn: async () => {
      const params: any = { page: 1, page_size: 100 };
      if (search) params.search = search;
      if (dept) params.department_id = dept;
      if (active !== "") params.is_active = active;
      const r = await api.get("/employees", { params });
      return r.data;
    },
  });

  const departments = useQuery({
    queryKey: ["departments"],
    queryFn: () => api.get("/departments").then(r => r.data),
  });

  const downloadTemplate = async () => {
    const r = await api.get("/employees/import/template", { responseType: "blob" });
    const url = URL.createObjectURL(r.data);
    const a = document.createElement("a"); a.href = url; a.download = "employees_template.xlsx"; a.click();
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Employees</h1>
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={downloadTemplate}>
            <Upload className="inline mr-1" size={14}/> Import Template
          </button>
          <Link to="/employees/new" className="btn-primary">
            <Plus className="inline mr-1" size={14}/> Add Employee
          </Link>
        </div>
      </div>

      <div className="card p-3 flex gap-3 items-center">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-3 text-slate-400"/>
          <input className="input pl-9" placeholder="Search by name or code…"
                 value={search} onChange={e=>setSearch(e.target.value)} />
        </div>
        <select className="input w-56" value={dept} onChange={e=>setDept(e.target.value as any)}>
          <option value="">All Departments</option>
          {(departments.data ?? []).map((d: any) =>
            <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <select className="input w-40" value={active === "" ? "" : String(active)}
                onChange={e => setActive(e.target.value === "" ? "" : e.target.value === "true")}>
          <option value="true">Active</option>
          <option value="false">Inactive</option>
          <option value="">All</option>
        </select>
      </div>

      <div className="card overflow-hidden">
        <table className="tbl">
          <thead>
            <tr>
              <th>Code</th><th>Name</th><th>Department</th><th>Designation</th>
              <th>Type</th><th>DOJ</th><th>Status</th><th></th>
            </tr>
          </thead>
          <tbody>
            {employees.isLoading && <tr><td colSpan={8} className="text-center py-6">Loading…</td></tr>}
            {(employees.data?.items ?? []).map((e: any) => (
              <tr key={e.id}>
                <td className="font-mono text-xs">{e.emp_code}</td>
                <td className="font-medium">{e.first_name} {e.last_name}</td>
                <td>{departments.data?.find((d:any)=>d.id===e.department_id)?.name ?? "—"}</td>
                <td>{e.designation_id ?? "—"}</td>
                <td>{e.employment_type}</td>
                <td className="text-xs">{e.date_of_joining ?? "—"}</td>
                <td><span className={e.is_active ? "badge-success" : "badge-muted"}>
                  {e.is_active ? "Active" : "Inactive"}</span></td>
                <td>
                  <Link to={`/employees/${e.id}`} className="text-brand-500 mr-3"><Eye size={16}/></Link>
                  <Link to={`/employees/${e.id}/edit`} className="text-slate-600"><Edit size={16}/></Link>
                </td>
              </tr>
            ))}
            {employees.data && employees.data.items.length === 0 &&
              <tr><td colSpan={8} className="text-center py-6 text-slate-400">No employees found</td></tr>}
          </tbody>
        </table>
      </div>
      <div className="text-xs text-slate-500">Total: {employees.data?.total ?? 0}</div>
    </div>
  );
}
