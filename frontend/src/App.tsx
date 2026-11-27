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
import { useSession } from './auth/session';

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
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const session = useSession();
  const location = useLocation();
  if (session.isPending) {
    return (
      <div className="grid min-h-dvh place-items-center bg-canvas">
        <LoaderCircle className="size-8 animate-spin text-brand-500" aria-label="Loading…" />
      </div>
    );
  }
  return session.data?.user?.role ? (
    <>{children}</>
  ) : (
    <Navigate to="/login" replace state={{ from: location.pathname }} />
  );
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

              {/* Workspace Shell & Sub-routes */}
              <Route
                path="/workspace"
                element={<Navigate to="/workspace/queue" replace />}
              />
              <Route
                path="/workspace/queue"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <ReviewQueuePage />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/workspace/application/:id"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <ApplicationDetailPage />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/workspace/tools/analyse"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <AnalyseDocumentView />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/workspace/tools/integrity"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <IntegrityView />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/workspace/tools/issuer-simulator"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <IssuerSimulatorView />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/workspace/governance/rules"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <RulesView />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/workspace/governance/audit"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <AuditLogView />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/workspace/governance/platform"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <PlatformView />
                    </AppShell>
                  </ProtectedRoute>
                }
              />

              {/* Existing legacy routes for backwards compatibility */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/applicant" element={<ApplicantPage />} />
              <Route path="/officer" element={<OfficerPage />} />

              {/* Pramana alias routes */}
              <Route path="/scan" element={<Navigate to="/workspace/tools/analyse" replace />} />
              <Route path="/portal" element={<Navigate to="/applicant" replace />} />
              <Route path="/dashboard" element={<Navigate to="/workspace/queue" replace />} />

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
