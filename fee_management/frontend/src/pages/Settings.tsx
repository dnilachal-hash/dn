import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import {
  Building2, FileText, CreditCard, Save, Loader2, Upload, Plus, ToggleLeft, ToggleRight, X, Check
} from 'lucide-react'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'

const TABS = ['Organisation', 'Receipt Format', 'Payment Modes']

// ─── Organisation Tab ─────────────────────────────────────────────────────────
function OrganisationTab() {
  const qc = useQueryClient()
  const logoRef = useRef<HTMLInputElement>(null)
  const [logoFile, setLogoFile] = useState<File | null>(null)
  const [logoPreview, setLogoPreview] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['settings-org'],
    queryFn: () => client.get('/settings/organisation').then((r) => r.data),
  })

  const { register, handleSubmit, reset, formState: { errors } } = useForm({
    defaultValues: {
      college_name: '',
      address: '',
      phone: '',
      email: '',
      website: '',
      gstin: '',
      receipt_header: '',
      receipt_footer: '',
    },
  })

  // Reset form when data loads
  useEffect(() => {
    if (data) {
      reset({
        college_name: data.college_name || '',
        address: data.address || '',
        phone: data.phone || '',
        email: data.email || '',
        website: data.website || '',
        gstin: data.gstin || '',
        receipt_header: data.receipt_header || '',
        receipt_footer: data.receipt_footer || '',
      })
    }
  }, [data])

  const mutation = useMutation({
    mutationFn: async (formData: any) => {
      await client.put('/settings/organisation', formData)
      if (logoFile) {
        const fd = new FormData()
        fd.append('logo', logoFile)
        await client.post('/settings/logo', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['settings-org'] })
      toast.success('Organisation settings saved!')
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed to save'),
  })

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    setLogoFile(f)
    const reader = new FileReader()
    reader.onload = (ev) => setLogoPreview(ev.target?.result as string)
    reader.readAsDataURL(f)
  }

  if (isLoading) return <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div>

  return (
    <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="md:col-span-2">
          <label className="label">College Name *</label>
          <input {...register('college_name', { required: 'Required' })} className={`input ${errors.college_name ? 'input-error' : ''}`} placeholder="Full name of the college" />
        </div>
        <div className="md:col-span-2">
          <label className="label">Address</label>
          <textarea {...register('address')} className="input" rows={2} placeholder="College address" />
        </div>
        <div>
          <label className="label">Phone</label>
          <input {...register('phone')} className="input" placeholder="+91 XXXXX XXXXX" />
        </div>
        <div>
          <label className="label">Email</label>
          <input {...register('email')} type="email" className="input" placeholder="college@example.com" />
        </div>
        <div>
          <label className="label">Website</label>
          <input {...register('website')} className="input" placeholder="https://www.college.edu" />
        </div>
        <div>
          <label className="label">GSTIN</label>
          <input {...register('gstin')} className="input" placeholder="GST Identification Number" />
        </div>
        <div className="md:col-span-2">
          <label className="label">Receipt Header Text</label>
          <textarea {...register('receipt_header')} className="input" rows={2} placeholder="Text to appear at the top of every receipt" />
        </div>
        <div className="md:col-span-2">
          <label className="label">Receipt Footer Text</label>
          <textarea {...register('receipt_footer')} className="input" rows={2} placeholder="Text to appear at the bottom of every receipt" />
        </div>

        {/* Logo upload */}
        <div className="md:col-span-2">
          <label className="label">College Logo</label>
          <div className="flex items-center gap-4">
            {(logoPreview || data?.logo_url) && (
              <img
                src={logoPreview || data?.logo_url}
                alt="Logo"
                className="w-16 h-16 object-contain border rounded-lg"
              />
            )}
            <button
              type="button"
              onClick={() => logoRef.current?.click()}
              className="btn-secondary"
            >
              <Upload size={15} /> Upload Logo
            </button>
            {logoFile && <span className="text-sm text-gray-600">{logoFile.name}</span>}
          </div>
          <input ref={logoRef} type="file" accept="image/*" className="hidden" onChange={handleLogoChange} />
          <p className="text-xs text-gray-400 mt-1">PNG or JPG, recommended 200x100px</p>
        </div>
      </div>

      <div className="mt-6 pt-4 border-t">
        <button type="submit" disabled={mutation.isPending} className="btn-primary">
          {mutation.isPending ? <><Loader2 size={15} className="animate-spin" /> Saving…</> : <><Save size={15} /> Save Organisation Settings</>}
        </button>
      </div>
    </form>
  )
}

