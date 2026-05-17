import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import {
  Plus, Edit2, Key, ToggleLeft, ToggleRight, X, Loader2, Check, AlertCircle
} from 'lucide-react'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'

const ROLES = [
  { value: 'super_admin', label: 'Super Admin' },
  { value: 'accounts_user', label: 'Accounts User' },
  { value: 'viewer', label: 'Viewer' },
  { value: 'auditor', label: 'Auditor' },
]

const ROLE_BADGE: Record<string, string> = {
  super_admin: 'badge-indigo',
  accounts_user: 'badge-success',
  viewer: 'badge-gray',
  auditor: 'badge-info',
}

function UserModal({ item, onClose }: { item?: any; onClose: () => void }) {
  const qc = useQueryClient()
  const isEdit = !!item
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      username: item?.username || '',
      full_name: item?.full_name || '',
      email: item?.email || '',
      role: item?.role || 'accounts_user',
      password: '',
      is_active: item?.is_active !== false,
      force_password_change: item?.force_password_change || false,
    },
  })
  const mutation = useMutation({
    mutationFn: (data: any) => {
      const payload: any = {
        full_name: data.full_name,
        email: data.email,
        role: data.role,
        is_active: data.is_active,
        force_password_change: data.force_password_change,
      }
      if (!isEdit) {
        payload.username = data.username
        payload.password = data.password
      }
      return isEdit
        ? client.put(`/users/${item.id}`, payload).then((r) => r.data)
        : client.post('/users/', payload).then((r) => r.data)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      toast.success(isEdit ? 'User updated!' : 'User created!')
      onClose()
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed to save'),
  })

  return (
    <div className="modal-backdrop">
      <div className="modal max-w-md">
        <div className="modal-header">
          <h3 className="modal-title">{isEdit ? 'Edit User' : 'Add User'}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
          <div className="modal-body space-y-4">
            {!isEdit && (
              <div>
                <label className="label">Username *</label>
                <input
                  {...register('username', { required: 'Required', pattern: { value: /^[a-z0-9_]+$/, message: 'Lowercase letters, numbers, underscores only' } })}
                  className={`input ${errors.username ? 'input-error' : ''}`}
                  placeholder="username"
                />
                {errors.username && <p className="text-red-500 text-xs mt-1">{errors.username.message as string}</p>}
              </div>
            )}
            <div>
              <label className="label">Full Name *</label>
              <input {...register('full_name', { required: 'Required' })} className={`input ${errors.full_name ? 'input-error' : ''}`} placeholder="Full name" />
              {errors.full_name && <p className="text-red-500 text-xs mt-1">{errors.full_name.message as string}</p>}
            </div>
            <div>
              <label className="label">Email</label>
              <input {...register('email')} type="email" className="input" placeholder="email@example.com" />
            </div>
            <div>
              <label className="label">Role *</label>
              <select {...register('role', { required: 'Required' })} className="input">
                {ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
            </div>
            {!isEdit && (
              <div>
                <label className="label">Password *</label>
                <input
                  {...register('password', { required: !isEdit ? 'Required' : false, minLength: { value: 6, message: 'Min 6 characters' } })}
                  type="password"
                  className={`input ${errors.password ? 'input-error' : ''}`}
                  placeholder="Initial password"
                />
                {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message as string}</p>}
              </div>
            )}
            <div className="flex gap-6">
              <div className="flex items-center gap-2">
                <input {...register('is_active')} type="checkbox" id="u_active" className="w-4 h-4 text-indigo-600 rounded" />
                <label htmlFor="u_active" className="text-sm font-medium text-gray-700">Active</label>
              </div>
              <div className="flex items-center gap-2">
                <input {...register('force_password_change')} type="checkbox" id="u_force" className="w-4 h-4 text-amber-500 rounded" />
                <label htmlFor="u_force" className="text-sm font-medium text-gray-700">Force Password Change</label>
              </div>
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary">
              {mutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
              {isEdit ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function ResetPasswordModal({ user: u, onClose }: { user: any; onClose: () => void }) {
  const qc = useQueryClient()
  const [newPassword, setNewPassword] = useState('')
  const [forceChange, setForceChange] = useState(true)
  const mutation = useMutation({
    mutationFn: () =>
      client.post(`/users/${u.id}/reset-password`, { new_password: newPassword, force_password_change: forceChange }).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      toast.success('Password reset!')
      onClose()
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed'),
  })
  return (
    <div className="modal-backdrop">
      <div className="modal max-w-sm">
        <div className="modal-header">
          <h3 className="modal-title">Reset Password — {u.username}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <div className="modal-body space-y-4">
          <div>
            <label className="label">New Password</label>
            <input
              type="password"
              className="input"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Minimum 6 characters"
            />
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" id="fc" checked={forceChange} onChange={(e) => setForceChange(e.target.checked)} className="w-4 h-4 text-amber-500 rounded" />
            <label htmlFor="fc" className="text-sm text-gray-700">Force user to change password on next login</label>
          </div>
        </div>
        <div className="modal-footer">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={() => mutation.mutate()} disabled={newPassword.length < 6 || mutation.isPending} className="btn-danger">
            {mutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <Key size={14} />}
            Reset Password
          </button>
        </div>
      </div>
    </div>
  )
}

export default function UserManagement() {
  const { user: currentUser } = useAuthStore()
  const qc = useQueryClient()
  const [modal, setModal] = useState<any>(null) // {type: 'edit'|'add'|'reset', user?}

  if (currentUser?.role !== 'super_admin') {
    return (
      <div className="card text-center py-12">
        <AlertCircle className="mx-auto text-red-400 mb-3" size={40} />
        <p className="text-gray-600">Access restricted to super administrators only.</p>
      </div>
    )
  }

  const { data, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => client.get('/users/').then((r) => r.data),
  })

  const toggleMutation = useMutation({
    mutationFn: (u: any) =>
      client.patch(`/users/${u.id}`, { is_active: !u.is_active }).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed'),
  })

  const users = data?.items || data || []

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">User Management</h1>
        <button onClick={() => setModal({ type: 'add' })} className="btn-primary">
          <Plus size={16} /> Add User
        </button>
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
                <th>Username</th>
                <th>Full Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Active</th>
                <th>Force Change</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 && (
                <tr>
                  <td colSpan={7} className="text-center text-gray-400 py-12">No users found.</td>
                </tr>
              )}
              {users.map((u: any) => (
                <tr key={u.id}>
                  <td className="font-mono font-medium">{u.username}</td>
                  <td>{u.full_name}</td>
                  <td className="text-sm text-gray-600">{u.email || '-'}</td>
                  <td>
                    <span className={ROLE_BADGE[u.role] || 'badge-gray'}>
                      {ROLES.find((r) => r.value === u.role)?.label || u.role}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => u.id !== currentUser?.id && toggleMutation.mutate(u)}
                      disabled={u.id === currentUser?.id}
                      className="flex items-center gap-1 text-sm"
                      title={u.id === currentUser?.id ? "Can't disable yourself" : 'Toggle active'}
                    >
                      {u.is_active !== false ? (
                        <><ToggleRight size={22} className="text-emerald-500" /><span className="text-emerald-700 text-xs">Active</span></>
                      ) : (
                        <><ToggleLeft size={22} className="text-gray-400" /><span className="text-gray-500 text-xs">Inactive</span></>
                      )}
                    </button>
                  </td>
                  <td>
                    {u.force_password_change ? (
                      <span className="badge-warning text-xs">Yes</span>
                    ) : (
                      <span className="badge-gray text-xs">No</span>
                    )}
                  </td>
                  <td>
                    <div className="flex gap-1.5">
                      <button
                        onClick={() => setModal({ type: 'edit', user: u })}
                        className="btn-secondary btn-sm"
                        title="Edit"
                      >
                        <Edit2 size={13} />
                      </button>
                      <button
                        onClick={() => setModal({ type: 'reset', user: u })}
                        className="btn-secondary btn-sm"
                        title="Reset Password"
                      >
                        <Key size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {(modal?.type === 'add' || modal?.type === 'edit') && (
        <UserModal item={modal.user} onClose={() => setModal(null)} />
      )}
      {modal?.type === 'reset' && (
        <ResetPasswordModal user={modal.user} onClose={() => setModal(null)} />
      )}
    </div>
  )
}

