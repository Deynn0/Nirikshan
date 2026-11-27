import React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppShell } from '../workspace/AppShell';
import { InstitutionPortalLayout } from '../portal/InstitutionPortalLayout';
import { ApplicationDetailPage } from '../../pages/workspace/ApplicationDetailPage';
import { MyApplicationsPage } from '../../pages/portal/MyApplicationsPage';
import { NewApplicationPage } from '../../pages/portal/NewApplicationPage';
import { InstitutionWorkspacePage } from '../../pages/portal/InstitutionWorkspacePage';
import { AuthProvider } from '../../context/AuthContext';
import { ThemeProvider } from '../../context/ThemeContext';
import { isValidUsername, VALID_USERNAMES } from '../../api';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const setupSession = (role: 'officer' | 'verifier' | 'admin' | 'institution', username: string) => {
  localStorage.setItem(
    'nirikshan_session',
    JSON.stringify({
      token: `token-${username}`,
      username,
      role: role === 'institution' ? 'applicant' : 'officer',
      appRole: role,
      displayName: `${username} display`,
    })
  );
};

const renderWithContext = (ui: React.ReactElement, initialEntries = ['/']) => {
  const qc = createTestQueryClient();
  return render(
    <QueryClientProvider client={qc}>
      <ThemeProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

describe('Role-Based Access Control & Navigation', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('validates allowed usernames: officer, verifier, admin, and inst1 to inst11', () => {
    expect(isValidUsername('officer')).toBe(true);
    expect(isValidUsername('verifier')).toBe(true);
    expect(isValidUsername('admin')).toBe(true);

    for (let i = 1; i <= 11; i++) {
      expect(isValidUsername(`inst${i}`)).toBe(true);
    }

    expect(isValidUsername('invalid_user')).toBe(false);
    expect(isValidUsername('guest')).toBe(false);
    expect(isValidUsername('inst12')).toBe(false);
  });

  it('renders AppShell with full sidebar for officer and admin, but restricts audit and platform for verifier', () => {
    // 1. Officer
    setupSession('officer', 'officer');
    const { unmount: unmountOfficer } = renderWithContext(
      <AppShell>
        <div>Officer Content</div>
      </AppShell>
    );
    expect(screen.getAllByText(/Review queue/i)[0]).toBeInTheDocument();
    expect(screen.getByText(/Audit Log/i)).toBeInTheDocument();
    expect(screen.getByText(/Platform Settings/i)).toBeInTheDocument();
    expect(screen.getByText(/AICTE Scrutiny Officer/i)).toBeInTheDocument();
    unmountOfficer();

    // 2. Verifier
    setupSession('verifier', 'verifier');
    const { unmount: unmountVerifier } = renderWithContext(
      <AppShell>
        <div>Verifier Content</div>
      </AppShell>
    );
    expect(screen.getAllByText(/Review queue/i)[0]).toBeInTheDocument();
    expect(screen.getByText(/Verification Cell/i)).toBeInTheDocument();
    // Audit Log and Platform must be hidden from sidebar
    expect(screen.queryByText(/Audit Log/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Platform Settings/i)).not.toBeInTheDocument();
    unmountVerifier();
  });

  it('renders InstitutionPortalLayout with topbar only (no left sidebar) and bilingual toggle', () => {
    setupSession('institution', 'inst1');
    renderWithContext(
      <InstitutionPortalLayout>
        <div>Institution Portal Content</div>
      </InstitutionPortalLayout>
    );

    expect(screen.getByText(/निरीक्षण आवेदक संस्थान पोर्टल/i)).toBeInTheDocument();
    expect(screen.getByText(/My Applications/i)).toBeInTheDocument();
    expect(screen.getByText(/New Application/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Toggle language/i)).toBeInTheDocument();
  });

  it('shows exclusive action buttons for officer on ApplicationDetailPage', () => {
    setupSession('officer', 'officer');
    renderWithContext(<ApplicationDetailPage />);

    // Officer has all decision actions
    expect(screen.getByRole('button', { name: /Run \/ Replay Validation/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Ask why/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Evidence pack/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Rectify/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Decide \/ Record Outcome/i })).toBeInTheDocument();
  });

  it('restricts decision buttons for verifier on ApplicationDetailPage', () => {
    setupSession('verifier', 'verifier');
    renderWithContext(<ApplicationDetailPage />);

    // Verifier can validate
    expect(screen.getByRole('button', { name: /Validate Evidence/i })).toBeInTheDocument();
    expect(screen.getByText(/Verification Cell · Validation Mode/i)).toBeInTheDocument();

    // No decision buttons
    expect(screen.queryByRole('button', { name: /Ask why/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Evidence pack/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Rectify/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Decide \/ Record Outcome/i })).not.toBeInTheDocument();
  });

  it('renders MyApplicationsPage tailored to applicant institution with progress stages and active deficiencies', () => {
    setupSession('institution', 'inst1');
    renderWithContext(<MyApplicationsPage />);

    expect(screen.getByText(/Statutory Scrutiny & Approval Progress/i)).toBeInTheDocument();
    expect(screen.getByText(/Application A1/i)).toBeInTheDocument();
    expect(screen.getByText(/STAGE 01/i)).toBeInTheDocument();
    expect(screen.getByText(/STAGE 02/i)).toBeInTheDocument();
    expect(screen.getByText(/STAGE 03/i)).toBeInTheDocument();
  });

  it('renders NewApplicationPage multi-step upload wizard for institutions', () => {
    setupSession('institution', 'inst1');
    renderWithContext(<NewApplicationPage />);

    expect(screen.getByText(/New Institutional & Program Application/i)).toBeInTheDocument();
    expect(screen.getByText(/1\. College & Program/i)).toBeInTheDocument();
    expect(screen.getByText(/Continue to Land & Norms/i)).toBeInTheDocument();
  });

  it('renders InstitutionWorkspacePage for uploading missing/corrected documents and responding to deficiencies', () => {
    setupSession('institution', 'inst1');
    renderWithContext(<InstitutionWorkspacePage />, ['/portal/applications/A1']);

    expect(screen.getByText(/Officer Deficiency Queries/i)).toBeInTheDocument();
    expect(screen.getByText(/Institution Rectification Clarification/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Submit Compliance Response/i })).toBeInTheDocument();
  });
});
