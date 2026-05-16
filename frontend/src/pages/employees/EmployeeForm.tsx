import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";

const tabs = ["Personal", "Employment", "Statutory", "Bank"] as const;

export default function EmployeeForm() {
  const { id } = useParams();
  const isEdit = !!id;
  const navigate = useNavigate();
  const [tab, setTab] = useState<typeof tabs[number]>("Personal");
  const [form, setForm] = useState<any>({
    emp_code: "", first_name: "", last_name: "", email: "", phone: "",
    dob: "", gender: "M", marital_status: "SINGLE", father_name: "", address: "", state: "",
    pan: "", aadhaar: "", uan: "", esi_ip_number: "",
    department_id: "", designation_id: "",
    date_of_joining: "", employment_type: "PERMANENT",
    city_tier: "NON_METRO", state_for_pt: "",
    epf_applicable: true, esi_applicable: true, pt_applicable: true, lwf_applicable: true, tds_applicable: true,
    bank_details: [{ account_number: "", ifsc: "", bank_name: "", branch: "", is_primary: true }],
  });
  const [error, setError] = useState<string | null>(null);
  const departments = useQuery({ queryKey: ["departments"], queryFn: () => api.get("/departments").then(r => r.data) });
  const designations = useQuery({ queryKey: ["designations"], queryFn: () => api.get("/designations").then(r => r.data) });

  useEffect(() => {
    if (!isEdit) return;
    api.get(`/employees/${id}`).then(r => {
      const d = r.data;
      setForm({ ...form, ...d, pan: "", aadhaar: "", bank_details: d.bank_details?.length ? d.bank_details : form.bank_details });
    });
  }, [id]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(null);
    try {
      const payload = { ...form };
      Object.keys(payload).forEach(k => { if (payload[k] === "") payload[k] = null; });
      if (isEdit) {
        await api.put(`/employees/${id}`, payload);
      } else {
        await api.post("/employees", payload);
      }
      navigate("/employees");
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Save failed");
    }
  };

  const upd = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-1">{isEdit ? "Edit" : "New"} Employee</h1>
      <p className="text-sm text-slate-500 mb-4">Personal, employment, statutory, and bank details.</p>
      <div className="card">
        <div className="border-b flex">
          {tabs.map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm border-b-2 ${tab === t ? "border-brand-500 text-brand-700" : "border-transparent text-slate-500"}`}>
              {t}
            </button>
          ))}
        </div>
        <form onSubmit={onSubmit} className="p-4 space-y-4">
          {tab === "Personal" && (
            <div className="grid grid-cols-2 gap-3">
              <div><label className="label">Employee Code *</label>
                <input className="input" required value={form.emp_code} disabled={isEdit} onChange={e=>upd("emp_code", e.target.value)} /></div>
              <div><label className="label">First Name *</label>
                <input className="input" required value={form.first_name} onChange={e=>upd("first_name", e.target.value)} /></div>
              <div><label className="label">Last Name</label>
                <input className="input" value={form.last_name} onChange={e=>upd("last_name", e.target.value)} /></div>
              <div><label className="label">Email</label>
                <input className="input" type="email" value={form.email} onChange={e=>upd("email", e.target.value)} /></div>
              <div><label className="label">Phone</label>
                <input className="input" value={form.phone} onChange={e=>upd("phone", e.target.value)} /></div>
              <div><label className="label">DOB</label>
                <input className="input" type="date" value={form.dob || ""} onChange={e=>upd("dob", e.target.value)} /></div>
              <div><label className="label">Gender</label>
                <select className="input" value={form.gender} onChange={e=>upd("gender", e.target.value)}>
                  <option>M</option><option>F</option><option>O</option></select></div>
              <div><label className="label">Marital Status</label>
                <select className="input" value={form.marital_status} onChange={e=>upd("marital_status", e.target.value)}>
                  <option>SINGLE</option><option>MARRIED</option></select></div>
              <div className="col-span-2"><label className="label">Address</label>
                <input className="input" value={form.address} onChange={e=>upd("address", e.target.value)} /></div>
              <div><label className="label">State</label>
                <input className="input" value={form.state} onChange={e=>upd("state", e.target.value)} /></div>
              <div><label className="label">Father's Name</label>
                <input className="input" value={form.father_name} onChange={e=>upd("father_name", e.target.value)} /></div>
            </div>
          )}
          {tab === "Employment" && (
            <div className="grid grid-cols-2 gap-3">
              <div><label className="label">Department</label>
                <select className="input" value={form.department_id || ""} onChange={e=>upd("department_id", e.target.value ? Number(e.target.value) : null)}>
                  <option value="">—</option>
                  {(departments.data ?? []).map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select></div>
              <div><label className="label">Designation</label>
                <select className="input" value={form.designation_id || ""} onChange={e=>upd("designation_id", e.target.value ? Number(e.target.value) : null)}>
                  <option value="">—</option>
                  {(designations.data ?? []).map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select></div>
              <div><label className="label">Date of Joining</label>
                <input className="input" type="date" value={form.date_of_joining || ""} onChange={e=>upd("date_of_joining", e.target.value)} /></div>
              <div><label className="label">Employment Type</label>
                <select className="input" value={form.employment_type} onChange={e=>upd("employment_type", e.target.value)}>
                  <option>PERMANENT</option><option>CONTRACT</option><option>PROBATION</option></select></div>
              <div><label className="label">City Tier</label>
                <select className="input" value={form.city_tier} onChange={e=>upd("city_tier", e.target.value)}>
                  <option>METRO</option><option>NON_METRO</option></select></div>
              <div><label className="label">State (for PT)</label>
                <input className="input" placeholder="e.g. MH, KA, DL" value={form.state_for_pt || ""} onChange={e=>upd("state_for_pt", e.target.value)} /></div>
            </div>
          )}
          {tab === "Statutory" && (
            <div className="grid grid-cols-2 gap-3">
              <div><label className="label">PAN</label>
                <input className="input" value={form.pan} onChange={e=>upd("pan", e.target.value)} /></div>
              <div><label className="label">Aadhaar</label>
                <input className="input" value={form.aadhaar} onChange={e=>upd("aadhaar", e.target.value)} /></div>
              <div><label className="label">UAN (EPF)</label>
                <input className="input" value={form.uan || ""} onChange={e=>upd("uan", e.target.value)} /></div>
              <div><label className="label">ESI IP Number</label>
                <input className="input" value={form.esi_ip_number || ""} onChange={e=>upd("esi_ip_number", e.target.value)} /></div>
              <div className="col-span-2 grid grid-cols-5 gap-2 pt-2">
                {(["epf", "esi", "pt", "lwf", "tds"] as const).map(k => (
                  <label key={k} className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={form[`${k}_applicable`]} onChange={e=>upd(`${k}_applicable`, e.target.checked)} />
                    <span className="uppercase">{k}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
          {tab === "Bank" && (
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2"><label className="label">Account Number</label>
                <input className="input" value={form.bank_details[0].account_number}
                       onChange={e=>upd("bank_details", [{...form.bank_details[0], account_number: e.target.value}])} /></div>
              <div><label className="label">IFSC</label>
                <input className="input" value={form.bank_details[0].ifsc}
                       onChange={e=>upd("bank_details", [{...form.bank_details[0], ifsc: e.target.value}])} /></div>
              <div><label className="label">Bank Name</label>
                <input className="input" value={form.bank_details[0].bank_name}
                       onChange={e=>upd("bank_details", [{...form.bank_details[0], bank_name: e.target.value}])} /></div>
              <div className="col-span-2"><label className="label">Branch</label>
                <input className="input" value={form.bank_details[0].branch}
                       onChange={e=>upd("bank_details", [{...form.bank_details[0], branch: e.target.value}])} /></div>
            </div>
          )}
          {error && <div className="text-sm text-red-600">{error}</div>}
          <div className="flex justify-end gap-2 pt-3 border-t">
            <button type="button" className="btn-secondary" onClick={() => navigate("/employees")}>Cancel</button>
            <button type="submit" className="btn-primary">Save</button>
          </div>
        </form>
      </div>
    </div>
  );
}
