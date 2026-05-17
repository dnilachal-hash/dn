import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: number
  username: string
  full_name: string
  role: string
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  forcePasswordChange: boolean
  setAuth: (
    user: User,
    accessToken: string,
    refreshToken: string,
    forcePasswordChange: boolean
  ) => void
  clearAuth: () => void
  hasPermission: (perm: string) => boolean
}

const ROLE_PERMISSIONS: Record<string, string[]> = {
  super_admin: [
    'MANAGE_STUDENTS', 'VIEW_STUDENTS', 'COLLECT_FEES', 'VIEW_RECEIPTS',
    'VIEW_REPORTS', 'EXPORT_REPORTS', 'VIEW_FEE_STRUCTURES', 'VIEW_FEE_HEADS',
    'VIEW_COURSES', 'MANAGE_COURSES', 'MANAGE_FEE_HEADS', 'MANAGE_FEE_STRUCTURES',
    'MANAGE_FINANCIAL_YEARS', 'MANAGE_USERS', 'VIEW_AUDIT_LOGS', 'MANAGE_SETTINGS',
    'BACKUP_RESTORE', 'CANCEL_RECEIPTS', 'CORRECT_RECEIPTS', 'BULK_UPLOAD',
    'MANAGE_RECEIPTS',
  ],
  accounts_user: [
    'MANAGE_STUDENTS', 'VIEW_STUDENTS', 'COLLECT_FEES', 'VIEW_RECEIPTS',
    'VIEW_REPORTS', 'EXPORT_REPORTS', 'VIEW_FEE_STRUCTURES', 'VIEW_FEE_HEADS',
    'VIEW_COURSES', 'BULK_UPLOAD', 'CANCEL_RECEIPTS',
  ],
  viewer: [
    'VIEW_STUDENTS', 'VIEW_RECEIPTS', 'VIEW_REPORTS', 'VIEW_FEE_STRUCTURES',
    'VIEW_FEE_HEADS', 'VIEW_COURSES',
  ],
  auditor: [
    'VIEW_STUDENTS', 'VIEW_RECEIPTS', 'VIEW_REPORTS', 'VIEW_AUDIT_LOGS',
    'VIEW_FEE_STRUCTURES',
  ],
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      forcePasswordChange: false,

      setAuth: (user, accessToken, refreshToken, forcePasswordChange) =>
        set({ user, accessToken, refreshToken, forcePasswordChange }),

      clearAuth: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          forcePasswordChange: false,
        }),

      hasPermission: (perm: string) => {
        const { user } = get()
        if (!user) return false
        const perms = ROLE_PERMISSIONS[user.role] ?? []
        return perms.includes(perm)
      },
    }),
    {
      name: 'hmc-auth',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        forcePasswordChange: state.forcePasswordChange,
      }),
    }
  )
)
