import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'
import type { Role } from '../api/types'
import { NotFoundPage } from '../pages/PlaceholderPage'
import { useAuth } from './useAuth'

/**
 * Sends logged-out visitors to the login page, then back here afterwards. This only
 * hides pages: the API checks every request itself, so it is not what keeps data safe.
 */
export function RequireAuth({ children, role }: { children: ReactNode; role?: Role }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return null
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  // Non-admins see "not found" rather than a hint that an admin area exists
  if (role && user.role !== role) return <NotFoundPage />
  return children
}
