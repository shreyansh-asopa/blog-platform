import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { setUnauthorizedHandler, tokenStore } from '../api/client'
import { authApi } from '../api/endpoints'
import { AuthContext, type AuthState } from './useAuth'

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [token, setToken] = useState(tokenStore.get)

  // Who the token belongs to. The role comes from here, not from the token, because the
  // backend re-reads it on every request: a demoted admin loses the Admin link at once
  const me = useQuery({
    queryKey: ['me', token],
    queryFn: authApi.me,
    enabled: token !== null,
    retry: false,
    staleTime: 5 * 60_000,
  })

  const logout = useCallback(() => {
    tokenStore.set(null)
    setToken(null)
    // Drop everything cached for this user (their drafts, liked_by_me flags, ...)
    queryClient.clear()
  }, [queryClient])

  // An expired or revoked token anywhere in the app logs the user out
  useEffect(() => setUnauthorizedHandler(logout), [logout])

  const login = useCallback(
    async (username: string, password: string) => {
      const { access_token } = await authApi.login(username, password)
      tokenStore.set(access_token)
      queryClient.clear()
      setToken(access_token)
    },
    [queryClient],
  )

  const value = useMemo<AuthState>(
    () => ({
      user: token ? (me.data ?? null) : null,
      loading: token !== null && me.isPending,
      login,
      logout,
    }),
    [token, me.data, me.isPending, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
