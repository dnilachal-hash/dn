import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import {
  Plus, Edit2, Lock, Unlock, CheckCircle, AlertTriangle, X, Loader2, Check
} from 'lucide-react'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'
import { format } from 'date-fns'

interface FYForm {
  name: string
  start_date: string
  end_date: string
  next_receipt_number: number
}

function FYModal({ item, onClose }: { item?: any; onClose: () => void }) {
  const qc = useQueryClient()

  const getDefaults = () => {
    if (item) {
      return {
        name: item.name,
        start_date: item.start_date?.slice(0, 10) || '',
        end_date: item.end_date?.slice(0, 10) || '',
        next_receipt_number: item.next_receipt_number || 1,
      }
    }
    const year = new Date().getFullYear()
    return {
      name: `${year}-${year + 1}`,
      start_date: `${year}-04-01`,
      end_date: `${year + 1}-03-31`,
      next_receipt_number: 1,
    }
  }

  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<FYForm>({
    defaultValues: getDefaults(),
  })

  const watchName = watch('name')

  // Auto-fill dates from FY name like "2025-2026"
  const handleNameChange = (val: string) => {
    setValue('name', val)
    const match = val.match(/^(\d{4})-(\d{4})$/)
    if (match) {
      setValue('start_date', `${match[1]}-04-01`)
      setValue('end_date', `${match[2]}-03-31`)
    }
  }

  const mutation = useMutation({
    mutationFn: (data: FYForm) =>
      item
        ? client.put(`/financial-years/${item.id}`, data).then((r) => r.data)
        : client.post('/financial-years/', data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['financial-years'] })
      toast.success(item ? 'Financial year updated!' : 'Financial year created!')
      onClose()
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed to save'),
  })

  return (
    <div className="modal-backdrop">
      <div className="modal max-w-md">
        <div className="modal-header">
          <h3 className="modal-title">{item ? 'Edit Financial Year' : 'New Financial Year'}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
          <div className="modal-body space-y-4">
            <div>
              <label className="label">FY Name *</label>
              <input
                {...register('name', { required: 'Required' })}
                className={`input ${errors.name ? 'input-error' : ''}`}
                placeholder="e.g. 2025-2026"
                onChange={(e) => handleNameChange(e.target.value)}
              />
              <p className="text-xs text-gray-400 mt-1">Format: YYYY-YYYY (dates auto-filled)</p>
              {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name.message}</p>}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Start Date *</label>
                <input {...register('start_date', { required: 'Required' })} type="date" className="input" />
              </div>
              <div>
                <label className="label">End Date *</label>
                <input {...register('end_date', { required: 'Required' })} type="date" className="input" />
              </div>
            </div>
            <div>
              <label className="label">Next Receipt Number</label>
              <input
                {...register('next_receipt_number', { valueAsNumber: true, min: 1 })}
                type="number"
                min={1}
                className="input"
              />
              <p className="text-xs text-gray-400 mt-1">The next receipt issued will have this sequence number</p>
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

