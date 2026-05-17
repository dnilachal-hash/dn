import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { TrendingUp, Users, Receipt, AlertCircle, IndianRupee, Clock } from 'lucide-react'
import client from '../api/client'
import { format, parseISO } from 'date-fns'

const fmt = (n: number) => '₹' + (n || 0).toLocaleString('en-IN')

const PIE_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

function StatCard({
  label, value, sub, icon, color,
}: {
  label: string; value: string; sub?: string; icon: React.ReactNode; color: string
}) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`stat-icon ${color}`}>{icon}</div>
      <div>
        <div className="text-2xl font-bold text-gray-900">{value}</div>
        <div className="text-sm text-gray-600">{label}</div>
        {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => client.get('/reports/dashboard').then((r) => r.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="card text-center py-12">
        <AlertCircle className="mx-auto text-red-400 mb-3" size={40} />
        <p className="text-gray-600">Failed to load dashboard data. Please try again.</p>
      </div>
    )
  }

  const d = data || {}
  const stats = d.stats || {}
  const monthlyData = d.monthly_collection || []
  const paymentModes = d.payment_mode_breakdown || []
  const recentReceipts = d.recent_receipts || []
  const pendingCheques = d.pending_cheques || []

  const barData = monthlyData.map((m: any) => ({
    month: m.month_label || m.month,
    amount: m.total || m.amount || 0,
  }))

  const pieData = paymentModes.map((p: any) => ({
    name: p.payment_mode || p.mode,
    value: p.total || p.amount || 0,
  }))

  return (
    <div className="space-y-6">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <div className="text-sm text-gray-500">{format(new Date(), 'EEEE, dd MMMM yyyy')}</div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          label="Today's Collection"
          value={fmt(stats.today_collection || 0)}
          sub={`${stats.today_receipt_count || 0} receipts`}
          icon={<IndianRupee size={22} className="text-indigo-600" />}
          color="bg-indigo-50"
        />
        <StatCard
          label="This Month"
          value={fmt(stats.month_collection || 0)}
          sub={format(new Date(), 'MMMM yyyy')}
          icon={<TrendingUp size={22} className="text-emerald-600" />}
          color="bg-emerald-50"
        />
        <StatCard
          label="FY Collection"
          value={fmt(stats.fy_collection || 0)}
          sub={stats.financial_year || 'Current FY'}
          icon={<Receipt size={22} className="text-blue-600" />}
          color="bg-blue-50"
        />
        <StatCard
          label="Pending Dues"
          value={(stats.pending_dues_count || 0).toLocaleString('en-IN')}
          sub={`${fmt(stats.pending_dues_amount || 0)} outstanding`}
          icon={<AlertCircle size={22} className="text-amber-600" />}
          color="bg-amber-50"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Monthly Bar Chart */}
        <div className="card xl:col-span-2">
          <div className="card-header">
            <h2 className="card-title">Monthly Collection (Last 6 Months)</h2>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={barData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}K`}
              />
              <Tooltip
                formatter={(v: number) => [fmt(v), 'Collection']}
                contentStyle={{ borderRadius: 8, fontSize: 13 }}
              />
              <Bar dataKey="amount" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Payment Mode Pie */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Payment Modes</h2>
          </div>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  dataKey="value"
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                  labelLine={false}
                >
                  {pieData.map((_: any, i: number) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: number) => fmt(v)} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
              No data available
            </div>
          )}
        </div>
      </div>

      {/* Tables Row */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Recent Receipts */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Recent Receipts</h2>
            <Link to="/receipts" className="text-indigo-600 text-sm hover:underline">
              View All
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="tbl">
              <thead>
                <tr>
                  <th>Receipt No</th>
                  <th>Student</th>
                  <th>Amount</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {recentReceipts.length === 0 && (
                  <tr>
                    <td colSpan={4} className="text-center text-gray-400 py-6">
                      No recent receipts
                    </td>
                  </tr>
                )}
                {recentReceipts.map((r: any) => (
                  <tr key={r.id}>
                    <td>
                      <Link
                        to={`/receipts/${r.id}`}
                        className="text-indigo-600 hover:underline font-medium"
                      >
                        {r.receipt_number}
                      </Link>
                    </td>
                    <td className="max-w-[160px] truncate">{r.student_name}</td>
                    <td className="font-medium">{fmt(r.total_amount)}</td>
                    <td className="text-gray-500">
                      {r.receipt_date
                        ? format(parseISO(r.receipt_date), 'dd/MM/yyyy')
                        : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pending Cheques */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title flex items-center gap-2">
              <Clock size={18} className="text-amber-500" />
              Pending Cheques
            </h2>
            <Link to="/reports?tab=cheque" className="text-indigo-600 text-sm hover:underline">
              View All
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="tbl">
              <thead>
                <tr>
                  <th>Receipt No</th>
                  <th>Student</th>
                  <th>Cheque No</th>
                  <th>Amount</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {pendingCheques.length === 0 && (
                  <tr>
                    <td colSpan={5} className="text-center text-gray-400 py-6">
                      No pending cheques
                    </td>
                  </tr>
                )}
                {pendingCheques.map((c: any) => (
                  <tr key={c.id}>
                    <td>
                      <Link
                        to={`/receipts/${c.id}`}
                        className="text-indigo-600 hover:underline font-medium"
                      >
                        {c.receipt_number}
                      </Link>
                    </td>
                    <td className="max-w-[130px] truncate">{c.student_name}</td>
                    <td>{c.cheque_number || '-'}</td>
                    <td className="font-medium">{fmt(c.total_amount)}</td>
                    <td>
                      <span className="badge-warning">{c.cheque_status || 'PENDING'}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
