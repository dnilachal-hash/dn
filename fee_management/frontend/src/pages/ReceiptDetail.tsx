import { useState } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, useFieldArray } from 'react-hook-form'
import toast from 'react-hot-toast'
import { ChevronLeft, Printer, XCircle, Edit2, X, Loader2, Check, AlertCircle } from 'lucide-react'
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

function CancelModal({ receipt, onClose }: { receipt: any; onClose: () => void }) {
  const qc = useQueryClient()
  const [reason, setReason] = useState('')
  const mutation = useMutation({
    mutationFn: () => client.post(`/receipts/${receipt.id}/cancel`, { reason }).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['receipt', receipt.id.toString()] })
      toast.success('Receipt cancelled')
      onClose()
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed'),
  })
  return (
    <div className="modal-backdrop">
      <div className="modal max-w-sm">
        <div className="modal-header">
          <h3 className="modal-title text-red-700 flex items-center gap-2">
            <AlertCircle size={18} /> Cancel Receipt
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <div className="modal-body space-y-3">
          <p className="text-sm text-gray-700">You are cancelling receipt <strong>{receipt.receipt_number}</strong>. This action cannot be undone.</p>
          <div>
            <label className="label">Reason for Cancellation *</label>
            <textarea className="input" rows={3} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Provide a reason..." />
          </div>
        </div>
        <div className="modal-footer">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={() => mutation.mutate()} disabled={!reason.trim() || mutation.isPending} className="btn-danger">
            {mutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <XCircle size={14} />}
            Cancel Receipt
          </button>
        </div>
      </div>
    </div>
  )
}