// ─── Receipt Format Tab ───────────────────────────────────────────────────────
function ReceiptFormatTab() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['settings-receipt'],
    queryFn: () => client.get('/settings/receipt-format').then((r) => r.data),
  })
  const { data: fys } = useQuery({ queryKey: ['financial-years'], queryFn: () => client.get('/financial-years/').then((r) => r.data) })
  const fyList = fys?.items || fys || []
  const activeFy = fyList.find((fy: any) => fy.is_active)

  const { register, handleSubmit, watch } = useForm({
    defaultValues: {
      numbering_format: data?.numbering_format || 'SIMPLE',
      prefix: data?.prefix || '',
      padding: data?.padding || 4,
      include_fy: data?.include_fy || false,
      active_financial_year_id: data?.active_financial_year_id?.toString() || activeFy?.id?.toString() || '',
    },
  })

  const watchFormat = watch('numbering_format')

  const mutation = useMutation({
    mutationFn: (d: any) => client.put('/settings/receipt-format', {
      ...d,
      padding: Number(d.padding),
      active_financial_year_id: d.active_financial_year_id ? Number(d.active_financial_year_id) : null,
    }).then((r) => r.data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['settings-receipt'] }); toast.success('Receipt format saved!') },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed'),
  })

  if (isLoading) return <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div>

  return (
    <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div>
          <label className="label">Numbering Format</label>
          <select {...register('numbering_format')} className="input">
            <option value="SIMPLE">Simple (e.g., 0001)</option>
            <option value="PREFIXED">Prefixed (e.g., HMC-2025/0001)</option>
            <option value="FY_PREFIXED">FY Prefixed (e.g., 2025-26/0001)</option>
          </select>
        </div>

        {watchFormat !== 'SIMPLE' && (
          <div>
            <label className="label">Custom Prefix</label>
            <input {...register('prefix')} className="input" placeholder="e.g., HMC or leave blank for FY" />
          </div>
        )}

        <div>
          <label className="label">Number Padding (digits)</label>
          <input {...register('padding', { valueAsNumber: true })} type="number" min={1} max={10} className="input" />
          <p className="text-xs text-gray-400 mt-1">e.g., 4 = 0001, 0002...</p>
        </div>

        <div className="flex items-center gap-2 mt-6">
          <input {...register('include_fy')} type="checkbox" id="inc_fy" className="w-4 h-4 text-indigo-600 rounded" />
          <label htmlFor="inc_fy" className="text-sm font-medium text-gray-700">Include FY in receipt number</label>
        </div>

        <div>
          <label className="label">Active Financial Year (for new receipts)</label>
          <select {...register('active_financial_year_id')} className="input">
            <option value="">Use system default</option>
            {fyList.map((fy: any) => (
              <option key={fy.id} value={fy.id}>{fy.name}{fy.is_active ? ' (Active)' : ''}</option>
            ))}
          </select>
        </div>

        {/* Preview */}
        <div className="md:col-span-2 bg-indigo-50 border border-indigo-200 rounded-lg p-4">
          <div className="text-sm font-medium text-indigo-800 mb-1">Preview</div>
          <div className="font-mono text-lg text-indigo-700">
            {watchFormat === 'SIMPLE' && '0001'}
            {watchFormat === 'PREFIXED' && `${watch('prefix') || 'HMC'}-${'0'.repeat(Math.max(0, (watch('padding') || 4) - 1))}1`}
            {watchFormat === 'FY_PREFIXED' && `2025-26/${'0'.repeat(Math.max(0, (watch('padding') || 4) - 1))}1`}
          </div>
        </div>
      </div>

      <div className="mt-6 pt-4 border-t">
        <button type="submit" disabled={mutation.isPending} className="btn-primary">
          {mutation.isPending ? <><Loader2 size={15} className="animate-spin" /> Saving…</> : <><Save size={15} /> Save Receipt Format</>}
        </button>
      </div>
    </form>
  )
}

