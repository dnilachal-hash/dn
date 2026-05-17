import { useState, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Database, Download, Upload, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react'
import client from '../api/client'
import { format, parseISO } from 'date-fns'
import { useAuthStore } from '../store/authStore'

export default function Backup() {
  const { user } = useAuthStore()
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [restoreFile, setRestoreFile] = useState<File | null>(null)
  const [backingUp, setBackingUp] = useState(false)
  const [restoring, setRestoring] = useState(false)
  const [restoreConfirm, setRestoreConfirm] = useState(false)

  if (user?.role !== 'super_admin') {
    return (
      <div className="card text-center py-12 text-gray-500">
        Access restricted to super administrators only.
      </div>
    )
  }

  const { data: backups, isLoading } = useQuery({
    queryKey: ['backups'],
    queryFn: () => client.get('/settings/backups/').then((r) => r.data),
  })

  const handleCreateBackup = async () => {
    setBackingUp(true)
    try {
      const res = await client.post('/settings/backup', {}, { responseType: 'blob' })
      const disposition = res.headers['content-disposition']
      let filename = `backup_${format(new Date(), 'yyyyMMdd_HHmmss')}.zip`
      if (disposition) {
        const match = disposition.match(/filename="?([^"]+)"?/)
        if (match) filename = match[1]
      }
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Backup created and downloaded!')
      qc.invalidateQueries({ queryKey: ['backups'] })
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Backup failed')
    } finally {
      setBackingUp(false)
    }
  }

  const handleDownloadBackup = async (filename: string) => {
    try {
      const res = await client.get(`/settings/backups/${filename}`, { responseType: 'blob' })
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast.error('Download failed')
    }
  }

  const handleRestore = async () => {
    if (!restoreFile) { toast.error('Please select a backup file'); return }
    setRestoring(true)
    const form = new FormData()
    form.append('file', restoreFile)
    try {
      await client.post('/settings/restore', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      toast.success('Restore completed! Application will reload.')
      setTimeout(() => window.location.reload(), 2000)
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Restore failed')
    } finally {
      setRestoring(false)
      setRestoreConfirm(false)
    }
  }

  const backupList = backups?.items || backups || []

  return (
    <div className="max-w-4xl space-y-8">
      <div className="page-header">
        <h1 className="page-title">Backup & Restore</h1>
      </div>

      {/* Create Backup */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center">
            <Database size={20} className="text-indigo-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Create Backup</h2>
            <p className="text-sm text-gray-500">Download a complete backup of all application data</p>
          </div>
        </div>
        <button
          onClick={handleCreateBackup}
          disabled={backingUp}
          className="btn-primary"
        >
          {backingUp ? (
            <><Loader2 size={16} className="animate-spin" /> Creating Backup…</>
          ) : (
            <><Database size={16} /> Create Backup Now</>
          )}
        </button>
      </div>

      {/* Existing Backups */}
      <div className="card">
        <h2 className="card-title mb-4">Available Backups</h2>
        {isLoading ? (
          <div className="flex justify-center py-8"><div className="animate-spin w-7 h-7 border-4 border-indigo-600 border-t-transparent rounded-full" /></div>
        ) : (
          <table className="tbl">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Size</th>
                <th>Created At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {backupList.length === 0 && (
                <tr>
                  <td colSpan={4} className="text-center text-gray-400 py-8">
                    No backup files found
                  </td>
                </tr>
              )}
              {backupList.map((b: any) => (
                <tr key={b.filename}>
                  <td className="font-mono text-sm">{b.filename}</td>
                  <td className="text-sm text-gray-600">
                    {b.size_bytes
                      ? b.size_bytes > 1024 * 1024
                        ? `${(b.size_bytes / (1024 * 1024)).toFixed(1)} MB`
                        : `${(b.size_bytes / 1024).toFixed(0)} KB`
                      : b.size || '-'}
                  </td>
                  <td className="text-sm">
                    {b.created_at ? format(parseISO(b.created_at), 'dd/MM/yyyy HH:mm') : '-'}
                  </td>
                  <td>
                    <button
                      onClick={() => handleDownloadBackup(b.filename)}
                      className="btn-secondary btn-sm"
                    >
                      <Download size={13} /> Download
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Restore */}
      <div className="card border-2 border-red-100">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center">
            <Upload size={20} className="text-red-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-red-800">Restore from Backup</h2>
            <p className="text-sm text-red-600">Upload a backup file to restore the database</p>
          </div>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <div className="flex items-start gap-3">
            <AlertTriangle size={18} className="text-red-600 shrink-0 mt-0.5" />
            <div className="text-sm text-red-800">
              <strong>Warning:</strong> This will <strong>OVERWRITE all current data</strong> with the backup.
              A pre-restore backup will be created automatically before proceeding.
              This action cannot be undone.
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="label">Select Backup File</label>
            <div
              className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:border-red-400 transition-colors cursor-pointer"
              onClick={() => fileRef.current?.click()}
            >
              <Upload size={28} className="mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-gray-600 font-medium">Click to select backup file</p>
              <p className="text-xs text-gray-400">Supports .zip, .db, .sql files</p>
              {restoreFile && (
                <div className="mt-2 inline-flex items-center gap-2 bg-red-50 text-red-700 rounded-lg px-3 py-1.5 text-sm">
                  <CheckCircle size={14} />
                  {restoreFile.name}
                </div>
              )}
            </div>
            <input
              ref={fileRef}
              type="file"
              accept=".zip,.db,.sql,.bak"
              className="hidden"
              onChange={(e) => setRestoreFile(e.target.files?.[0] || null)}
            />
          </div>

          {!restoreConfirm ? (
            <button
              onClick={() => setRestoreConfirm(true)}
              disabled={!restoreFile}
              className="btn-danger"
            >
              <Upload size={16} /> Restore from Backup
            </button>
          ) : (
            <div className="bg-red-50 border border-red-300 rounded-lg p-4 space-y-3">
              <p className="text-red-800 font-medium text-sm">
                Are you absolutely sure? This will replace ALL current data with the backup:
                <strong> {restoreFile?.name}</strong>
              </p>
              <div className="flex gap-3">
                <button onClick={() => setRestoreConfirm(false)} className="btn-secondary">
                  No, Cancel
                </button>
                <button
                  onClick={handleRestore}
                  disabled={restoring}
                  className="btn-danger"
                >
                  {restoring ? (
                    <><Loader2 size={16} className="animate-spin" /> Restoring…</>
                  ) : (
                    'Yes, Restore Now'
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