function CorrectModal({ receipt, onClose }: { receipt: any; onClose: () => void }) {
  const qc = useQueryClient()
  const { data: feeHeads } = useQuery({ queryKey: ['fee-heads'], queryFn: () => client.get('/fee-heads/').then((r) => r.data) })
  const feeHeadList = feeHeads?.items || feeHeads || []

  const { register, handleSubmit, control, formState: { errors } } = useForm({
    defaultValues: {
      receipt_number: receipt.receipt_number,
      receipt_date: receipt.receipt_date?.slice(0, 10),
      student_name: receipt.student_name,
      payment_mode: receipt.payment_mode,
      remarks: receipt.remarks || '',
      reason: '',
      items: receipt.items?.map((i: any) => ({
        fee_head_id: i.fee_head_id?.toString(),
        amount: i.amount,
      })) || [],
    },
  })

  const { fields, append, remove } = useFieldArray({ control, name: 'items' })

  const mutation = useMutation({
    mutationFn: (data: any) => client.put(`/receipts/${receipt.id}`, {
      ...data,
      items: data.items.map((i: any) => ({ fee_head_id: Number(i.fee_head_id), amount: parseFloat(i.amount) })),
    }).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['receipt', receipt.id.toString()] })
      toast.success('Receipt corrected!')
      onClose()
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed to correct'),
  })

  return (
    <div className="modal-backdrop">
      <div className="modal max-w-2xl">
        <div className="modal-header">
          <h3 className="modal-title">Correct Receipt</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
          <div className="modal-body space-y-4">
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
              This will create a corrected version. Original receipt is preserved in history.
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Receipt Number</label>
                <input {...register('receipt_number')} className="input" />
              </div>
              <div>
                <label className="label">Receipt Date</label>
                <input {...register('receipt_date')} type="date" className="input" />
              </div>
              <div>
                <label className="label">Student Name</label>
                <input {...register('student_name')} className="input" />
              </div>
              <div>
                <label className="label">Payment Mode</label>
                <select {...register('payment_mode')} className="input">
                  {['CASH', 'CHEQUE', 'DEMAND_DRAFT', 'NEFT', 'UPI', 'CARD', 'ONLINE'].map((m) => (
                    <option key={m} value={m}>{m.replace('_', ' ')}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Fee Items */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="label mb-0">Fee Items</label>
                <button type="button" onClick={() => append({ fee_head_id: '', amount: 0 })} className="btn-secondary btn-sm">
                  <Edit2 size={13} /> Add Row
                </button>
              </div>
              <table className="tbl border border-gray-200 rounded-lg overflow-hidden">
                <thead><tr><th>Fee Head</th><th>Amount</th><th></th></tr></thead>
                <tbody>
                  {fields.map((f, i) => (
                    <tr key={f.id}>
                      <td>
                        <select {...register(`items.${i}.fee_head_id`)} className="input py-1 text-sm">
                          <option value="">Select</option>
                          {feeHeadList.map((fh: any) => <option key={fh.id} value={fh.id}>{fh.name}</option>)}
                        </select>
                      </td>
                      <td>
                        <input {...register(`items.${i}.amount`)} type="number" step="0.01" className="input py-1 text-sm" />
                      </td>
                      <td>
                        <button type="button" onClick={() => remove(i)} className="text-red-400 hover:text-red-600"><X size={14} /></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div>
              <label className="label">Remarks</label>
              <textarea {...register('remarks')} className="input" rows={2} />
            </div>
            <div>
              <label className="label">Reason for Correction *</label>
              <textarea {...register('reason', { required: 'Required' })} className={`input ${errors.reason ? 'input-error' : ''}`} rows={2} placeholder="Mandatory reason for correction..." />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary">
              {mutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
              Save Correction
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function ReceiptDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { hasPermission, user } = useAuthStore()
  const [cancelModal, setCancelModal] = useState(false)
  const [correctModal, setCorrectModal] = useState(searchParams.get('edit') === '1')

  const { data: receipt, isLoading, error } = useQuery({
    queryKey: ['receipt', id],
    queryFn: () => client.get(`/receipts/${id}`).then((r) => r.data),
  })

  const handlePrint = async () => {
    try {
      const res = await client.get(`/receipts/${id}/pdf`, { responseType: 'blob' })
      const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      window.open(url, '_blank')
    } catch {
      toast.error('Failed to generate PDF')
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full" />
      </div>
    )
  }
  if (error || !receipt) {
    return (
      <div className="card text-center py-12">
        <AlertCircle className="mx-auto text-red-400 mb-3" size={40} />
        <p className="text-gray-600">Receipt not found.</p>
        <button onClick={() => navigate('/receipts')} className="btn-secondary mt-4">Back</button>
      </div>
    )
  }

  const items = receipt.items || []
  const total = items.reduce((s: number, i: any) => s + (i.amount || 0), 0)
  const pd = receipt.payment_details || {}

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/receipts')} className="btn-secondary btn-sm">
            <ChevronLeft size={14} /> Receipts
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{receipt.receipt_number}</h1>
            <div className="flex items-center gap-2 mt-1">
              <span className={STATUS_BADGE[receipt.status] || 'badge-gray'}>{receipt.status}</span>
              <span className="text-sm text-gray-500">
                {receipt.receipt_date ? format(parseISO(receipt.receipt_date), 'dd MMMM yyyy') : '-'}
              </span>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={handlePrint} className="btn-secondary">
            <Printer size={15} /> Print PDF
          </button>
          {receipt.status === 'ACTIVE' && hasPermission('CANCEL_RECEIPTS') && (
            <button onClick={() => setCancelModal(true)} className="btn-danger">
              <XCircle size={15} /> Cancel
            </button>
          )}
          {receipt.status === 'ACTIVE' && user?.role === 'super_admin' && (
            <button onClick={() => setCorrectModal(true)} className="btn-primary">
              <Edit2 size={15} /> Correct
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Receipt Info */}
        <div className="card">
          <h2 className="card-title mb-4">Receipt Information</h2>
          <dl className="space-y-2 text-sm">
            {[
              ['Receipt Number', receipt.receipt_number],
              ['Receipt Date', receipt.receipt_date ? format(parseISO(receipt.receipt_date), 'dd/MM/yyyy') : '-'],
              ['Financial Year', receipt.financial_year_name],
              ['Payment Mode', receipt.payment_mode?.replace('_', ' ')],
              ['Status', null],
            ].map(([k, v]) => (
              <div key={k as string} className="flex gap-2">
                <dt className="text-gray-500 w-36 shrink-0">{k}:</dt>
                {k === 'Status' ? (
                  <dd><span className={STATUS_BADGE[receipt.status] || 'badge-gray'}>{receipt.status}</span></dd>
                ) : (
                  <dd className="font-medium text-gray-800">{v as string || '-'}</dd>
                )}
              </div>
            ))}
          </dl>

          {/* Payment details */}
          {(pd.cheque_number || pd.upi_reference || pd.transaction_id || pd.bank_name) && (
            <>
              <div className="border-t my-3" />
              <h3 className="text-sm font-semibold text-gray-600 mb-2">Payment Details</h3>
              <dl className="space-y-1.5 text-sm">
                {pd.cheque_number && <div className="flex gap-2"><dt className="text-gray-500 w-36">Cheque No:</dt><dd className="font-mono">{pd.cheque_number}</dd></div>}
                {pd.cheque_date && <div className="flex gap-2"><dt className="text-gray-500 w-36">Cheque Date:</dt><dd>{pd.cheque_date}</dd></div>}
                {pd.bank_name && <div className="flex gap-2"><dt className="text-gray-500 w-36">Bank:</dt><dd>{pd.bank_name}</dd></div>}
                {pd.branch_name && <div className="flex gap-2"><dt className="text-gray-500 w-36">Branch:</dt><dd>{pd.branch_name}</dd></div>}
                {pd.upi_reference && <div className="flex gap-2"><dt className="text-gray-500 w-36">UPI Ref:</dt><dd className="font-mono">{pd.upi_reference}</dd></div>}
                {pd.transaction_id && <div className="flex gap-2"><dt className="text-gray-500 w-36">Transaction ID:</dt><dd className="font-mono">{pd.transaction_id}</dd></div>}
                {pd.cheque_status && (
                  <div className="flex gap-2">
                    <dt className="text-gray-500 w-36">Cheque Status:</dt>
                    <dd><span className={pd.cheque_status === 'CLEARED' ? 'badge-success' : pd.cheque_status === 'BOUNCED' ? 'badge-danger' : 'badge-warning'}>{pd.cheque_status}</span></dd>
                  </div>
                )}
              </dl>
            </>
          )}

          {receipt.remarks && (
            <>
              <div className="border-t my-3" />
              <p className="text-sm text-gray-500">Remarks: <span className="text-gray-800">{receipt.remarks}</span></p>
            </>
          )}
        </div>

        {/* Student Info */}
        <div className="card">
          <h2 className="card-title mb-4">Student Information</h2>
          <dl className="space-y-2 text-sm">
            {[
              ['Student Name', receipt.student_name],
              ['Admission No', receipt.admission_number],
              ['Roll Number', receipt.roll_number],
              ['Course', receipt.course_name],
              ['Batch', receipt.batch_name],
              ['Session', receipt.session_name],
            ].map(([k, v]) => v ? (
              <div key={k} className="flex gap-2">
                <dt className="text-gray-500 w-36 shrink-0">{k}:</dt>
                <dd className="font-medium text-gray-800">{v}</dd>
              </div>
            ) : null)}
          </dl>
        </div>
      </div>

      {/* Fee Items */}
      <div className="card mt-6">
        <h2 className="card-title mb-4">Fee Items</h2>
        <table className="tbl">
          <thead>
            <tr>
              <th>Fee Head</th>
              <th className="text-right">Amount</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item: any) => (
              <tr key={item.id || item.fee_head_id}>
                <td>{item.fee_head_name || item.name}</td>
                <td className="text-right font-medium">{fmt(item.amount)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td className="font-bold text-gray-900">Total</td>
              <td className="text-right font-bold text-gray-900 text-lg">{fmt(total)}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Correction History */}
      {receipt.corrections && receipt.corrections.length > 0 && (
        <div className="card mt-6">
          <h2 className="card-title mb-4">Correction History</h2>
          <div className="space-y-3">
            {receipt.corrections.map((c: any, i: number) => (
              <div key={i} className="border border-amber-200 bg-amber-50 rounded-lg p-3">
                <div className="flex justify-between text-sm">
                  <span className="font-medium text-amber-800">Corrected on {c.corrected_at ? format(parseISO(c.corrected_at), 'dd/MM/yyyy HH:mm') : '-'}</span>
                  <span className="text-amber-700">by {c.corrected_by_name || c.corrected_by}</span>
                </div>
                {c.reason && <p className="text-sm text-amber-700 mt-1">Reason: {c.reason}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Audit */}
      {receipt.created_by_name && (
        <div className="text-xs text-gray-400 mt-4 text-right">
          Created by {receipt.created_by_name} on {receipt.created_at ? format(parseISO(receipt.created_at), 'dd/MM/yyyy HH:mm') : '-'}
        </div>
      )}

      {cancelModal && <CancelModal receipt={receipt} onClose={() => setCancelModal(false)} />}
      {correctModal && <CorrectModal receipt={receipt} onClose={() => setCorrectModal(false)} />}
    </div>
  )
}
