import { Navigate, Route, Routes } from 'react-router-dom'
import { PrivateLayout } from '@/shared/components/PrivateLayout'
import { PublicLayout } from '@/shared/components/PublicLayout'
import { GuestRoute, PrivateRoute } from '@/shared/components/PrivateRoute'
import { LoginPage } from '@/features/auth/pages/LoginPage'
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage'
import { HcpSearchPage } from '@/features/hcp/pages/HcpSearchPage'
import { InteractionPage } from '@/features/interactions/pages/InteractionPage'
import { InteractionHistoryPage } from '@/features/interactions/pages/InteractionHistoryPage'
import { InteractionDetailPage } from '@/features/interactions/pages/InteractionDetailPage'
import { NotFoundPage } from '@/shared/pages/NotFoundPage'
import { ROUTES } from '@/shared/constants/routes'

export function AppRouter() {
  return (
    <Routes>
      <Route
        element={
          <GuestRoute>
            <PublicLayout />
          </GuestRoute>
        }
      >
        <Route path={ROUTES.login} element={<LoginPage />} />
      </Route>

      <Route
        element={
          <PrivateRoute>
            <PrivateLayout />
          </PrivateRoute>
        }
      >
        <Route path={ROUTES.dashboard} element={<DashboardPage />} />
        <Route path={ROUTES.hcps} element={<HcpSearchPage />} />
        <Route path="/hcps/:hcpId/interactions/new" element={<InteractionPage />} />
        <Route path={ROUTES.interactions} element={<InteractionHistoryPage />} />
        <Route path="/interactions/:id" element={<InteractionDetailPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>

      <Route path="*" element={<Navigate to={ROUTES.login} replace />} />
    </Routes>
  )
}
