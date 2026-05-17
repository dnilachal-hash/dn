import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Edit2, DollarSign, Printer, ChevronLeft, AlertCircle } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'

const fmt = (n: number) => '₹' + (n || 0).toLocaleString('en-IN')

const STATUS_BADGE: Record<string, string> = {
  ACTIVE: 'badge-success',
  INACTIVE: 'badge-danger',
  ALUMNI: 'badge-info',
  SUSPENDED: 'badge-warning',
  DROPOUT: 'badge-gray',
}

const RECEIPT_STATUS: Record<string, string> = {
  ACTIVE: 'badge-success',
  CANCELLED: 'badge-danger',
  CORRECTED: 'badge-warning',
  IMPORTED: 'badge-info',
}

export default function StudentDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { hasPermission } = useAuthStore()

  const { data: student, isLoading, error } = useQuery({
    queryKey: ['student', id],
    queryFn: () => client.get(`/students/${id}`).then((r) => r.data),
  })

  const { data: feeSummary } = useQuery({
    queryKey: ['student-fee-summary', id],
    queryFn: () => client.get(`/students/${id}/fee-summary`).then((r) => r.data),
    enabled: !!id,
  })

  const { data: receipts } = useQuery({
    queryKey: ['student-receipts', id],
    queryFn: () =>
      client.get('/receipts/', { params: { student_id: id, limit: 50 } }).then((r) => r.data),
    enabled: !!id,
  })

  const handlePrintStatement = async () => {
    try {
      const res = await client.get(`/reports/export/pdf?report=student_ledger&student_id=${id}`, {
        responseType: 'blob',
      })
      const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      window.open(url, '_blank')
    } catch {
      toast.error('Failed to generate statement')
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full" />
      </div>
    )
  }
  if (error || !student) {
    return (
      <div className="card text-center py-12">
        <AlertCircle className="mx-auto text-red-400 mb-3" size={40} />
        <p className="text-gray-600">Student not found.</p>
        <button onClick={() => navigate('/students')} className="btn-secondary mt-4">Back to Students</button>
      </div>
    )
  }

  const feeItems = feeSummary?.items || feeSummary || []
  const totalDue = feeItems.reduce((s: number, f: any) => s + (f.total_due || 0), 0)
  const totalPaid = feeItems.reduce((s: number, f: any) => s + (f.paid || 0), 0)
  const totalBalance = totalDue - totalPaid

  const receiptList = receipts?.items || receipts || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/students')} className="btn-secondary btn-sm">
            <ChevronLeft size={14} />
            Students
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{student.full_name}</h1>
            <p className="text-sm text-gray-500">
              {student.admission_number && `Admission: ${student.admission_number}`}
              {student.roll_number && ` · Roll: ${student.roll_number}`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handlePrintStatement} className="btn-secondary">
            <Printer size={15} />
            Print Statement
          </button>
          {hasPermission('COLLECT_FEES') && (
            <Link to={`/fee-collection?student_id=${id}`} className="btn-success">
              <DollarSign size={15} />
              Collect Fee
            </Link>
          )}
          {hasPermission('MANAGE_STUDENTS') && (
            <Link to={`/students/${id}/edit`} className="btn-primary">
              <Edit2 size={15} />
              Edit
            </Link>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Student Details */}
        <div className="xl:col-span-2 card">
          <h2 className="card-title mb-4">Student Information</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3 text-sm">
            {/* Personal */}
            <div className="sm:col-span-2">
              <h3 className="font-semibold text-gray-600 text-xs uppercase tracking-wide mb-2 mt-1">Personal</h3>
            </div>
            {[
              ['Full Name', student.full_name],
              ['Father', student.father_name],
              ['Mother', student.mother_name],
              ['Guardian', student.guardian_name],
              ['Date of Birth', student.dob ? format(parseISO(student.dob), 'dd/MM/yyyy') : '-'],
              ['Gender', student.gender],
              ['Category', student.category_name || student.category?.name || '-'],
              ['Mobile', student.mobile],
              ['Email', student.email],
            ].map(([k, v]) => v ? (
              <div key={k} className="flex gap-2">
                <dt className="text-gray-500 w-32 shrink-0">{k}:</dt>
                <dd className="font-medium text-gray-800">{v}</dd>
              </div>
            ) : null)}
            {student.address && (
              <div className="sm:col-span-2 flex gap-2">
                <dt className="text-gray-500 w-32 shrink-0">Address:</dt>
                <dd className="font-medium text-gray-800">{student.address}</dd>
              </div>
            )}

            {/* Academic */}
            <div className="sm:col-span-2">
              <h3 className="font-semibold text-gray-600 text-xs uppercase tracking-wide mb-2 mt-3">Academic</h3>
            </div>
            {[
              ['Course', student.course_name || student.course?.name],
              ['Batch', student.batch_name || student.batch?.name],
              ['Session', student.session_name || student.session?.name],
              ['Year', student.professional_year ? `Year ${student.professional_year}` : null],
              ['Roll Number', student.roll_number],
              ['Admission No', student.admission_number],
              ['Registration No', student.registration_number],
              ['Enrollment No', student.enrollment_number],
              ['Admission Date', student.admission_date ? format(parseISO(student.admission_date), 'dd/MM/yyyy') : null],
            ].map(([k, v]) => v ? (
              <div key={k} className="flex gap-2">
                <dt className="text-gray-500 w-32 shrink-0">{k}:</dt>
                <dd className="font-medium text-gray-800">{v}</dd>
              </div>
            ) : null)}
            <div className="flex gap-2">
              <dt className="text-gray-500 w-32 shrink-0">Status:</dt>
              <dd>
                <span className={STATUS_BADGE[student.student_status] || 'badge-gray'}>
                  {student.student_status || 'ACTIVE'}
                </span>
              </dd>
            </div>

            {/* Other */}
            <div className="sm:col-span-2">
              <h3 className="font-semibold text-gray-600 text-xs uppercase tracking-wide mb-2 mt-3">Other</h3>
            </div>
            <div className="flex gap-2">
              <dt className="text-gray-500 w-32 shrink-0">Hostel:</dt>
              <dd className="font-medium">{student.is_hostel ? 'Yes' : 'No'}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="text-gray-500 w-32 shrink-0">Transport:</dt>
              <dd className="font-medium">{student.is_transport ? 'Yes' : 'No'}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="text-gray-500 w-32 shrink-0">Scholarship:</dt>
              <dd className="font-medium">{student.scholarship_status || 'NONE'}</dd>
            </div>
            {student.remarks && (
              <div className="sm:col-span-2 flex gap-2">
                <dt className="text-gray-500 w-32 shrink-0">Remarks:</dt>
                <dd className="font-medium text-gray-800">{student.remarks}</dd>
              </div>
            )}
          </div>
        </div>

        {/* Fee Summary */}
        <div className="card">
          <h2 className="card-title mb-4">Fee Summary</h2>
          {feeItems.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-6">No fee structure assigned</p>
          ) : (
            <>
              <table className="tbl mb-4">
                <thead>
                  <tr>
                    <th>Fee Head</th>
                    <th className="text-right">Due</th>
                    <th className="text-right">Paid</th>
                    <th className="text-right">Balance</th>
                  </tr>
                </thead>
                <tbody>
                  {feeItems.map((f: any) => (
                    <tr key={f.fee_head_id || f.id}>
                      <td className="text-sm">{f.fee_head_name || f.name}</td>
                      <td className="text-right text-sm">{fmt(f.total_due)}</td>
                      <td className="text-right text-sm text-emerald-700">{fmt(f.paid)}</td>
                      <td className={`text-right text-sm font-medium ${f.balance > 0 ? 'text-red-600' : 'text-gray-700'}`}>
                        {fmt(f.balance || f.total_due - f.paid)}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td className="font-bold">Total</td>
                    <td className="text-right font-bold">{fmt(totalDue)}</td>
                    <td className="text-right font-bold text-emerald-700">{fmt(totalPaid)}</td>
                    <td className={`text-right font-bold ${totalBalance > 0 ? 'text-red-600' : 'text-emerald-700'}`}>
                      {fmt(totalBalance)}
                    </td>
                  </tr>
                </tfoot>
              </table>
              {totalBalance > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
                  <div className="text-red-700 font-semibold text-sm">Outstanding Due</div>
                  <div className="text-red-800 text-xl font-bold">{fmt(totalBalance)}</div>
                </div>
              )}
              {totalBalance <= 0 && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-center">
                  <div className="text-emerald-700 font-semibold text-sm">All Fees Cleared</div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Receipt History */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Receipt History</h2>
          <span className="text-sm text-gray-500">{receiptList.length} receipt(s)</span>
        </div>
        <div className="overflow-x-auto">
          <table className="tbl">
            <thead>
              <tr>
                <th>Receipt No</th>
                <th>Date</th>
                <th>Payment Mode</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {receiptList.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center text-gray-400 py-8">No receipts found</td>
                </tr>
              )}
              {receiptList.map((r: any) => (
                <tr key={r.id}>
                  <td className="font-medium text-indigo-700">{r.receipt_number}</td>
                  <td>{r.receipt_date ? format(parseISO(r.receipt_date), 'dd/MM/yyyy') : '-'}</td>
                  <td>{r.payment_mode || '-'}</td>
                  <td className="font-medium">{fmt(r.total_amount)}</td>
                  <td>
                    <span className={RECEIPT_STATUS[r.status] || 'badge-gray'}>
                      {r.status || 'ACTIVE'}
                    </span>
                  </td>
                  <td>
                    <Link to={`/receipts/${r.id}`} className="btn-secondary btn-sm">
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