// ─── Payment Modes Tab ─────────────────────────────────────────────────────────
function PaymentModesTab() {
  const qc = useQueryClient()
  const [showAdd, setShowAdd] = useState(false)
  const [newMode, setNewMode] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['settings-payment-modes'],
    queryFn: () => client.get('/settings/payment-modes').then((r) => r.data),
  })

  const toggleMutation = useMutation({
    mutationFn: (m: any) =>
      client.patch(`/settings/payment-modes/${m.id || m.value}`, { is_active: !m.is_active }).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['settings-payment-modes'] }),
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed'),
  })

  const addMutation = useMutation({
    mutationFn: () =>
      client.post('/settings/payment-modes', { name: newMode, value: newMode.toUpperCase().replace(/\s+/g, '_'), is_active: true }).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['settings-payment-modes'] })
      setNewMode('')
      setShowAdd(false)
      toast.success('Payment mode added!')
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed'),
  })

  const modes = data?.items || data || []

  if (isLoading) return <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div>

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <span className="text-sm text-gray-500">{modes.length} payment mode(s)</span>
        <button onClick={() => setShowAdd(!showAdd)} className="btn-secondary btn-sm">
          <Plus size={14} /> Add Mode
        </button>
      </div>

      {showAdd && (
        <div className="flex gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
          <input
            className="input flex-1"
            placeholder="New payment mode name (e.g., RTGS)"
            value={newMode}
            onChange={(e) => setNewMode(e.target.value)}
          />
          <button onClick={() => addMutation.mutate()} disabled={!newMode.trim() || addMutation.isPending} className="btn-primary btn-sm">
            {addMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
            Add
          </button>
          <button onClick={() => setShowAdd(false)} className="btn-secondary btn-sm"><X size={14} /></button>
        </div>
      )}

      <table className="tbl">
        <thead><tr><th>Payment Mode</th><th>Value/Code</th><th>Status</th><th>Toggle</th></tr></thead>
        <tbody>
          {modes.map((m: any) => (
            <tr key={m.id || m.value}>
              <td className="font-medium">{m.name || m.label}</td>
              <td className="font-mono text-sm">{m.value || m.code}</td>
              <td><span className={m.is_active !== false ? 'badge-success' : 'badge-danger'}>{m.is_active !== false ? 'Active' : 'Inactive'}</span></td>
              <td>
                <button onClick={() => toggleMutation.mutate(m)} className="flex items-center gap-1">
                  {m.is_active !== false ? (
                    <ToggleRight size={22} className="text-emerald-500" />
                  ) : (
                    <ToggleLeft size={22} className="text-gray-400" />
                  )}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function Settings() {
  const { user } = useAuthStore()
  const [tab, setTab] = useState(0)

  if (user?.role !== 'super_admin') {
    return (
      <div className="card text-center py-12 text-gray-500">
        Access restricted to super administrators only.
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
      </div>

      <div className="tabs">
        {TABS.map((t, i) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(i)}
            className={`tab flex items-center gap-2 ${tab === i ? 'tab-active' : ''}`}
          >
            {i === 0 && <Building2 size={14} />}
            {i === 1 && <FileText size={14} />}
            {i === 2 && <CreditCard size={14} />}
            {t}
          </button>
        ))}
      </div>

      <div className="card rounded-tl-none">
        {tab === 0 && <OrganisationTab />}
        {tab === 1 && <ReceiptFormatTab />}
        {tab === 2 && <PaymentModesTab />}
      </div>
    </div>
  )
}
