import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, X, Loader2, Check } from 'lucide-react'
import toast from 'react-hot-toast'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'
import { useForm } from 'react-hook-form'

const TABS = ['Courses', 'Batches', 'Academic Sessions', 'Student Categories']

// Generic confirm delete modal
function ConfirmDelete({ name, onConfirm, onCancel }: { name: string; onConfirm: () => void; onCancel: () => void }) {
  return (
    <div className="modal-backdrop">
      <div className="modal max-w-sm">
        <div className="modal-header">
          <h3 className="modal-title text-red-700">Confirm Delete</h3>
          <button onClick={onCancel} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <div className="modal-body">
          <p className="text-gray-700">Are you sure you want to delete <strong>{name}</strong>?</p>
          <p className="text-sm text-red-600 mt-2">This action cannot be undone.</p>
        </div>
        <div className="modal-footer">
          <button onClick={onCancel} className="btn-secondary">Cancel</button>
          <button onClick={onConfirm} className="btn-danger">Delete</button>
        </div>
      </div>
    </div>
  )
}

// ─── Courses Tab ────────────────────────────────────────────────────────────
function CourseModal({ item, onClose }: { item?: any; onClose: () => void }) {
  const qc = useQueryClient()
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      name: item?.name || '',
      code: item?.code || '',
      duration_years: item?.duration_years || 4,
      description: item?.description || '',
    },
  })
  const mutation = useMutation({
    mutationFn: (data: any) =>
      item
        ? client.put(`/courses/${item.id}`, data).then((r) => r.data)
        : client.post('/courses/', data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['courses-list'] })
      toast.success(item ? 'Course updated!' : 'Course created!')
      onClose()
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed to save'),
  })
  return (
    <div className="modal-backdrop">
      <div className="modal max-w-md">
        <div className="modal-header">
          <h3 className="modal-title">{item ? 'Edit Course' : 'Add Course'}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
          <div className="modal-body space-y-4">
            <div>
              <label className="label">Course Name *</label>
              <input {...register('name', { required: 'Required' })} className={`input ${errors.name ? 'input-error' : ''}`} />
              {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name.message as string}</p>}
            </div>
            <div>
              <label className="label">Course Code</label>
              <input {...register('code')} className="input" placeholder="e.g. BHMS" />
            </div>
            <div>
              <label className="label">Duration (Years)</label>
              <input {...register('duration_years', { valueAsNumber: true })} type="number" min={1} max={10} className="input" />
            </div>
            <div>
              <label className="label">Description</label>
              <textarea {...register('description')} className="input" rows={2} />
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

