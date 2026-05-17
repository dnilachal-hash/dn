import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, Filter, Download, ChevronDown, ChevronUp } from 'lucide-react'
import client from '../api/client'
import toast from 'react-hot-toast'
import { format, parseISO } from 'date-fns'
import { useAuthStore } from '../store/authStore'

const ACTION_BADGE: Record<string, string> = {
  CREATE: 'badge-success',
  UPDATE: 'badge-info',
  DELETE: 'badge-danger',
  LOGIN: 'badge-indigo',
  LOGOUT: 'badge-gray',
  CANCEL: 'badge-warning',
  CORRECT: 'badge-warning',
  LOCK: 'badge-warning',
  UNLOCK: 'badge-info',
  EXPORT: 'badge-gray',
}

function JsonExpand({ data }: { data: any }) {
  const [open, setOpen] = useState(false)
  if (!data) return <span className="text-gray-400 text-xs">-</span>
  const str = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
  const preview = str.length > 60 ? str.slice(0, 60) + '…' : str
  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 text-xs text-indigo-600 hover:underline"
      >
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        {open ? 'Hide' : 'Show'}
      </button>
      {open && (
        <pre className="mt-1 text-xs bg-gray-50 border border-gray-200 rounded p-2 max-h-40 overflow-auto whitespace-pre-wrap">
          {str}
        </pre>
      )}
      {!open && (
        <span className="text-xs text-gray-500 font-mono">{preview}</span>
      )}
    </div>
  )
}

export default function AuditLogs() {
  const { hasPermission } = useAuthStore()
  const [userFilter, setUserFilter] = useState('')
  const [action, setAction] = useState('')
  const [entity, setEntity] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [page, setPage] = useState(1)
  const limit = 30

  if (!hasPermission('VIEW_AUDIT_LOGS')) {
    return (
      <div className="card text-center py-12 text-gray-500">
        You don't have permission to view audit logs.
      </div>
    )
  }

  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', userFilter, action, entity, dateFrom, dateTo, page],
    queryFn: () =>
      client.get('/audit-logs/', {
        params: {
          user: userFilter || undefined,
          action: action || undefined,
          entity: entity || undefined,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
          skip: (page - 1) * limit,
          limit,
        },
      }).then((r) => r.data),
    placeholderData: (prev) => prev,
  })

  const handleExport = async () => {
    try {
      const res = await client.get('/reports/export/excel', {
        params: { report: 'audit_logs', user: userFilter || undefined, action: action || undefined, entity: entity || undefined, date_from: dateFrom || undefined, date_to: dateTo || undefined },
        responseType: 'blob',
      })
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = 'audit_logs.xlsx'
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast.error('Export failed')
    }
  }

  const logs = data?.items || data || []
  const total = data?.total || logs.length
  const totalPages = Math.ceil(total / limit)

  const resetFilters = () => {
    setUserFilter(''); setAction(''); setEntity(''); setDateFrom(''); setDateTo(''); setPage(1)
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Audit Logs</h1>
        <button onClick={handleExport} className="btn-secondary">
          <Download size={15} /> Export
        </button>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex flex-wrap gap-3 items-end">
          <div className="min-w-[160px]">
            <label className="label">Username</label>
            <input
              className="input"
              placeholder="Filter by user..."
              value={userFilter}
              onChange={(e) => { setUserFilter(e.target.value); setPage(1) }}
            />
          </div>
          <div className="min-w-[130px]">
            <label className="label">Action</label>
            <select className="input" value={action} onChange={(e) => { setAction(e.target.value); setPage(1) }}>
              <option value="">All Actions</option>
              {['CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'CANCEL', 'CORRECT', 'LOCK', 'UNLOCK', 'EXPORT'].map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>
          <div className="min-w-[130px]">
            <label className="label">Entity</label>
            <select className="input" value={entity} onChange={(e) => { setEntity(e.target.value); setPage(1) }}>
              <option value="">All Entities</option>
              {['student', 'receipt', 'fee_structure', 'fee_head', 'financial_year', 'user', 'setting', 'backup'].map((e) => (
                <option key={e} value={e}>{e.replace('_', ' ')}</option>
              ))}
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
          <button onClick={resetFilters} className="btn-secondary">
            <Filter size={14} /> Reset
          </button>
        </div>
      </div>

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
                  <th>Date/Time</th>
                  <th>User</th>
                  <th>Role</th>
                  <th>Action</th>
                  <th>Entity</th>
                  <th>Old Value</th>
                  <th>New Value</th>
                  <th>Reason</th>
                  <th>IP</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 && (
                  <tr>
                    <td colSpan={9} className="text-center text-gray-400 py-12">
                      No audit logs found.
                    </td>
                  </tr>
                )}
                {logs.map((log: any) => (
                  <tr key={log.id}>
                    <td className="whitespace-nowrap text-xs text-gray-600">
                      {log.timestamp || log.created_at
                        ? format(parseISO(log.timestamp || log.created_at), 'dd/MM/yyyy HH:mm:ss')
                        : '-'}
                    </td>
                    <td className="font-medium">{log.username || log.user?.username || '-'}</td>
                    <td>
                      <span className="badge-gray capitalize text-xs">
                        {log.user_role || log.role || log.user?.role || '-'}
                      </span>
                    </td>
                    <td>
                      <span className={ACTION_BADGE[log.action] || 'badge-gray'}>
                        {log.action}
                      </span>
                    </td>
                    <td className="text-sm">
                      <span className="font-medium capitalize">{log.entity_type || log.entity || '-'}</span>
                      {(log.entity_id || log.record_id) && (
                        <span className="text-gray-400 ml-1">#{log.entity_id || log.record_id}</span>
                      )}
                    </td>
                    <td className="max-w-[150px]">
                      <JsonExpand data={log.old_value || log.old_data} />
                    </td>
                    <td className="max-w-[150px]">
                      <JsonExpand data={log.new_value || log.new_data} />
                    </td>
                    <td className="text-xs text-gray-600 max-w-[150px]">
                      {log.reason || '-'}
                    </td>
                    <td className="text-xs text-gray-500 font-mono">
                      {log.ip_address || log.ip || '-'}
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
              Showing {(page - 1) * limit + 1}–{Math.min(page * limit, total)} of {total.toLocaleString('en-IN')} entries
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
