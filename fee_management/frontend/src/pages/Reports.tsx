import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts'
import { Download, FileText, BarChart3, Users, DollarSign, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import client from '../api/client'
import { format, parseISO } from 'date-fns'
import { useAuthStore } from '../store/authStore'

const fmt = (n: number) => '₹' + (n || 0).toLocaleString('en-IN')
const PIE_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

const REPORT_TABS = [
  { id: 'daily', label: 'Daily Collection', icon: <DollarSign size={15} /> },
  { id: 'monthly', label: 'Monthly Collection', icon: <BarChart3 size={15} /> },
  { id: 'fy_summary', label: 'FY Summary', icon: <FileText size={15} /> },
  { id: 'student_ledger', label: 'Student Ledger', icon: <Users size={15} /> },
  { id: 'fee_head_wise', label: 'Fee Head Wise', icon: <FileText size={15} /> },
  { id: 'payment_mode', label: 'Payment Mode Wise', icon: <BarChart3 size={15} /> },
  { id: 'dues', label: 'Dues Report', icon: <AlertCircle size={15} /> },
  { id: 'cheque_status', label: 'Cheque Status', icon: <FileText size={15} /> },
  { id: 'cancelled', label: 'Cancelled Receipts', icon: <FileText size={15} /> },
  { id: 'corrected', label: 'Corrected Receipts', icon: <FileText size={15} /> },
]

async function exportReport(report: string, params: Record<string, string>, type: 'excel' | 'pdf') {
  try {
    const ext = type === 'excel' ? '.xlsx' : '.pdf'
    const mime = type === 'excel' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 'application/pdf'
    const res = await client.get(`/reports/export/${type}`, {
      params: { report, ...params },
      responseType: 'blob',
    })
    const url = URL.createObjectURL(new Blob([res.data], { type: mime }))
    const a = document.createElement('a')
    a.href = url
    a.download = `${report}_report${ext}`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    toast.error('Export failed')
  }
}

function ExportButtons({ report, params }: { report: string; params: Record<string, string> }) {
  return (
    <div className="flex gap-2">
      <button onClick={() => exportReport(report, params, 'excel')} className="btn-secondary btn-sm">
        <Download size={13} /> Excel
      </button>
      <button onClick={() => exportReport(report, params, 'pdf')} className="btn-secondary btn-sm">
        <Download size={13} /> PDF
      </button>
    </div>
  )
}

// ─── Daily Collection ─────────────────────────────────────────────────────────
function DailyCollection() {
  const [date, setDate] = useState(format(new Date(), 'yyyy-MM-dd'))
  const { data, isLoading } = useQuery({
    queryKey: ['report-daily', date],
    queryFn: () => client.get('/reports/daily-collection', { params: { date } }).then((r) => r.data),
    enabled: !!date,
  })
  const rows = data?.rows || []
  const total = rows.reduce((s: number, r: any) => s + (r.amount || 0), 0)
  return (
    <div>
      <div className="flex flex-wrap items-end gap-4 mb-4">
        <div><label className="label">Date</label><input type="date" className="input w-auto" value={date} onChange={(e) => setDate(e.target.value)} /></div>
        <ExportButtons report="daily_collection" params={{ date }} />
      </div>
      {isLoading ? <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div> : (
        <>
          <div className="mb-3 text-sm font-medium text-gray-700">Total: <span className="text-indigo-700 text-base">{fmt(total)}</span></div>
          <table className="tbl">
            <thead><tr><th>Receipt No</th><th>Student</th><th>Course</th><th>Mode</th><th className="text-right">Amount</th></tr></thead>
            <tbody>
              {rows.length === 0 && <tr><td colSpan={5} className="text-center text-gray-400 py-6">No collections on this date</td></tr>}
              {rows.map((r: any) => (
                <tr key={r.id}><td className="font-medium">{r.receipt_number}</td><td>{r.student_name}</td><td>{r.course_name || '-'}</td><td>{r.payment_mode}</td><td className="text-right font-medium">{fmt(r.amount || r.total_amount)}</td></tr>
              ))}
            </tbody>
            {rows.length > 0 && <tfoot><tr><td colSpan={4} className="text-right font-bold">Total</td><td className="text-right font-bold">{fmt(total)}</td></tr></tfoot>}
          </table>
        </>
      )}
    </div>
  )
}

// ─── Monthly Collection ───────────────────────────────────────────────────────
function MonthlyCollection() {
  const now = new Date()
  const [month, setMonth] = useState(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`)
  const { data, isLoading } = useQuery({
    queryKey: ['report-monthly', month],
    queryFn: () => client.get('/reports/monthly-collection', { params: { month } }).then((r) => r.data),
    enabled: !!month,
  })
  const rows = data?.rows || []
  const dailyBreakdown = data?.daily_breakdown || []
  const total = data?.total_amount || rows.reduce((s: number, r: any) => s + (r.amount || r.total_amount || 0), 0)
  return (
    <div>
      <div className="flex flex-wrap items-end gap-4 mb-4">
        <div><label className="label">Month</label><input type="month" className="input w-auto" value={month} onChange={(e) => setMonth(e.target.value)} /></div>
        <ExportButtons report="monthly_collection" params={{ month }} />
      </div>
      {isLoading ? <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div> : (
        <>
          <div className="mb-3 text-sm font-medium text-gray-700">Total: <span className="text-indigo-700 text-base">{fmt(total)}</span></div>
          {dailyBreakdown.length > 0 && (
            <div className="mb-6">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={dailyBreakdown}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}K`} />
                  <Tooltip formatter={(v: number) => [fmt(v), 'Amount']} />
                  <Bar dataKey="amount" fill="#6366f1" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          <table className="tbl">
            <thead><tr><th>Receipt No</th><th>Date</th><th>Student</th><th>Mode</th><th className="text-right">Amount</th></tr></thead>
            <tbody>
              {rows.length === 0 && <tr><td colSpan={5} className="text-center text-gray-400 py-6">No data for this month</td></tr>}
              {rows.map((r: any) => (
                <tr key={r.id}><td className="font-medium">{r.receipt_number}</td><td>{r.receipt_date ? format(parseISO(r.receipt_date), 'dd/MM/yyyy') : '-'}</td><td>{r.student_name}</td><td>{r.payment_mode}</td><td className="text-right font-medium">{fmt(r.amount || r.total_amount)}</td></tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}

// ─── FY Summary ───────────────────────────────────────────────────────────────
function FYSummary() {
  const { data: fys } = useQuery({ queryKey: ['financial-years'], queryFn: () => client.get('/financial-years/').then((r) => r.data) })
  const fyList = fys?.items || fys || []
  const activeFy = fyList.find((fy: any) => fy.is_active)
  const [fyId, setFyId] = useState(activeFy?.id?.toString() || '')
  const { data, isLoading } = useQuery({
    queryKey: ['report-fy', fyId],
    queryFn: () => client.get('/reports/fy-summary', { params: { financial_year_id: fyId } }).then((r) => r.data),
    enabled: !!fyId,
  })
  const rows = data?.fee_head_summary || []
  return (
    <div>
      <div className="flex flex-wrap items-end gap-4 mb-4">
        <div>
          <label className="label">Financial Year</label>
          <select className="input w-48" value={fyId} onChange={(e) => setFyId(e.target.value)}>
            <option value="">Select FY</option>
            {fyList.map((fy: any) => <option key={fy.id} value={fy.id}>{fy.name}</option>)}
          </select>
        </div>
        {fyId && <ExportButtons report="fy_summary" params={{ financial_year_id: fyId }} />}
      </div>
      {isLoading ? <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div> : data && (
        <>
          <div className="grid grid-cols-3 gap-4 mb-6">
            {[['Total Receipts', data.total_receipts], ['Total Collected', fmt(data.total_collected)], ['Total Dues', fmt(data.total_dues)]].map(([k, v]) => (
              <div key={k as string} className="card bg-indigo-50 border-indigo-200 text-center py-3">
                <div className="text-xl font-bold text-indigo-700">{v}</div>
                <div className="text-xs text-indigo-600 mt-0.5">{k}</div>
              </div>
            ))}
          </div>
          <table className="tbl">
            <thead><tr><th>Fee Head</th><th className="text-right">Total Due</th><th className="text-right">Collected</th><th className="text-right">Balance</th></tr></thead>
            <tbody>
              {rows.map((r: any) => (
                <tr key={r.fee_head_id}><td className="font-medium">{r.fee_head_name}</td><td className="text-right">{fmt(r.total_due)}</td><td className="text-right text-emerald-700">{fmt(r.collected)}</td><td className={`text-right font-medium ${r.balance > 0 ? 'text-red-600' : ''}`}>{fmt(r.balance)}</td></tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}

// ─── Student Ledger ───────────────────────────────────────────────────────────
function StudentLedger() {
  const [search, setSearch] = useState('')
  const [suggestions, setSuggestions] = useState<any[]>([])
  const [student, setStudent] = useState<any>(null)
  const { data, isLoading } = useQuery({
    queryKey: ['report-ledger', student?.id],
    queryFn: () => client.get(`/reports/student-ledger/${student.id}`).then((r) => r.data),
    enabled: !!student,
  })
  const handleSearch = async (val: string) => {
    setSearch(val)
    if (val.length < 2) { setSuggestions([]); return }
    const res = await client.get('/students/', { params: { search: val, limit: 6 } })
    setSuggestions(res.data?.items || res.data || [])
  }
  const rows = data?.fee_heads || []
  const receipts = data?.receipts || []
  return (
    <div>
      <div className="flex flex-wrap items-end gap-4 mb-4">
        <div className="relative flex-1 min-w-[220px]">
          <label className="label">Search Student</label>
          <input className="input" placeholder="Name, roll, admission no..." value={search} onChange={(e) => handleSearch(e.target.value)} />
          {suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg z-20 mt-1">
              {suggestions.map((s: any) => (
                <button key={s.id} type="button" onClick={() => { setStudent(s); setSearch(s.full_name); setSuggestions([]) }} className="w-full text-left px-3 py-2 hover:bg-indigo-50 text-sm border-b border-gray-100 last:border-0">
                  <span className="font-medium">{s.full_name}</span> <span className="text-gray-400 text-xs">{s.admission_number}</span>
                </button>
              ))}
            </div>
          )}
        </div>
        {student && <ExportButtons report="student_ledger" params={{ student_id: student.id.toString() }} />}
      </div>
      {isLoading ? <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div> : data && (
        <>
          <div className="font-semibold text-gray-700 mb-2">{data.student?.full_name}</div>
          <table className="tbl mb-6">
            <thead><tr><th>Fee Head</th><th className="text-right">Total Due</th><th className="text-right">Paid</th><th className="text-right">Balance</th></tr></thead>
            <tbody>{rows.map((r: any) => <tr key={r.fee_head_id}><td>{r.fee_head_name}</td><td className="text-right">{fmt(r.total_due)}</td><td className="text-right text-emerald-700">{fmt(r.paid)}</td><td className={`text-right font-medium ${r.balance > 0 ? 'text-red-600' : ''}`}>{fmt(r.balance)}</td></tr>)}</tbody>
          </table>
          <h3 className="font-semibold text-gray-700 mb-2">Receipt History</h3>
          <table className="tbl">
            <thead><tr><th>Receipt No</th><th>Date</th><th>Mode</th><th className="text-right">Amount</th><th>Status</th></tr></thead>
            <tbody>
              {receipts.length === 0 && <tr><td colSpan={5} className="text-center text-gray-400 py-4">No receipts</td></tr>}
              {receipts.map((r: any) => <tr key={r.id}><td className="font-medium text-indigo-700">{r.receipt_number}</td><td>{r.receipt_date ? format(parseISO(r.receipt_date), 'dd/MM/yyyy') : '-'}</td><td>{r.payment_mode}</td><td className="text-right">{fmt(r.total_amount)}</td><td><span className={r.status === 'ACTIVE' ? 'badge-success' : 'badge-danger'}>{r.status}</span></td></tr>)}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}

// ─── Dues Report ──────────────────────────────────────────────────────────────
function DuesReport() {
  const { data: courses } = useQuery({ queryKey: ['courses-list'], queryFn: () => client.get('/courses/').then((r) => r.data) })
  const courseList = courses?.items || courses || []
  const { data: fys } = useQuery({ queryKey: ['financial-years'], queryFn: () => client.get('/financial-years/').then((r) => r.data) })
  const fyList = fys?.items || fys || []
  const [courseId, setCourseId] = useState('')
  const [fyId, setFyId] = useState('')
  const { data, isLoading } = useQuery({
    queryKey: ['report-dues', courseId, fyId],
    queryFn: () => client.get('/reports/dues', { params: { course_id: courseId || undefined, financial_year_id: fyId || undefined } }).then((r) => r.data),
  })
  const rows = data?.rows || []
  return (
    <div>
      <div className="flex flex-wrap items-end gap-3 mb-4">
        <div>
          <label className="label">Course</label>
          <select className="input w-44" value={courseId} onChange={(e) => setCourseId(e.target.value)}>
            <option value="">All Courses</option>
            {courseList.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Financial Year</label>
          <select className="input w-44" value={fyId} onChange={(e) => setFyId(e.target.value)}>
            <option value="">All FYs</option>
            {fyList.map((fy: any) => <option key={fy.id} value={fy.id}>{fy.name}</option>)}
          </select>
        </div>
        <ExportButtons report="dues" params={{ course_id: courseId, financial_year_id: fyId }} />
      </div>
      {isLoading ? <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div> : (
        <table className="tbl">
          <thead><tr><th>Student</th><th>Admission No</th><th>Course</th><th className="text-right">Total Due</th><th className="text-right">Paid</th><th className="text-right">Balance</th></tr></thead>
          <tbody>
            {rows.length === 0 && <tr><td colSpan={6} className="text-center text-gray-400 py-6">No dues found</td></tr>}
            {rows.sort((a: any, b: any) => (b.balance || 0) - (a.balance || 0)).map((r: any) => (
              <tr key={r.student_id}><td className="font-medium">{r.student_name}</td><td>{r.admission_number || '-'}</td><td>{r.course_name || '-'}</td><td className="text-right">{fmt(r.total_due)}</td><td className="text-right text-emerald-700">{fmt(r.paid)}</td><td className="text-right font-bold text-red-600">{fmt(r.balance)}</td></tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

// ─── Payment Mode Wise ────────────────────────────────────────────────────────
function PaymentModeReport() {
  const { data: fys } = useQuery({ queryKey: ['financial-years'], queryFn: () => client.get('/financial-years/').then((r) => r.data) })
  const fyList = fys?.items || fys || []
  const [fyId, setFyId] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const { data, isLoading } = useQuery({
    queryKey: ['report-modes', fyId, dateFrom, dateTo],
    queryFn: () => client.get('/reports/payment-mode-wise', { params: { financial_year_id: fyId || undefined, date_from: dateFrom || undefined, date_to: dateTo || undefined } }).then((r) => r.data),
  })
  const rows = data?.rows || []
  const pieData = rows.map((r: any) => ({ name: r.payment_mode?.replace('_', ' '), value: r.total_amount }))
  return (
    <div>
      <div className="flex flex-wrap items-end gap-3 mb-4">
        <div>
          <label className="label">FY</label>
          <select className="input w-44" value={fyId} onChange={(e) => setFyId(e.target.value)}>
            <option value="">All</option>
            {fyList.map((fy: any) => <option key={fy.id} value={fy.id}>{fy.name}</option>)}
          </select>
        </div>
        <div><label className="label">From</label><input type="date" className="input" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} /></div>
        <div><label className="label">To</label><input type="date" className="input" value={dateTo} onChange={(e) => setDateTo(e.target.value)} /></div>
        <ExportButtons report="payment_mode_wise" params={{ financial_year_id: fyId, date_from: dateFrom, date_to: dateTo }} />
      </div>
      {isLoading ? <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div> : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" outerRadius={90} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                {pieData.map((_: any, i: number) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={(v: number) => fmt(v)} />
            </PieChart>
          </ResponsiveContainer>
          <table className="tbl self-start">
            <thead><tr><th>Payment Mode</th><th className="text-right">Receipts</th><th className="text-right">Amount</th></tr></thead>
            <tbody>
              {rows.map((r: any) => <tr key={r.payment_mode}><td className="font-medium">{r.payment_mode?.replace('_', ' ')}</td><td className="text-right">{r.receipt_count}</td><td className="text-right font-medium">{fmt(r.total_amount)}</td></tr>)}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ─── Cheque Status ─────────────────────────────────────────────────────────────
function ChequeStatusReport() {
  const [status, setStatus] = useState('')
  const { data, isLoading } = useQuery({
    queryKey: ['report-cheques', status],
    queryFn: () => client.get('/reports/cheque-status', { params: { cheque_status: status || undefined } }).then((r) => r.data),
  })
  const rows = data?.rows || []
  return (
    <div>
      <div className="flex flex-wrap items-end gap-3 mb-4">
        <div>
          <label className="label">Cheque Status</label>
          <select className="input w-44" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All</option>
            <option value="PENDING">Pending</option>
            <option value="CLEARED">Cleared</option>
            <option value="BOUNCED">Bounced</option>
            <option value="RETURNED">Returned</option>
          </select>
        </div>
        <ExportButtons report="cheque_status" params={{ cheque_status: status }} />
      </div>
      {isLoading ? <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div> : (
        <table className="tbl">
          <thead><tr><th>Receipt No</th><th>Student</th><th>Cheque No</th><th>Cheque Date</th><th>Bank</th><th className="text-right">Amount</th><th>Status</th></tr></thead>
          <tbody>
            {rows.length === 0 && <tr><td colSpan={7} className="text-center text-gray-400 py-6">No cheque records found</td></tr>}
            {rows.map((r: any) => (
              <tr key={r.id}>
                <td className="font-medium text-indigo-700">{r.receipt_number}</td>
                <td>{r.student_name}</td>
                <td className="font-mono">{r.cheque_number}</td>
                <td>{r.cheque_date || '-'}</td>
                <td>{r.bank_name || '-'}</td>
                <td className="text-right">{fmt(r.total_amount)}</td>
                <td><span className={r.cheque_status === 'CLEARED' ? 'badge-success' : r.cheque_status === 'BOUNCED' ? 'badge-danger' : 'badge-warning'}>{r.cheque_status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

// ─── Generic date-range report ─────────────────────────────────────────────────
function DateRangeReport({ reportKey, apiPath }: { reportKey: string; apiPath: string }) {
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const { data, isLoading } = useQuery({
    queryKey: [reportKey, dateFrom, dateTo],
    queryFn: () => client.get(apiPath, { params: { date_from: dateFrom || undefined, date_to: dateTo || undefined } }).then((r) => r.data),
  })
  const rows = data?.rows || data?.items || data || []
  return (
    <div>
      <div className="flex flex-wrap items-end gap-3 mb-4">
        <div><label className="label">From Date</label><input type="date" className="input" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} /></div>
        <div><label className="label">To Date</label><input type="date" className="input" value={dateTo} onChange={(e) => setDateTo(e.target.value)} /></div>
        <ExportButtons report={reportKey.replace('report-', '')} params={{ date_from: dateFrom, date_to: dateTo }} />
      </div>
      {isLoading ? <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div> : (
        <table className="tbl">
          <thead><tr><th>Receipt No</th><th>Date</th><th>Student</th><th>Reason</th><th className="text-right">Amount</th></tr></thead>
          <tbody>
            {(Array.isArray(rows) ? rows : []).length === 0 && <tr><td colSpan={5} className="text-center text-gray-400 py-6">No records found</td></tr>}
            {(Array.isArray(rows) ? rows : []).map((r: any) => (
              <tr key={r.id}><td className="font-medium">{r.receipt_number}</td><td>{r.receipt_date ? format(parseISO(r.receipt_date), 'dd/MM/yyyy') : '-'}</td><td>{r.student_name}</td><td>{r.reason || r.correction_reason || '-'}</td><td className="text-right">{fmt(r.total_amount)}</td></tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

// ─── Fee Head Wise ─────────────────────────────────────────────────────────────
function FeeHeadWiseReport() {
  const { data: fys } = useQuery({ queryKey: ['financial-years'], queryFn: () => client.get('/financial-years/').then((r) => r.data) })
  const fyList = fys?.items || fys || []
  const [fyId, setFyId] = useState('')
  const { data, isLoading } = useQuery({
    queryKey: ['report-fee-head', fyId],
    queryFn: () => client.get('/reports/fee-head-wise', { params: { financial_year_id: fyId || undefined } }).then((r) => r.data),
  })
  const rows = data?.rows || []
  return (
    <div>
      <div className="flex flex-wrap items-end gap-3 mb-4">
        <div>
          <label className="label">Financial Year</label>
          <select className="input w-44" value={fyId} onChange={(e) => setFyId(e.target.value)}>
            <option value="">All</option>
            {fyList.map((fy: any) => <option key={fy.id} value={fy.id}>{fy.name}</option>)}
          </select>
        </div>
        <ExportButtons report="fee_head_wise" params={{ financial_year_id: fyId }} />
      </div>
      {isLoading ? <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div> : (
        <table className="tbl">
          <thead><tr><th>Fee Head</th><th className="text-right">Total Due</th><th className="text-right">Collected</th><th className="text-right">Balance</th><th className="text-right">Students</th></tr></thead>
          <tbody>
            {rows.length === 0 && <tr><td colSpan={5} className="text-center text-gray-400 py-6">No data</td></tr>}
            {rows.map((r: any) => <tr key={r.fee_head_id}><td className="font-medium">{r.fee_head_name}</td><td className="text-right">{fmt(r.total_due)}</td><td className="text-right text-emerald-700">{fmt(r.collected)}</td><td className={`text-right font-medium ${r.balance > 0 ? 'text-red-600' : ''}`}>{fmt(r.balance)}</td><td className="text-right">{r.student_count || 0}</td></tr>)}
          </tbody>
        </table>
      )}
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function Reports() {
  const { hasPermission } = useAuthStore()
  const [tab, setTab] = useState('daily')
  if (!hasPermission('VIEW_REPORTS')) {
    return <div className="card text-center py-12 text-gray-500">You don't have permission to view reports.</div>
  }
  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Reports</h1>
      </div>
      <div className="flex flex-wrap gap-1 border-b border-gray-200 mb-6">
        {REPORT_TABS.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${tab === t.id ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
            {t.icon}{t.label}
          </button>
        ))}
      </div>
      <div className="card">
        {tab === 'daily' && <DailyCollection />}
        {tab === 'monthly' && <MonthlyCollection />}
        {tab === 'fy_summary' && <FYSummary />}
        {tab === 'student_ledger' && <StudentLedger />}
        {tab === 'fee_head_wise' && <FeeHeadWiseReport />}
        {tab === 'payment_mode' && <PaymentModeReport />}
        {tab === 'dues' && <DuesReport />}
        {tab === 'cheque_status' && <ChequeStatusReport />}
        {tab === 'cancelled' && <DateRangeReport reportKey="report-cancelled" apiPath="/reports/cancelled-receipts" />}
        {tab === 'corrected' && <DateRangeReport reportKey="report-corrected" apiPath="/reports/corrected-receipts" />}
      </div>
    </div>
  )
}
