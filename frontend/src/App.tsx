import { Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AppLayout } from '@/components/layout/AppLayout';
import { LoginPage } from '@/pages/auth/LoginPage';
import { DashboardPage } from '@/pages/dashboard/DashboardPage';
import { RemindersPage } from '@/pages/reminders/RemindersPage';
import { RequestsPage } from '@/pages/requests/RequestsPage';
import { PaymentsPage } from '@/pages/payments/PaymentsPage';
import { AssetsPage } from '@/pages/assets/AssetsPage';
import { ChallengesPage } from '@/pages/challenges/ChallengesPage';
import { WheelPage } from '@/pages/wheel/WheelPage';
import { GiftsPage } from '@/pages/gifts/GiftsPage';
import { NotificationsPage } from '@/pages/notifications/NotificationsPage';
import { AgentPage } from '@/pages/agent/AgentPage';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { useAuth } from '@/context/AuthContext';
import { LoadingState } from '@/components/common/LoadingState';

export default function App() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingState message="Checking your account..." />;
  }

  return (
    <>
      <Routes>
        <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="reminders" element={<RemindersPage />} />
            <Route path="requests" element={<RequestsPage />} />
            <Route path="payments" element={<PaymentsPage />} />
            <Route path="assets" element={<AssetsPage />} />
            <Route path="challenges" element={<ChallengesPage />} />
            <Route path="wheel" element={<WheelPage />} />
            <Route path="gifts" element={<GiftsPage />} />
            <Route path="notifications" element={<NotificationsPage />} />
            <Route path="agent" element={<AgentPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to={isAuthenticated ? '/' : '/login'} replace />} />
      </Routes>
      <Toaster position="top-right" />
    </>
  );
}
