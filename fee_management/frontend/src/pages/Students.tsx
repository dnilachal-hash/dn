import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Search, Filter, ChevronLeft, ChevronRight, Eye, Edit2 } from 'lucide-react'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'

const STATUS_BADGE: Record<string, string> = {
  ACTIVE: 'badge-success',
  INACTIVE: 'badge-danger',
  ALUMNI: 'badge-info',
  SUSPENDED: 'badge-warning',
  DROPOUT: 'badge-gray',
}

export default function Students() {
  const navigate = useNavigate()
  const { hasPermission } = useAuthStore()
  const canManage = hasPermission('MANAGE_STUDENTS')

  const [search, setSearch] = useState('')
  const [courseId, setCourseId] = useState('')
  const [batchId, setBatchId] = useState('')
  const [sessionId, setSessionId] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const limit = 20

  const { data: courses } = useQuery({
    queryKey: ['courses-list'],
    queryFn: () => client.get('/courses/').then((r) => r.data),
  })
  const { data: batches } = useQuery({
    queryKey: ['batches-list', courseId],
    queryFn: () =>
      client.get('/courses/batches/', { params: courseId ? { course_id: courseId } : {} }).then((r) => r.data),
  })
  const { data: sessions } = useQuery({
    queryKey: ['sessions-list'],
    queryFn: () => client.get('/courses/sessions/').then((r) => r.data),
  })

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['students', search, courseId, batchId, sessionId, status, page],
    queryFn: () =>
      client
        .get('/students/', {
          params: {
            search: search || undefined,
            course_id: courseId || undefined,
            batch_id: batchId || undefined,
            session_id: sessionId || undefined,
            status: status || undefined,
            skip: (page - 1) * limit,
            limit,
          },
        })
        .then((r) => r.data),
    placeholderData: (prev) => prev,
  })

  const students = data?.items || data || []
  const total = data?.total || students.length
  const totalPages = Math.ceil(total / limit)

  const resetFilters = () => {
    setSearch('')
    setCourseId('')
    setBatchId('')
    setSessionId('')
    setStatus('')
    setPage(1)
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Students</h1>
        {canManage && (
          <Link to="/students/new" className="btn-primary">
            <Plus size={16} />
            Add Student
          </Link>
        )}
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[220px]">
            <label className="label">Search</label>
            <div className="relative">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                className="input pl-9"
                placeholder="Name, roll, admission no, mobile..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1) }}
              />
            </div>
          </div>

          <div className="min-w-[150px]">
            <label className="label">Course</label>
            <select
              className="input"
              value={courseId}
              onChange={(e) => { setCourseId(e.target.value); setBatchId(''); setPage(1) }}
            >
              <option value="">All Courses</option>
              {(courses?.items || courses || []).map((c: any) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div className="min-w-[150px]">
            <label className="label">Batch</label>
            <select
              className="input"
              value={batchId}
              onChange={(e) => { setBatchId(e.target.value); setPage(1) }}
            >
              <option value="">All Batches</option>
              {(batches?.items || batches || []).map((b: any) => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </div>

          <div className="min-w-[150px]">
            <label className="label">Session</label>
            <select
              className="input"
              value={sessionId}
              onChange={(e) => { setSessionId(e.target.value); setPage(1) }}
            >
              <option value="">All Sessions</option>
              {(sessions?.items || sessions || []).map((s: any) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>

          <div className="min-w-[130px]">
            <label className="label">Status</label>
            <select
              className="input"
              value={status}
              onChange={(e) => { setStatus(e.target.value); setPage(1) }}
            >
              <option value="">All Status</option>
              <option value="ACTIVE">Active</option>
              <option value="INACTIVE">Inactive</option>
              <option value="ALUMNI">Alumni</option>
              <option value="SUSPENDED">Suspended</option>
              <option value="DROPOUT">Dropout</option>
            </select>
          </div>

          <button onClick={resetFilters} className="btn-secondary">
            <Filter size={14} />
            Reset
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
                  <th>Admission No</th>
                  <th>Name</th>
                  <th>Course</th>
                  <th>Batch</th>
                  <th>Session</th>
                  <th>Year</th>
                  <th>Mobile</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {students.length === 0 && (
                  <tr>
                    <td colSpan={9} className="text-center text-gray-400 py-12">
                      No students found. Try adjusting your filters.
                    </td>
                  </tr>
                )}
                {students.map((s: any) => (
                  <tr
                    key={s.id}
                    className="cursor-pointer"
                    onClick={() => navigate(`/students/${s.id}`)}
                  >
                    <td className="font-medium text-indigo-700">{s.admission_number || '-'}</td>
                    <td>
                      <div className="font-medium text-gray-900">{s.full_name}</div>
                      {s.roll_number && (
                        <div className="text-xs text-gray-400">Roll: {s.roll_number}</div>
                      )}
                    </td>
                    <td>{s.course_name || s.course?.name || '-'}</td>
                    <td>{s.batch_name || s.batch?.name || '-'}</td>
                    <td>{s.session_name || s.session?.name || '-'}</td>
                    <td>{s.professional_year ? `Year ${s.professional_year}` : '-'}</td>
                    <td>{s.mobile || '-'}</td>
                    <td>
                      <span className={STATUS_BADGE[s.student_status] || 'badge-gray'}>
                        {s.student_status || 'ACTIVE'}
                      </span>
                    </td>
                    <td onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center gap-2">
                        <Link
                          to={`/students/${s.id}`}
                          className="btn-secondary btn-sm"
                          title="View"
                        >
                          <Eye size={13} />
                        </Link>
                        {canManage && (
                          <Link
                            to={`/students/${s.id}/edit`}
                            className="btn-secondary btn-sm"
                            title="Edit"
                          >
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
              Showing {(page - 1) * limit + 1}–{Math.min(page * limit, total)} of {total.toLocaleString('en-IN')} students
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-secondary btn-sm"
              >
                <ChevronLeft size={14} />
              </button>
              <span className="text-sm text-gray-700">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="btn-secondary btn-sm"
              >
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
