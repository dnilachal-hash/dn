import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Plus, Edit2, ToggleLeft, ToggleRight, X, Loader2, Check } from 'lucide-react'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'

function FeeHeadModal({ item, onClose }: { item?: any; onClose: () => void }) {
  const qc = useQueryClient()
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      name: item?.name || '',
      code: item?.code || '',
      head_type: item?.head_type || 'TUITION',
      frequency: item?.frequency || 'ANNUAL',
      is_compulsory: item?.is_compulsory !== false,
      is_refundable: item?.is_refundable || false,
      is_active: item?.is_active !== false,
      description: item?.description || '',
    },
  })
  const mutation = useMutation({
    mutationFn: (data: any) =>
      item
        ? client.put(`/fee-heads/${item.id}`, data).then((r) => r.data)
        : client.post('/fee-heads/', data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fee-heads'] })
      toast.success(item ? 'Fee head updated!' : 'Fee head created!')
      onClose()
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed to save'),
  })

  return (
    <div className="modal-backdrop">
      <div className="modal max-w-lg">
        <div className="modal-header">
          <h3 className="modal-title">{item ? 'Edit Fee Head' : 'Add Fee Head'}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
          <div className="modal-body space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Fee Head Name *</label>
                <input
                  {...register('name', { required: 'Required' })}
                  className={`input ${errors.name ? 'input-error' : ''}`}
                  placeholder="e.g. Tuition Fee"
                />
                {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name.message as string}</p>}
              </div>
              <div>
                <label className="label">Code</label>
                <input {...register('code')} className="input" placeholder="e.g. TF" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Type</label>
                <select {...register('head_type')} className="input">
                  <option value="TUITION">Tuition</option>
                  <option value="HOSTEL">Hostel</option>
                  <option value="TRANSPORT">Transport</option>
                  <option value="EXAM">Exam</option>
                  <option value="LIBRARY">Library</option>
                  <option value="SPORTS">Sports</option>
                  <option value="LAB">Lab</option>
                  <option value="MISC">Miscellaneous</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
              <div>
                <label className="label">Frequency</label>
                <select {...register('frequency')} className="input">
                  <option value="ANNUAL">Annual</option>
                  <option value="SEMESTER">Per Semester</option>
                  <option value="MONTHLY">Monthly</option>
                  <option value="ONETIME">One-time</option>
                </select>
              </div>
            </div>

            <div>
              <label className="label">Description</label>
              <textarea {...register('description')} className="input" rows={2} />
            </div>

            <div className="flex flex-wrap gap-6">
              <div className="flex items-center gap-2">
                <input {...register('is_compulsory')} type="checkbox" id="fh_compulsory" className="w-4 h-4 text-indigo-600 rounded" />
                <label htmlFor="fh_compulsory" className="text-sm font-medium text-gray-700">Compulsory</label>
              </div>
              <div className="flex items-center gap-2">
                <input {...register('is_refundable')} type="checkbox" id="fh_refundable" className="w-4 h-4 text-indigo-600 rounded" />
                <label htmlFor="fh_refundable" className="text-sm font-medium text-gray-700">Refundable</label>
              </div>
              <div className="flex items-center gap-2">
                <input {...register('is_active')} type="checkbox" id="fh_active" className="w-4 h-4 text-indigo-600 rounded" />
                <label htmlFor="fh_active" className="text-sm font-medium text-gray-700">Active</label>
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

export default function FeeHeads() {
  const qc = useQueryClient()
  const { user, hasPermission } = useAuthStore()
  const canManage = user?.role === 'super_admin' || hasPermission('MANAGE_FEE_HEADS')
  const [modal, setModal] = useState<any>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['fee-heads'],
    queryFn: () => client.get('/fee-heads/').then((r) => r.data),
  })

  const toggleMutation = useMutation({
    mutationFn: (item: any) =>
      client.patch(`/fee-heads/${item.id}`, { is_active: !item.is_active }).then((r) => r.data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['fee-heads'] }) },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed'),
  })

  const items = data?.items || data || []

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Fee Heads</h1>
        {canManage && (
          <button onClick={() => setModal({})} className="btn-primary">
            <Plus size={16} />
            Add Fee Head
          </button>
        )}
      </div>

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full" />
          </div>
        ) : (
          <table className="tbl">
            <thead>
              <tr>
                <th>Name</th>
                <th>Code</th>
                <th>Type</th>
                <th>Frequency</th>
                <th>Compulsory</th>
                <th>Refundable</th>
                <th>Status</th>
                {canManage && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && (
                <tr>
                  <td colSpan={8} className="text-center text-gray-400 py-12">
                    No fee heads configured yet.
                  </td>
                </tr>
              )}
              {items.map((fh: any) => (
                <tr key={fh.id}>
                  <td className="font-medium text-gray-900">
                    {fh.name}
                    {fh.description && (
                      <div className="text-xs text-gray-400 font-normal">{fh.description}</div>
                    )}
                  </td>
                  <td className="font-mono text-sm">{fh.code || '-'}</td>
                  <td>
                    <span className="badge-info capitalize">{fh.head_type?.toLowerCase() || '-'}</span>
                  </td>
                  <td className="text-sm capitalize">{fh.frequency?.toLowerCase() || '-'}</td>
                  <td>
                    <span className={fh.is_compulsory ? 'badge-success' : 'badge-gray'}>
                      {fh.is_compulsory ? 'Yes' : 'No'}
                    </span>
                  </td>
                  <td>
                    <span className={fh.is_refundable ? 'badge-info' : 'badge-gray'}>
                      {fh.is_refundable ? 'Yes' : 'No'}
                    </span>
                  </td>
                  <td>
                    {canManage ? (
                      <button
                        onClick={() => toggleMutation.mutate(fh)}
                        disabled={toggleMutation.isPending}
                        className="flex items-center gap-1 text-sm"
                        title="Toggle Active"
                      >
                        {fh.is_active ? (
                          <><ToggleRight size={22} className="text-emerald-500" /><span className="text-emerald-700">Active</span></>
                        ) : (
                          <><ToggleLeft size={22} className="text-gray-400" /><span className="text-gray-500">Inactive</span></>
                        )}
                      </button>
                    ) : (
                      <span className={fh.is_active ? 'badge-success' : 'badge-danger'}>
                        {fh.is_active ? 'Active' : 'Inactive'}
                      </span>
                    )}
                  </td>
                  {canManage && (
                    <td>
                      <button
                        onClick={() => setModal({ editing: fh })}
                        className="btn-secondary btn-sm"
                      >
                        <Edit2 size={13} />
                        Edit
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {modal !== null && (
        <FeeHeadModal item={modal.editing} onClose={() => setModal(null)} />
      )}
    </div>
  )
}
