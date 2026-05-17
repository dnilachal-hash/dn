import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, useFieldArray } from 'react-hook-form'
import toast from 'react-hot-toast'
import {
  Plus, Edit2, Lock, Unlock, Copy, Users, X, Loader2, Check, Trash2, Eye
} from 'lucide-react'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'

const fmt = (n: number) => '₹' + (n || 0).toLocaleString('en-IN')

// ─── Create/Edit Modal ────────────────────────────────────────────────────────
function FeeStructureModal({ item, onClose }: { item?: any; onClose: () => void }) {
  const qc = useQueryClient()
  const { data: courses } = useQuery({ queryKey: ['courses-list'], queryFn: () => client.get('/courses/').then((r) => r.data) })
  const { data: batches } = useQuery({ queryKey: ['batches-list', ''], queryFn: () => client.get('/courses/batches/').then((r) => r.data) })
  const { data: sessions } = useQuery({ queryKey: ['sessions-list'], queryFn: () => client.get('/courses/sessions/').then((r) => r.data) })
  const { data: fys } = useQuery({ queryKey: ['financial-years'], queryFn: () => client.get('/financial-years/').then((r) => r.data) })
  const { data: feeHeads } = useQuery({ queryKey: ['fee-heads'], queryFn: () => client.get('/fee-heads/').then((r) => r.data) })

  const courseList = courses?.items || courses || []
  const batchList = batches?.items || batches || []
  const sessionList = sessions?.items || sessions || []
  const fyList = fys?.items || fys || []
  const feeHeadList = (feeHeads?.items || feeHeads || []).filter((fh: any) => fh.is_active !== false)

  const defaultItems = item?.items?.map((i: any) => ({
    fee_head_id: i.fee_head_id?.toString() || '',
    amount: i.amount || 0,
    is_compulsory: i.is_compulsory !== false,
  })) || [{ fee_head_id: '', amount: 0, is_compulsory: true }]

  const { register, handleSubmit, control, formState: { errors } } = useForm({
    defaultValues: {
      name: item?.name || '',
      course_id: item?.course_id?.toString() || '',
      batch_id: item?.batch_id?.toString() || '',
      session_id: item?.session_id?.toString() || '',
      financial_year_id: item?.financial_year_id?.toString() || '',
      applicable_from: item?.applicable_from?.slice(0, 10) || '',
      items: defaultItems,
    },
  })

  const { fields, append, remove } = useFieldArray({ control, name: 'items' })

  const mutation = useMutation({
    mutationFn: (data: any) => {
      const payload = {
        ...data,
        course_id: data.course_id ? Number(data.course_id) : null,
        batch_id: data.batch_id ? Number(data.batch_id) : null,
        session_id: data.session_id ? Number(data.session_id) : null,
        financial_year_id: data.financial_year_id ? Number(data.financial_year_id) : null,
        items: data.items.map((i: any) => ({
          fee_head_id: Number(i.fee_head_id),
          amount: parseFloat(i.amount),
          is_compulsory: i.is_compulsory,
        })),
      }
      return item
        ? client.put(`/fee-structures/${item.id}`, payload).then((r) => r.data)
        : client.post('/fee-structures/', payload).then((r) => r.data)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fee-structures'] })
      toast.success(item ? 'Updated!' : 'Fee structure created!')
      onClose()
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed'),
  })

  return (
    <div className="modal-backdrop">
      <div className="modal max-w-2xl">
        <div className="modal-header">
          <h3 className="modal-title">{item ? 'Edit Fee Structure' : 'Create Fee Structure'}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
          <div className="modal-body space-y-4">
            <div>
              <label className="label">Structure Name *</label>
              <input {...register('name', { required: 'Required' })} className={`input ${errors.name ? 'input-error' : ''}`} placeholder="e.g. BHMS Year 1 FY 2025-26" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Course</label>
                <select {...register('course_id')} className="input">
                  <option value="">All Courses</option>
                  {courseList.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Batch</label>
                <select {...register('batch_id')} className="input">
                  <option value="">All Batches</option>
                  {batchList.map((b: any) => <option key={b.id} value={b.id}>{b.name}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Session</label>
                <select {...register('session_id')} className="input">
                  <option value="">All Sessions</option>
                  {sessionList.map((s: any) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Financial Year *</label>
                <select {...register('financial_year_id', { required: 'Required' })} className={`input ${errors.financial_year_id ? 'input-error' : ''}`}>
                  <option value="">Select FY</option>
                  {fyList.map((fy: any) => <option key={fy.id} value={fy.id}>{fy.name}</option>)}
                </select>
              </div>
            </div>

            {/* Fee Items */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="label mb-0">Fee Items</label>
                <button
                  type="button"
                  onClick={() => append({ fee_head_id: '', amount: 0, is_compulsory: true })}
                  className="btn-secondary btn-sm"
                >
                  <Plus size={13} /> Add Row
                </button>
              </div>
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <table className="tbl">
                  <thead>
                    <tr>
                      <th>Fee Head *</th>
                      <th>Amount (₹)</th>
                      <th>Compulsory</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {fields.map((field, idx) => (
                      <tr key={field.id}>
                        <td className="w-1/2">
                          <select
                            {...register(`items.${idx}.fee_head_id`, { required: true })}
                            className="input py-1 text-sm"
                          >
                            <option value="">Select Fee Head</option>
                            {feeHeadList.map((fh: any) => <option key={fh.id} value={fh.id}>{fh.name}</option>)}
                          </select>
                        </td>
                        <td>
                          <input
                            {...register(`items.${idx}.amount`, { required: true, min: 0 })}
                            type="number"
                            step="0.01"
                            min={0}
                            className="input py-1 text-sm"
                            placeholder="0.00"
                          />
                        </td>
                        <td>
                          <input
                            {...register(`items.${idx}.is_compulsory`)}
                            type="checkbox"
                            className="w-4 h-4 text-indigo-600 rounded"
                          />
                        </td>
                        <td>
                          {fields.length > 1 && (
                            <button type="button" onClick={() => remove(idx)} className="text-red-400 hover:text-red-600">
                              <Trash2 size={15} />
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary">
              {mutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
              {item ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Detail View Modal ────────────────────────────────────────────────────────
function DetailModal({ id, onClose }: { id: number; onClose: () => void }) {
  const { data, isLoading } = useQuery({
    queryKey: ['fee-structure-detail', id],
    queryFn: () => client.get(`/fee-structures/${id}`).then((r) => r.data),
  })
  const total = (data?.items || []).reduce((s: number, i: any) => s + (i.amount || 0), 0)
  return (
    <div className="modal-backdrop">
      <div className="modal max-w-lg">
        <div className="modal-header">
          <h3 className="modal-title">{data?.name || 'Fee Structure'}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <div className="modal-body">
          {isLoading ? <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div> : (
            <>
              <div className="grid grid-cols-2 gap-3 text-sm mb-4">
                {[['Course', data?.course_name], ['Batch', data?.batch_name], ['Session', data?.session_name], ['Financial Year', data?.financial_year_name]].map(([k, v]) => v ? (
                  <div key={k}><span className="text-gray-500">{k}: </span><span className="font-medium">{v}</span></div>
                ) : null)}
              </div>
              <table className="tbl">
                <thead><tr><th>Fee Head</th><th className="text-right">Amount</th><th>Compulsory</th></tr></thead>
                <tbody>
                  {(data?.items || []).map((i: any) => (
                    <tr key={i.id}><td>{i.fee_head_name}</td><td className="text-right">{fmt(i.amount)}</td><td><span className={i.is_compulsory ? 'badge-success' : 'badge-gray'}>{i.is_compulsory ? 'Yes' : 'No'}</span></td></tr>
                  ))}
                </tbody>
                <tfoot><tr><td className="font-bold">Total</td><td className="text-right font-bold">{fmt(total)}</td><td></td></tr></tfoot>
              </table>
            </>
          )}
        </div>
        <div className="modal-footer"><button onClick={onClose} className="btn-secondary">Close</button></div>
      </div>
    </div>
  )
}

// ─── Copy Modal ───────────────────────────────────────────────────────────────
function CopyModal({ id, onClose }: { id: number; onClose: () => void }) {
  const qc = useQueryClient()
  const { data: fys } = useQuery({ queryKey: ['financial-years'], queryFn: () => client.get('/financial-years/').then((r) => r.data) })
  const fyList = fys?.items || fys || []
  const [newName, setNewName] = useState('')
  const [newFyId, setNewFyId] = useState('')
  const mutation = useMutation({
    mutationFn: () => client.post(`/fee-structures/${id}/copy`, { new_name: newName, financial_year_id: newFyId ? Number(newFyId) : undefined }).then((r) => r.data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['fee-structures'] }); toast.success('Copied!'); onClose() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed to copy'),
  })
  return (
    <div className="modal-backdrop">
      <div className="modal max-w-sm">
        <div className="modal-header">
          <h3 className="modal-title">Copy Fee Structure</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <div className="modal-body space-y-4">
          <div>
            <label className="label">New Name *</label>
            <input className="input" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Name for the copy" />
          </div>
          <div>
            <label className="label">Target Financial Year</label>
            <select className="input" value={newFyId} onChange={(e) => setNewFyId(e.target.value)}>
              <option value="">Same as original</option>
              {fyList.map((fy: any) => <option key={fy.id} value={fy.id}>{fy.name}</option>)}
            </select>
          </div>
        </div>
        <div className="modal-footer">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={() => mutation.mutate()} disabled={!newName || mutation.isPending} className="btn-primary">
            {mutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <Copy size={14} />}
            Copy
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Assign to Students Modal ─────────────────────────────────────────────────
function AssignModal({ structure, onClose }: { structure: any; onClose: () => void }) {
  const [courseId, setCourseId] = useState(structure.course_id?.toString() || '')
  const [batchId, setBatchId] = useState(structure.batch_id?.toString() || '')
  const [overwrite, setOverwrite] = useState(false)
  const [result, setResult] = useState<any>(null)
  const { data: courses } = useQuery({ queryKey: ['courses-list'], queryFn: () => client.get('/courses/').then((r) => r.data) })
  const { data: batches } = useQuery({ queryKey: ['batches-list', courseId], queryFn: () => client.get('/courses/batches/', { params: courseId ? { course_id: courseId } : {} }).then((r) => r.data) })
  const courseList = courses?.items || courses || []
  const batchList = batches?.items || batches || []

  const mutation = useMutation({
    mutationFn: () =>
      client.post(`/fee-structures/${structure.id}/assign`, {
        course_id: courseId ? Number(courseId) : null,
        batch_id: batchId ? Number(batchId) : null,
        overwrite,
      }).then((r) => r.data),
    onSuccess: (data) => { setResult(data); toast.success('Assignment complete!') },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed'),
  })

  return (
    <div className="modal-backdrop">
      <div className="modal max-w-md">
        <div className="modal-header">
          <h3 className="modal-title">Assign to Students</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <div className="modal-body space-y-4">
          <p className="text-sm text-gray-600">Assign <strong>{structure.name}</strong> to students matching the filters below.</p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Course</label>
              <select className="input" value={courseId} onChange={(e) => { setCourseId(e.target.value); setBatchId('') }}>
                <option value="">All Courses</option>
                {courseList.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Batch</label>
              <select className="input" value={batchId} onChange={(e) => setBatchId(e.target.value)}>
                <option value="">All Batches</option>
                {batchList.map((b: any) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" id="overwrite" checked={overwrite} onChange={(e) => setOverwrite(e.target.checked)} className="w-4 h-4 text-indigo-600 rounded" />
            <label htmlFor="overwrite" className="text-sm text-gray-700">Overwrite existing assignments</label>
          </div>
          {result && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-sm text-emerald-800">
              Assigned to {result.assigned_count} students. {result.skipped_count ? `Skipped: ${result.skipped_count}` : ''}
            </div>
          )}
        </div>
        <div className="modal-footer">
          <button onClick={onClose} className="btn-secondary">Close</button>
          <button onClick={() => mutation.mutate()} disabled={mutation.isPending} className="btn-primary">
            {mutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <Users size={14} />}
            Assign
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function FeeStructures() {
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'super_admin'
  const canManage = isAdmin || user?.role === 'accounts_user'
  const [modal, setModal] = useState<any>(null) // {type: 'edit'|'detail'|'copy'|'assign', id?, item?}

  const [fyFilter, setFyFilter] = useState('')

  const { data: fys } = useQuery({ queryKey: ['financial-years'], queryFn: () => client.get('/financial-years/').then((r) => r.data) })
  const fyList = fys?.items || fys || []

  const { data, isLoading } = useQuery({
    queryKey: ['fee-structures', fyFilter],
    queryFn: () => client.get('/fee-structures/', { params: fyFilter ? { financial_year_id: fyFilter } : {} }).then((r) => r.data),
  })

  const freezeMutation = useMutation({
    mutationFn: ({ id, freeze }: { id: number; freeze: boolean }) =>
      client.post(`/fee-structures/${id}/${freeze ? 'freeze' : 'unfreeze'}`).then((r) => r.data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ['fee-structures'] })
      toast.success(vars.freeze ? 'Structure frozen!' : 'Structure unfrozen!')
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed'),
  })

  const items = data?.items || data || []

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Fee Structures</h1>
        {canManage && (
          <button onClick={() => setModal({ type: 'edit' })} className="btn-primary">
            <Plus size={16} /> New Structure
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="card mb-6 py-4">
        <div className="flex items-center gap-3">
          <label className="label mb-0 shrink-0">Filter by FY:</label>
          <select className="input w-48" value={fyFilter} onChange={(e) => setFyFilter(e.target.value)}>
            <option value="">All Financial Years</option>
            {fyList.map((fy: any) => <option key={fy.id} value={fy.id}>{fy.name}</option>)}
          </select>
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-16"><div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full" /></div>
        ) : (
          <table className="tbl">
            <thead>
              <tr>
                <th>Name</th>
                <th>Course</th>
                <th>Batch</th>
                <th>Session</th>
                <th>Financial Year</th>
                <th>Total Amount</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && (
                <tr><td colSpan={8} className="text-center text-gray-400 py-12">No fee structures found.</td></tr>
              )}
              {items.map((fs: any) => (
                <tr key={fs.id}>
                  <td className="font-medium text-gray-900">{fs.name}</td>
                  <td>{fs.course_name || '-'}</td>
                  <td>{fs.batch_name || '-'}</td>
                  <td>{fs.session_name || '-'}</td>
                  <td>{fs.financial_year_name || '-'}</td>
                  <td className="font-medium">{fmt(fs.total_amount)}</td>
                  <td>
                    <div className="flex gap-1">
                      <span className={fs.is_active !== false ? 'badge-success' : 'badge-danger'}>
                        {fs.is_active !== false ? 'Active' : 'Inactive'}
                      </span>
                      {fs.is_frozen && <span className="badge-warning">Frozen</span>}
                    </div>
                  </td>
                  <td>
                    <div className="flex gap-1 flex-wrap">
                      <button onClick={() => setModal({ type: 'detail', id: fs.id })} className="btn-secondary btn-sm" title="View"><Eye size={13} /></button>
                      {canManage && !fs.is_frozen && (
                        <button onClick={() => setModal({ type: 'edit', item: fs })} className="btn-secondary btn-sm" title="Edit"><Edit2 size={13} /></button>
                      )}
                      {canManage && (
                        <>
                          <button onClick={() => setModal({ type: 'copy', id: fs.id })} className="btn-secondary btn-sm" title="Copy"><Copy size={13} /></button>
                          <button onClick={() => setModal({ type: 'assign', item: fs })} className="btn-secondary btn-sm" title="Assign"><Users size={13} /></button>
                          {isAdmin && (
                            <button
                              onClick={() => freezeMutation.mutate({ id: fs.id, freeze: !fs.is_frozen })}
                              className={fs.is_frozen ? 'btn-success btn-sm' : 'btn-secondary btn-sm'}
                              title={fs.is_frozen ? 'Unfreeze' : 'Freeze'}
                            >
                              {fs.is_frozen ? <Unlock size={13} /> : <Lock size={13} />}
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {modal?.type === 'edit' && <FeeStructureModal item={modal.item} onClose={() => setModal(null)} />}
      {modal?.type === 'detail' && <DetailModal id={modal.id} onClose={() => setModal(null)} />}
      {modal?.type === 'copy' && <CopyModal id={modal.id} onClose={() => setModal(null)} />}
      {modal?.type === 'assign' && <AssignModal structure={modal.item} onClose={() => setModal(null)} />}
    </div>
  )
}