function LockConfirmModal({ fy, onConfirm, onCancel }: { fy: any; onConfirm: () => void; onCancel: () => void }) {
  return (
    <div className="modal-backdrop">
      <div className="modal max-w-sm">
        <div className="modal-header">
          <h3 className="modal-title text-amber-700 flex items-center gap-2">
            <AlertTriangle size={18} />
            {fy.is_locked ? 'Unlock Financial Year?' : 'Lock Financial Year?'}
          </h3>
          <button onClick={onCancel} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <div className="modal-body space-y-3">
          <p className="text-gray-700">
            {fy.is_locked
              ? `Unlocking FY <strong>${fy.name}</strong> will allow new receipts to be created.`
              : `Locking FY <strong>${fy.name}</strong> will prevent new receipts from being issued for this financial year.`}
          </p>
          {!fy.is_locked && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-amber-800 text-sm flex items-start gap-2">
              <AlertTriangle size={16} className="shrink-0 mt-0.5" />
              <span>This will prevent new receipts for this FY. Existing receipts are not affected.</span>
            </div>
          )}
          <p className="text-sm text-gray-500">FY: <strong>{fy.name}</strong></p>
        </div>
        <div className="modal-footer">
          <button onClick={onCancel} className="btn-secondary">Cancel</button>
          <button onClick={onConfirm} className={fy.is_locked ? 'btn-success' : 'btn-danger'}>
            {fy.is_locked ? 'Unlock FY' : 'Lock FY'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function FinancialYears() {
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'super_admin'
  const [modal, setModal] = useState<any>(null)
  const [lockTarget, setLockTarget] = useState<any>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['financial-years'],
    queryFn: () => client.get('/financial-years/').then((r) => r.data),
  })

  const setActiveMutation = useMutation({
    mutationFn: (id: number) => client.post(`/financial-years/${id}/set-active`).then((r) => r.data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['financial-years'] }); toast.success('Active FY updated!') },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed'),
  })

  const lockMutation = useMutation({
    mutationFn: ({ id, lock }: { id: number; lock: boolean }) =>
      client.post(`/financial-years/${id}/${lock ? 'lock' : 'unlock'}`).then((r) => r.data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ['financial-years'] })
      toast.success(vars.lock ? 'Financial year locked!' : 'Financial year unlocked!')
      setLockTarget(null)
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed'),
  })

  const items = data?.items || data || []

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Financial Years</h1>
        {isAdmin && (
          <button onClick={() => setModal({})} className="btn-primary">
            <Plus size={16} />
            New Financial Year
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
                <th>FY Name</th>
                <th>Start Date</th>
                <th>End Date</th>
                <th>Next Receipt #</th>
                <th>Active</th>
                <th>Locked</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && (
                <tr>
                  <td colSpan={7} className="text-center text-gray-400 py-12">
                    No financial years configured. Create one to get started.
                  </td>
                </tr>
              )}
              {items.map((fy: any) => (
                <tr key={fy.id}>
                  <td className="font-semibold text-gray-900">
                    {fy.name}
                    {fy.is_active && (
                      <span className="ml-2 badge-indigo text-xs">Current</span>
                    )}
                  </td>
                  <td>{fy.start_date ? format(new Date(fy.start_date), 'dd MMM yyyy') : '-'}</td>
                  <td>{fy.end_date ? format(new Date(fy.end_date), 'dd MMM yyyy') : '-'}</td>
                  <td className="font-mono">{fy.next_receipt_number || 1}</td>
                  <td>
                    {fy.is_active ? (
                      <span className="badge-success flex items-center gap-1 w-fit">
                        <CheckCircle size={12} /> Active
                      </span>
                    ) : (
                      <span className="badge-gray">Inactive</span>
                    )}
                  </td>
                  <td>
                    {fy.is_locked ? (
                      <span className="badge-danger flex items-center gap-1 w-fit">
                        <Lock size={12} /> Locked
                      </span>
                    ) : (
                      <span className="badge-success">Open</span>
                    )}
                  </td>
                  <td>
                    <div className="flex gap-2 flex-wrap">
                      {isAdmin && (
                        <>
                          <button
                            onClick={() => setModal({ editing: fy })}
                            className="btn-secondary btn-sm"
                            title="Edit"
                          >
                            <Edit2 size={13} />
                          </button>
                          {!fy.is_active && (
                            <button
                              onClick={() => setActiveMutation.mutate(fy.id)}
                              disabled={setActiveMutation.isPending}
                              className="btn-success btn-sm"
                              title="Set as Active"
                            >
                              <CheckCircle size={13} />
                              Set Active
                            </button>
                          )}
                          <button
                            onClick={() => setLockTarget(fy)}
                            className={fy.is_locked ? 'btn-success btn-sm' : 'btn-secondary btn-sm'}
                            title={fy.is_locked ? 'Unlock' : 'Lock'}
                          >
                            {fy.is_locked ? <Unlock size={13} /> : <Lock size={13} />}
                            {fy.is_locked ? 'Unlock' : 'Lock'}
                          </button>
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

      {modal !== null && (
        <FYModal item={modal.editing} onClose={() => setModal(null)} />
      )}
      {lockTarget && (
        <LockConfirmModal
          fy={lockTarget}
          onConfirm={() => lockMutation.mutate({ id: lockTarget.id, lock: !lockTarget.is_locked })}
          onCancel={() => setLockTarget(null)}
        />
      )}
    </div>
  )
}