function CoursesTab() {
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'super_admin' || user?.role === 'accounts_user'
  const [modal, setModal] = useState<any>(null) // null | {editing?: item}
  const [deleteTarget, setDeleteTarget] = useState<any>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['courses-list'],
    queryFn: () => client.get('/courses/').then((r) => r.data),
  })
  const deleteMutation = useMutation({
    mutationFn: (id: number) => client.delete(`/courses/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['courses-list'] }); toast.success('Deleted!') },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Delete failed'),
  })

  const items = data?.items || data || []
  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <span className="text-sm text-gray-500">{items.length} course(s)</span>
        {isAdmin && (
          <button onClick={() => setModal({})} className="btn-primary btn-sm">
            <Plus size={14} /> Add Course
          </button>
        )}
      </div>
      {isLoading ? (
        <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div>
      ) : (
        <table className="tbl">
          <thead><tr><th>Name</th><th>Code</th><th>Duration</th><th>Description</th>{isAdmin && <th>Actions</th>}</tr></thead>
          <tbody>
            {items.length === 0 && <tr><td colSpan={5} className="text-center text-gray-400 py-8">No courses found</td></tr>}
            {items.map((c: any) => (
              <tr key={c.id}>
                <td className="font-medium">{c.name}</td>
                <td>{c.code || '-'}</td>
                <td>{c.duration_years ? `${c.duration_years} years` : '-'}</td>
                <td className="max-w-[200px] truncate text-gray-500">{c.description || '-'}</td>
                {isAdmin && (
                  <td>
                    <div className="flex gap-2">
                      <button onClick={() => setModal({ editing: c })} className="btn-secondary btn-sm"><Edit2 size={13} /></button>
                      <button onClick={() => setDeleteTarget(c)} className="btn-danger btn-sm"><Trash2 size={13} /></button>
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {modal !== null && (
        <CourseModal item={modal.editing} onClose={() => setModal(null)} />
      )}
      {deleteTarget && (
        <ConfirmDelete
          name={deleteTarget.name}
          onConfirm={() => { deleteMutation.mutate(deleteTarget.id); setDeleteTarget(null) }}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  )
}

// ─── Batches Tab ─────────────────────────────────────────────────────────────
function BatchModal({ item, courses, onClose }: { item?: any; courses: any[]; onClose: () => void }) {
  const qc = useQueryClient()
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      name: item?.name || '',
      course_id: item?.course_id?.toString() || '',
      start_year: item?.start_year || new Date().getFullYear(),
      end_year: item?.end_year || new Date().getFullYear() + 4,
      is_active: item?.is_active !== false,
    },
  })
  const mutation = useMutation({
    mutationFn: (data: any) =>
      item
        ? client.put(`/courses/batches/${item.id}`, { ...data, course_id: Number(data.course_id) }).then((r) => r.data)
        : client.post('/courses/batches/', { ...data, course_id: Number(data.course_id) }).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['batches-list'] })
      toast.success(item ? 'Batch updated!' : 'Batch created!')
      onClose()
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed to save'),
  })
  return (
    <div className="modal-backdrop">
      <div className="modal max-w-md">
        <div className="modal-header">
          <h3 className="modal-title">{item ? 'Edit Batch' : 'Add Batch'}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
          <div className="modal-body space-y-4">
            <div>
              <label className="label">Batch Name *</label>
              <input {...register('name', { required: 'Required' })} className={`input ${errors.name ? 'input-error' : ''}`} placeholder="e.g. 2021-2025" />
            </div>
            <div>
              <label className="label">Course *</label>
              <select {...register('course_id', { required: 'Required' })} className={`input ${errors.course_id ? 'input-error' : ''}`}>
                <option value="">Select Course</option>
                {courses.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Start Year</label>
                <input {...register('start_year', { valueAsNumber: true })} type="number" className="input" />
              </div>
              <div>
                <label className="label">End Year</label>
                <input {...register('end_year', { valueAsNumber: true })} type="number" className="input" />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input {...register('is_active')} type="checkbox" id="batch_active" className="w-4 h-4 text-indigo-600 rounded" />
              <label htmlFor="batch_active" className="text-sm font-medium text-gray-700">Active</label>
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

function BatchesTab() {
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'super_admin' || user?.role === 'accounts_user'
  const [modal, setModal] = useState<any>(null)
  const [deleteTarget, setDeleteTarget] = useState<any>(null)

  const { data: courses } = useQuery({ queryKey: ['courses-list'], queryFn: () => client.get('/courses/').then((r) => r.data) })
  const { data, isLoading } = useQuery({ queryKey: ['batches-list', ''], queryFn: () => client.get('/courses/batches/').then((r) => r.data) })
  const deleteMutation = useMutation({
    mutationFn: (id: number) => client.delete(`/courses/batches/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['batches-list'] }); toast.success('Deleted!') },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Delete failed'),
  })

  const items = data?.items || data || []
  const courseList = courses?.items || courses || []
  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <span className="text-sm text-gray-500">{items.length} batch(es)</span>
        {isAdmin && (
          <button onClick={() => setModal({})} className="btn-primary btn-sm"><Plus size={14} /> Add Batch</button>
        )}
      </div>
      {isLoading ? (
        <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div>
      ) : (
        <table className="tbl">
          <thead><tr><th>Batch Name</th><th>Course</th><th>Start Year</th><th>End Year</th><th>Status</th>{isAdmin && <th>Actions</th>}</tr></thead>
          <tbody>
            {items.length === 0 && <tr><td colSpan={6} className="text-center text-gray-400 py-8">No batches found</td></tr>}
            {items.map((b: any) => (
              <tr key={b.id}>
                <td className="font-medium">{b.name}</td>
                <td>{b.course_name || courseList.find((c: any) => c.id === b.course_id)?.name || '-'}</td>
                <td>{b.start_year || '-'}</td>
                <td>{b.end_year || '-'}</td>
                <td><span className={b.is_active !== false ? 'badge-success' : 'badge-danger'}>{b.is_active !== false ? 'Active' : 'Inactive'}</span></td>
                {isAdmin && (
                  <td><div className="flex gap-2">
                    <button onClick={() => setModal({ editing: b })} className="btn-secondary btn-sm"><Edit2 size={13} /></button>
                    <button onClick={() => setDeleteTarget(b)} className="btn-danger btn-sm"><Trash2 size={13} /></button>
                  </div></td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {modal !== null && <BatchModal item={modal.editing} courses={courseList} onClose={() => setModal(null)} />}
      {deleteTarget && <ConfirmDelete name={deleteTarget.name} onConfirm={() => { deleteMutation.mutate(deleteTarget.id); setDeleteTarget(null) }} onCancel={() => setDeleteTarget(null)} />}
    </div>
  )
}

// ─── Sessions Tab ─────────────────────────────────────────────────────────────
function SessionModal({ item, onClose }: { item?: any; onClose: () => void }) {
  const qc = useQueryClient()
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: { name: item?.name || '', start_date: item?.start_date?.slice(0,10) || '', end_date: item?.end_date?.slice(0,10) || '', is_active: item?.is_active !== false },
  })
  const mutation = useMutation({
    mutationFn: (data: any) => item ? client.put(`/courses/sessions/${item.id}`, data).then((r) => r.data) : client.post('/courses/sessions/', data).then((r) => r.data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['sessions-list'] }); toast.success(item ? 'Session updated!' : 'Session created!'); onClose() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed'),
  })
  return (
    <div className="modal-backdrop">
      <div className="modal max-w-md">
        <div className="modal-header">
          <h3 className="modal-title">{item ? 'Edit Session' : 'Add Session'}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
          <div className="modal-body space-y-4">
            <div>
              <label className="label">Session Name *</label>
              <input {...register('name', { required: 'Required' })} className={`input ${errors.name ? 'input-error' : ''}`} placeholder="e.g. 2024-25" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="label">Start Date</label><input {...register('start_date')} type="date" className="input" /></div>
              <div><label className="label">End Date</label><input {...register('end_date')} type="date" className="input" /></div>
            </div>
            <div className="flex items-center gap-2">
              <input {...register('is_active')} type="checkbox" id="sess_active" className="w-4 h-4 text-indigo-600 rounded" />
              <label htmlFor="sess_active" className="text-sm font-medium text-gray-700">Active</label>
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

function SessionsTab() {
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'super_admin'
  const [modal, setModal] = useState<any>(null)
  const [deleteTarget, setDeleteTarget] = useState<any>(null)
  const { data, isLoading } = useQuery({ queryKey: ['sessions-list'], queryFn: () => client.get('/courses/sessions/').then((r) => r.data) })
  const deleteMutation = useMutation({
    mutationFn: (id: number) => client.delete(`/courses/sessions/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['sessions-list'] }); toast.success('Deleted!') },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Delete failed'),
  })
  const items = data?.items || data || []
  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <span className="text-sm text-gray-500">{items.length} session(s)</span>
        {isAdmin && <button onClick={() => setModal({})} className="btn-primary btn-sm"><Plus size={14} /> Add Session</button>}
      </div>
      {isLoading ? <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div> : (
        <table className="tbl">
          <thead><tr><th>Session Name</th><th>Start Date</th><th>End Date</th><th>Status</th>{isAdmin && <th>Actions</th>}</tr></thead>
          <tbody>
            {items.length === 0 && <tr><td colSpan={5} className="text-center text-gray-400 py-8">No sessions found</td></tr>}
            {items.map((s: any) => (
              <tr key={s.id}>
                <td className="font-medium">{s.name}</td>
                <td>{s.start_date?.slice(0,10) || '-'}</td>
                <td>{s.end_date?.slice(0,10) || '-'}</td>
                <td><span className={s.is_active !== false ? 'badge-success' : 'badge-danger'}>{s.is_active !== false ? 'Active' : 'Inactive'}</span></td>
                {isAdmin && <td><div className="flex gap-2"><button onClick={() => setModal({ editing: s })} className="btn-secondary btn-sm"><Edit2 size={13} /></button><button onClick={() => setDeleteTarget(s)} className="btn-danger btn-sm"><Trash2 size={13} /></button></div></td>}
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {modal !== null && <SessionModal item={modal.editing} onClose={() => setModal(null)} />}
      {deleteTarget && <ConfirmDelete name={deleteTarget.name} onConfirm={() => { deleteMutation.mutate(deleteTarget.id); setDeleteTarget(null) }} onCancel={() => setDeleteTarget(null)} />}
    </div>
  )
}

// ─── Categories Tab ───────────────────────────────────────────────────────────
function CategoryModal({ item, onClose }: { item?: any; onClose: () => void }) {
  const qc = useQueryClient()
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: { name: item?.name || '', description: item?.description || '', is_active: item?.is_active !== false },
  })
  const mutation = useMutation({
    mutationFn: (data: any) => item ? client.put(`/courses/categories/${item.id}`, data).then((r) => r.data) : client.post('/courses/categories/', data).then((r) => r.data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['categories-list'] }); toast.success(item ? 'Category updated!' : 'Category created!'); onClose() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed'),
  })
  return (
    <div className="modal-backdrop">
      <div className="modal max-w-sm">
        <div className="modal-header">
          <h3 className="modal-title">{item ? 'Edit Category' : 'Add Category'}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
          <div className="modal-body space-y-4">
            <div>
              <label className="label">Category Name *</label>
              <input {...register('name', { required: 'Required' })} className={`input ${errors.name ? 'input-error' : ''}`} placeholder="e.g. General, OBC, SC/ST" />
            </div>
            <div>
              <label className="label">Description</label>
              <textarea {...register('description')} className="input" rows={2} />
            </div>
            <div className="flex items-center gap-2">
              <input {...register('is_active')} type="checkbox" id="cat_active" className="w-4 h-4 text-indigo-600 rounded" />
              <label htmlFor="cat_active" className="text-sm font-medium text-gray-700">Active</label>
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

function CategoriesTab() {
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'super_admin'
  const [modal, setModal] = useState<any>(null)
  const [deleteTarget, setDeleteTarget] = useState<any>(null)
  const { data, isLoading } = useQuery({ queryKey: ['categories-list'], queryFn: () => client.get('/courses/categories/').then((r) => r.data) })
  const deleteMutation = useMutation({
    mutationFn: (id: number) => client.delete(`/courses/categories/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['categories-list'] }); toast.success('Deleted!') },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Delete failed'),
  })
  const items = data?.items || data || []
  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <span className="text-sm text-gray-500">{items.length} categories</span>
        {isAdmin && <button onClick={() => setModal({})} className="btn-primary btn-sm"><Plus size={14} /> Add Category</button>}
      </div>
      {isLoading ? <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div> : (
        <table className="tbl">
          <thead><tr><th>Name</th><th>Description</th><th>Status</th>{isAdmin && <th>Actions</th>}</tr></thead>
          <tbody>
            {items.length === 0 && <tr><td colSpan={4} className="text-center text-gray-400 py-8">No categories found</td></tr>}
            {items.map((c: any) => (
              <tr key={c.id}>
                <td className="font-medium">{c.name}</td>
                <td className="text-gray-500">{c.description || '-'}</td>
                <td><span className={c.is_active !== false ? 'badge-success' : 'badge-danger'}>{c.is_active !== false ? 'Active' : 'Inactive'}</span></td>
                {isAdmin && <td><div className="flex gap-2"><button onClick={() => setModal({ editing: c })} className="btn-secondary btn-sm"><Edit2 size={13} /></button><button onClick={() => setDeleteTarget(c)} className="btn-danger btn-sm"><Trash2 size={13} /></button></div></td>}
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {modal !== null && <CategoryModal item={modal.editing} onClose={() => setModal(null)} />}
      {deleteTarget && <ConfirmDelete name={deleteTarget.name} onConfirm={() => { deleteMutation.mutate(deleteTarget.id); setDeleteTarget(null) }} onCancel={() => setDeleteTarget(null)} />}
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function Courses() {
  const [tab, setTab] = useState(0)
  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Courses & Academic Setup</h1>
      </div>
      <div className="tabs">
        {TABS.map((t, i) => (
          <button key={t} type="button" onClick={() => setTab(i)} className={`tab ${tab === i ? 'tab-active' : ''}`}>{t}</button>
        ))}
      </div>
      <div className="card rounded-tl-none">
        {tab === 0 && <CoursesTab />}
        {tab === 1 && <BatchesTab />}
        {tab === 2 && <SessionsTab />}
        {tab === 3 && <CategoriesTab />}
      </div>
    </div>
  )
}
