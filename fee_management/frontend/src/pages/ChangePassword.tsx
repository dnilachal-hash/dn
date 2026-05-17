import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Building2, Eye, EyeOff, Loader2, CheckCircle, XCircle } from 'lucide-react'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'

interface ChangePasswordForm {
  current_password: string
  new_password: string
  confirm_password: string
}

const PASSWORD_RULES = [
  { label: 'At least 8 characters', test: (p: string) => p.length >= 8 },
  { label: 'At least one uppercase letter', test: (p: string) => /[A-Z]/.test(p) },
  { label: 'At least one digit', test: (p: string) => /\d/.test(p) },
  { label: 'At least one special character', test: (p: string) => /[^A-Za-z0-9]/.test(p) },
]

export default function ChangePassword() {
  const navigate = useNavigate()
  const { forcePasswordChange, user, clearAuth } = useAuthStore()
  const [showCurrent, setShowCurrent] = useState(false)
  const [showNew, setShowNew] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [newPwd, setNewPwd] = useState('')

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ChangePasswordForm>()

  const watchedNew = watch('new_password', '')

  const onSubmit = async (data: ChangePasswordForm) => {
    if (data.new_password !== data.confirm_password) {
      toast.error('Passwords do not match')
      return
    }
    const allPassed = PASSWORD_RULES.every((r) => r.test(data.new_password))
    if (!allPassed) {
      toast.error('Password does not meet requirements')
      return
    }
    setLoading(true)
    try {
      await client.post('/auth/change-password', {
        current_password: data.current_password,
        new_password: data.new_password,
      })
      toast.success('Password changed successfully!')
      if (forcePasswordChange) {
        // Update store — reload auth so forcePasswordChange = false
        clearAuth()
        navigate('/login')
        toast('Please log in with your new password.')
      } else {
        navigate('/dashboard')
      }
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'Failed to change password.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-indigo-900 to-indigo-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white/10 backdrop-blur rounded-2xl mb-4">
            <Building2 size={32} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Change Password</h1>
          {forcePasswordChange && (
            <p className="text-amber-300 text-sm mt-2 bg-amber-900/30 border border-amber-700/40 rounded-lg px-4 py-2">
              You must change your password before continuing.
            </p>
          )}
          {!forcePasswordChange && (
            <p className="text-indigo-300 text-sm mt-1">Update your account password</p>
          )}
        </div>

        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label className="label">Current Password</label>
              <div className="relative">
                <input
                  {...register('current_password', { required: 'Current password is required' })}
                  type={showCurrent ? 'text' : 'password'}
                  className={`input pr-10 ${errors.current_password ? 'input-error' : ''}`}
                  placeholder="Enter current password"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrent(!showCurrent)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showCurrent ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.current_password && (
                <p className="text-red-500 text-xs mt-1">{errors.current_password.message}</p>
              )}
            </div>

            <div>
              <label className="label">New Password</label>
              <div className="relative">
                <input
                  {...register('new_password', { required: 'New password is required' })}
                  type={showNew ? 'text' : 'password'}
                  className={`input pr-10 ${errors.new_password ? 'input-error' : ''}`}
                  placeholder="Enter new password"
                  onChange={(e) => setNewPwd(e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => setShowNew(!showNew)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showNew ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.new_password && (
                <p className="text-red-500 text-xs mt-1">{errors.new_password.message}</p>
              )}

              {/* Password strength rules */}
              {watchedNew.length > 0 && (
                <div className="mt-2 space-y-1">
                  {PASSWORD_RULES.map((rule) => {
                    const passed = rule.test(watchedNew)
                    return (
                      <div key={rule.label} className="flex items-center gap-2 text-xs">
                        {passed ? (
                          <CheckCircle size={12} className="text-emerald-500 shrink-0" />
                        ) : (
                          <XCircle size={12} className="text-red-400 shrink-0" />
                        )}
                        <span className={passed ? 'text-emerald-700' : 'text-red-500'}>
                          {rule.label}
                        </span>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            <div>
              <label className="label">Confirm New Password</label>
              <div className="relative">
                <input
                  {...register('confirm_password', { required: 'Please confirm your password' })}
                  type={showConfirm ? 'text' : 'password'}
                  className={`input pr-10 ${errors.confirm_password ? 'input-error' : ''}`}
                  placeholder="Confirm new password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.confirm_password && (
                <p className="text-red-500 text-xs mt-1">{errors.confirm_password.message}</p>
              )}
            </div>

            <div className="flex gap-3 pt-2">
              {!forcePasswordChange && (
                <button
                  type="button"
                  onClick={() => navigate(-1)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
              )}
              <button
                type="submit"
                disabled={loading}
                className="btn-primary flex-1 py-2.5"
              >
                {loading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Saving…
                  </>
                ) : (
                  'Change Password'
                )}
              </button>
            </div>
          </form>
        </div>

        <p className="text-center text-indigo-300 text-xs mt-6">
          Logged in as <span className="font-medium">{user?.full_name}</span>
        </p>
      </div>
    </div>
  )
}
