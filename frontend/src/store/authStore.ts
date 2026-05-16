import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface User {
  id: number;
  username: string;
  email?: string;
  full_name?: string;
  role: string;
  permissions: string[];
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  forcePasswordChange: boolean;
  setAuth: (data: { access_token: string; refresh_token: string; user: User; force_password_change: boolean }) => void;
  logout: () => void;
  hasPermission: (perm: string) => boolean;
  clearForcePasswordChange: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      forcePasswordChange: false,
      setAuth: (d) =>
        set({
          user: d.user,
          accessToken: d.access_token,
          refreshToken: d.refresh_token,
          forcePasswordChange: d.force_password_change,
        }),
      logout: () => set({ user: null, accessToken: null, refreshToken: null, forcePasswordChange: false }),
      hasPermission: (perm) => get().user?.permissions.includes(perm) ?? false,
      clearForcePasswordChange: () => set({ forcePasswordChange: false }),
    }),
    { name: "hmc-payroll-auth" },
  ),
);
