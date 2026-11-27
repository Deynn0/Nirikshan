import React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LoginPage } from '../../pages/LoginPage';
import { AuthProvider } from '../../context/AuthContext';
import { ThemeProvider } from '../../context/ThemeContext';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const renderLogin = (initialEntries = ['/login']) => {
  const qc = createTestQueryClient();
  return render(
    <QueryClientProvider client={qc}>
      <ThemeProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={initialEntries}>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/workspace/queue" element={<div>Workspace Queue</div>} />
              <Route path="/applicant" element={<div>Applicant Portal</div>} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

describe('LoginPage Component', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders Pramana workspace and sign in to review headline', () => {
    renderLogin();

    expect(screen.getByText(/Pramana workspace/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Sign in to review/i })).toBeInTheDocument();
    expect(screen.getByText(/Demo accounts \(synthetic data\)/i)).toBeInTheDocument();
  });

  it('renders username and password inputs and allows typing', () => {
    renderLogin();

    const usernameInput = screen.getByPlaceholderText('officer');
    expect(usernameInput).toBeInTheDocument();
    fireEvent.change(usernameInput, { target: { value: 'officer.test' } });
    expect(usernameInput).toHaveValue('officer.test');
  });

  it('displays demo accounts for officials and institutions', async () => {
    renderLogin();

    const officerCard = await screen.findByText(/Dr. Arvind Sharma/i);
    expect(officerCard).toBeInTheDocument();
    expect(screen.getByText(/IIT Delhi/i)).toBeInTheDocument();
  });

  it('does not go blank or redirect when /api/auth/me returns default unauthenticated principal', async () => {
    localStorage.setItem(
      'nirikshan_session',
      JSON.stringify({
        token: 'stale-unauth-token',
        username: 'officer',
        role: 'officer',
      })
    );
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/auth/me')) {
        return new Response(
          JSON.stringify({
            user_id: 'usr-default-applicant',
            username: 'applicant_default',
            role: 'applicant',
            full_name: '',
            institution_id: null,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        );
      }
      return new Response(JSON.stringify({ detail: 'Not Found' }), { status: 404 });
    });

    renderLogin();

    expect(await screen.findByRole('heading', { name: /Sign in to review/i })).toBeInTheDocument();
    expect(localStorage.getItem('nirikshan_session')).toBeNull();
  });

  it('redirects authenticated officer after verifying stored token against /api/auth/me', async () => {
    localStorage.setItem(
      'nirikshan_session',
      JSON.stringify({
        token: 'valid-jwt-token',
        username: 'officer',
        role: 'officer',
        appRole: 'officer',
      })
    );
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/auth/me')) {
        return new Response(
          JSON.stringify({
            user_id: 'usr-123',
            username: 'officer',
            role: 'officer',
            full_name: 'Dr. Arvind Sharma',
            institution_id: null,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        );
      }
      return new Response(JSON.stringify({ detail: 'Not Found' }), { status: 404 });
    });

    renderLogin();

    await waitFor(() => {
      expect(screen.getByText('Workspace Queue')).toBeInTheDocument();
    });
  });

  it('ignores legacy auto-login token and renders login page cleanly', () => {
    localStorage.setItem(
      'nirikshan_session',
      JSON.stringify({
        token: 'offline-jwt-demo-token-12345',
        username: 'AICTE-Scrutiny-Officer-01',
        role: 'officer',
      })
    );

    renderLogin();

    expect(screen.getByRole('heading', { name: /Sign in to review/i })).toBeInTheDocument();
    expect(localStorage.getItem('nirikshan_session')).toBeNull();
  });
});
