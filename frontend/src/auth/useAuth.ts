import { createContext, useContext } from 'react'
import type { User } from '../api/types'

export interface AuthState {
  /** The logged-in user, or null when logged out */
  user: User | null
  /** True while a saved token is being checked on first load */
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthState | null>(null)

export function useAuth(): AuthState {
  const auth = useContext(AuthContext)
  if (!auth) throw new Error('useAuth must be used inside <AuthProvider>')
  return auth
}
