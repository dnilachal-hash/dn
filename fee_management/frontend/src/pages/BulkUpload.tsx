import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import {
  Upload, Download, CheckCircle, XCircle, AlertCircle, Loader2, RotateCcw, Check
} from 'lucide-react'
import client from '../api/client'
import { format, parseISO } from 'date-fns'

const STEPS = ['Upload File', 'Preview & Validate', 'Confirm']

const STATUS_BADGE: Record<string, string> = {
  PENDING: 'badge-warning',
  PROCESSING: 'badge-info',
  COMPLETED: 'badge-success',
  FAILED: 'badge-danger',
  ROLLED_BACK: 'badge-gray',
}

export default function BulkUpload() {
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [step, setStep] = useState(0)
  const [file, setFile] = useState<File | null>(null)
  const [sessionId, setSessionId] = useState<number | null>(null)
  const [preview, setPreview] = useState<any>(null)
  const [committing, setCommitting] = useState(false)

  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ['bulk-upload-sessions'],
    queryFn: () => client.get('/bulk-upload/sessions/').then((r) => r.data),
  })

  const handleDownloadTemplate = async () => {
    try {
      const res = await client.get('/bulk-upload/template', { responseType: 'blob' })
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = 'student_import_template.xlsx'
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast.error('Failed to download template')
    }
  }

  const uploadMutation = useMutation({
    mutationFn: async (f: File) => {
      const form = new FormData()
      form.append('file', f)
      return client.post('/bulk-upload/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then((r) => r.data)
    },
    onSuccess: (data) => {
      setPreview(data)
      setSessionId(data.session_id)
      setStep(1)
      toast.success('File uploaded and validated!')
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Upload failed'),
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    setFile(f)
  }

  const handleUpload = () => {
    if (!file) { toast.error('Please select a file'); return }
    uploadMutation.mutate(file)
  }

  const handleCommit = async () => {
    if (!sessionId) return
    setCommitting(true)
    try {
      await client.post(`/bulk-upload/sessions/${sessionId}/commit`)
      toast.success('Bulk upload committed successfully!')
      qc.invalidateQueries({ queryKey: ['bulk-upload-sessions'] })
      setStep(2)
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Commit failed')
    } finally {
      setCommitting(false)
    }
  }

  const handleRollback = async (sid: number) => {
    if (!window.confirm('Are you sure you want to rollback this upload? All imported records will be deleted.')) return
    try {
      await client.post(`/bulk-upload/sessions/${sid}/rollback`)
      toast.success('Rollback completed')
      qc.invalidateQueries({ queryKey: ['bulk-upload-sessions'] })
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Rollback failed')
    }
  }

  const handleDownloadErrors = async () => {
    if (!sessionId) return
    try {
      const res = await client.get(`/bulk-upload/sessions/${sessionId}/errors`, { responseType: 'blob' })
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = 'failed_rows.xlsx'
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast.error('Failed to download error file')
    }
  }

  const rows = preview?.rows || []
  const successCount = rows.filter((r: any) => r.status === 'SUCCESS').length
  const failedCount = rows.filter((r: any) => r.status === 'FAILED').length
  const dupCount = rows.filter((r: any) => r.status === 'DUPLICATE').length

  const sessions = history?.items || history || []

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Bulk Upload</h1>
        <button onClick={handleDownloadTemplate} className="btn-secondary">
          <Download size={15} /> Download Template
        </button>
      </div>

      {/* Stepper */}
      <div className="flex items-center gap-0 mb-8">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              step === i ? 'bg-indigo-600 text-white' : step > i ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-500'
            }`}>
              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                step > i ? 'bg-emerald-500 text-white' : step === i ? 'bg-white text-indigo-600' : 'bg-gray-300 text-gray-600'
              }`}>
                {step > i ? <Check size={12} /> : i + 1}
              </span>
              {s}
            </div>
            {i < STEPS.length - 1 && (
              <div className={`h-0.5 w-8 ${step > i ? 'bg-emerald-400' : 'bg-gray-200'}`} />
            )}
          </div>
        ))}
      </div>

      {/* Step 1: Upload */}
      {step === 0 && (
        <div className="card max-w-xl">
          <h2 className="card-title mb-4">Upload Student Excel File</h2>
          <div
            className="border-2 border-dashed border-gray-300 rounded-xl p-10 text-center hover:border-indigo-400 transition-colors cursor-pointer"
            onClick={() => fileRef.current?.click()}
          >
            <Upload size={36} className="mx-auto text-gray-400 mb-3" />
            <p className="text-gray-600 font-medium mb-1">Click to select file</p>
            <p className="text-sm text-gray-400">Supports .xlsx and .xls files</p>
            {file && (
              <div className="mt-3 inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 rounded-lg px-3 py-1.5 text-sm">
                <CheckCircle size={14} />
                {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </div>
            )}
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".xlsx,.xls"
            className="hidden"
            onChange={handleFileChange}
          />

          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
            <strong>Instructions:</strong>
            <ul className="mt-1 space-y-0.5 list-disc list-inside">
              <li>Download the template above and fill in student data</li>
              <li>Do not modify the column headers</li>
              <li>Required fields: Full Name, Course, Batch</li>
              <li>Dates should be in DD/MM/YYYY format</li>
            </ul>
          </div>

          <div className="flex gap-3 mt-5">
            <button
              onClick={handleUpload}
              disabled={!file || uploadMutation.isPending}
              className="btn-primary flex-1"
            >
              {uploadMutation.isPending ? (
                <><Loader2 size={16} className="animate-spin" /> Uploading & Validating…</>
              ) : (
                <><Upload size={16} /> Upload & Validate</>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Preview */}
      {step === 1 && preview && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-3 gap-4">
            <div className="card bg-emerald-50 border-emerald-200 text-center py-4">
              <div className="text-3xl font-bold text-emerald-700">{successCount}</div>
              <div className="text-sm text-emerald-600">Ready to Import</div>
            </div>
            <div className="card bg-red-50 border-red-200 text-center py-4">
              <div className="text-3xl font-bold text-red-700">{failedCount}</div>
              <div className="text-sm text-red-600">Errors</div>
            </div>
            <div className="card bg-amber-50 border-amber-200 text-center py-4">
              <div className="text-3xl font-bold text-amber-700">{dupCount}</div>
              <div className="text-sm text-amber-600">Duplicates</div>
            </div>
          </div>

          {failedCount > 0 && (
            <button onClick={handleDownloadErrors} className="btn-secondary">
              <Download size={15} /> Download Failed Rows
            </button>
          )}

          {/* Preview table */}
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-200 font-semibold text-gray-700">
              Row Preview ({rows.length} rows)
            </div>
            <div className="overflow-x-auto max-h-80 overflow-y-auto">
              <table className="tbl">
                <thead>
                  <tr>
                    <th>Row</th>
                    <th>Name</th>
                    <th>Admission No</th>
                    <th>Course</th>
                    <th>Status</th>
                    <th>Error</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r: any, i: number) => (
                    <tr key={i}>
                      <td className="font-mono text-xs">{r.row_number || i + 2}</td>
                      <td>{r.full_name || '-'}</td>
                      <td>{r.admission_number || '-'}</td>
                      <td>{r.course || '-'}</td>
                      <td>
                        <span className={
                          r.status === 'SUCCESS' ? 'badge-success' :
                          r.status === 'DUPLICATE' ? 'badge-warning' : 'badge-danger'
                        }>
                          {r.status}
                        </span>
                      </td>
                      <td className="text-red-600 text-xs max-w-[200px] truncate">{r.error || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={() => { setStep(0); setFile(null); setPreview(null) }} className="btn-secondary">
              Back
            </button>
            <button
              onClick={handleCommit}
              disabled={successCount === 0 || committing}
              className="btn-success"
            >
              {committing ? <><Loader2 size={16} className="animate-spin" /> Committing…</> : (
                <><CheckCircle size={16} /> Commit {successCount} Students</>
              )}
            </button>
            {sessionId && (
              <button onClick={() => handleRollback(sessionId)} className="btn-danger">
                Rollback / Discard
              </button>
            )}
          </div>
        </div>
      )}

      {/* Step 3: Done */}
      {step === 2 && (
        <div className="card max-w-md text-center py-10">
          <CheckCircle size={48} className="mx-auto text-emerald-500 mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Upload Complete!</h2>
          <p className="text-gray-600 mb-6">
            {successCount} student(s) imported successfully.
            {failedCount > 0 && ` ${failedCount} row(s) had errors.`}
          </p>
          <button onClick={() => { setStep(0); setFile(null); setPreview(null); setSessionId(null) }} className="btn-primary">
            Upload Another File
          </button>
        </div>
      )}

      {/* History */}
      <div className="card mt-8">
        <h2 className="card-title mb-4">Upload History</h2>
        {historyLoading ? (
          <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div>
        ) : (
          <table className="tbl">
            <thead>
              <tr>
                <th>Date</th>
                <th>Filename</th>
                <th>Total Rows</th>
                <th>Success</th>
                <th>Failed</th>
                <th>Status</th>
                <th>Uploaded By</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sessions.length === 0 && (
                <tr><td colSpan={8} className="text-center text-gray-400 py-8">No upload history</td></tr>
              )}
              {sessions.map((s: any) => (
                <tr key={s.id}>
                  <td className="whitespace-nowrap">{s.created_at ? format(parseISO(s.created_at), 'dd/MM/yyyy HH:mm') : '-'}</td>
                  <td className="max-w-[150px] truncate text-sm">{s.filename}</td>
                  <td>{s.total_rows}</td>
                  <td className="text-emerald-700 font-medium">{s.success_count}</td>
                  <td className="text-red-600 font-medium">{s.failed_count}</td>
                  <td><span className={STATUS_BADGE[s.status] || 'badge-gray'}>{s.status}</span></td>
                  <td>{s.uploaded_by_name || '-'}</td>
                  <td>
                    {s.status === 'COMPLETED' && (
                      <button
                        onClick={() => handleRollback(s.id)}
                        className="btn-danger btn-sm"
                        title="Rollback"
                      >
                        <RotateCcw size={13} /> Rollback
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
