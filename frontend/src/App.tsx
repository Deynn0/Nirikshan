import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
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

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30, // 30 seconds
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
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
                  <AppShell>
                    <ReviewQueuePage />
                  </AppShell>
                }
              />
              <Route
                path="/workspace/application/:id"
                element={
                  <AppShell>
                    <ApplicationDetailPage />
                  </AppShell>
                }
              />
              <Route
                path="/workspace/tools/analyse"
                element={
                  <AppShell>
                    <AnalyseDocumentView />
                  </AppShell>
                }
              />
              <Route
                path="/workspace/tools/integrity"
                element={
                  <AppShell>
                    <IntegrityView />
                  </AppShell>
                }
              />
              <Route
                path="/workspace/tools/issuer-simulator"
                element={
                  <AppShell>
                    <IssuerSimulatorView />
                  </AppShell>
                }
              />
              <Route
                path="/workspace/governance/rules"
                element={
                  <AppShell>
                    <RulesView />
                  </AppShell>
                }
              />
              <Route
                path="/workspace/governance/audit"
                element={
                  <AppShell>
                    <AuditLogView />
                  </AppShell>
                }
              />
              <Route
                path="/workspace/governance/platform"
                element={
                  <AppShell>
                    <PlatformView />
                  </AppShell>
                }
              />

              {/* Existing legacy routes for backwards compatibility */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/applicant" element={<ApplicantPage />} />
              <Route path="/officer" element={<OfficerPage />} />

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
