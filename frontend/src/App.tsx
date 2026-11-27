import React, { Component } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LoaderCircle } from 'lucide-react';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { LandingPage } from './pages/LandingPage';
import { AppShell } from './components/workspace/AppShell';
import { ReviewQueuePage } from './pages/workspace/ReviewQueuePage';
import { ApplicationDetailPage } from './pages/workspace/ApplicationDetailPage';
import {
  AnalyseDocumentView,
  IntegrityView,
  IssuerSimulatorView,
  RulesView,
  AuditLogView,
  PlatformView,
} from './pages/workspace/ToolsAndGovernanceViews';
import { LoginPage } from './pages/LoginPage';
import { ApplicantPage } from './pages/ApplicantPage';
import { OfficerPage } from './pages/OfficerPage';
import { InstitutionPortalLayout } from './components/portal/InstitutionPortalLayout';
import { MyApplicationsPage } from './pages/portal/MyApplicationsPage';
import { NewApplicationPage } from './pages/portal/NewApplicationPage';
import { InstitutionWorkspacePage } from './pages/portal/InstitutionWorkspacePage';
import { useSession } from './auth/session';
import type { Role } from './types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30, // 30 seconds
      retry: 1,
    },
  },
});

class AppErrorBoundary extends Component<
  { children: React.ReactNode },
  { error: Error | null }
> {
  override state: { error: Error | null } = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  override render() {
    if (this.state.error) {
      return (
        <div className="grid min-h-dvh place-items-center bg-[#fbf8f5] px-6 text-center text-[#1c1622]">
          <div className="max-w-md space-y-4 rounded-2xl border border-[#ece4e5] bg-white p-6 shadow-sm">
            <h1 className="text-lg font-semibold">Something went wrong</h1>
            <p className="text-sm text-[#4a4252]">{this.state.error.message}</p>
            <button
              type="button"
              onClick={() => {
                this.setState({ error: null });
                window.location.assign('/login');
              }}
              className="rounded-xl bg-[#7428ea] px-4 py-2 text-sm font-semibold text-white hover:bg-[#5d1fc2] cursor-pointer"
            >
              Return to sign in
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

/**
 * Renders children only when the verified session confirms authentication.
 * Shows a loading indicator while an existing session check is in-flight so we
 * never flash-redirect or show a blank screen before we know the real auth state.
 */
const ProtectedRoute: React.FC<{
  children: React.ReactNode;
  allowedRoles?: Role[];
}> = ({ children, allowedRoles }) => {
  const session = useSession();
  const location = useLocation();
  if (session.isPending) {
    return (
      <div className="grid min-h-dvh place-items-center bg-canvas">
        <LoaderCircle className="size-8 animate-spin text-brand-500" aria-label="Loading…" />
      </div>
    );
  }
  const role = session.data?.user?.role;
  if (!role) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (allowedRoles && !allowedRoles.includes(role)) {
    const target = role === 'institution' ? '/portal' : '/dashboard';
    return <Navigate to={target} replace />;
  }
  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <AppErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <AuthProvider>
            <BrowserRouter>
              <Routes>
                {/* Landing Page */}
                <Route path="/" element={<LandingPage />} />

                {/* Login Page */}
                <Route path="/login" element={<LoginPage />} />

                {/* Official Scrutiny Console: officer, verifier, admin */}
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute allowedRoles={['officer', 'verifier', 'admin']}>
                      <AppShell>
                        <ReviewQueuePage />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/workspace"
                  element={<Navigate to="/dashboard" replace />}
                />
                <Route
                  path="/workspace/queue"
                  element={<Navigate to="/dashboard" replace />}
                />
                <Route
                  path="/dashboard/application/:id"
                  element={
                    <ProtectedRoute allowedRoles={['officer', 'verifier', 'admin']}>
                      <AppShell>
                        <ApplicationDetailPage />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/workspace/application/:id"
                  element={
                    <ProtectedRoute allowedRoles={['officer', 'verifier', 'admin']}>
                      <AppShell>
                        <ApplicationDetailPage />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/analyse"
                  element={
                    <ProtectedRoute allowedRoles={['officer', 'verifier', 'admin']}>
                      <AppShell>
                        <AnalyseDocumentView />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/workspace/tools/analyse"
                  element={<Navigate to="/analyse" replace />}
                />
                <Route
                  path="/integrity"
                  element={
                    <ProtectedRoute allowedRoles={['officer', 'verifier', 'admin']}>
                      <AppShell>
                        <IntegrityView />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/workspace/tools/integrity"
                  element={<Navigate to="/integrity" replace />}
                />
                <Route
                  path="/issuers"
                  element={
                    <ProtectedRoute allowedRoles={['officer', 'verifier', 'admin']}>
                      <AppShell>
                        <IssuerSimulatorView />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/workspace/tools/issuer-simulator"
                  element={<Navigate to="/issuers" replace />}
                />
                <Route
                  path="/rules"
                  element={
                    <ProtectedRoute allowedRoles={['officer', 'verifier', 'admin']}>
                      <AppShell>
                        <RulesView />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/workspace/governance/rules"
                  element={<Navigate to="/rules" replace />}
                />

                {/* Governance: Audit & Platform (Restricted from Verifiers, Allowed for Officer & Admin) */}
                <Route
                  path="/audit"
                  element={
                    <ProtectedRoute allowedRoles={['officer', 'admin']}>
                      <AppShell>
                        <AuditLogView />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/workspace/governance/audit"
                  element={<Navigate to="/audit" replace />}
                />
                <Route
                  path="/platform"
                  element={
                    <ProtectedRoute allowedRoles={['officer', 'admin']}>
                      <AppShell>
                        <PlatformView />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/workspace/governance/platform"
                  element={<Navigate to="/platform" replace />}
                />

                {/* Institutional Applicant Portal: inst1 ... inst11 (Topbar Only Layout) */}
                <Route
                  path="/portal"
                  element={
                    <ProtectedRoute allowedRoles={['institution']}>
                      <InstitutionPortalLayout>
                        <MyApplicationsPage />
                      </InstitutionPortalLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/portal/new"
                  element={
                    <ProtectedRoute allowedRoles={['institution']}>
                      <InstitutionPortalLayout>
                        <NewApplicationPage />
                      </InstitutionPortalLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/portal/applications/:id"
                  element={
                    <ProtectedRoute allowedRoles={['institution']}>
                      <InstitutionPortalLayout>
                        <InstitutionWorkspacePage />
                      </InstitutionPortalLayout>
                    </ProtectedRoute>
                  }
                />

                {/* Legacy Aliases & Redirections */}
                <Route path="/applicant" element={<Navigate to="/portal" replace />} />
                <Route path="/officer" element={<Navigate to="/dashboard" replace />} />
                <Route path="/scan" element={<Navigate to="/analyse" replace />} />

                {/* Fallback */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </BrowserRouter>
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </AppErrorBoundary>
  );
};

export default App;
