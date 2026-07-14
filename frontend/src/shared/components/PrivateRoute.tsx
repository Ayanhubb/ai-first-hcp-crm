import { Navigate, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useAppSelector } from '@/app/hooks'
import { ROUTES } from '@/shared/constants/routes'

type GuardProps = {
  children: ReactNode
}

export function PrivateRoute({ children }: GuardProps) {
  const status = useAppSelector((s) => s.auth.status)
  const accessToken = useAppSelector((s) => s.auth.accessToken)
  const location = useLocation()

  if (status !== 'authenticated' || !accessToken) {
    return <Navigate to={ROUTES.login} replace state={{ from: location }} />
  }

  return <>{children}</>
}

export function GuestRoute({ children }: GuardProps) {
  const status = useAppSelector((s) => s.auth.status)
  const location = useLocation()
  const from = (location.state as { from?: { pathname?: string } } | null)?.from
    ?.pathname

  if (status === 'authenticated') {
    return <Navigate to={from || ROUTES.dashboard} replace />
  }

  return <>{children}</>
}
