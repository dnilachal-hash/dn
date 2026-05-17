import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { Search, Filter, ChevronLeft, ChevronRight, Eye, Printer, XCircle, Edit2 } from 'lucide-react'
import toast from 'react-hot-toast'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'
import { format, parseISO } from 'date-fns'

const fmt = (n: number) => '₹' + (n || 0).toLocaleString('en-IN')

const STATUS_BADGE: Record<string, string> = {
  ACTIVE: 'badge-success',
  CANCELLED: 'badge-danger',
  CORRECTED: 'badge-warning',
  IMPORTED: 'badge-info',
}

const PAYMENT_MODES = ['CASH', 'CHEQUE', 'DEMAND_DRAFT', 'NEFT', 'UPI', 'CARD', 'ONLINE']

export default function Receipts() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { hasPermission, user } = useAuthStore()

  const [search, setSearch] = useState('')
  const [fyId, setFyId] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [status, setStatus] = useState('')
  const [mode, setMode] = useState('')
  const [page, setPage] = useState(1)
  const limit = 25

  const { data: fys } = useQuery({
    queryKey: ['financial-years'],
    queryFn: () => client.get('/financial-years/').then((r) => r.data),
  })
  const fyList = fys?.items || fys || []

  const { data, isLoading } = useQuery({
    queryKey: ['receipts', search, fyId, dateFrom, dateTo, status, mode, page],
    queryFn: () =>
      client.get('/receipts/', {
        params: {
          search: search || undefined,
          financial_year_id: fyId || undefined,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
          status: status || undefined,
          payment_mode: mode || undefined,
          skip: (page - 1) * limit,
          limit,
        },
      }).then((r) => r.data),
    placeholderData: (prev) => prev,
  })

  const cancelMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) =>
      client.post(`/receipts/${id}/cancel`, { reason }).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['receipts'] })
      toast.success('Receipt cancelled')
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed to cancel'),
  })

  const handleCancel = (receipt: any) => {
    const reason = window.prompt(`Cancel receipt ${receipt.receipt_number}?\nEnter reason:`)
    if (reason !== null && reason.trim()) {
      cancelMutation.mutate({ id: receipt.id, reason: reason.trim() })
    }
  }

  const handlePrint = async (id: number) => {
    try {
      const res = await client.get(`/receipts/${id}/pdf`, { responseType: 'blob' })
      const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      window.open(url, '_blank')
    } catch {
      toast.error('Failed to generate PDF')
    }
  }

  const receipts = data?.items || data || []
  const total = data?.total || receipts.length
  const totalPages = Math.ceil(total / limit)

  const resetFilters = () => {
    setSearch(''); setFyId(''); setDateFrom(''); setDateTo(''); setStatus(''); setMode(''); setPage(1)
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Receipts</h1>
        {hasPermission('COLLECT_FEES') && (
          <Link to="/fee-collection" className="btn-primary">
            New Collection
          </Link>
        )}
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="label">Search</label>
            <div className="relative">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                className="input pl-9"
                placeholder="Receipt no, student name..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1) }}
              />
            </div>
          </div>

          <div className="min-w-[140px]">
            <label className="label">Financial Year</label>
            <select className="input" value={fyId} onChange={(e) => { setFyId(e.target.value); setPage(1) }}>
              <option value="">All FYs</option>
              {fyList.map((fy: any) => <option key={fy.id} value={fy.id}>{fy.name}</option>)}
            </select>
          </div>

          <div>
            <label className="label">From Date</label>
            <input type="date" className="input" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(1) }} />
          </div>
          <div>
            <label className="label">To Date</label>
            <input type="date" className="input" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setPage(1) }} />
          </div>

          <div className="min-w-[130px]">
            <label className="label">Status</label>
            <select className="input" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }}>
              <option value="">All Status</option>
              <option value="ACTIVE">Active</option>
              <option value="CANCELLED">Cancelled</option>
              <option value="CORRECTED">Corrected</option>
              <option value="IMPORTED">Imported</option>
            </select>
          </div>

          <div className="min-w-[130px]">
            <label className="label">Payment Mode</label>
            <select className="input" value={mode} onChange={(e) => { setMode(e.target.value); setPage(1) }}>
              <option value="">All Modes</option>
              {PAYMENT_MODES.map((m) => <option key={m} value={m}>{m.replace('_', ' ')}</option>)}
            </select>
          </div>

          <button onClick={resetFilters} className="btn-secondary">
            <Filter size={14} /> Reset
          </button>
        </div>
      </div>

      {/* Summary line */}
      {data?.summary && (
        <div className="card mb-4 py-3 flex flex-wrap gap-6">
          <div className="text-sm">
            <span className="text-gray-500">Total: </span>
            <span className="font-bold text-gray-900">{fmt(data.summary.total_amount)}</span>
          </div>
          {Object.entries(data.summary.by_mode || {}).map(([m, amt]) => (
            <div key={m} className="text-sm">
              <span className="text-gray-500">{m}: </span>
              <span className="font-medium">{fmt(amt as number)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="flex justify-center py-16">
              <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full" />
            </div>
          ) : (
            <table className="tbl">
              <thead>
                <tr>
                  <th>Receipt No</th>
                  <th>Date</th>
                  <th>Student</th>
                  <th>Course</th>
                  <th>Amount</th>
                  <th>Mode</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {receipts.length === 0 && (
                  <tr>
                    <td colSpan={8} className="text-center text-gray-400 py-12">
                      No receipts found.
                    </td>
                  </tr>
                )}
                {receipts.map((r: any) => (
                  <tr
                    key={r.id}
                    className="cursor-pointer"
                    onClick={() => navigate(`/receipts/${r.id}`)}
                  >
                    <td className="font-medium text-indigo-700">{r.receipt_number}</td>
                    <td className="whitespace-nowrap">
                      {r.receipt_date ? format(parseISO(r.receipt_date), 'dd/MM/yyyy') : '-'}
                    </td>
                    <td>
                      <div className="font-medium text-gray-900">{r.student_name}</div>
                      {r.admission_number && (
                        <div className="text-xs text-gray-400">{r.admission_number}</div>
                      )}
                    </td>
                    <td className="text-sm text-gray-600">{r.course_name || '-'}</td>
                    <td className="font-semibold">{fmt(r.total_amount)}</td>
                    <td>
                      <span className="badge-gray capitalize text-xs">{r.payment_mode?.replace('_', ' ') || '-'}</span>
                    </td>
                    <td>
                      <span className={STATUS_BADGE[r.status] || 'badge-gray'}>
                        {r.status}
                      </span>
                    </td>
                    <td onClick={(e) => e.stopPropagation()}>
                      <div className="flex gap-1.5">
                        <Link to={`/receipts/${r.id}`} className="btn-secondary btn-sm" title="View">
                          <Eye size={13} />
                        </Link>
                        <button
                          onClick={() => handlePrint(r.id)}
                          className="btn-secondary btn-sm"
                          title="Print PDF"
                        >
                          <Printer size={13} />
                        </button>
                        {r.status === 'ACTIVE' && hasPermission('CANCEL_RECEIPTS') && (
                          <button
                            onClick={() => handleCancel(r)}
                            className="btn-danger btn-sm"
                            title="Cancel"
                          >
                            <XCircle size={13} />
                          </button>
                        )}
                        {r.status === 'ACTIVE' && user?.role === 'super_admin' && (
                          <Link to={`/receipts/${r.id}?edit=1`} className="btn-secondary btn-sm" title="Correct">
                            <Edit2 size={13} />
                          </Link>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
            <div className="text-sm text-gray-500">
              Showing {(page - 1) * limit + 1}–{Math.min(page * limit, total)} of {total.toLocaleString('en-IN')} receipts
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary btn-sm">
                <ChevronLeft size={14} />
              </button>
              <span className="text-sm text-gray-700">Page {page} of {totalPages}</span>
              <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="btn-secondary btn-sm">
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
